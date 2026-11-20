from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CRAWL_STARTED = "scraping"
CRAWL_ACTIVE = ("scraping",)
CRAWL_CANCELLED = "cancelled"
CRAWL_FAILED = "failed"
CRAWL_COMPLETED = "completed"


class FirecrawlError(Exception):
    """Base class for structured Firecrawl client errors."""

    error_code = "firecrawl_error"

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class FirecrawlAuthError(FirecrawlError):
    error_code = "firecrawl_auth_error"


class FirecrawlPaymentRequiredError(FirecrawlError):
    error_code = "firecrawl_payment_required"


class FirecrawlValidationError(FirecrawlError):
    error_code = "firecrawl_validation_error"


class FirecrawlNotFoundError(FirecrawlError):
    error_code = "firecrawl_not_found"


class FirecrawlRateLimitError(FirecrawlError):
    error_code = "firecrawl_rate_limited"


class FirecrawlServerError(FirecrawlError):
    error_code = "firecrawl_server_error"


class FirecrawlNetworkError(FirecrawlError):
    error_code = "firecrawl_network_error"


class FirecrawlTimeoutError(FirecrawlError):
    error_code = "firecrawl_timeout"


class CrawlStart:
    def __init__(self, id: str, url: str) -> None:
        self.id = id
        self.url = url


class CrawlDocument:
    def __init__(
        self,
        url: str,
        final_url: str,
        title: str | None,
        status_code: int | None,
        markdown: str,
        error: str | None,
    ) -> None:
        self.url = url
        self.final_url = final_url
        self.title = title
        self.status_code = status_code
        self.markdown = markdown
        self.error = error


class CrawlStatus:
    def __init__(
        self,
        status: str,
        total: int = 0,
        completed: int = 0,
        credits_used: int = 0,
        documents: list[CrawlDocument] | None = None,
        error: str | None = None,
    ) -> None:
        self.status = status
        self.total = total
        self.completed = completed
        self.credits_used = credits_used
        self.documents = documents or []
        self.error = error

    @property
    def is_terminal(self) -> bool:
        return self.status in (CRAWL_COMPLETED, CRAWL_FAILED, CRAWL_CANCELLED)


