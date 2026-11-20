from __future__ import annotations

import logging
import math
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DiscoveryCredentialMissingError,
    DiscoveryInvalidUrlError,
    DiscoveryTimeoutError,
)
from app.database.engine import get_session_factory
from app.models.discovery_models import DiscoveryJob
from app.scrapers import sources
from app.scrapers.firecrawl_client import (
    CRAWL_COMPLETED,
    CRAWL_FAILED,
    CRAWL_CANCELLED,
    CrawlStatus,
    FirecrawlClient,
    FirecrawlError,
    FirecrawlRateLimitError,
    FirecrawlAuthError,
    client_from_settings,
)
from app.services.credential_service import get_firecrawl_credential

logger = logging.getLogger(__name__)

STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _relevance_tokens(keywords: str, skills: list[str]) -> set[str]:
    tokens: set[str] = set()
    for text in (keywords, " ".join(skills or [])):
        tokens.update(_TOKEN_RE.findall(text.lower()))
    return {token for token in tokens if len(token) >= 3}


def _keyword_relevance(title: str, url: str, snippet: str, tokens: set[str]) -> tuple[bool, int]:
    if not tokens:
        return True, 0
    haystack = f"{title or ''} {url or ''} {snippet}".lower()
    found = sum(1 for token in tokens if token in haystack)
    return found > 0, found


def _clip_snippet(markdown: str, max_bytes: int) -> str:
    snippet = markdown.strip()
    if len(snippet) <= max_bytes:
        return snippet
    truncated = snippet[:max_bytes]
    last_space = truncated.rfind(" ")
    if last_space > max_bytes // 2:
        return truncated[:last_space]
    return truncated


def _result_payload(
    index: int,
    url: str,
    title: str | None,
    status_code: int | None,
    markdown: str,
    relevant: bool,
    found_keywords: int,
    max_bytes: int,
) -> dict[str, Any]:
    return {
        "url": url,
        "title": title,
        "status_code": status_code,
        "domain": sources.normalize_domain(url),
        "snippet": _clip_snippet(markdown, max_bytes),
        "relevant": relevant,
        "found_keywords": found_keywords,
        "order": index,
    }


def run_discovery_job(
    job_id: str,
    client_factory: Callable[[str], FirecrawlClient] | None = None,
    session_factory: Callable[[], Session] | None = None,
) -> None:
    """Execute a persisted discovery job inside its own database session.

    Runs in a worker thread. Uses a fresh session so it can commit progress
    independently of any request-scoped session.
    """
    factory = session_factory or get_session_factory
    with factory() as session:
        job = session.get(DiscoveryJob, job_id)
        if job is None:
            logger.error("discovery_job_not_found job_id=%s", job_id)
            return
        if job.status in (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED):
            return
        _execute_job(session, job, client_factory or client_from_settings)


def build_client_or_fail(session: Session, user_id: str, client_factory: Callable[[str], FirecrawlClient]) -> tuple[FirecrawlClient | None, str | None]:
    credential = get_firecrawl_credential(session, user_id)
    if credential is None or not credential.is_active:
        return None, DiscoveryCredentialMissingError().message
    try:
        from app.services.credential_service import decrypt_firecrawl_credential

        api_key = decrypt_firecrawl_credential(credential)
    except Exception:
        return None, "Stored Firecrawl credential could not be decrypted."
    if not api_key:
        return None, "Stored Firecrawl credential is empty."
    return client_factory(api_key), None


def _fail_job(session: Session, job: DiscoveryJob, message: str) -> None:
    job.status = STATUS_FAILED
    job.error_message = message
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()


