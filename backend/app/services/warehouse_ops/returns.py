"""Return grading, damage photos and the pending-grading backfill."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.logistics import LogisticsReturnCase
from app.models.warehouse import (
    ReturnGrading,
)
from app.schemas.warehouse_operations import (
    ReturnGradingCreate,
    ReturnGradingListResponse,
    ReturnGradingResponse,
    ReturnGradingUpdate,
)
from app.services.warehouse_ops.common import _get_warehouse

# ======================
# Returns / Grading Operations
# ======================

async def _backfill_pending_return_gradings(
    db: AsyncSession,
    warehouse_id: UUID,
) -> None:
    linked_cases = (
        await db.execute(
            select(LogisticsReturnCase).where(
                LogisticsReturnCase.warehouse_id == warehouse_id,
                LogisticsReturnCase.reference_code.is_not(None),
            )
        )
    ).scalars().all()
    case_by_ref = {
        case.reference_code: case for case in linked_cases if case.reference_code
    }

    photo_review_refs = [
        ref for ref, case in case_by_ref.items() if getattr(case, "flow_type", None) == "photo_review"
    ]
    removed_any = False
    if photo_review_refs:
        stray_pending_gradings = (
            await db.execute(
                select(ReturnGrading).where(
                    ReturnGrading.warehouse_id == warehouse_id,
                    ReturnGrading.status == "pending",
                    ReturnGrading.rma_code.in_(photo_review_refs),
                )
            )
        ).scalars().all()
        for grading in stray_pending_gradings:
            await db.delete(grading)
            removed_any = True

    existing_rma_codes = set(
        (
            await db.execute(
                select(ReturnGrading.rma_code).where(ReturnGrading.warehouse_id == warehouse_id)
            )
        ).scalars().all()
    )

    return_cases = [
        case for case in linked_cases
        if getattr(case, "flow_type", None) == "pickup_inspection"
        and case.status in {
            "Pending",
            "Approved",
            "Pickup Requested",
            "Pickup Approved",
            "Pickup Scheduled",
            "Collected",
            "At Warehouse",
            "Arrived at Warehouse",
        }
    ]

    created_any = False
    for case in return_cases:
        if not case.reference_code or case.reference_code in existing_rma_codes:
            continue

        item_condition = "Awaiting Pickup" if case.status == "Pickup Scheduled" else "Pending Inspection"
        db.add(
            ReturnGrading(
                warehouse_id=warehouse_id,
                order_id=case.order_id,
                rma_code=case.reference_code,
                item_condition=item_condition,
                condition_notes=case.reason,
                disposition="pending",
                status="pending",
            )
        )
        existing_rma_codes.add(case.reference_code)
        created_any = True

    if created_any or removed_any:
        await db.commit()


async def get_return_gradings(
    db: AsyncSession,
    warehouse_id: UUID,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ReturnGradingListResponse:
    """Get all return gradings for a warehouse."""
    await _get_warehouse(db, warehouse_id)

    if status_filter in (None, "pending"):
        await _backfill_pending_return_gradings(db, warehouse_id)

    query = select(ReturnGrading).where(ReturnGrading.warehouse_id == warehouse_id)

    if status_filter:
        query = query.where(ReturnGrading.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = (
        query
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .order_by(ReturnGrading.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    gradings = result.scalars().all()

    items = []
    for grading in gradings:
        order_tracking = grading.order.tracking_code if grading.order else None
        grader_name = grading.grader.name if grading.grader else None

        items.append(ReturnGradingResponse(
            id=grading.id,
            warehouse_id=grading.warehouse_id,
            order_id=grading.order_id,
            order_tracking=order_tracking,
            rma_code=grading.rma_code,
            item_condition=grading.item_condition,
            condition_notes=grading.condition_notes,
            disposition=grading.disposition,
            is_genuine=grading.is_genuine,
            recommended_outcome=grading.recommended_outcome,
            inspection_remarks=grading.inspection_remarks,
            damage_photo_url=grading.damage_photo_url,
            graded_by=grading.graded_by,
            grader_name=grader_name,
            graded_at=grading.graded_at,
            status=grading.status,
            created_at=grading.created_at,
        ))

    return ReturnGradingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    data: ReturnGradingCreate,
    graded_by: UUID | None = None,
) -> ReturnGradingResponse:
    """Create a new return grading."""
    await _get_warehouse(db, warehouse_id)

    # Check for duplicate RMA code
    result = await db.execute(
        select(ReturnGrading).where(ReturnGrading.rma_code == data.rma_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RMA code already exists"
        )

    grading = ReturnGrading(
        warehouse_id=warehouse_id,
        order_id=data.order_id,
        rma_code=data.rma_code,
        item_condition=data.item_condition,
        condition_notes=data.condition_notes,
        disposition=data.disposition,
        is_genuine=data.is_genuine,
        recommended_outcome=data.recommended_outcome,
        inspection_remarks=data.inspection_remarks,
        graded_by=graded_by,
        graded_at=datetime.now(UTC) if graded_by else None,
        status="pending",
    )
    db.add(grading)
    await db.commit()
    await db.refresh(grading)

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=None,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=None,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )


async def update_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    data: ReturnGradingUpdate,
) -> ReturnGradingResponse:
    """Update a return grading."""
    result = await db.execute(
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .where(ReturnGrading.id == grading_id, ReturnGrading.warehouse_id == warehouse_id)
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    provided_fields = data.model_fields_set
    if "item_condition" in provided_fields:
        grading.item_condition = data.item_condition
    if "condition_notes" in provided_fields:
        grading.condition_notes = data.condition_notes
    if "disposition" in provided_fields:
        grading.disposition = data.disposition
    if "is_genuine" in provided_fields:
        grading.is_genuine = data.is_genuine
    if "recommended_outcome" in provided_fields:
        grading.recommended_outcome = data.recommended_outcome
    if "inspection_remarks" in provided_fields:
        grading.inspection_remarks = data.inspection_remarks

    await db.commit()
    await db.refresh(grading)

    order_tracking = grading.order.tracking_code if grading.order else None
    grader_name = grading.grader.name if grading.grader else None

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=order_tracking,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=grader_name,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )


async def upload_damage_photo(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    file: UploadFile,
) -> str:
    """Upload a damage photo for a return grading."""
    result = await db.execute(
        select(ReturnGrading).where(
            ReturnGrading.id == grading_id,
            ReturnGrading.warehouse_id == warehouse_id,
        )
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    # For now, store base64 or you could save to disk/S3
    # This is a simplified implementation - in production use S3 or similar
    import base64
    content = await file.read()
    photo_data = base64.b64encode(content).decode('utf-8')
    photo_url = f"data:{file.content_type};base64,{photo_data}"

    grading.damage_photo_url = photo_url
    await db.commit()

    return photo_url


async def complete_return_grading(
    db: AsyncSession,
    warehouse_id: UUID,
    grading_id: UUID,
    graded_by: UUID | None = None,
) -> ReturnGradingResponse:
    """Mark a return grading as completed."""
    result = await db.execute(
        select(ReturnGrading)
        .options(selectinload(ReturnGrading.order), selectinload(ReturnGrading.grader))
        .where(ReturnGrading.id == grading_id, ReturnGrading.warehouse_id == warehouse_id)
    )
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return grading not found")

    grading.status = "completed"
    grading.graded_at = datetime.now(UTC)
    if graded_by:
        grading.graded_by = graded_by

    # Sync condition and status back to the LM's LogisticsReturnCase so the
    # Logistic Manager can see the WM's physical assessment.
    if grading.rma_code:
        return_case = (await db.execute(
            select(LogisticsReturnCase).where(LogisticsReturnCase.reference_code == grading.rma_code)
        )).scalar_one_or_none()
        if return_case:
            return_case.condition = grading.item_condition
            if getattr(return_case, "flow_type", None) == "pickup_inspection":
                return_case.status = "Physically Inspected"
            db.add(return_case)

    await db.commit()
    await db.refresh(grading)

    order_tracking = grading.order.tracking_code if grading.order else None
    grader_name = grading.grader.name if grading.grader else None

    return ReturnGradingResponse(
        id=grading.id,
        warehouse_id=grading.warehouse_id,
        order_id=grading.order_id,
        order_tracking=order_tracking,
        rma_code=grading.rma_code,
        item_condition=grading.item_condition,
        condition_notes=grading.condition_notes,
        disposition=grading.disposition,
        is_genuine=grading.is_genuine,
        recommended_outcome=grading.recommended_outcome,
        inspection_remarks=grading.inspection_remarks,
        damage_photo_url=grading.damage_photo_url,
        graded_by=grading.graded_by,
        grader_name=grader_name,
        graded_at=grading.graded_at,
        status=grading.status,
        created_at=grading.created_at,
    )
