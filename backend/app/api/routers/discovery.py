from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import AuthUser
from app.database.engine import get_session
from app.schemas.discovery import (
    DiscoveryCancelResponse,
    DiscoveryHistoryResponse,
    DiscoveryJobResponse,
    DiscoverySearchRequest,
)
from app.services import discovery_orchestrator

router = APIRouter(prefix="/discovery", tags=["discovery"])

Session = Annotated[Session, Depends(get_session)]
AuthenticatedUser = Annotated[AuthUser, Depends(get_current_user)]


@router.post("/search", response_model=DiscoveryJobResponse, status_code=202)
def search(payload: DiscoverySearchRequest, user: AuthenticatedUser, session: Session) -> dict[str, object]:
    job = discovery_orchestrator.create_job(session, user.user_id, payload)
    return discovery_orchestrator.job_to_response(job)


@router.get("/{job_id}", response_model=DiscoveryJobResponse)
def get_discovery_job(job_id: str, user: AuthenticatedUser, session: Session) -> dict[str, object]:
    job = discovery_orchestrator.get_job(session, user.user_id, job_id)
    return discovery_orchestrator.job_to_response(job)


@router.post("/{job_id}/cancel", response_model=DiscoveryCancelResponse)
def cancel_discovery_job(job_id: str, user: AuthenticatedUser, session: Session) -> DiscoveryCancelResponse:
    job = discovery_orchestrator.cancel_job(session, user.user_id, job_id)
    return DiscoveryCancelResponse(id=job.id, status=job.status, cancelled=True)


@router.get("", response_model=DiscoveryHistoryResponse)
def discovery_history(
    user: AuthenticatedUser,
    session: Session,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    jobs, total = discovery_orchestrator.list_jobs(session, user.user_id, limit=limit, offset=offset)
    return {
        "total": total,
        "items": [
            {
                "id": job.id,
                "category": job.category,
                "keywords": job.keywords,
                "status": job.status,
                "result_count": job.result_count,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }
            for job in jobs
        ],
    }
