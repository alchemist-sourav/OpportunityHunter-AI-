from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "OpportunityHunter AI"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
    assert isinstance(data["database_configured"], bool)
    assert isinstance(data["firecrawl_configured"], bool)


def test_health_endpoint_leaks_no_secrets(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    body = response.json()
    assert "FIRECRAWL_API_KEY" not in str(body)
    assert "firecrawl_api_key" not in body
    assert "database_url" not in body
    assert "supabase" not in body


def test_unknown_route_returns_structured_404(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_error"


def test_root_not_found(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 404
