from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user_models import UserProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate

_LIST_FIELDS = ("skills", "preferred_job_roles", "preferred_opportunity_types", "preferred_locations")
_STR_FIELDS = ("full_name", "experience_level", "remote_preference")


def get_profile(session: Session, user_id: str) -> UserProfile | None:
    return session.get(UserProfile, user_id)


def create_profile(session: Session, user_id: str, data: ProfileCreate) -> UserProfile:
    payload: dict[str, Any] = data.model_dump()
    profile = UserProfile(user_id=user_id, **payload)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def update_profile(session: Session, profile: UserProfile, data: ProfileUpdate) -> UserProfile:
    for field in _LIST_FIELDS + _STR_FIELDS:
        value = getattr(data, field)
        if value is not None:
            if field in _LIST_FIELDS:
                value = [item.strip() for item in value if item.strip()]
            setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


def delete_profile(session: Session, user_id: str) -> bool:
    result = session.execute(delete(UserProfile).where(UserProfile.user_id == user_id))
    session.commit()
    return result.rowcount > 0


def profile_to_response(profile: UserProfile) -> dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "skills": profile.skills or [],
        "experience_level": profile.experience_level,
        "preferred_job_roles": profile.preferred_job_roles or [],
        "preferred_opportunity_types": profile.preferred_opportunity_types or [],
        "preferred_locations": profile.preferred_locations or [],
        "remote_preference": profile.remote_preference,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def apply_create_to_model(profile: UserProfile, data: ProfileCreate) -> None:
    for field in ("full_name", "skills", "experience_level", "preferred_job_roles", "preferred_opportunity_types", "preferred_locations", "remote_preference"):
        setattr(profile, field, getattr(data, field))
