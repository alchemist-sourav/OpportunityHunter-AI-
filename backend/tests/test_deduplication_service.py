from __future__ import annotations

import pytest

from app.scrapers.deduplication_service import (
    normalize_url,
    generate_fingerprint,
    generate_opportunity_fingerprint,
    is_similar_opportunity,
    DuplicateDetector,
)
from app.models.opportunity_models import Opportunity


class TestNormalizeUrl:
    def test_basic_normalization(self) -> None:
        result = normalize_url("https://www.example.com/path?utm_source=google&param=value")
        assert result.domain == "example.com"
        assert result.path == "/path"
        assert "utm_source" not in result.query_params
        assert result.query_params.get("param") == "value"

    def test_www_stripping(self) -> None:
        result = normalize_url("https://www.example.com/path")
        assert result.domain == "example.com"

    def test_trailing_slash_removal(self) -> None:
        result = normalize_url("https://example.com/path/")
        assert result.path == "/path"

    def test_case_insensitive(self) -> None:
        result = normalize_url("HTTPS://EXAMPLE.COM/PATH")
        assert result.domain == "example.com"
        assert result.url.startswith("https://")

    def test_remove_all_tracking_params(self) -> None:
        url = "https://example.com/job?utm_source=linkedin&utm_medium=email&utm_campaign=hiring&ref=linkedin&fbclid=123"
        result = normalize_url(url)
        assert result.query_params == {}

    def test_preserve_non_tracking_params(self) -> None:
        url = "https://example.com/job?utm_source=google&page=2&sort=date"
        result = normalize_url(url)
        assert result.query_params.get("page") == "2"
        assert result.query_params.get("sort") == "date"
        assert "utm_source" not in result.query_params


class TestGenerateFingerprint:
    def test_fingerprint_consistency(self) -> None:
        fp1 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        fp2 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        assert fp1 == fp2

    def test_fingerprint_different_title(self) -> None:
        fp1 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        fp2 = generate_fingerprint("Senior Software Engineer", "TechCorp", "https://example.com/job/1")
        assert fp1 != fp2

    def test_fingerprint_different_company(self) -> None:
        fp1 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        fp2 = generate_fingerprint("Software Engineer", "OtherCorp", "https://example.com/job/1")
        assert fp1 != fp2

    def test_fingerprint_different_url(self) -> None:
        fp1 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        fp2 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/2")
        assert fp1 != fp2

    def test_fingerprint_normalizes_whitespace(self) -> None:
        fp1 = generate_fingerprint("Software  Engineer", "TechCorp", "https://example.com/job/1")
        fp2 = generate_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        assert fp1 == fp2

    def test_fingerprint_normalizes_case(self) -> None:
        fp1 = generate_fingerprint("SOFTWARE ENGINEER", "TECHCORP", "https://example.com/job/1")
        fp2 = generate_fingerprint("software engineer", "techcorp", "https://example.com/job/1")
        assert fp1 == fp2


class TestGenerateOpportunityFingerprint:
    def test_returns_fingerprint_object(self) -> None:
        fp = generate_opportunity_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        assert hasattr(fp, 'fingerprint')
        assert hasattr(fp, 'title_normalized')
        assert hasattr(fp, 'company_normalized')
        assert hasattr(fp, 'url_normalized')

    def test_title_normalization(self) -> None:
        fp = generate_opportunity_fingerprint("Software  Engineer!", "TechCorp", "https://example.com/job/1")
        assert fp.title_normalized == "software engineer"

    def test_company_normalization(self) -> None:
        fp = generate_opportunity_fingerprint("Software Engineer", "TechCorp Inc.", "https://example.com/job/1")
        assert fp.company_normalized == "techcorp inc"

    def test_url_normalization(self) -> None:
        fp = generate_opportunity_fingerprint("Software Engineer", "TechCorp", "https://www.example.com/job?utm_source=test")
        assert fp.url_normalized == "https://example.com/job"


class TestDuplicateDetector:
    @pytest.fixture
    def mock_session(self, monkeypatch: pytest.MonkeyPatch):
        from sqlalchemy.orm import Session
        from unittest.mock import MagicMock
        
        mock_session = MagicMock(spec=Session)
        return mock_session

    def test_detect_exact_fingerprint_match(self, mock_session) -> None:
        from app.models.opportunity_models import Opportunity
        
        # Generate the actual fingerprint for the test data
        fp = generate_opportunity_fingerprint("Software Engineer", "TechCorp", "https://example.com/job/1")
        
        existing = Opportunity(
            id="opp-1",
            fingerprint=fp.fingerprint,
            title="Software Engineer",
            company_name="TechCorp",
            source_url="https://example.com/job/1",
            source_domain="example.com",
        )
        mock_session.scalar.return_value = existing
        
        detector = DuplicateDetector(mock_session)
        result, fp_result = detector.check_and_register("Software Engineer", "TechCorp", "https://example.com/job/1")
        
        assert result is existing
        assert fp_result.fingerprint == fp.fingerprint

    def test_no_duplicate_returns_none(self, mock_session) -> None:
        mock_session.scalar.return_value = None
        
        detector = DuplicateDetector(mock_session)
        result = detector.check_and_register("New Job", "NewCorp", "https://example.com/new")
        
        assert result is None


class TestIsSimilarOpportunity:
    def test_exact_fingerprint_match(self) -> None:
        from app.models.opportunity_models import Opportunity
        
        existing = Opportunity(
            id="opp-1",
            fingerprint="abc123",
            source_url="https://example.com/job/1",
        )
        
        result = is_similar_opportunity(existing, "Software Engineer", "TechCorp", "https://example.com/job/1")
        assert result is True

    def test_same_url_normalized(self) -> None:
        from app.models.opportunity_models import Opportunity
        
        existing = Opportunity(
            id="opp-1",
            fingerprint="different123",
            source_url="https://www.example.com/job?utm_source=test",
        )
        
        result = is_similar_opportunity(existing, "Any Title", "Any Company", "https://example.com/job")
        assert result is True