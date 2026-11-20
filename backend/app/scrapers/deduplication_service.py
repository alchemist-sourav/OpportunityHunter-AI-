from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qsl, urlunparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.opportunity_models import Opportunity

logger = logging.getLogger(__name__)

TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    "fbclid", "gclid", "msclkid", "dclid", "ttclid", "li_fat_id",
    "ref", "referrer", "source", "origin", "campaign",
    "mc_cid", "mc_eid", "_hsenc", "_hsmi",
    "igshid", "igsh", "share_id",
    "affiliate", "aff_id", "partner_id",
    "pk_campaign", "pk_kwd",
    "yclid", "wbraid", "gbraid",
})


@dataclass
class NormalizedUrl:
    url: str
    domain: str
    path: str
    query_params: dict[str, str]


@dataclass
class OpportunityFingerprint:
    fingerprint: str
    title_normalized: str
    company_normalized: str
    url_normalized: str


def normalize_url(url: str) -> NormalizedUrl:
    """Normalize a URL by removing tracking parameters and standardizing format."""
    parsed = urlparse(url.strip())
    domain = parsed.netloc.lower().lstrip("www.")
    path = parsed.path.rstrip("/")
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    filtered_params = {k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS}
    new_query = "&".join(f"{k}={v}" for k, v in sorted(filtered_params.items()))
    normalized = urlunparse((
        parsed.scheme.lower(),
        domain,
        path,
        "",
        new_query,
        "",
    ))
    return NormalizedUrl(
        url=normalized,
        domain=domain,
        path=path,
        query_params=filtered_params,
    )


def generate_fingerprint(
    title: str | None,
    company_name: str | None,
    url: str,
) -> str:
    """Generate a deterministic fingerprint for deduplication."""
    title_norm = (title or "").lower().strip()
    title_norm = re.sub(r"\s+", " ", title_norm)
    title_norm = re.sub(r"[^\w\s]", "", title_norm)

    company_norm = (company_name or "").lower().strip()
    company_norm = re.sub(r"\s+", " ", company_norm)
    company_norm = re.sub(r"[^\w\s]", "", company_norm)

    url_norm = normalize_url(url).url

    parts = [title_norm, company_norm, url_norm]
    content = "|".join(parts)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:64]


def generate_opportunity_fingerprint(
    title: str | None,
    company_name: str | None,
    url: str,
) -> OpportunityFingerprint:
    title_norm = (title or "").lower().strip()
    title_norm = re.sub(r"\s+", " ", title_norm)
    title_norm = re.sub(r"[^\w\s]", "", title_norm)

    company_norm = (company_name or "").lower().strip()
    company_norm = re.sub(r"\s+", " ", company_norm)
    company_norm = re.sub(r"[^\w\s]", "", company_norm)

    url_norm = normalize_url(url).url

    fingerprint = hashlib.sha256(f"{title_norm}|{company_norm}|{url_norm}".encode("utf-8")).hexdigest()[:64]

    return OpportunityFingerprint(
        fingerprint=fingerprint,
        title_normalized=title_norm,
        company_normalized=company_norm,
        url_normalized=url_norm,
    )


def find_duplicate_by_fingerprint(session: Session, fingerprint: str) -> Opportunity | None:
    return session.scalar(select(Opportunity).where(Opportunity.fingerprint == fingerprint))


def find_potential_duplicates(
    session: Session,
    title: str | None,
    company_name: str | None,
    url: str,
    fingerprint: str,
) -> list[Opportunity]:
    candidates = []
    exact = find_duplicate_by_fingerprint(session, fingerprint)
    if exact:
        candidates.append(exact)

    if title and company_name:
        title_words = set((title or "").lower().split())
        company_words = set((company_name or "").lower().split())
        if len(title_words) >= 3 and len(company_words) >= 1:
            stmt = select(Opportunity).where(
                Opportunity.title.ilike(f"%{title[:50]}%"),
                Opportunity.company_name.ilike(f"%{company_name[:50]}%"),
            ).limit(5)
            for opp in session.scalars(stmt):
                if opp not in candidates:
                    candidates.append(opp)

    return candidates


def is_similar_opportunity(
    existing: Opportunity,
    title: str | None,
    company_name: str | None,
    url: str,
    threshold: float = 0.85,
) -> bool:
    if existing.fingerprint == generate_fingerprint(title, company_name, url):
        return True

    if existing.source_url and url:
        if normalize_url(existing.source_url).url == normalize_url(url).url:
            return True

    return False


class DuplicateDetector:
    def __init__(self, session: Session) -> None:
        self.session = session

    def check_and_register(
        self,
        title: str | None,
        company_name: str | None,
        url: str,
    ) -> tuple[Opportunity | None, OpportunityFingerprint]:
        fingerprint = generate_opportunity_fingerprint(title, company_name, url)
        existing = find_duplicate_by_fingerprint(self.session, fingerprint.fingerprint)
        if existing:
            return existing, fingerprint

    def register_source(
        self,
        opportunity_id: str,
        discovery_job_id: str,
        user_id: str,
        source_url: str,
        raw_content_hash: str,
    ) -> None:
        from app.models.opportunity_models import OpportunitySource
        normalized = normalize_url(source_url)
        source = OpportunitySource(
            opportunity_id=opportunity_id,
            discovery_job_id=discovery_job_id,
            user_id=user_id,
            source_url=source_url,
            source_domain=normalized.domain,
            raw_content_hash=raw_content_hash,
        )
        self.session.add(source)