class FirecrawlClient:
    """Minimal backend-only HTTP client for the Firecrawl v2 API.

    Never logs API keys. Retries only transient failures (timeouts, network
    errors, 5xx) with bounded exponential backoff; authentication and
    rate-limit errors are surfaced immediately as structured exceptions.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev",
        timeout_seconds: int = 30,
        max_retries: int = 2,
        poll_interval_seconds: int = 5,
    ) -> None:
        if not api_key:
            raise ValueError("A Firecrawl API key is required.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._poll_interval = poll_interval_seconds
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FirecrawlClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── private helpers ───────────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self._base_url}{path}"
        attempts = self._max_retries + 1
        last_error: FirecrawlError | None = None
        for attempt in range(attempts):
            try:
                response = self._client.request(method, url, **kwargs)
            except httpx.TimeoutException as exc:
                last_error = FirecrawlTimeoutError("Firecrawl request timed out.", status_code=exc.__class__)
                logger.info("firecrawl_timeout method=%s path=%s attempt=%s", method, path, attempt + 1)
            except httpx.HTTPError as exc:
                last_error = FirecrawlNetworkError(f"Firecrawl request failed: {exc.__class__.__name__}.")
                logger.info("firecrawl_network_error method=%s path=%s attempt=%s", method, path, attempt + 1)
            else:
                error = self._map_error(response)
                if error is None:
                    return response
                last_error = error
                if not self._is_retryable(error):
                    raise error
                logger.info("firecrawl_retry method=%s path=%s status=%s attempt=%s", method, path, response.status_code, attempt + 1)
            if attempt < attempts - 1:
                time.sleep(0.5 * (2**attempt))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _is_retryable(error: FirecrawlError) -> bool:
        return isinstance(error, (FirecrawlServerError, FirecrawlTimeoutError, FirecrawlNetworkError))

    @staticmethod
    def _map_error(response: httpx.Response) -> FirecrawlError | None:
        if 200 <= response.status_code < 300:
            return None
        body = _json_body(response)
        message = body.get("error") or body.get("message") or f"Firecrawl returned HTTP {response.status_code}."
        code = body.get("code")
        if response.status_code in (401, 403):
            return FirecrawlAuthError(message, response.status_code, code)
        if response.status_code == 402:
            return FirecrawlPaymentRequiredError(message, response.status_code, code)
        if response.status_code in (400, 422):
            return FirecrawlValidationError(message, response.status_code, code)
        if response.status_code == 404:
            return FirecrawlNotFoundError(message, response.status_code, code)
        if response.status_code == 429:
            return FirecrawlRateLimitError(message, response.status_code, code)
        if response.status_code >= 500:
            return FirecrawlServerError(message, response.status_code, code)
        return FirecrawlError(message, response.status_code, code)

    # ── public capabilities ──────────────────────────────────────────────

    def scrape_url(self, url: str, formats: list[str] | None = None) -> CrawlDocument:
        response = self._request(
            "POST",
            "/v2/scrape",
            json={"url": url, "formats": formats or ["markdown"], "onlyMainContent": True},
        )
        payload = response.json()
        data = payload.get("data") or {}
        metadata = data.get("metadata") or {}
        return CrawlDocument(
            url=url,
            final_url=metadata.get("url") or metadata.get("sourceURL") or url,
            title=metadata.get("title"),
            status_code=metadata.get("statusCode"),
            markdown=data.get("markdown") or "",
            error=metadata.get("error") or data.get("error"),
        )

    def start_crawl(
        self,
        url: str,
        limit: int = 20,
        include_paths: list[str] | None = None,
        max_depth: int = 2,
    ) -> CrawlStart:
        payload: dict[str, Any] = {
            "url": url,
            "limit": limit,
            "maxDiscoveryDepth": max_depth,
            "ignoreQueryParameters": True,
            "ignoreRobotsTxt": False,
            "allowExternalLinks": False,
            "allowSubdomains": False,
            "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
        }
        if include_paths:
            payload["includePaths"] = include_paths
        response = self._request("POST", "/v2/crawl", json=payload)
        body = response.json()
        if not body.get("id"):
            raise FirecrawlValidationError("Firecrawl did not return a crawl id.")
        return CrawlStart(id=str(body["id"]), url=body.get("url") or url)

    def get_crawl_status(self, crawl_id: str) -> CrawlStatus:
        response = self._request("GET", f"/v2/crawl/{crawl_id}")
        body = response.json()
        status = str(body.get("status") or "")
        documents: list[CrawlDocument] = []
        for raw in body.get("data") or []:
            item = raw.get("data") or {}
            metadata = item.get("metadata") or {}
            url = metadata.get("sourceURL") or raw.get("url") or ""
            documents.append(
                CrawlDocument(
                    url=url,
                    final_url=metadata.get("url") or url,
                    title=metadata.get("title"),
                    status_code=metadata.get("statusCode"),
                    markdown=item.get("markdown") or "",
                    error=metadata.get("error") or item.get("error"),
                )
            )
        return CrawlStatus(
            status=status,
            total=int(body.get("total") or 0),
            completed=int(body.get("completed") or 0),
            credits_used=int(body.get("creditsUsed") or 0),
            documents=documents,
            error=body.get("error"),
        )

    def cancel_crawl(self, crawl_id: str) -> bool:
        try:
            response = self._request("DELETE", f"/v2/crawl/{crawl_id}")
        except FirecrawlNotFoundError:
            # Crawl doesn't exist - treat as already cancelled
            return True
        except FirecrawlServerError:
            # Server error - don't retry cancel, just return False
            return False
        body = _json_body(response)
        if isinstance(body.get("success"), bool):
            return body["success"]
        return response.status_code < 400


def _json_body(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def client_from_settings(api_key: str) -> FirecrawlClient:
    from app.core.config import get_settings

    settings = get_settings()
    return FirecrawlClient(
        api_key=api_key,
        base_url=settings.firecrawl_base_url,
        timeout_seconds=settings.firecrawl_timeout_seconds,
        max_retries=settings.discovery_max_retries,
        poll_interval_seconds=settings.discovery_poll_seconds,
    )
