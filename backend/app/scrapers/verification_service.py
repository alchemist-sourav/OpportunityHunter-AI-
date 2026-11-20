from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.models.opportunity_models import Opportunity, VerificationStatus
from app.scrapers.sources import validate_public_url

logger = logging.getLogger(__name__)

CLOSED_KEYWORDS = frozenset({
    "position filled", "position closed", "no longer accepting", "closed",
    "hiring complete", "role filled", "job filled", "expired",
    "application closed", "no longer available", "filled",
    "this position has been filled", "we have filled",
    "recruitment closed", "vacancy filled",
})

EXPIRED_KEYWORDS = frozenset({
    "deadline passed", "deadline has passed", "expired",
    "past deadline", "closing date passed",
})

REDIRECT_CHAIN_LIMIT = 5
VERIFICATION_TIMEOUT = 15.0
CONNECT_TIMEOUT = 5.0


@dataclass
class VerificationResult:
    status: VerificationStatus
    evidence: str | None
    failure_reason: str | None
    redirect_chain: list[str]
    final_url: str | None
    status_code: int | None
    response_time_ms: int
    checked_at: datetime


class VerificationService:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(VERIFICATION_TIMEOUT, connect=CONNECT_TIMEOUT),
                follow_redirects=True,
                max_redirects=REDIRECT_CHAIN_LIMIT,
                headers={"User-Agent": "OpportunityHunter-Verification/1.0"},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def verify(self, opportunity) -> VerificationResult:
        start_time = time.monotonic()
        redirect_chain = []
        final_url = None
        status_code = None
        evidence_parts = []
        failure_reason = None

        urls_to_check = []
        if opportunity.application_url:
            urls_to_check.append(("application_url", opportunity.application_url))
        if opportunity.source_url:
            urls_to_check.append(("source_url", opportunity.source_url))

        if not urls_to_check:
            return VerificationResult(
                status=VerificationStatus.UNCERTAIN,
                evidence="No URLs available for verification",
                failure_reason="No application or source URL",
                redirect_chain=[],
                final_url=None,
                status_code=None,
                response_time_ms=0,
                checked_at=datetime.now(timezone.utc),
            )

        client = await self._get_client()
        settings = get_settings()

        for url_type, url in urls_to_check:
            try:
                validate_public_url(url)
            except Exception as e:
                logger.warning("verification_url_blocked type=%s url=%s reason=%s", url_type, url[:120], e)
                continue

            try:
                response = await client.head(url, timeout=VERIFICATION_TIMEOUT)
            except httpx.TimeoutException:
                failure_reason = f"{url_type} request timed out"
                continue
            except httpx.TooManyRedirects:
                failure_reason = f"{url_type} exceeded redirect limit"
                continue
            except httpx.HTTPError as e:
                failure_reason = f"{url_type} network error: {type(e).__name__}"
                continue

            status_code = response.status_code
            final_url = str(response.url)
            redirect_chain.append(final_url)

            if response.history:
                for resp in response.history:
                    redirect_chain.append(str(resp.url))

            if 200 <= status_code < 300:
                try:
                    get_response = await client.get(final_url, timeout=VERIFICATION_TIMEOUT)
                    content = get_response.text.lower()
                    content_hash = hashlib.sha256(get_response.content).hexdigest()[:16]

                    evidence_parts.append(f"{url_type}: HTTP {status_code}")
                    evidence_parts.append(f"Final URL: {final_url}")
                    evidence_parts.append(f"Content hash: {content_hash}")

                    if self._check_closed_keywords(content):
                        return VerificationResult(
                            status=VerificationStatus.CLOSED,
                            evidence="; ".join(evidence_parts),
                            failure_reason=None,
                            redirect_chain=redirect_chain,
                            final_url=final_url,
                            status_code=status_code,
                            response_time_ms=int((time.monotonic() - start_time) * 1000),
                            checked_at=datetime.now(timezone.utc),
                        )

                    if self._check_expired_keywords(content):
                        return VerificationResult(
                            status=VerificationStatus.EXPIRED,
                            evidence="; ".join(evidence_parts),
                            failure_reason=None,
                            redirect_chain=redirect_chain,
                            final_url=final_url,
                            status_code=status_code,
                            response_time_ms=int((time.monotonic() - start_time) * 1000),
                            checked_at=datetime.now(timezone.utc),
                        )

                    evidence_parts.append("Page accessible and no closed/expired indicators found")

                except httpx.TimeoutException:
                    evidence_parts.append(f"{url_type}: HTTP {status_code} (HEAD OK, GET timeout)")
                except httpx.HTTPError:
                    evidence_parts.append(f"{url_type}: HTTP {status_code} (HEAD OK, GET failed)")

            elif status_code in (401, 403, 429):
                evidence_parts.append(f"{url_type}: HTTP {status_code} (access restricted)")
                failure_reason = f"Access restricted ({status_code})"
            elif status_code == 404:
                evidence_parts.append(f"{url_type}: HTTP 404 (not found)")
                failure_reason = "Page not found (404)"
            elif 500 <= status_code < 600:
                evidence_parts.append(f"{url_type}: HTTP {status_code} (server error)")
                failure_reason = f"Server error ({status_code})"
            else:
                evidence_parts.append(f"{url_type}: HTTP {status_code}")
                failure_reason = f"Unexpected status {status_code}"

        response_time_ms = int((time.monotonic() - start_time) * 1000)
        checked_at = datetime.now(timezone.utc)

        if status_code and 200 <= status_code < 300:
            if "access restricted" in " ".join(evidence_parts).lower():
                return VerificationResult(
                    status=VerificationStatus.UNCERTAIN,
                    evidence="; ".join(evidence_parts),
                    failure_reason=failure_reason,
                    redirect_chain=redirect_chain,
                    final_url=final_url,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    checked_at=checked_at,
                )
            return VerificationResult(
                status=VerificationStatus.ACTIVE,
                evidence="; ".join(evidence_parts),
                failure_reason=None,
                redirect_chain=redirect_chain,
                final_url=final_url,
                status_code=status_code,
                response_time_ms=response_time_ms,
                checked_at=checked_at,
            )

        if failure_reason and "not found" in failure_reason.lower():
            return VerificationResult(
                status=VerificationStatus.INACCESSIBLE,
                evidence="; ".join(evidence_parts),
                failure_reason=failure_reason,
                redirect_chain=redirect_chain,
                final_url=final_url,
                status_code=status_code,
                response_time_ms=response_time_ms,
                checked_at=checked_at,
            )

        return VerificationResult(
            status=VerificationStatus.UNCERTAIN,
            evidence="; ".join(evidence_parts),
            failure_reason=failure_reason,
            redirect_chain=redirect_chain,
            final_url=final_url,
            status_code=status_code,
            response_time_ms=response_time_ms,
            checked_at=checked_at,
        )

    def _check_closed_keywords(self, content: str) -> bool:
        content_lower = content.lower()
        return any(kw in content_lower for kw in CLOSED_KEYWORDS)

    def _check_expired_keywords(self, content: str) -> bool:
        content_lower = content.lower()
        return any(kw in content_lower for kw in EXPIRED_KEYWORDS)


