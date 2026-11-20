from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.opportunity import (
    OpportunityExtractRequest,
    OpportunityExtractResponse,
    OpportunityListResponse,
    OpportunityListItem,
    OpportunityResponse,
    OpportunitySourceResponse,
    OpportunitySourcesResponse,
    OpportunityVerifyRequest,
    OpportunityVerifyResponse,
)
from app.services import extraction_orchestrator

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

Session = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.patch("/{opportunity_id}/publish", response_model=OpportunityListItem)
def toggle_opportunity_public(
    opportunity_id: str,
    user: AuthenticatedUser,
    session: Session,
    is_public: bool = Body(..., description="Set is_public status for the opportunity"),
) -> OpportunityListItem:
    """Toggle whether an opportunity is publicly visible."""
    from app.models.opportunity_models import Opportunity

    opportunity = session.get(Opportunity, opportunity_id)
    if not opportunity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Check user ownership via opportunity sources
    has_access = session.scalar(
        select(OpportunitySource).where(
            OpportunitySource.opportunity_id == opportunity_id,
            OpportunitySource.user_id == user.user_id,
        )
    )
    if not has_access:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this opportunity"
        )

    opportunity.is_public = is_public
    session.add(opportunity)
    session.flush()

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


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    user: AuthenticatedUser,
    session: Session,
    category: str | None = Query(default=None, description="Filter by opportunity type"),
    verification_status: str | None = Query(default=None, description="Filter by verification status"),
    source_domain: str | None = Query(default=None, description="Filter by source domain"),
    location: str | None = Query(default=None, description="Filter by location"),
    remote_preference: str | None = Query(default=None, description="Filter by remote preference"),
    skills: str | None = Query(default=None, description="Comma-separated skills to filter"),
    search: str | None = Query(default=None, description="Search in title, company, description"),
    is_public: bool | None = Query(default=None, description="Filter public/private"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    stmt = select(OpportunityListItem.__annotations__['id'].comparator).select_from(OpportunityListItem)
    from app.models.opportunity_models import Opportunity

    stmt = select(Opportunity).options(selectinload(Opportunity.sources))

    if category:
        stmt = stmt.where(Opportunity.opportunity_type == category)
    if verification_status:
        stmt = stmt.where(Opportunity.verification_status == verification_status)
    if source_domain:
        stmt = stmt.where(Opportunity.source_domain == source_domain)
    if location:
        stmt = stmt.where(Opportunity.location.ilike(f"%{location}%"))
    if remote_preference:
        stmt = stmt.where(Opportunity.remote_preference == remote_preference)
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        for skill in skill_list:
            stmt = stmt.where(Opportunity.required_skills.contains([skill]))
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            Opportunity.title.ilike(search_term) |
            Opportunity.company_name.ilike(search_term) |
            Opportunity.description.ilike(search_term)
        )
    if is_public is not None:
        stmt = stmt.where(Opportunity.is_public == is_public)

    total = session.scalar(select(func.count()).select_from(Opportunity).where(stmt.whereclause if stmt.whereclause is not None else True)) or 0

    stmt = stmt.order_by(desc(Opportunity.created_at)).limit(limit).offset(offset)
    opportunities = session.scalars(stmt).all()

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

    return {
        "total": total,
        "items": items,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: str,
    user: AuthenticatedUser,
    session: Session,
) -> OpportunityResponse:
    from app.models.opportunity_models import Opportunity
    stmt = select(Opportunity).options(selectinload(Opportunity.sources)).where(Opportunity.id == opportunity_id)
    opportunity = session.scalar(stmt)
    if not opportunity:
        from app.core.exceptions import AppException
        raise AppException("Opportunity not found", status_code=404, error_code="opportunity_not_found")

    if not opportunity.is_public:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Access denied")

    return OpportunityResponse.from_attributes(opportunity)


@router.post("/extract/{job_id}", response_model=OpportunityExtractResponse)
def extract_from_discovery_job(
    job_id: str,
    payload: OpportunityExtractRequest,
    user: AuthenticatedUser,
    session: Session,
) -> OpportunityExtractResponse:
    result = extraction_orchestrator.extract_from_job(
        job_id=job_id,
        user_id=user.user_id,
        result_indices=payload.result_indices,
    )
    return OpportunityExtractResponse(
        created=result.get("created", []),
        updated=result.get("updated", []),
        skipped=result.get("skipped", []),
        errors=result.get("errors", []),
    )


@router.post("/{opportunity_id}/verify", response_model=OpportunityVerifyResponse)
async def verify_opportunity(
    opportunity_id: str,
    user: AuthenticatedUser,
    session: Session,
) -> OpportunityVerifyResponse:
    from app.services import extraction_orchestrator as eo
    from app.models.opportunity_models import Opportunity

    opportunity = session.get(Opportunity, opportunity_id)
    if not opportunity:
        from app.core.exceptions import AppException
        raise AppException("Opportunity not found", status_code=404, error_code="opportunity_not_found")

    if not opportunity.is_public:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Access denied")

    verified_opp = await eo.VerificationOrchestrator(session_factory=lambda: session).verify_opportunity(opportunity_id)
    if verified_opp:
        return OpportunityVerifyResponse(
            verified={opportunity_id: verified_opp.verification_status.value},
            errors=[],
        )
    else:
        return OpportunityVerifyResponse(
            verified={},
            errors=["Verification failed"],
        )


@router.post("/verify/batch", response_model=OpportunityVerifyResponse)
async def batch_verify_opportunities(
    payload: OpportunityVerifyRequest,
    user: AuthenticatedUser,
    session: Session,
) -> OpportunityVerifyResponse:
    from app.services import extraction_orchestrator as eo

    opp_ids = payload.opportunity_ids
    if not opp_ids:
        from app.models.opportunity_models import Opportunity
        stmt = select(Opportunity.id).where(Opportunity.verification_status == "unverified").limit(50)
        opp_ids = [str(row[0]) for row in session.execute(stmt).all()]

    verified = await eo.VerificationOrchestrator(session_factory=lambda: session).batch_verify(opp_ids)
    return OpportunityVerifyResponse(
        verified={k: v.value for k, v in verified.items()},
        errors=[],
    )


@router.get("/{opportunity_id}/sources", response_model=OpportunitySourcesResponse)
def get_opportunity_sources(
    opportunity_id: str,
    user: AuthenticatedUser,
    session: Session,
) -> OpportunitySourcesResponse:
    from app.models.opportunity_models import Opportunity, OpportunitySource

    opportunity = session.get(Opportunity, opportunity_id)
    if not opportunity:
        from app.core.exceptions import AppException
        raise AppException("Opportunity not found", status_code=404, error_code="opportunity_not_found")

    if not opportunity.is_public:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Access denied")

    sources = session.scalars(
        select(OpportunitySource).where(OpportunitySource.opportunity_id == opportunity_id)
    ).all()

    return OpportunitySourcesResponse(
        opportunity_id=opportunity_id,
        sources=[OpportunitySourceResponse.from_attributes(s) for s in sources],
    )