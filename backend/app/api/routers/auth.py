from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.core.security import AuthUser
from app.schemas.auth import CurrentUserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserResponse)
def me(user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(**user.to_dict())