class VerificationOrchestrator:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    async def verify_opportunity(self, opportunity_id: str) -> Opportunity | None:
        service = VerificationService()
        try:
            with self.session_factory() as session:
                opportunity = session.get(Opportunity, opportunity_id)
                if not opportunity:
                    logger.error("opportunity_not_found id=%s", opportunity_id)
                    return None

                result = await service.verify(opportunity)

                opportunity.verification_status = result.status
                opportunity.last_verified_at = result.checked_at
                opportunity.verification_evidence = result.evidence
                opportunity.verification_failure_reason = result.failure_reason
                opportunity.updated_at = datetime.now(timezone.utc)

                session.add(opportunity)
                session.commit()
                session.refresh(opportunity)

                logger.info("verification_complete id=%s status=%s", opportunity_id, result.status.value)
                return opportunity
        finally:
            await service.close()

    async def batch_verify(self, opportunity_ids: list[str]) -> dict[str, VerificationStatus]:
        results = {}
        service = VerificationService()
        try:
            with self.session_factory() as session:
                for opp_id in opportunity_ids:
                    opportunity = session.get(Opportunity, opp_id)
                    if not opportunity:
                        results[opp_id] = VerificationStatus.UNCERTAIN
                        continue

                    result = await service.verify(opportunity)
                    opportunity.verification_status = result.status
                    opportunity.last_verified_at = result.checked_at
                    opportunity.verification_evidence = result.evidence
                    opportunity.verification_failure_reason = result.failure_reason
                    opportunity.updated_at = datetime.now(timezone.utc)

                    session.add(opportunity)
                    results[opp_id] = result.status
                session.commit()
        finally:
            await service.close()
        return results