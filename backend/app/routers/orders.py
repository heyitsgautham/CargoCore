from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.logistics import LogisticsEscalationItem
from app.schemas.orders import (
    BatchConfirmRequest,
    CancelOrderRequest,
    ClusterResponse,
    DeliveryOtpSendResponse,
    DriverSuggestionResponse,
    OrderAssignmentPreview,
    OrderAssignRequest,
    OrderCreate,
    OrderEscalateRequest,
    OrderItemResponse,
    OrderItemUpsert,
    OrderListResponse,
    OrderResponse,
    OrderTripIntelligenceItem,
    OrderUpdate,
    ReturnTripResponse,
    TripCommandPushRequest,
    TripDeviationReportRequest,
)
from app.schemas.wallet import WalletPaymentRequest, WalletPaymentResponse
from app.services import clustering_service, orders_service, wallet_service

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.create_order(db, data, user)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None),
    search: str | None = Query(default=None),
    warehouse_substatus: str | None = Query(default=None, description="Filter by warehouse substatus (AWAITING_INBOUND, AWAITING_PICK, etc.)"),
    order_type: str | None = Query(default=None, description="Filter by order type (VENDOR, INDIVIDUAL, SERVICE_MOVE)"),
    pickup_type: str | None = Query(default=None, description="Filter by pickup type (hub, doorstep)"),
):
    return await orders_service.list_orders(
        db, user, page, page_size, status_filter, search,
        warehouse_substatus=warehouse_substatus, order_type=order_type, pickup_type=pickup_type
    )


@router.get("/assignment-preview", response_model=OrderAssignmentPreview)
async def get_assignment_preview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    warehouse_id: UUID | None = Query(default=None),
):
    return await orders_service.get_order_assignment_preview(db, warehouse_id)


@router.get("/ai-driver-suggestions", response_model=DriverSuggestionResponse)
async def get_ai_driver_suggestions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    AI-powered (Gemini 2.5 Pro) driver suggestions for every unassigned CONFIRMED order.
    Ranks available drivers by proximity, workload, and order priority.
    Falls back to nearest-neighbour distance matching if Gemini is unavailable.
    """
    from app.services import dispatch_ai_service
    suggestions = await dispatch_ai_service.suggest_drivers_for_orders(db)
    return DriverSuggestionResponse(suggestions=suggestions, total=len(suggestions))


@router.get("/return-suggestions", response_model=ReturnTripResponse)
async def get_return_trip_suggestions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Return-trip opportunities: drivers who recently completed a delivery and are
    within 8 km of a pending unassigned pickup.
    Gemini 2.5 Pro writes dispatch-quality explanations and re-ranks by urgency.
    """
    from app.services import dispatch_ai_service
    suggestions = await dispatch_ai_service.get_return_trip_suggestions(db)
    return ReturnTripResponse(suggestions=suggestions, total=len(suggestions))


@router.post("/cluster")
async def cluster_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    radius_km: float = Query(default=5.0, ge=1.0, le=50.0),
):
    from sqlalchemy import select

    from app.models.order import Order
    from app.schemas.orders import ClusterOrderItem, OrderCluster

    orders = (
        await db.execute(select(Order).where(Order.status == "CONFIRMED").order_by(Order.created_at.desc()))
    ).scalars().all()

    clusters, unbatched = await clustering_service.cluster_orders(db, list(orders), radius_km=radius_km)

    def _to_item(order):
        return ClusterOrderItem(
            id=order.id, tracking_code=order.tracking_code,
            delivery_addr=order.delivery_addr, pickup_addr=order.pickup_addr,
            cargo_type=order.cargo_type, vehicle_type=order.vehicle_type,
            total_amount=order.total_amount, scheduled_at=order.scheduled_at,
            delivery_lat=order.delivery_lat, delivery_lng=order.delivery_lng,
        )

    cluster_results = []
    for c in clusters:
        cluster_results.append(OrderCluster(
            cluster_id=c.cluster_id,
            centroid_lat=c.centroid_lat, centroid_lng=c.centroid_lng,
            orders=[_to_item(g.order) for g in c.orders],
            total_distance_km=c.total_distance_km,
            efficiency_pct=c.efficiency_pct,
            total_weight=sum(g.order.total_amount for g in c.orders),
            time_window=c.time_window,
            order_count=len(c.orders),
        ))

    avg_eff = sum(c.efficiency_pct for c in clusters) / len(clusters) if clusters else 0
    total_clustered = sum(len(c.orders) for c in clusters)
    total_orders = total_clustered + len(unbatched)
    miles_saved = avg_eff * 0.35 if clusters else 0  # rough estimate

    return ClusterResponse(
        clusters=cluster_results,
        unbatched=[_to_item(o) for o in unbatched],
        total_orders=total_orders,
        estimated_miles_saved_pct=round(miles_saved, 1),
        avg_efficiency_pct=round(avg_eff, 1),
    ).model_dump(mode="json")


