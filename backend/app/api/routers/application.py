from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListItem,
    ApplicationListResponse,
    ApplicationStatus,
)
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])

Session = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.post("", response_model=ApplicationResponse, status_code=201)
def create_application(
    payload: ApplicationCreate,
    user: AuthenticatedUser,
    session: Session,
) -> ApplicationResponse:
    """Save an opportunity to a user's application tracker."""
    application = application_service.save_opportunity(
        session=session,
        user_id=user.user_id,
        opportunity_id=payload.opportunity_id,
        status=payload.status,
        notes=payload.notes,
        deadline=payload.deadline,
    )
    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        opportunity_id=application.opportunity_id,
        status=application.status,
        applied_date=application.applied_date,
        deadline=application.deadline,
        notes=application.notes,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    user: AuthenticatedUser,
    session: Session,
    status: str | None = Query(default=None, description="Filter by application status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApplicationListResponse:
    """List applications for the authenticated user with pagination and filters."""
    result = application_service.get_user_applications(
        session=session,
        user_id=user.user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return ApplicationListResponse(
        total=result["total"],
        items=[
            ApplicationListItem(
                id=item.id,
                opportunity_id=item.opportunity_id,
                status=item.status,
                applied_date=item.applied_date,
                deadline=item.deadline,
                notes=item.notes,
                created_at=item.created_at,
            )
            for item in result["items"]
        ],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: str,
    user: AuthenticatedUser,
    session: Session,
) -> ApplicationResponse:
    """Get a specific application, ensuring the user owns it."""
    application = application_service.get_application(
        session=session,
        user_id=user.user_id,
        application_id=application_id,
    )
    if not application:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        opportunity_id=application.opportunity_id,
        status=application.status,
        applied_date=application.applied_date,
        deadline=application.deadline,
        notes=application.notes,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    user: AuthenticatedUser,
    session: Session,
) -> ApplicationResponse:
    """Update an application status and/or notes."""
    application = application_service.update_application(
        session=session,
        user_id=user.user_id,
        application_id=application_id,
        status=payload.status,
        notes=payload.notes,
        deadline=payload.deadline,
    )
    if not application:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationResponse(
        id=application.id,
        user_id=application.user_id,
        opportunity_id=application.opportunity_id,
        status=application.status,
        applied_date=application.applied_date,
        deadline=application.deadline,
        notes=application.notes,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: str,
    user: AuthenticatedUser,
    session: Session,
) -> None:
    """Delete an application from the tracker."""
    success = application_service.delete_application(
        session=session,
        user_id=user.user_id,
        application_id=application_id,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Application not found")