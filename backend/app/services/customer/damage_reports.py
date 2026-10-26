"""Customer damage reports and the staff review queue behind them."""

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.logistics import LogisticsReturnCase
from app.models.order import DamageReport as DamageReportModel
from app.models.order import Order
from app.models.user import User
from app.schemas.customer import (
    CustomerDamageReport,
    CustomerDamageReportCreate,
    CustomerDamageReportsResponse,
    DamageReviewQueueItem,
    DamageReviewUpdate,
)


async def get_customer_damage_reports(db: AsyncSession, user: User) -> CustomerDamageReportsResponse:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer damage reports are only available for individual users")

    reports = (
        await db.execute(
            select(DamageReportModel).where(DamageReportModel.customer_id == user.id).order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()

    ref_codes = [r.reference_code for r in reports if r.reference_code]
    return_cases: dict = {}
    if ref_codes:
        cases = (await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code.in_(ref_codes))
        )).scalars().all()
        return_cases = {c.reference_code: c for c in cases}

    def _resolve_status(report_status: str, return_case: LogisticsReturnCase | None) -> str:
        rc_status = return_case.status if return_case else None
        if return_case and getattr(return_case, "flow_type", None) == "photo_review" and rc_status in {"Inspected", "Physically Inspected"}:
            return "Claims Reviewed"
        return rc_status or report_status

    def _resolve_flow_type(report: DamageReportModel, return_case: LogisticsReturnCase | None) -> str:
        if return_case and getattr(return_case, "flow_type", None):
            return return_case.flow_type
        if getattr(report, "flow_type", None):
            return report.flow_type
        return "photo_review"

    return CustomerDamageReportsResponse(
        reports=[
            CustomerDamageReport(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                description=report.description,
                photos=report.photos or [],
                flow_type=_resolve_flow_type(report, return_cases.get(report.reference_code)),
                status=_resolve_status(
                    report.status,
                    return_cases.get(report.reference_code),
                ),
                qr_code=report.qr_code,
                created_at=report.created_at.isoformat(),
                refund_amount=return_cases[report.reference_code].refund_amount if report.reference_code in return_cases else None,
                condition=return_cases[report.reference_code].condition if report.reference_code in return_cases else None,
            )
            for report in reports
        ]
    )


async def create_customer_damage_report(db: AsyncSession, user: User, data: CustomerDamageReportCreate) -> CustomerDamageReport:
    if user.role.name != "INDIVIDUAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer damage reports are only available for individual users")

    order_uuid: uuid.UUID | None = None
    if data.order_id:
        try:
            order_uuid = uuid.UUID(data.order_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order ID format: '{data.order_id}'. Please select a valid order.",
            ) from None

    resolution_type = data.resolution_type if data.resolution_type in {"photo_review", "pickup_inspection"} else "photo_review"

    report = DamageReportModel(
        reference_code=f"DMG-{uuid.uuid4().hex[:6].upper()}",
        customer_id=user.id,
        order_id=order_uuid,
        description=data.description,
        photos=data.photos,
        flow_type=resolution_type,
        status="reported",
        qr_code=f"QR-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(report)
    await db.flush()

    # Auto-create a LogisticsReturnCase so it appears in the
    # Logistics Manager's Reverse Logistics view immediately.
    order_total = 0.0
    warehouse_id = None
    if order_uuid:
        order_row = (await db.execute(select(Order).where(Order.id == order_uuid))).scalar_one_or_none()
        if order_row:
            order_total = order_row.total_amount or 0.0
            warehouse_id = order_row.warehouse_id

    return_case = LogisticsReturnCase(
        warehouse_id=warehouse_id,
        order_id=order_uuid,
        reference_code=report.reference_code,
        customer_name=user.name or user.email,
        reason=data.description[:255],
        flow_type=resolution_type,
        condition="Reported",
        status="Pickup Requested" if resolution_type == "pickup_inspection" else "Reported",
        original_price=order_total,
        refund_amount=0.0,
        images=data.photos or [],
    )
    db.add(return_case)

    await db.flush()

    return CustomerDamageReport(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        description=report.description,
        photos=report.photos or [],
        flow_type=resolution_type,
        status=return_case.status,
        qr_code=report.qr_code,
        created_at=report.created_at.isoformat() if report.created_at else datetime.now().isoformat(),
    )


async def get_damage_review_queue(
    db: AsyncSession,
    user: User,
    status_filter: str | None = None,
    flow_type: str | None = None,
) -> list[DamageReviewQueueItem]:
    linked_cases = (
        await db.execute(
            select(LogisticsReturnCase).order_by(LogisticsReturnCase.created_at.desc())
        )
    ).scalars().all()

    cases_by_ref = {case.reference_code: case for case in linked_cases if case.reference_code}
    reports = (
        await db.execute(
            select(DamageReportModel).order_by(DamageReportModel.created_at.desc())
        )
    ).scalars().all()

    items: list[DamageReviewQueueItem] = []
    for report in reports:
        case = cases_by_ref.get(report.reference_code)
        resolved_flow = getattr(case, "flow_type", None) or getattr(report, "flow_type", None) or "photo_review"
        resolved_status = case.status if case else "Reported"

        if flow_type and resolved_flow != flow_type:
            continue
        if status_filter and resolved_status != status_filter:
            continue

        if user.warehouse_id and case and case.warehouse_id and case.warehouse_id != user.warehouse_id:
            continue

        items.append(
            DamageReviewQueueItem(
                id=report.reference_code,
                order_id=str(report.order_id) if report.order_id else "",
                customer=case.customer_name if case else (user.name or user.email),
                description=report.description,
                images=report.photos or [],
                flow_type=resolved_flow,
                status=resolved_status,
            )
        )

    return items


async def submit_damage_review(
    db: AsyncSession,
    user: User,
    reference_code: str,
    data: DamageReviewUpdate,
) -> DamageReviewQueueItem:
    report = (
        await db.execute(
            select(DamageReportModel).where(DamageReportModel.reference_code == reference_code)
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Damage report not found")

    case = (
        await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code == reference_code)
        )
    ).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked return case not found")

    if case.flow_type != "photo_review":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Damage review is only available for photo review cases")

    case.status = data.new_status or "Claims Reviewed"
    if data.damage_severity:
        case.condition = data.damage_severity
    if data.is_genuine is not None:
        case.wm_is_genuine = data.is_genuine
    if data.recommended_settlement:
        case.wm_recommended_outcome = data.recommended_settlement
    if data.remarks:
        case.wm_inspection_remarks = data.remarks
    db.add(case)

    report.status = "reviewed"
    db.add(report)
    await db.flush()

    return DamageReviewQueueItem(
        id=report.reference_code,
        order_id=str(report.order_id) if report.order_id else "",
        customer=case.customer_name,
        description=report.description,
        images=report.photos or [],
        flow_type=case.flow_type,
        status=case.status,
    )