@router.post("/optimize-routes")
async def optimize_routes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    optimize_for: str = "distance",
    prioritize_urgent: bool = False,
):
    return await orders_service.optimize_routes(db, optimize_for=optimize_for, prioritize_urgent=prioritize_urgent)


@router.post("/auto-balance")
async def auto_balance_drivers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Auto-balance workload across drivers by redistributing ASSIGNED orders
    from overloaded drivers to underutilized ones.
    Does NOT touch IN_TRANSIT orders (already being delivered).
    """
    return await orders_service.auto_balance_drivers(db)


@router.post("/batch-assign")
async def batch_assign_orders(
    data: BatchConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    from app.schemas.orders import OrderAssignRequest

    results = []
    for a in data.assignments:
        result = await orders_service.assign_order(
            db, a.order_id, OrderAssignRequest(driver_id=a.driver_id, vehicle_id=a.vehicle_id)
        )
        results.append(result)
    return [r.model_dump(mode="json") for r in results]


@router.get("/trip-intelligence", response_model=list[OrderTripIntelligenceItem])
async def list_trip_intelligence(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
    statuses: str = Query(default="ASSIGNED,IN_TRANSIT"),
):
    return await orders_service.list_trip_intelligence(db, statuses=statuses)


@router.get("/{order_id}/trip-intelligence", response_model=OrderTripIntelligenceItem)
async def get_trip_intelligence(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "DRIVER"))],
):
    return await orders_service.get_trip_intelligence(db, order_id, caller=user)


@router.post("/{order_id}/trip-intelligence/push", response_model=dict)
async def push_trip_command(
    order_id: UUID,
    data: TripCommandPushRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await orders_service.push_trip_command_update(db, order_id, data, caller=user)


@router.post("/{order_id}/trip-intelligence/deviation", response_model=dict)
async def report_trip_deviation(
    order_id: UUID,
    data: TripDeviationReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.report_trip_deviation(db, order_id, data, caller=user)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.get_order_detail(db, order_id, user)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await orders_service.update_order(db, order_id, user, data)


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER"))],
):
    return await orders_service.confirm_order(db, order_id, user)


@router.post("/{order_id}/assign", response_model=OrderResponse)
async def assign_order(
    order_id: UUID,
    data: OrderAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    return await orders_service.assign_order(db, order_id, data)


@router.post("/{order_id}/transition", response_model=OrderResponse)
async def transition_order(
    order_id: UUID,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER", "DRIVER"))],
):
    return await orders_service.transition_order(db, order_id, data.get("next_status", ""), caller=user)


@router.post("/{order_id}/complete-return", response_model=OrderResponse)
async def complete_return_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Driver calls this to complete a reverse-logistics (PARCEL_PICKUP) job.
    Transitions order to DELIVERED, sets warehouse_substatus=RETURN_ARRIVED,
    and auto-creates a pending ReturnGrading for the Warehouse Manager queue.
    """
    return await orders_service.complete_return_order(db, order_id, caller=user)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    await orders_service.soft_delete_order(db, order_id, user)
    await db.commit()


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    data: CancelOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await orders_service.cancel_order(db, order_id, data, user)
    await db.commit()
    return result


