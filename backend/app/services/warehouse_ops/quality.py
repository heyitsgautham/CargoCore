"""Quality checks before dispatch."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.warehouse import (
    QualityCheck,
)
from app.schemas.warehouse_operations import (
    QualityCheckListResponse,
    QualityCheckResponse,
    QualityCheckUpdate,
)
from app.services.warehouse_ops.common import (
    _get_order,
    _get_warehouse,
    _to_quality_check_response,
    _validate_substatus_transition,
)

# ======================
# Quality Check Operations
# ======================

async def create_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Create a new quality check record for an order."""
    await _get_warehouse(db, warehouse_id)
    order = await _get_order(db, order_id)

    if order.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to this warehouse"
        )

    # Check if QC already exists
    result = await db.execute(
        select(QualityCheck).where(QualityCheck.order_id == order_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Quality check already exists for this order"
        )

    qc = QualityCheck(
        order_id=order_id,
        warehouse_id=warehouse_id,
        performed_by=performed_by,
    )
    db.add(qc)
    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)


async def list_quality_checks(
    db: AsyncSession,
    warehouse_id: UUID,
    order_id: UUID | None = None,
) -> QualityCheckListResponse:
    """List quality checks for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    query = (
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.warehouse_id == warehouse_id)
        .order_by(QualityCheck.created_at.desc())
    )

    if order_id:
        query = query.where(QualityCheck.order_id == order_id)

    checks = (await db.execute(query)).scalars().all()
    return QualityCheckListResponse(
        items=[_to_quality_check_response(check) for check in checks],
        total=len(checks),
    )


async def get_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
) -> QualityCheckResponse:
    """Get a quality check by ID."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")
    return _to_quality_check_response(qc)


async def update_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
    data: QualityCheckUpdate,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Update a quality check."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")

    if data.goods_correct is not None:
        qc.goods_correct = data.goods_correct
    if data.count_correct is not None:
        qc.count_correct = data.count_correct
    if data.packaging_verified is not None:
        qc.packaging_verified = data.packaging_verified
    if data.labor_assigned is not None:
        qc.labor_assigned = data.labor_assigned
    if data.weight_verified is not None:
        qc.weight_verified = data.weight_verified
    if data.label_attached is not None:
        qc.label_attached = data.label_attached
    if data.notes is not None:
        qc.notes = data.notes

    if performed_by:
        qc.performed_by = performed_by

    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)


async def pass_quality_check(
    db: AsyncSession,
    warehouse_id: UUID,
    check_id: UUID,
    performed_by: UUID | None = None,
) -> QualityCheckResponse:
    """Mark a quality check as passed and advance order substatus."""
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer), selectinload(QualityCheck.order))
        .where(QualityCheck.id == check_id, QualityCheck.warehouse_id == warehouse_id)
    )
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality check not found")

    # Validate all checks are complete
    if not all([
        qc.goods_correct,
        qc.count_correct,
        qc.packaging_verified,
        qc.labor_assigned,
        qc.weight_verified,
        qc.label_attached,
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All quality check items must be verified before passing"
        )

    # Validate order substatus transition
    order = qc.order
    _validate_substatus_transition(order.warehouse_substatus, "QC_PASSED")

    qc.is_passed = True
    qc.checked_at = datetime.now(UTC)
    if performed_by:
        qc.performed_by = performed_by

    order.warehouse_substatus = "QC_PASSED"

    await db.commit()
    result = await db.execute(
        select(QualityCheck)
        .options(selectinload(QualityCheck.performer))
        .where(QualityCheck.id == qc.id)
    )
    qc = result.scalar_one()
    return _to_quality_check_response(qc)
