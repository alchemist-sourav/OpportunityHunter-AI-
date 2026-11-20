from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "OpportunityHunter AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    database_url: str | None = None
    database_pool_size: int = 5
    database_max_overflow: int = 10

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    # Supabase Auth JWT verification (server-side only; never expose the secret)
    supabase_jwt_secret: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"

    firecrawl_api_key: str | None = None
    firecrawl_base_url: str = "https://api.firecrawl.dev"
    firecrawl_timeout_seconds: int = 30
    firecrawl_validate_live: bool = False

    # AES-256-GCM key for per-user Firecrawl credential encryption (32-byte hex).
    # Phase 2: server-side only. No plaintext fallback is ever used.
    firecrawl_encryption_key: str | None = None

    # Phase 3: Opportunity discovery limits and safety.
    discovery_max_results: int = 20
    discovery_default_results: int = 20
    discovery_max_concurrent_jobs: int = 2
    discovery_daily_quota: int = 10
    discovery_max_domains: int = 8
    discovery_supported_domains: str = (
        "linkedin.com,wellfound.com,remoteok.com,workatastartup.com,"
        "internshala.com,upwork.com,freelancer.com,greenhouse.io,lever.co"
    )
    discovery_poll_seconds: int = 5
    discovery_max_wait_seconds: int = 300
    discovery_max_response_bytes: int = 200_000
    discovery_max_stored_results: int = 60
    discovery_max_retries: int = 2

    @property
    def supported_domain_list(self) -> list[str]:
        return [domain.strip().lower().lstrip(".") for domain in self.discovery_supported_domains.split(",") if domain.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