@router.post("/{order_id}/escalate", response_model=LogisticsEscalationItem)
async def escalate_order(
    order_id: UUID,
    data: OrderEscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "WAREHOUSE_MANAGER", "DISPATCHER"))],
):
    result = await orders_service.escalate_order(db, order_id, data, user)
    await db.commit()
    return result


@router.post("/{order_id}/wallet-pay", response_model=WalletPaymentResponse)
async def pay_order_with_wallet(
    order_id: UUID,
    data: WalletPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    from sqlalchemy import select as _select

    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    result = await wallet_service.apply_wallet_payment(
        db,
        order=order,
        user=user,
        amount=data.amount,
    )
    await db.commit()
    return result


@router.get("/track/{tracking_code}")
async def track_order(tracking_code: str, db: Annotated[AsyncSession, Depends(get_db)]):
    return await orders_service.track_order(db, tracking_code)


@router.get("/{order_id}/items", response_model=list[OrderItemResponse])
async def get_order_items(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(get_current_user)],
):
    return await orders_service.get_order_items(db, order_id)


@router.post("/{order_id}/items", response_model=list[OrderItemResponse])
async def upsert_items(
    order_id: UUID,
    items: list[OrderItemUpsert],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[object, Depends(get_current_user)],
):
    return await orders_service.upsert_order_items(db, order_id, items)


from pydantic import BaseModel, Field


class DeliveryOtpSendRequest(BaseModel):
    force_resend: bool = False


class PODRequest(BaseModel):
    otp_code: str | None = None
    image_data: str | None = None
    images_data: list[str] = []
    signature_data: str | None = None
    customer_name: str | None = None
    notes: str | None = None


