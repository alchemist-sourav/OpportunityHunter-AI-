from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.schemas.enums import ExperienceLevel, OpportunityType, RemotePreference
from app.scrapers.sources import normalize_domain, is_allowed_domain


class DiscoverySearchRequest(BaseModel):
    category: OpportunityType
    keywords: str = Field(min_length=1, max_length=300)
    skills: list[str] = Field(default_factory=list, max_length=20)
    locations: list[str] = Field(default_factory=list, max_length=10)
    remote_preference: RemotePreference = RemotePreference.NO_PREFERENCE
    experience_level: ExperienceLevel | None = None
    max_results: int = Field(default=20, ge=1)
    source_domains: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("keywords")
    @classmethod
    def _clean_keywords(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Keywords must not be empty.")
        return cleaned

    @field_validator("skills", "locations")
    @classmethod
    def _clean_string_list(cls, values: list[str]) -> list[str]:
        return [item.strip() for item in values if item.strip()][:20]

    @field_validator("source_domains")
    @classmethod
    def _normalize_sources(cls, values: list[str]) -> list[str]:
        allowed = set(get_settings().supported_domain_list)
        seen: set[str] = set()
        cleaned: list[str] = []
        for raw in values:
            domain = normalize_domain(raw)
            if not domain or domain in seen:
                continue
            seen.add(domain)
            if not is_allowed_domain(domain, allowed):
                raise ValueError(f"Domain '{domain}' is not an approved source.")
            cleaned.append(domain)
        return cleaned

    def model_post_init(self, __context: object) -> None:
        settings = get_settings()
        if self.max_results > settings.discovery_max_results:
            self.max_results = settings.discovery_max_results
        if not self.source_domains:
            self.source_domains = settings.supported_domain_list[: settings.discovery_max_domains]


class DiscoveryResultSchema(BaseModel):
    url: str
    title: str | None = None
    status_code: int | None = None
    domain: str | None = None
    snippet: str = ""
    relevant: bool = False
    found_keywords: int = 0


class DiscoveryJobResponse(BaseModel):
    id: str
    user_id: str
    category: str
    keywords: str
    skills: list[str]
    locations: list[str]
    remote_preference: str
    experience_level: str | None
    max_results: int
    source_domains: list[str]
    status: str
    cancel_requested: bool
    total_pages: int
    completed_pages: int
    result_count: int
    credits_used: int
    error_message: str | None
    results: list[DiscoveryResultSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class DiscoveryHistoryItem(BaseModel):
    id: str
    category: str
    keywords: str
    status: str
    result_count: int
    created_at: datetime
    updated_at: datetime


class DiscoveryHistoryResponse(BaseModel):
    total: int
    items: list[DiscoveryHistoryItem]


class DiscoveryCancelResponse(BaseModel):
    id: str
    status: str
    cancelled: bool
