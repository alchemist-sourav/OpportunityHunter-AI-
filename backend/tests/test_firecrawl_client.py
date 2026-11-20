from __future__ import annotations

import json
import pytest
import respx
import httpx

from app.scrapers.firecrawl_client import (
    FirecrawlClient,
    FirecrawlAuthError,
    FirecrawlRateLimitError,
    FirecrawlValidationError,
    FirecrawlNotFoundError,
    FirecrawlServerError,
    FirecrawlPaymentRequiredError,
    FirecrawlNetworkError,
    FirecrawlTimeoutError,
    CrawlStart,
    CrawlDocument,
    CrawlStatus,
)


class TestFirecrawlClient:
    @pytest.fixture
    def client(self) -> FirecrawlClient:
        return FirecrawlClient(api_key="fc-test-key", timeout_seconds=5, max_retries=1)

    @pytest.fixture
    def mock_crawl_start_response(self) -> dict:
        return {"id": "crawl-123", "url": "https://example.com"}

    @pytest.fixture
    def mock_crawl_status_running(self) -> dict:
        return {
            "status": "scraping",
            "total": 10,
            "completed": 5,
            "creditsUsed": 5,
            "data": [],
            "error": None,
        }

    @pytest.fixture
    def mock_crawl_status_completed(self) -> dict:
        return {
            "status": "completed",
            "total": 10,
            "completed": 10,
            "creditsUsed": 10,
            "data": [
                {
                    "url": "https://example.com/job/1",
                    "data": {
                        "markdown": "# Software Engineer\n\nGreat opportunity!",
                        "metadata": {
                            "sourceURL": "https://example.com/job/1",
                            "url": "https://example.com/job/1",
                            "title": "Software Engineer",
                            "statusCode": 200,
                        },
                    },
                    "error": None,
                },
                {
                    "url": "https://example.com/job/2",
                    "data": {
                        "markdown": "# Data Scientist\n\nAnalyze data.",
                        "metadata": {
                            "sourceURL": "https://example.com/job/2",
                            "url": "https://example.com/job/2",
                            "title": "Data Scientist",
                            "statusCode": 200,
                        },
                    },
                    "error": None,
                },
            ],
            "error": None,
        }

    def test_scrape_url_success(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "markdown": "# Test Page",
                        "metadata": {
                            "sourceURL": "https://example.com",
                            "url": "https://example.com",
                            "title": "Test Page",
                            "statusCode": 200,
                        },
                    }
                },
            )
        )

        result = client.scrape_url("https://example.com")

        assert isinstance(result, CrawlDocument)
        assert result.url == "https://example.com"
        assert result.title == "Test Page"
        assert result.status_code == 200
        assert "Test Page" in result.markdown

    def test_scrape_url_with_formats(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "markdown": "# Test",
                        "html": "<h1>Test</h1>",
                        "metadata": {"sourceURL": "https://example.com", "title": "Test"},
                    }
                },
            )
        )

        result = client.scrape_url("https://example.com", formats=["markdown", "html"])
        assert result.markdown == "# Test"

    def test_start_crawl_success(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/crawl").mock(
            return_value=httpx.Response(200, json={"id": "crawl-123", "url": "https://example.com"})
        )

        result = client.start_crawl("https://example.com", limit=20)

        assert isinstance(result, CrawlStart)
        assert result.id == "crawl-123"
        assert result.url == "https://example.com"

    def test_start_crawl_missing_id_raises(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/crawl").mock(
            return_value=httpx.Response(200, json={"url": "https://example.com"})
        )

        with pytest.raises(FirecrawlValidationError, match="did not return a crawl id"):
            client.start_crawl("https://example.com")

    def test_get_crawl_status_completed(self, client: FirecrawlClient, respx_mock: respx.Router, mock_crawl_status_completed: dict) -> None:
        respx_mock.get("https://api.firecrawl.dev/v2/crawl/crawl-123").mock(
            return_value=httpx.Response(200, json=mock_crawl_status_completed)
        )

        result = client.get_crawl_status("crawl-123")

        assert isinstance(result, CrawlStatus)
        assert result.status == "completed"
        assert result.total == 10
        assert result.completed == 10
        assert result.credits_used == 10
        assert len(result.documents) == 2
        assert result.documents[0].title == "Software Engineer"
        assert result.documents[1].title == "Data Scientist"

    def test_get_crawl_status_running(self, client: FirecrawlClient, respx_mock: respx.Router, mock_crawl_status_running: dict) -> None:
        respx_mock.get("https://api.firecrawl.dev/v2/crawl/crawl-123").mock(
            return_value=httpx.Response(200, json=mock_crawl_status_running)
        )

        result = client.get_crawl_status("crawl-123")

        assert result.status == "scraping"
        assert not result.is_terminal

    def test_cancel_crawl_success(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.delete("https://api.firecrawl.dev/v2/crawl/crawl-123").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = client.cancel_crawl("crawl-123")
        assert result is True

    def test_cancel_crawl_not_found_returns_true(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        """Cancel on non-existent crawl returns True (idempotent)."""
        respx_mock.delete("https://api.firecrawl.dev/v2/crawl/crawl-123").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )

        result = client.cancel_crawl("crawl-123")
        assert result is True

    def test_cancel_crawl_other_failure_returns_false(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.delete("https://api.firecrawl.dev/v2/crawl/crawl-123").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        result = client.cancel_crawl("crawl-123")
        assert result is False

    # Error mapping tests
    def test_auth_error_401(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized", "code": "invalid_api_key"})
        )

        with pytest.raises(FirecrawlAuthError) as exc:
            client.scrape_url("https://example.com")
        assert exc.value.status_code == 401
        assert exc.value.code == "invalid_api_key"

    def test_auth_error_403(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(403, json={"error": "Forbidden", "code": "access_denied"})
        )

        with pytest.raises(FirecrawlAuthError):
            client.scrape_url("https://example.com")

    def test_rate_limit_error_429(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(429, json={"error": "Rate limit exceeded", "code": "rate_limited"})
        )

        with pytest.raises(FirecrawlRateLimitError) as exc:
            client.scrape_url("https://example.com")
        assert exc.value.status_code == 429

    def test_validation_error_400(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(400, json={"error": "Invalid URL", "code": "validation_error"})
        )

        with pytest.raises(FirecrawlValidationError):
            client.scrape_url("https://example.com")

    def test_not_found_error_404(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.get("https://api.firecrawl.dev/v2/crawl/unknown").mock(
            return_value=httpx.Response(404, json={"error": "Not found", "code": "not_found"})
        )

        with pytest.raises(FirecrawlNotFoundError):
            client.get_crawl_status("unknown")

    def test_payment_required_402(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(402, json={"error": "Payment required", "code": "payment_required"})
        )

        with pytest.raises(FirecrawlPaymentRequiredError):
            client.scrape_url("https://example.com")

    def test_server_error_500(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            return_value=httpx.Response(500, json={"error": "Internal error", "code": "server_error"})
        )

        with pytest.raises(FirecrawlServerError):
            client.scrape_url("https://example.com")

    def test_network_error_retries_then_raises(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            side_effect=httpx.NetworkError("Connection failed")
        )

        with pytest.raises(FirecrawlNetworkError):
            client.scrape_url("https://example.com")

    def test_timeout_error_retries_then_raises(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(FirecrawlTimeoutError):
            client.scrape_url("https://example.com")

    def test_no_retry_on_auth_error(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        """Auth errors should not be retried."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(401, json={"error": "Unauthorized"})

        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(side_effect=handler)

        with pytest.raises(FirecrawlAuthError):
            client.scrape_url("https://example.com")

        assert call_count == 1  # Should not retry

    def test_no_retry_on_rate_limit(self, client: FirecrawlClient, respx_mock: respx.Router) -> None:
        """Rate limit errors should not be retried."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(429, json={"error": "Rate limited"})

        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(side_effect=handler)

        with pytest.raises(FirecrawlRateLimitError):
            client.scrape_url("https://example.com")

        assert call_count == 1  # Should not retry

    def test_retries_on_server_error(self, respx_mock: respx.Router) -> None:
        """Server errors should be retried."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(500, json={"error": "Internal error"})
            return httpx.Response(200, json={"data": {"markdown": "OK", "metadata": {}}})

        # Create a client with max_retries=2 (3 total attempts)
        client = FirecrawlClient(api_key="fc-test-key", max_retries=2)
        respx_mock.post("https://api.firecrawl.dev/v2/scrape").mock(side_effect=handler)

        result = client.scrape_url("https://example.com")
        assert result.markdown == "OK"
        assert call_count == 3  # Initial + 2 retries


class TestCrawlStatus:
    def test_is_terminal_completed(self) -> None:
        status = CrawlStatus(status="completed", total=10, completed=10)
        assert status.is_terminal is True

    def test_is_terminal_failed(self) -> None:
        status = CrawlStatus(status="failed", total=10, completed=5)
        assert status.is_terminal is True

    def test_is_terminal_cancelled(self) -> None:
        status = CrawlStatus(status="cancelled", total=10, completed=0)
        assert status.is_terminal is True

    def test_is_terminal_running(self) -> None:
        status = CrawlStatus(status="scraping", total=10, completed=5)
        assert status.is_terminal is False


class TestFirecrawlClientConfiguration:
    def test_client_from_settings_uses_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.scrapers.firecrawl_client import client_from_settings

        monkeypatch.setenv("FIRECRAWL_BASE_URL", "https://custom.firecrawl.dev")
        monkeypatch.setenv("FIRECRAWL_TIMEOUT_SECONDS", "60")
        monkeypatch.setenv("DISCOVERY_MAX_RETRIES", "3")
        monkeypatch.setenv("DISCOVERY_POLL_SECONDS", "10")

        # Need to clear the lru_cache
        from app.core.config import get_settings
        get_settings.cache_clear()

        client = client_from_settings("fc-test-key")
        assert client._base_url == "https://custom.firecrawl.dev"
        assert client._timeout == 60
        assert client._max_retries == 3
        assert client._poll_interval == 10

    def test_client_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="API key is required"):
            FirecrawlClient(api_key="")

    def test_client_strips_trailing_slash_from_base_url(self) -> None:
        client = FirecrawlClient(api_key="fc-test", base_url="https://api.firecrawl.dev/")
        assert client._base_url == "https://api.firecrawl.dev"