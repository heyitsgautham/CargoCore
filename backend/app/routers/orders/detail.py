"""Single-order lifecycle: read, update, confirm, assign, transition, cancel, escalate, pay from wallet, tracking lookup and line items."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.logistics import LogisticsEscalationItem
from app.schemas.orders import (
    CancelOrderRequest,
    OrderAssignRequest,
    OrderEscalateRequest,
    OrderItemResponse,
    OrderItemUpsert,
    OrderResponse,
    OrderUpdate,
)
from app.schemas.wallet import WalletPaymentRequest, WalletPaymentResponse
from app.services import orders_service, wallet_service

router = APIRouter()


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
