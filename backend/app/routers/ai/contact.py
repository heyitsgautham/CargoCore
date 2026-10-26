"""Public contact form submissions and the staff inbox behind them."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.routers.ai.access import SUPPORT_ROLES
from app.schemas.ai import (
    ContactSubmissionCreatePublic,
    ContactSubmissionListResponse,
    ContactSubmissionReplyRequest,
    ContactSubmissionResponse,
    ContactSubmissionUpdate,
)
from app.services import ai_support_service

router = APIRouter()


@router.post(
    "/contact-submissions/public",
    response_model=ContactSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a public contact form",
    description="Public website contact form endpoint used by the Contact page.",
)
async def create_public_contact_submission(
    data: ContactSubmissionCreatePublic,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ai_support_service.create_public_contact_submission(db=db, data=data)


@router.get(
    "/contact-submissions",
    response_model=ContactSubmissionListResponse,
    summary="List support contact submissions",
)
async def list_contact_submissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.list_contact_submissions(db=db)


@router.put(
    "/contact-submissions/{submission_id}",
    response_model=ContactSubmissionResponse,
    summary="Update a support contact submission",
)
async def update_contact_submission(
    submission_id: UUID,
    data: ContactSubmissionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.update_contact_submission(
        db=db,
        submission_id=submission_id,
        data=data,
    )


@router.post(
    "/contact-submissions/{submission_id}/reply",
    response_model=ContactSubmissionResponse,
    summary="Reply to a support contact submission by email",
)
async def reply_to_contact_submission(
    submission_id: UUID,
    data: ContactSubmissionReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    return await ai_support_service.reply_to_contact_submission(
        db=db,
        submission_id=submission_id,
        data=data,
        actor=user,
    )


@router.delete(
    "/contact-submissions/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a support contact submission",
)
async def delete_contact_submission(
    submission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role(*SUPPORT_ROLES))],
):
    await ai_support_service.delete_contact_submission(db=db, submission_id=submission_id)
