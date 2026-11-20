import time
from datetime import datetime, timezone

import jwt
import pytest

from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationNotConfiguredError,
    ForbiddenError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.core import security
from app.core.security import AuthUser

JWT_SECRET = "test-supabase-jwt-secret-0123456789abcdef"
ISSUER = "https://project.supabase.co/auth/v1"
AUDIENCE = "authenticated"


def _settings() -> Settings:
    return Settings(
        supabase_jwt_secret=JWT_SECRET,
        supabase_jwt_issuer=ISSUER,
        supabase_jwt_audience=AUDIENCE,
    )


def _make_token(
    sub: str = "user-123",
    role: str = "authenticated",
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expires_in: int = 60,
    provider: str = "email",
    email: str = "a@example.com",
) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "iss": issuer,
        "aud": audience,
        "exp": int(datetime.now(timezone.utc).timestamp()) + expires_in,
        "email": email,
        "email_verified": True,
        "app_metadata": {"provider": provider},
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def _settings_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: _settings())


def test_verify_valid_token_returns_user() -> None:
    user = security.verify_supabase_token(_make_token())
    assert isinstance(user, AuthUser)
    assert user.user_id == "user-123"
    assert user.email == "a@example.com"
    assert user.role == "authenticated"
    assert user.provider == "email"
    assert user.email_verified is True


def test_verify_missing_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: Settings(supabase_jwt_secret=None, supabase_url="https://x.supabase.co"))
    with pytest.raises(AuthenticationNotConfiguredError):
        security.verify_supabase_token(_make_token())


def test_verify_missing_issuer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "get_settings", lambda: Settings(supabase_jwt_secret=JWT_SECRET, supabase_jwt_issuer=None, supabase_url=None))
    with pytest.raises(AuthenticationNotConfiguredError):
        security.verify_supabase_token(_make_token())


def test_verify_expired_token_raises() -> None:
    token = _make_token(expires_in=-60)
    with pytest.raises(TokenExpiredError):
        security.verify_supabase_token(token)


def test_verify_wrong_issuer_raises() -> None:
    token = _make_token(issuer="https://evil.example.com")
    with pytest.raises(InvalidIssuerError):
        security.verify_supabase_token(token)


def test_verify_wrong_audience_raises() -> None:
    token = _make_token(audience="service_role")
    with pytest.raises(InvalidAudienceError):
        security.verify_supabase_token(token)


def test_verify_bad_signature_raises() -> None:
    token = jwt.encode(
        {"sub": "x", "role": "authenticated", "iss": ISSUER, "aud": AUDIENCE, "exp": int(time.time()) + 60},
        "wrong-secret-padding-0123456789abcdef",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        security.verify_supabase_token(token)


def test_verify_forbidden_role_raises() -> None:
    token = _make_token(role="service_role")
    with pytest.raises(ForbiddenError):
        security.verify_supabase_token(token)


def test_verify_missing_subject_raises() -> None:
    payload = {
        "role": "authenticated",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": int(datetime.now(timezone.utc).timestamp()) + 60,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        security.verify_supabase_token(token)


def test_resolve_issuer_prefers_explicit() -> None:
    assert security.resolve_issuer() == ISSUER


def test_resolve_issuer_falls_back_to_supabase_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: Settings(supabase_jwt_secret=JWT_SECRET, supabase_jwt_issuer=None, supabase_url="https://x.supabase.co"),
    )
    assert security.resolve_issuer() == "https://x.supabase.co/auth/v1"