def _execute_job(
    session: Session,
    job: DiscoveryJob,
    client_factory: Callable[[str], FirecrawlClient],
) -> None:
    from app.core.config import get_settings

    settings = get_settings()

    client, error = build_client_or_fail(session, job.user_id, client_factory)
    if client is None:
        _fail_job(session, job, error or "Firecrawl credential is unavailable.")
        return

    try:
        with client:
            job.status = STATUS_RUNNING
            job.cancel_requested = False
            session.commit()

            results: list[dict[str, Any]] = []
            max_stored = settings.discovery_max_stored_results
            max_bytes = settings.discovery_max_response_bytes
            tokens = _relevance_tokens(job.keywords, job.skills)
            domains = list(job.source_domains or [])
            per_domain_limit = max(1, math.ceil(min(job.max_results, max_stored) / max(1, len(domains))))
            total_credits = 0
            total_pages_seen = 0
            completed_pages_seen = 0
            max_wait = settings.discovery_max_wait_seconds
            poll = settings.discovery_poll_seconds

            for domain in domains:
                if job.cancel_requested:
                    break
                seed = sources.seed_url_for_domain(domain)
                try:
                    sources.validate_public_url(seed)
                except DiscoveryInvalidUrlError as exc:
                    logger.warning("discovery_skip_domain domain=%s reason=%s", domain, exc.message)
                    continue

                try:
                    crawl = client.start_crawl(seed, limit=per_domain_limit, max_depth=2)
                except FirecrawlAuthError:
                    _fail_job(session, job, "Firecrawl rejected the API key.")
                    return
                except FirecrawlRateLimitError:
                    _fail_job(session, job, "Firecrawl rate limit was exceeded.")
                    return
                except FirecrawlError as exc:
                    logger.warning("discovery_crawl_start_failed domain=%s code=%s", domain, exc.error_code)
                    continue

                job.external_job_id = crawl.id
                session.commit()

                status = _poll_crawl(client, crawl.id, poll_interval=poll, max_wait=max_wait, cancelled=lambda: job.cancel_requested)
                if status is None:
                    continue  # timed out; per-domain skip, kept running overall

                total_credits += status.credits_used
                total_pages_seen += status.total
                completed_pages_seen += status.completed
                for doc in status.documents:
                    if len(results) >= max_stored:
                        break
                    if doc.error:
                        continue
                    try:
                        sources.validate_public_url(doc.final_url)
                    except DiscoveryInvalidUrlError:
                        logger.info("discovery_drop_url reason=pinned_private_state url=%s", doc.final_url[:120])
                        continue
                    relevant, found = _keyword_relevance(doc.title, doc.final_url, doc.markdown, tokens)
                    results.append(
                        _result_payload(
                            index=len(results),
                            url=doc.final_url,
                            title=doc.title,
                            status_code=doc.status_code,
                            markdown=doc.markdown,
                            relevant=relevant,
                            found_keywords=found,
                            max_bytes=max_bytes,
                        )
                    )

                if status.status == CRAWL_CANCELLED:
                    job.status = STATUS_CANCELLED
                    job.cancel_requested = True
                    break

            job.credits_used = max(job.credits_used, total_credits)
            job.result_count = len(results)
            job.results = results
            job.total_pages = total_pages_seen
            job.completed_pages = completed_pages_seen
            job.completed_at = datetime.now(timezone.utc)
            if job.status == STATUS_CANCELLED or job.cancel_requested:
                job.status = STATUS_CANCELLED
                job.cancel_requested = True
                session.commit()
                return
            job.status = STATUS_COMPLETED
            session.commit()
    except DiscoveryTimeoutError:
        _fail_job(session, job, "Discovery exceeded the allowable wait time.")
    except Exception as exc:
        logger.exception("discovery_job_unexpected job_id=%s", job.id)
        _fail_job(session, job, "Discovery failed unexpectedly. Details are hidden from the client.")


def _poll_crawl(
    client: FirecrawlClient,
    crawl_id: str,
    poll_interval: int,
    max_wait: int,
    cancelled: Callable[[], bool],
) -> CrawlStatus | None:
    deadline = time.monotonic() + max_wait
    last_status: CrawlStatus | None = None
    while time.monotonic() < deadline:
        if cancelled():
            try:
                client.cancel_crawl(crawl_id)
            except FirecrawlError:
                logger.info("discovery_cancel_external_failed crawl_id=%s", crawl_id)
            return CrawlStatus(status=CRAWL_CANCELLED)
        try:
            last_status = client.get_crawl_status(crawl_id)
        except FirecrawlError as exc:
            logger.warning("discovery_poll_failed code=%s retrying", exc.error_code)
            time.sleep(poll_interval)
            continue
        if last_status.is_terminal:
            return last_status
        time.sleep(poll_interval)
    if cancelled():
        return CrawlStatus(status=CRAWL_CANCELLED)
    raise DiscoveryTimeoutError()
