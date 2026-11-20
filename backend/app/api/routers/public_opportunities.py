from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.database.engine import get_session
from app.models.opportunity_models import Opportunity
from app.schemas.opportunity import OpportunityListItem, OpportunityListResponse

router = APIRouter(prefix="/public", tags=["public_opportunities"])

# Simple in-memory rate limiter
_rate_limiter = {}
_RATE_LIMIT = 100  # requests per minute
_RATE_WINDOW = 60  # seconds


def _check_rate_limit(client_ip: str) -> None:
    """Check rate limit for client IP. Raises 429 if exceeded."""
    now = __import__("time").time()
    
    if client_ip not in _rate_limiter:
        _rate_limiter[client_ip] = []
    
    # Remove timestamps outside the window
    _rate_limiter[client_ip] = [t for t in _rate_limiter[client_ip] if now - t < _RATE_WINDOW]
    
    if len(_rate_limiter[client_ip]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 100 requests per minute.",
        )
    
    _rate_limiter[client_ip].append(now)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxy headers."""
    # Check for forwarded headers (common in production deployments)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Apply rate limiting as a dependency
def rate_limit_dependency(request: Request):
    """FastAPI dependency that checks rate limit."""
    client_ip = get_client_ip(request)
    _check_rate_limit(client_ip)
    return client_ip


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/opportunities", response_model=OpportunityListResponse)
def public_list_opportunities(
    session: SessionDep,
    request: Request,
    category: str | None = Query(
        default=None,
        description="Filter by opportunity type (internship, full_time_job, fresher_job, freelance_project)",
    ),
    verification_status: str | None = Query(
        default=None,
        description="Filter by verification status (active, unverified, expired, closed, inaccessible, uncertain)",
    ),
    location: str | None = Query(
        default=None, description="Filter by location (city, state, or country)"
    ),
    remote_preference: str | None = Query(
        default=None,
        description="Filter by remote preference (remote_only, hybrid, onsite_only, no_preference)",
    ),
    experience_level: str | None = Query(
        default=None,
        description="Filter by experience level (student, fresher, junior, experienced)",
    ),
    skills: str | None = Query(
        default=None,
        description="Comma-separated skills to match against required skills",
    ),
    search: str | None = Query(
        default=None, description="Search in title, company name, or description"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Page offset for pagination"),
) -> OpportunityListResponse:
    """
    Public endpoint for browsing opportunities.
    No authentication required. Only returns is_public=true opportunities.
    All filters are optional and can be combined.
    """

    # Rate limiting - check client IP
    client_ip = get_client_ip(request)
    _check_rate_limit(client_ip)

    # Base query: only public opportunities
    stmt = select(Opportunity).where(Opportunity.is_public == True)
    count_stmt = select(func.count()).select_from(Opportunity).where(Opportunity.is_public == True)

    # Apply filters
    if category:
        try:
            from app.models.opportunity_models import OpportunityType
            category_enum = OpportunityType(category)
            stmt = stmt.where(Opportunity.opportunity_type == category_enum)
            count_stmt = count_stmt.where(Opportunity.opportunity_type == category_enum)
        except ValueError:
            pass  # Invalid category value, skip filter

    if verification_status:
        from app.models.opportunity_models import VerificationStatus
        try:
            vs_enum = VerificationStatus(verification_status)
            stmt = stmt.where(Opportunity.verification_status == vs_enum)
            count_stmt = count_stmt.where(Opportunity.verification_status == vs_enum)
        except ValueError:
            pass

    if location:
        stmt = stmt.where(Opportunity.location.ilike(f"%{location}%"))
        count_stmt = count_stmt.where(Opportunity.location.ilike(f"%{location}%"))

    if remote_preference:
        from app.schemas.enums import RemotePreference
        try:
            rp_enum = RemotePreference(remote_preference)
            stmt = stmt.where(Opportunity.remote_preference == rp_enum)
            count_stmt = count_stmt.where(Opportunity.remote_preference == rp_enum)
        except ValueError:
            pass

    if experience_level:
        from app.schemas.enums import ExperienceLevel
        try:
            el_enum = ExperienceLevel(experience_level)
            stmt = stmt.where(Opportunity.experience_level == el_enum)
            count_stmt = count_stmt.where(Opportunity.experience_level == el_enum)
        except ValueError:
            pass

    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        for skill in skill_list:
            stmt = stmt.where(Opportunity.required_skills.contains([skill]))
            # Also add to count stmt for consistency
            count_stmt = count_stmt.where(Opportunity.required_skills.contains([skill]))

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            Opportunity.title.ilike(search_term)
            | Opportunity.company_name.ilike(search_term)
            | Opportunity.description.ilike(search_term)
        )
        count_stmt = count_stmt.where(
            Opportunity.title.ilike(search_term)
            | Opportunity.company_name.ilike(search_term)
            | Opportunity.description.ilike(search_term)
        )

    # Get total count before pagination
    total = session.scalar(count_stmt) or 0

    # Apply ordering and pagination
    stmt = stmt.order_by(desc(Opportunity.created_at)).limit(limit).offset(offset)
    opportunities = session.scalars(stmt).all()

    # Build response items - only expose safe fields
    items = [
        OpportunityListItem(
            id=opp.id,
            title=opp.title,
            company_name=opp.company_name,
            opportunity_type=opp.opportunity_type,
            location=opp.location,
            remote_preference=opp.remote_preference,
            salary_min=opp.salary_min,
            salary_max=opp.salary_max,
            salary_currency=opp.salary_currency,
            verification_status=opp.verification_status,
            source_domain=opp.source_domain,
            created_at=opp.created_at,
        )
        for opp in opportunities
    ]

    return OpportunityListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityListItem)
def public_get_opportunity(
    session: SessionDep,
    request: Request,
    opportunity_id: str,
) -> OpportunityListItem:
    """
    Public endpoint for getting a single opportunity detail.
    Only returns is_public=true opportunities.
    """

    # Rate limiting
    client_ip = get_client_ip(request)
    _check_rate_limit(client_ip)

    stmt = select(Opportunity).where(
        Opportunity.id == opportunity_id, Opportunity.is_public == True
    )
    opportunity = session.scalar(stmt)

    if not opportunity:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404, detail="Opportunity not found or not publicly accessible"
        )

    # Only expose safe fields for public display
    return OpportunityListItem(
        id=opportunity.id,
        title=opportunity.title,
        company_name=opportunity.company_name,
        opportunity_type=opportunity.opportunity_type,
        location=opportunity.location,
        remote_preference=opportunity.remote_preference,
        salary_min=opportunity.salary_min,
        salary_max=opportunity.salary_max,
        salary_currency=opportunity.salary_currency,
        verification_status=opportunity.verification_status,
        source_domain=opportunity.source_domain,
        created_at=opportunity.created_at,
    )