@router.post("/{order_id}/delivery-otp/send", response_model=DeliveryOtpSendResponse)
async def send_delivery_otp(
    order_id: UUID,
    data: DeliveryOtpSendRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.send_delivery_otp(db, order_id, user, force_resend=data.force_resend)

@router.post("/{order_id}/proof-of-delivery", response_model=OrderResponse)
async def upload_proof_of_delivery(
    order_id: UUID,
    data: PODRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    return await orders_service.upload_proof_of_delivery(
        db,
        order_id,
        user,
        otp_code=data.otp_code,
        image_data=data.image_data,
        images_data=data.images_data,
        signature_data=data.signature_data,
        customer_name=data.customer_name,
        notes=data.notes,
    )


@router.get("/{order_id}/proof-of-delivery", response_class=HTMLResponse)
async def get_proof_of_delivery_html(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Generate and return Proof of Delivery HTML document with real data."""
    from datetime import datetime
    from pathlib import Path

    # Fetch order with POD data
    order = await orders_service.get_order_detail(db, order_id, user)

    # Debug logging
    print(f"[POD HTML] Order {order.id}")
    print(f"[POD HTML] Driver: {order.assigned_driver_name}")
    print(f"[POD HTML] Customer: {order.customer_name} / {order.customer_phone}")
    print(f"[POD HTML] Signature length: {len(order.pod_signature) if order.pod_signature else 0}")
    print(f"[POD HTML] Photos count: {len(order.pod_photos)}")
    print(f"[POD HTML] Delivered at: {order.delivered_at}")

    # Read HTML template
    template_path = Path(__file__).parent.parent.parent.parent / "html-slips" / "ProofOfDelivery.html"
    with open(template_path, encoding="utf-8") as f:
        html_content = f.read()

    # Get driver details
    driver_name = order.assigned_driver_name or "Driver"
    driver_code = f"DRV-{str(order.assigned_driver_id)[-4:]}" if order.assigned_driver_id else ""

    # Format delivery date/time
    delivery_date = "N/A"
    delivery_time = "N/A"
    delivery_dt_source = order.delivered_at or order.service_otp_verified_at or order.scheduled_at or order.created_at
    if delivery_dt_source:
        dt = datetime.fromisoformat(str(delivery_dt_source)) if isinstance(delivery_dt_source, str) else delivery_dt_source
        delivery_date = dt.strftime("%B %d, %Y")
        delivery_time = dt.strftime("%I:%M %p").upper()

    # Customer details
    customer_name = order.customer_name or "Customer"
    customer_phone = order.customer_phone or "N/A"

    # Address details - split delivery_addr
    delivery_address_parts = (order.delivery_addr or "N/A").split(",")
    delivery_address = delivery_address_parts[0].strip() if delivery_address_parts else "N/A"
    delivery_city = delivery_address_parts[1].strip() if len(delivery_address_parts) > 1 else ""
    delivery_state_zip = delivery_address_parts[2].strip() if len(delivery_address_parts) > 2 else ""

    driver_display = f"{driver_name} ({driver_code})" if driver_code else driver_name

    signature_source = order.poc_signature or order.pod_signature
    signature_html = '<div class="text-center text-gray-400 text-xs flex items-center justify-center h-full">No signature captured</div>'
    if signature_source and len(signature_source.strip()) > 0:
        sig_data = signature_source if signature_source.startswith("data:") else f"data:image/png;base64,{signature_source}"
        signature_html = f'<img src="{sig_data}" alt="Customer Signature" class="w-full h-full object-contain"/>'

    signature_box_html = (
        '<div id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2 overflow-hidden flex items-center justify-center">'
        f"{signature_html}"
        "</div>"
    )

    def _photo_slot_html(photo: str | None, slot_id: str, alt_text: str) -> str:
        if photo:
            photo_data = photo if photo.startswith("data:") else f"data:image/jpeg;base64,{photo}"
            return (
                f'<div id="{slot_id}" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2 overflow-hidden">'
                f'<img src="{photo_data}" alt="{alt_text}" class="w-full h-full object-cover"/>'
                "</div>"
            )
        return (
            f'<div id="{slot_id}" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2">'
            '<span class="text-[35px]">📷</span>'
            "</div>"
        )

    replacements = {
        "CC-12345": str(order.tracking_code) if order.tracking_code else str(order.id)[:8].upper(),
        "December 20, 2024 - 01:45 PM": f"{delivery_date} - {delivery_time}" if delivery_date != "N/A" and delivery_time != "N/A" else delivery_date,
        "December 20, 2024": delivery_date,
        "01:45 PM": delivery_time,
        "Sarah Khan | +91 98765 43210": f"{customer_name} | {customer_phone}",
        "Sarah Khan": customer_name,
        "+91 98765 43210": customer_phone,
        "Prakash Reddy (DRV-8765)": driver_display,
        "456 Maple Avenue, Indiranagar": delivery_address,
        "Bangalore, Karnataka - 560038": f"{delivery_city}, {delivery_state_zip}".strip(" ,-") if delivery_city else delivery_state_zip,
        "Name: Sarah Khan": f"Name: {customer_name}",
        '<div id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2"></div>': signature_box_html,
        '<div id="pod-p1" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(order.pod_photos[0] if order.pod_photos and len(order.pod_photos) > 0 else None, "pod-p1", "Before Unloading"),
        '<div id="pod-p2" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(order.pod_photos[1] if order.pod_photos and len(order.pod_photos) > 1 else None, "pod-p2", "Items at Location"),
        '<div id="pod-p3" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(order.pod_photos[2] if order.pod_photos and len(order.pod_photos) > 2 else None, "pod-p3", "After Placement"),
    }

    for old, new in replacements.items():
        html_content = html_content.replace(old, new)

    return html_content



class PayOrderRequest(BaseModel):
    payment_ref: str | None = None
    payment_mode: str = "ONLINE"     # ONLINE | COD | PARTIAL
    payment_method: str | None = None
    amount: float | None = None      # defaults to order.total_amount
    notes: str | None = None


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: UUID,
    data: PayOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Record a payment for an order. Online (Razorpay) or COD by driver."""
    from sqlalchemy import select as _select

    from app.models.order import Order as _Order
    from app.services import finance_service

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    amount = data.amount if (data.amount and data.amount > 0) else order.total_amount

    pmt = await finance_service.record_order_payment(
        db=db,
        order_id=order_id,
        amount=amount,
        payment_mode=data.payment_mode,
        payment_method=data.payment_method,
        payment_ref=data.payment_ref,
        collected_by_user=user if data.payment_mode.upper() == "COD" else None,
        notes=data.notes,
    )
    await db.commit()

    return {
        "payment_id": str(pmt.id),
        "payment_ref": pmt.payment_ref,
        "order_id": str(order_id),
        "amount": pmt.amount,
        "status": pmt.status,
        "payment_mode": pmt.payment_mode,
        "payment_method": pmt.payment_method,
    }


class HouseShiftSignoffRequest(BaseModel):
    signature_data: str
    customer_name: str | None = None
    notes: str | None = None


@router.post("/{order_id}/house-shift-signoff", response_model=OrderResponse)
async def house_shift_signoff(
    order_id: UUID,
    data: HouseShiftSignoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Complete a house-shift job with customer sign-off signature (no OTP required)."""
    return await orders_service.house_shift_signoff(
        db,
        order_id,
        user,
        signature_data=data.signature_data,
        customer_name=data.customer_name,
        notes=data.notes,
    )


class JobRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None


@router.post("/{order_id}/job-rating", response_model=OrderResponse)
async def submit_job_rating(
    order_id: UUID,
    data: JobRatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Submit driver's self-rating (1–5 stars) and optional feedback for a completed job."""
    return await orders_service.submit_job_rating(
        db,
        order_id,
        user,
        rating=data.rating,
        feedback=data.feedback,
    )


class CustomerRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None


@router.post("/{order_id}/customer-rating", response_model=OrderResponse)
async def submit_customer_rating(
    order_id: UUID,
    data: CustomerRatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Submit customer/vendor rating (1–5 stars) of the driver for a completed order."""
    return await orders_service.submit_customer_rating(
        db,
        order_id,
        user,
        rating=data.rating,
        feedback=data.feedback,
    )


class PackingReturnItem(BaseModel):
    name: str
    sku: str | None = None
    count: int = 0


class PackingReturnRequest(BaseModel):
    items: list[PackingReturnItem]
    notes: str | None = None
    submitted_at: str | None = None
    skipped: bool = False


@router.post("/{order_id}/packing-return", response_model=OrderResponse)
async def submit_packing_return(
    order_id: UUID,
    data: PackingReturnRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
):
    """Driver submits how many packing assets they are returning to warehouse."""
    from sqlalchemy import select as _select

    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    order.packing_return_data = {
        "items": [{"name": i.name, "sku": i.sku, "count": i.count} for i in data.items],
        "notes": data.notes or "",
        "submitted_at": data.submitted_at,
        "submitted_by": str(user.id),
        "skipped": data.skipped,
    }
    await db.commit()
    await db.refresh(order)
    return await orders_service.get_order_detail(db, order_id, user)


class AssetLogItem(BaseModel):
    name: str
    sku: str | None = None
    sent_out: int = 0
    returned: int = 0


class AssetLogRequest(BaseModel):
    items: list[AssetLogItem]
    notes: str | None = None


@router.post("/{order_id}/asset-log")
async def save_asset_log(
    order_id: UUID,
    data: AssetLogRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("LOGISTIC_MANAGER", "DISPATCHER"))],
):
    """
    Dispatcher saves the packing asset return log for an order.
    For each item with returned > 0, creates an RETURN inventory movement
    to add the items back into warehouse stock.
    """
    from fastapi import HTTPException
    from sqlalchemy import select as _select

    from app.models.inventory import InventoryItem, InventoryMovement
    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    warehouse_id = order.warehouse_id
    restored_count = 0

    for item in data.items:
        if item.returned <= 0:
            continue

        inv_item = None

        # 1. Try exact SKU match first
        if item.sku:
            inv_item = (await db.execute(
                _select(InventoryItem).where(
                    InventoryItem.warehouse_id == warehouse_id,
                    InventoryItem.sku == item.sku,
                )
            )).scalar_one_or_none()

        # 2. Fall back to name-based match
        if inv_item is None and item.name:
            name_lower = item.name.lower()
            all_inv = (await db.execute(
                _select(InventoryItem).where(InventoryItem.warehouse_id == warehouse_id)
            )).scalars().all()
            for candidate in all_inv:
                candidate_text = ((candidate.name or "") + " " + (candidate.category or "")).lower()
                if any(word in candidate_text for word in name_lower.split() if len(word) > 3):
                    inv_item = candidate
                    break

        if inv_item is None:
            continue

        # Idempotency: skip if a RETURN movement already exists for this item + order
        existing = (await db.execute(
            _select(InventoryMovement).where(
                InventoryMovement.item_id == inv_item.id,
                InventoryMovement.reference_order_id == order_id,
                InventoryMovement.movement_type == "RETURN",
            ).limit(1)
        )).scalar_one_or_none()

        if existing:
            # Update quantity if the log is being revised
            existing.quantity = item.returned
            inv_item.quantity_on_hand = max(0, inv_item.quantity_on_hand - existing.quantity + item.returned)
        else:
            movement = InventoryMovement(
                item_id=inv_item.id,
                movement_type="RETURN",
                quantity=item.returned,
                reference_order_id=order_id,
                performed_by=user.id,
            )
            db.add(movement)
            inv_item.quantity_on_hand += item.returned

        restored_count += 1

    await db.commit()
    return {
        "order_id": str(order_id),
        "items_restored": restored_count,
        "message": f"Asset log saved. {restored_count} item type(s) restored to inventory.",
    }


@router.post("/{order_id}/simulate-arrival", response_model=dict)
async def simulate_driver_arrival(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Dev/demo endpoint: simulate the assigned driver arriving within 50 m of the
    pickup address.  Updates the driver's current_location so the live tracking
    map shows the truck near the pickup pin and the geofence alert fires on the
    customer's screen.
    """
    import random

    from fastapi import HTTPException
    from sqlalchemy import select as _select

    from app.models.logistics import LogisticsDriverProfile
    from app.models.order import Order as _Order

    order = (await db.execute(_select(_Order).where(_Order.id == order_id))).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the customer who owns the order (or staff) may call this
    if str(order.customer_id) != str(user.id) and user.role not in {
        "LOGISTIC_MANAGER", "DISPATCHER", "WAREHOUSE_MANAGER", "ADMIN"
    }:
        raise HTTPException(status_code=403, detail="Not authorised")

    if not order.assigned_driver_id:
        raise HTTPException(status_code=400, detail="No driver assigned to this order yet")

    lat = order.pickup_lat
    lng = order.pickup_lng
    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Pickup coordinates not available for this order")

    # Offset by ~30–50 m (≈0.00027°–0.00045°) so it looks natural
    offset_deg = 0.0003
    sim_lat = round(lat + random.uniform(-offset_deg, offset_deg), 6)
    sim_lng = round(lng + random.uniform(-offset_deg, offset_deg), 6)

    profile = (
        await db.execute(
            _select(LogisticsDriverProfile).where(
                LogisticsDriverProfile.user_id == order.assigned_driver_id
            )
        )
    ).scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    profile.current_location = f"{sim_lat},{sim_lng}"
    await db.commit()

    return {
        "order_id": str(order_id),
        "driver_id": str(order.assigned_driver_id),
        "simulated_lat": sim_lat,
        "simulated_lng": sim_lng,
        "message": "Driver location updated to within 50 m of pickup. Geofence alert will fire.",
    }
