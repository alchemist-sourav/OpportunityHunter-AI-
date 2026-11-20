from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import ProfileNotFoundError
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])

Session = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.get("", response_model=ProfileResponse)
def get_profile(user: AuthenticatedUser, session: Session) -> ProfileResponse:
    profile = profile_service.get_profile(session, user.user_id)
    if profile is None:
        raise ProfileNotFoundError()
    return ProfileResponse(**profile_service.profile_to_response(profile))


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(payload: ProfileCreate, user: AuthenticatedUser, session: Session) -> ProfileResponse:
    existing = profile_service.get_profile(session, user.user_id)
    if existing is not None:
        profile_service.apply_create_to_model(existing, payload)
        session.commit()
        session.refresh(existing)
        return ProfileResponse(**profile_service.profile_to_response(existing))
    profile = profile_service.create_profile(session, user.user_id, payload)
    return ProfileResponse(**profile_service.profile_to_response(profile))


@router.patch("", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdate, user: AuthenticatedUser, session: Session) -> ProfileResponse:
    profile = profile_service.get_profile(session, user.user_id)
    if profile is None:
        raise ProfileNotFoundError()
    updated = profile_service.update_profile(session, profile, payload)
    return ProfileResponse(**profile_service.profile_to_response(updated))


@router.delete("", status_code=204)
def delete_profile(user: AuthenticatedUser, session: Session) -> None:
    profile_service.delete_profile(session, user.user_id)
