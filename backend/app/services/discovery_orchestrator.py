from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    DiscoveryCancellationNotAllowedError,
    DiscoveryConcurrencyLimitError,
    DiscoveryJobNotFoundError,
    DiscoveryQuotaExceededError,
)
from app.models.discovery_models import DiscoveryJob
from app.schemas.discovery import DiscoverySearchRequest
from app.scrapers.discovery_service import run_discovery_job

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("pending", "running")


def job_to_response(job: DiscoveryJob) -> dict[str, object]:
    return {
        "id": job.id,
        "user_id": job.user_id,
        "category": job.category,
        "keywords": job.keywords,
        "skills": job.skills or [],
        "locations": job.locations or [],
        "remote_preference": job.remote_preference,
        "experience_level": job.experience_level,
        "max_results": job.max_results,
        "source_domains": job.source_domains or [],
        "status": job.status,
        "cancel_requested": job.cancel_requested,
        "total_pages": job.total_pages,
        "completed_pages": job.completed_pages,
        "result_count": job.result_count,
        "credits_used": job.credits_used,
        "error_message": job.error_message,
        "results": job.results or [],
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
    }


def _count_active(session: Session, user_id: str) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(DiscoveryJob).where(
                DiscoveryJob.user_id == user_id,
                DiscoveryJob.status.in_(ACTIVE_STATUSES),
            )
        )
        or 0
    )


def _count_created_today(session: Session, user_id: str) -> int:
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        session.scalar(
            select(func.count()).select_from(DiscoveryJob).where(
                DiscoveryJob.user_id == user_id,
                DiscoveryJob.created_at >= start_of_day,
            )
        )
        or 0
    )


def launch_background_job(job_id: str) -> None:
    thread = threading.Thread(target=run_discovery_job, kwargs={"job_id": job_id}, daemon=True)
    thread.start()


def create_job(session: Session, user_id: str, request: DiscoverySearchRequest) -> DiscoveryJob:
    settings = get_settings()
    if _count_active(session, user_id) >= settings.discovery_max_concurrent_jobs:
        raise DiscoveryConcurrencyLimitError()
    if _count_created_today(session, user_id) >= settings.discovery_daily_quota:
        raise DiscoveryQuotaExceededError()

    job = DiscoveryJob(
        id=str(uuid.uuid4()),
        user_id=user_id,
        category=request.category.value,
        keywords=request.keywords,
        skills=request.skills,
        locations=request.locations,
        remote_preference=request.remote_preference.value,
        experience_level=request.experience_level.value if request.experience_level else None,
        max_results=request.max_results,
        source_domains=request.source_domains,
        status="pending",
        cancel_requested=False,
        results=[],
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    launch_background_job(job.id)
    return job


def get_job(session: Session, user_id: str, job_id: str) -> DiscoveryJob:
    job = session.scalar(
        select(DiscoveryJob).where(DiscoveryJob.id == job_id, DiscoveryJob.user_id == user_id)
    )
    if job is None:
        raise DiscoveryJobNotFoundError()
    return job


def list_jobs(session: Session, user_id: str, limit: int = 20, offset: int = 0) -> tuple[list[DiscoveryJob], int]:
    total = int(
        session.scalar(
            select(func.count()).select_from(DiscoveryJob).where(DiscoveryJob.user_id == user_id)
        )
        or 0
    )
    jobs = list(
        session.scalars(
            select(DiscoveryJob)
            .where(DiscoveryJob.user_id == user_id)
            .order_by(DiscoveryJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return jobs, total


def cancel_job(session: Session, user_id: str, job_id: str) -> DiscoveryJob:
    job = get_job(session, user_id, job_id)
    if job.status not in ACTIVE_STATUSES:
        raise DiscoveryCancellationNotAllowedError()
    job.cancel_requested = True
    session.commit()
    session.refresh(job)
    return job
