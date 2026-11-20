from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import DiscoveryJobNotFoundError
from app.models.discovery_models import DiscoveryJob
from app.models.opportunity_models import Opportunity, OpportunitySource
from app.scrapers.deduplication_service import (
    DuplicateDetector,
    generate_fingerprint,
    generate_opportunity_fingerprint,
)
from app.scrapers.extraction_service import ExtractionService
from app.scrapers.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)


class ExtractionOrchestrator:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        extraction_service: ExtractionService | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.extraction_service = extraction_service or ExtractionService()

    def extract_from_job(
        self,
        job_id: str,
        user_id: str,
        result_indices: list[int] | None = None,
    ) -> dict[str, Any]:
        with self.session_factory() as session:
            job = session.get(DiscoveryJob, job_id)
            if not job:
                raise DiscoveryJobNotFoundError()
            if job.user_id != user_id:
                raise DiscoveryJobNotFoundError()

            if job.status != "completed":
                return {
                    "created": [],
                    "updated": [],
                    "skipped": [],
                    "errors": ["Job is not completed"],
                }

            results = job.results or []
            if result_indices is not None:
                selected = [results[i] for i in result_indices if 0 <= i < len(results)]
            else:
                selected = results

            created = []
            updated = []
            skipped = []
            errors = []

            for idx, result in enumerate(selected):
                try:
                    opportunity_id = self._process_result(
                        session=session,
                        job=job,
                        user_id=user_id,
                        result=result,
                        result_index=idx,
                    )
                    if opportunity_id:
                        created.append(opportunity_id)
                except Exception as e:
                    logger.exception("extraction_failed job_id=%s index=%d", job_id, idx)
                    errors.append(f"Result {idx}: {str(e)}")

            return {
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
            }

    def _process_result(
        self,
        session: Session,
        job: DiscoveryJob,
        user_id: str,
        result: dict[str, Any],
        result_index: int,
    ) -> str | None:
        url = result.get("url")
        if not url:
            return None

        title = result.get("title")
        markdown = result.get("snippet", "")
        metadata = {
            "sourceURL": url,
            "url": url,
            "title": title,
        }

        extraction_result = self.extraction_service.extract(url, markdown, metadata)

        fingerprint = generate_fingerprint(
            extraction_result.title,
            extraction_result.company_name,
            url,
        )

        detector = DuplicateDetector(session)
        existing = detector.check_and_register(
            extraction_result.title,
            extraction_result.company_name,
            url,
        )

        raw_content = result.get("markdown", "") + result.get("title", "") + str(result.get("status_code", ""))
        content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()[:64]

        if existing:
            detector.register_source(
                opportunity_id=existing.id,
                discovery_job_id=job.id,
                user_id=user_id,
                source_url=url,
                raw_content_hash=content_hash,
            )
            logger.info("opportunity_exists_registered_source opp_id=%s source=%s", existing.id, url[:120])
            return None

        opportunity_id = str(uuid.uuid4())
        opportunity = Opportunity(
            id=opportunity_id,
            fingerprint=generate_fingerprint(
                extraction_result.title,
                extraction_result.company_name,
                url,
            ),
            title=extraction_result.title,
            company_name=extraction_result.company_name,
            description=extraction_result.description,
            opportunity_type=extraction_result.opportunity_type,
            required_skills=extraction_result.required_skills,
            experience_level=extraction_result.experience_level,
            location=extraction_result.location,
            remote_preference=extraction_result.remote_preference,
            salary_min=extraction_result.salary_min,
            salary_max=extraction_result.salary_max,
            salary_currency=extraction_result.salary_currency,
            application_url=extraction_result.application_url,
            source_url=url,
            source_domain=result.get("domain", ""),
            application_deadline=extraction_result.application_deadline,
            employment_type=extraction_result.employment_type,
        )

        session.add(opportunity)
        session.flush()

        source = OpportunitySource(
            opportunity_id=opportunity_id,
            discovery_job_id=job.id,
            user_id=user_id,
            source_url=url,
            source_domain=result.get("domain", ""),
            raw_content_hash=hashlib.sha256(str(result).encode("utf-8")).hexdigest()[:64],
        )
        session.add(source)
        session.commit()

        logger.info("opportunity_created id=%s title=%s", opportunity_id, extraction_result.title[:80] if extraction_result.title else "unknown")
        return opportunity_id

    def extract_batch(
        self,
        job_ids: list[str],
        user_id: str,
    ) -> dict[str, dict[str, Any]]:
        results = {}
        for job_id in job_ids:
            try:
                results[job_id] = self.extract_from_job(job_id, user_id)
            except Exception as e:
                logger.exception("batch_extraction_failed job_id=%s", job_id)
                results[job_id] = {"error": str(e)}
        return results