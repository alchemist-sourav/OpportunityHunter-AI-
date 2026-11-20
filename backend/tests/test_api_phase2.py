from datetime import datetime, timezone
from typing import Iterator

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.database import engine as engine_mod
from app.database.base import Base
from app.main import app
from app.services import encryption as encryption_mod

JWT_SECRET = "test-jwt-secret-0123456789abcdef"
ISSUER = "https://project.supabase.co/auth/v1"
AUDIENCE = "authenticated"
ENCRYPTION_KEY_HEX = "cd" * 32

FIRECRAWL_KEY = "fc_test_1234567890abcde"


def _settings() -> Settings:
    return Settings(
        supabase_jwt_secret=JWT_SECRET,
        supabase_jwt_issuer=ISSUER,
        supabase_jwt_audience=AUDIENCE,
        firecrawl_encryption_key=ENCRYPTION_KEY_HEX,
        firecrawl_validate_live=False,
    )


def _make_token(sub: str = "user-123", email: str = "a@example.com") -> str:
    payload = {
        "sub": sub,
        "role": "authenticated",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": int(datetime.now(timezone.utc).timestamp()) + 60,
        "email": email,
        "email_verified": True,
        "app_metadata": {"provider": "email"},
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture()
def session_factory() -> sessionmaker:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def client(
    session_factory: sessionmaker,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setattr(engine_mod, "get_settings", _settings)
    from app.core import security as security_mod

    monkeypatch.setattr(security_mod, "get_settings", _settings)
    monkeypatch.setattr(encryption_mod, "get_settings", _settings)
    from app.services import credential_service as credential_mod

    monkeypatch.setattr(credential_mod, "get_settings", _settings)

    def _override_get_session() -> Iterator[Session]:
        with session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[engine_mod.get_session] = _override_get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── /auth/me ──────────────────────────────────────────────────────────────


def test_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_token"


def test_me_rejects_non_bearer_scheme(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_me_returns_current_user(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=_auth(_make_token("user-111", "b@example.com")))
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-111"
    assert body["email"] == "b@example.com"
    assert body["role"] == "authenticated"
    assert body["provider"] == "email"
    assert body["email_verified"] is True


# ── /profile ──────────────────────────────────────────────────────────────


def test_profile_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/profile").status_code == 401


def test_profile_get_404_when_missing(client: TestClient) -> None:
    response = client.get("/api/v1/profile", headers=_auth(_make_token("user-123")))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "profile_not_found"


def test_profile_create_get_returns_201(client: TestClient) -> None:
    headers = _auth(_make_token("user-123"))
    payload: dict[str, object] = {
        "full_name": "Ada Lovelace",
        "skills": ["python", "ml"],
        "experience_level": "junior",
        "preferred_job_roles": ["ml engineer"],
        "preferred_opportunity_types": ["full_time_job"],
        "preferred_locations": ["remote"],
        "remote_preference": "remote_only",
    }
    created = client.post("/api/v1/profile", json=payload, headers=headers)
    assert created.status_code == 201
    assert created.json()["user_id"] == "user-123"
    assert created.json()["full_name"] == "Ada Lovelace"

    fetched = client.get("/api/v1/profile", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["skills"] == ["python", "ml"]


def test_profile_is_private_to_owner(client: TestClient) -> None:
    payload: dict[str, object] = {
        "full_name": "Ada",
        "skills": [],
        "experience_level": "fresher",
        "preferred_job_roles": [],
        "preferred_opportunity_types": [],
        "preferred_locations": [],
        "remote_preference": "no_preference",
    }
    client.post("/api/v1/profile", json=payload, headers=_auth(_make_token("user-a")))
    other = client.get("/api/v1/profile", headers=_auth(_make_token("user-b")))
    assert other.status_code == 404


def test_profile_patch_updates_only_provided_fields(client: TestClient) -> None:
    headers = _auth(_make_token("user-123"))
    create: dict[str, object] = {
        "full_name": "Ada",
        "skills": ["python"],
        "experience_level": "junior",
        "preferred_job_roles": [],
        "preferred_opportunity_types": [],
        "preferred_locations": [],
        "remote_preference": "no_preference",
    }
    client.post("/api/v1/profile", json=create, headers=headers)

    updated = client.patch("/api/v1/profile", json={"skills": ["python", "sql"]}, headers=headers)
    assert updated.status_code == 200
    body = updated.json()
    assert body["skills"] == ["python", "sql"]
    assert body["full_name"] == "Ada"
    assert body["experience_level"] == "junior"


def test_profile_patch_404_when_missing(client: TestClient) -> None:
    response = client.patch("/api/v1/profile", json={"full_name": "X"}, headers=_auth(_make_token("user-404")))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "profile_not_found"


def test_profile_delete_removes_profile(client: TestClient) -> None:
    headers = _auth(_make_token("user-123"))
    payload: dict[str, object] = {
        "full_name": "Ada",
        "skills": [],
        "experience_level": "student",
        "preferred_job_roles": [],
        "preferred_opportunity_types": [],
        "preferred_locations": [],
        "remote_preference": "no_preference",
    }
    client.post("/api/v1/profile", json=payload, headers=headers)
    assert client.delete("/api/v1/profile", headers=headers).status_code == 204
    assert client.get("/api/v1/profile", headers=headers).status_code == 404


def test_profile_rejects_invalid_experience_level(client: TestClient) -> None:
    payload: dict[str, object] = {
        "full_name": "Ada",
        "skills": [],
        "experience_level": "senior",
        "preferred_job_roles": [],
        "preferred_opportunity_types": [],
        "preferred_locations": [],
        "remote_preference": "no_preference",
    }
    response = client.post("/api/v1/profile", json=payload, headers=_auth(_make_token("user-123")))
    assert response.status_code == 422


# ── /credentials/firecrawl ────────────────────────────────────────────────


def test_credential_status_unconfigured_by_default(client: TestClient) -> None:
    response = client.get("/api/v1/credentials/firecrawl/status", headers=_auth(_make_token("user-123")))
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "firecrawl"
    assert body["configured"] is False
    assert body["algorithm"] is None


def test_credential_put_stores_encrypted_and_hides_key(client: TestClient) -> None:
    response = client.put(
        "/api/v1/credentials/firecrawl",
        json={"api_key": FIRECRAWL_KEY},
        headers=_auth(_make_token("user-123")),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "firecrawl"
    assert body["configured"] is True
    assert body["validation"] == "format_valid"
    assert FIRECRAWL_KEY not in response.text
    assert "api_key" not in body

    status = client.get("/api/v1/credentials/firecrawl/status", headers=_auth(_make_token("user-123")))
    assert status.json()["configured"] is True
    assert status.json()["algorithm"] == "aes-256-gcm"
    assert status.json()["key_version"] == 1


def test_credential_is_scoped_to_user(client: TestClient) -> None:
    client.put("/api/v1/credentials/firecrawl", json={"api_key": FIRECRAWL_KEY}, headers=_auth(_make_token("user-a")))
    status = client.get("/api/v1/credentials/firecrawl/status", headers=_auth(_make_token("user-b")))
    assert status.json()["configured"] is False


def test_credential_delete_clears_then_404s(client: TestClient) -> None:
    headers = _auth(_make_token("user-123"))
    client.put("/api/v1/credentials/firecrawl", json={"api_key": FIRECRAWL_KEY}, headers=headers)
    deleted = client.delete("/api/v1/credentials/firecrawl", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["configured"] is False

    again = client.delete("/api/v1/credentials/firecrawl", headers=headers)
    assert again.status_code == 404
    assert again.json()["error"]["code"] == "credential_not_found"


def test_credential_put_rejects_short_key(client: TestClient) -> None:
    response = client.put(
        "/api/v1/credentials/firecrawl",
        json={"api_key": "short"},
        headers=_auth(_make_token("user-123")),
    )
    assert response.status_code == 422
