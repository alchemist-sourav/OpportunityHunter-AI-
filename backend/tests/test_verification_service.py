from __future__ import annotations

import pytest
import respx
import httpx

from app.scrapers.verification_service import VerificationService, VerificationResult, VerificationStatus


class TestVerificationService:
    @pytest.fixture
    def service(self) -> VerificationService:
        return VerificationService()

    @pytest.fixture
    def mock_opportunity(self):
        from app.models.opportunity_models import Opportunity
        return Opportunity(
            id="opp-1",
            application_url="https://example.com/apply/1",
            source_url=None,
            source_domain="example.com",
        )

    def _make_response(self, status_code: int, text: str = "", url: str = "", headers: dict | None = None) -> httpx.Response:
        """Create a mock httpx.Response with the given parameters."""
        return httpx.Response(status_code, text=text, headers=headers or {})

    @pytest.mark.asyncio
    async def test_verify_no_urls(self, service: VerificationService) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(id="opp-1", application_url=None, source_url=None)
        
        result = await service.verify(opp)
        
        assert result.status == VerificationStatus.UNCERTAIN
        assert result.failure_reason == "No application or source URL"
        assert result.redirect_chain == []

    @pytest.mark.asyncio
    async def test_verify_active(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=self._make_response(200)
        )
        respx_mock.get("https://example.com/apply/1").mock(
            return_value=httpx.Response(200, text="Great job opportunity! Apply now.")
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.ACTIVE
        assert result.status_code == 200
        assert "example.com/apply/1" in result.final_url

    @pytest.mark.asyncio
    async def test_verify_closed(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=self._make_response(200)
        )
        respx_mock.get("https://example.com/apply/1").mock(
            return_value=httpx.Response(200, text="This position has been filled. Position closed.")
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.CLOSED

    @pytest.mark.asyncio
    async def test_verify_expired(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=self._make_response(200)
        )
        respx_mock.get("https://example.com/apply/1").mock(
            return_value=httpx.Response(200, text="Deadline has passed. Application period ended.")
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_verify_404(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(404)
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.INACCESSIBLE
        assert result.failure_reason is not None
        assert "404" in result.failure_reason

    @pytest.mark.asyncio
    async def test_verify_403(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(403)
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.UNCERTAIN
        assert result.failure_reason is not None

    @pytest.mark.asyncio
    async def test_verify_429(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(429)
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.UNCERTAIN
        assert result.failure_reason is not None

    @pytest.mark.asyncio
    async def test_verify_500(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(500)
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.UNCERTAIN
        assert result.failure_reason is not None

    @pytest.mark.asyncio
    async def test_verify_timeout(self, service: VerificationService, mock_opportunity, respx_mock: respx.Router) -> None:
        respx_mock.head("https://example.com/apply/1").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        result = await service.verify(mock_opportunity)
        
        assert result.status == VerificationStatus.UNCERTAIN
        assert result.failure_reason is not None

    @pytest.mark.asyncio
    async def test_verify_source_url_fallback(self, service: VerificationService, respx_mock: respx.Router) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(
            id="opp-1",
            application_url=None,
            source_url="https://example.com/job/1",
            source_domain="example.com",
        )
        
        respx_mock.head("https://example.com/job/1").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.get("https://example.com/job/1").mock(
            return_value=httpx.Response(200, text="Job description here")
        )
        
        result = await service.verify(opp)
        
        assert result.status == VerificationStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_verify_both_urls(self, service: VerificationService, respx_mock: respx.Router) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(
            id="opp-1",
            application_url="https://example.com/apply/1",
            source_url="https://example.com/job/1",
            source_domain="example.com",
        )
        
        # Application URL returns 404
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(404)
        )
        # Source URL returns 200
        respx_mock.head("https://example.com/job/1").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.get("https://example.com/job/1").mock(
            return_value=httpx.Response(200, text="Job details")
        )
        
        result = await service.verify(opp)
        
        assert result.status == VerificationStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_verify_redirect_chain(self, service: VerificationService, respx_mock: respx.Router) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(
            id="opp-1",
            application_url="https://example.com/apply/1",
            source_url=None,
            source_domain="example.com",
        )
        
        respx_mock.head("https://example.com/apply/1").mock(
            return_value=httpx.Response(301, headers={"Location": "https://example.com/apply/2"})
        )
        respx_mock.head("https://example.com/apply/2").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.get("https://example.com/apply/2").mock(
            return_value=httpx.Response(200, text="Final page")
        )
        
        result = await service.verify(opp)
        
        assert result.status == VerificationStatus.ACTIVE
        assert len(result.redirect_chain) >= 1

    @pytest.mark.asyncio
    async def test_verify_private_ip_blocked(self, service: VerificationService) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(
            id="opp-1",
            application_url="http://192.168.1.100/job",
            source_url="http://192.168.1.100/job",
            source_domain="192.168.1.100",
        )
        
        result = await service.verify(opp)
        
        assert result.status in (VerificationStatus.UNCERTAIN, VerificationStatus.INACCESSIBLE)

    @pytest.mark.asyncio
    async def test_verify_metadata_endpoint_blocked(self, service: VerificationService) -> None:
        from app.models.opportunity_models import Opportunity
        opp = Opportunity(
            id="opp-1",
            application_url="http://169.254.169.254/latest/meta-data/",
            source_url="http://169.254.169.254/latest/meta-data/",
            source_domain="169.254.169.254",
        )
        
        result = await service.verify(opp)
        
        assert result.status in (VerificationStatus.UNCERTAIN, VerificationStatus.INACCESSIBLE)