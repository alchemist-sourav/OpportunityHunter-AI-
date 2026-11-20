import pytest

from app.core.config import Settings
from app.core.redact import redact_secret

_ENV_KEYS = (
    "DATABASE_URL",
    "DATABASE_POOL_SIZE",
    "DATABASE_MAX_OVERFLOW",
    "CORS_ORIGINS",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_JWT_ISSUER",
    "SUPABASE_JWT_AUDIENCE",
    "FIRECRAWL_API_KEY",
    "FIRECRAWL_BASE_URL",
    "FIRECRAWL_TIMEOUT_SECONDS",
    "FIRECRAWL_VALIDATE_LIVE",
    "FIRECRAWL_ENCRYPTION_KEY",
    "DEBUG",
    "ENVIRONMENT",
    "LOG_LEVEL",
    "API_PREFIX",
)


def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    settings = Settings(_env_file=None)
    assert settings.app_name == "OpportunityHunter AI"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.api_prefix == "/api/v1"
    assert settings.database_url is None
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.cors_origin_list == ["http://localhost:3000", "http://127.0.0.1:3000"]
    assert settings.firecrawl_api_key is None
    assert settings.firecrawl_base_url == "https://api.firecrawl.dev"
    assert settings.firecrawl_validate_live is False
    assert settings.firecrawl_encryption_key is None
    assert settings.supabase_jwt_secret is None
    assert settings.supabase_jwt_issuer is None
    assert settings.supabase_jwt_audience == "authenticated"


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost:5432/oh")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com, https://app.example.com")
    settings = Settings(_env_file=None)
    assert settings.database_url == "postgresql+psycopg2://u:p@localhost:5432/oh"
    assert settings.firecrawl_api_key == "fc-test-key"
    assert settings.environment == "production"
    assert settings.cors_origin_list == ["https://example.com", "https://app.example.com"]


def test_secrets_are_redacted_before_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    _clean_env(monkeypatch)
    monkeypatch.setenv("FIRECRAWL_API_KEY", "super-secret-do-not-leak")
    settings = Settings(_env_file=None)
    assert settings.firecrawl_api_key == "super-secret-do-not-leak"
    assert redact_secret(settings.firecrawl_api_key) == "redacted"
    assert "super-secret-do-not-leak" not in redact_secret(settings.firecrawl_api_key)
    assert redact_secret(settings.database_url) == "<not set>"
