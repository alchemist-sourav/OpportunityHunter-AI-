from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import ForbiddenError
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.matching import (
    MatchDetailResponse,
    MatchingRecommendationsResponse,
    MatchingRecalculateResponse,
    RecalculateRequest,
)
from app.matching.matching_service import get_matching_service

router = APIRouter(prefix="/matching", tags=["matching"])

SessionDep = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.get("/recommendations", response_model=MatchingRecommendationsResponse)
def get_recommendations(
    user: AuthenticatedUser,
    session: SessionDep,
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    opportunity_type: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote_preference: str | None = Query(default=None),
    skills: str | None = Query(default=None),
    min_salary: int | None = Query(default=None),
    max_salary: int | None = Query(default=None),
) -> MatchingRecommendationsResponse:
    """Return ranked recommendations for the authenticated user."""
    filters: dict[str, object] = {}
    if opportunity_type:
        filters["opportunity_type"] = opportunity_type
    if location:
        filters["location"] = location
    if remote_preference:
        filters["remote_preference"] = remote_preference
    if skills:
        filters["skills"] = skills
    if min_salary is not None:
        filters["min_salary"] = min_salary
    if max_salary is not None:
        filters["max_salary"] = max_salary

    matching_service = get_matching_service()
    # Fetch enough records to apply the requested offset, then return one page.
    recommendations = matching_service.get_recommendations(
        user_id=user.user_id,
        limit=limit + offset,
        min_score=min_score,
        filters=filters,
    )
    items = recommendations[offset : offset + limit]

    return MatchingRecommendationsResponse(
        total=len(recommendations),
        items=items,
        limit=limit,
        offset=offset,
    )


@router.get("/{opportunity_id}", response_model=MatchDetailResponse)
def get_opportunity_match(
    opportunity_id: str,
    user: AuthenticatedUser,
    session: SessionDep,
) -> MatchDetailResponse:
    """Return the authenticated user's match explanation for an opportunity."""
    match = get_matching_service().get_detailed_match(user.user_id, opportunity_id)
    if not match:
        from app.core.exceptions import AppException

        raise AppException("Match not found", status_code=404, error_code="match_not_found")
    return match


@router.post("/recalculate", response_model=MatchingRecalculateResponse)
def recalculate_matches(
    user: AuthenticatedUser,
    session: SessionDep,
    payload: RecalculateRequest | None = None,
) -> MatchingRecalculateResponse:
    """Recalculate matches for the authenticated user only."""
    if payload and payload.user_id and payload.user_id != user.user_id:
        raise ForbiddenError("Can only recalculate matches for your own profile")

    count = get_matching_service().recalculate_all_for_user(user.user_id)
    return MatchingRecalculateResponse(
        recalculated_count=count,
        message=f"Recalculated matches for {count} opportunities",
    )
