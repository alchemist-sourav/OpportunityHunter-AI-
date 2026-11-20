from __future__ import annotations

import pytest

from app.scrapers.extraction_service import DeterministicExtractor, ExtractionResult, OpportunityType, EmploymentType


class TestDeterministicExtractor:
    @pytest.fixture
    def extractor(self) -> DeterministicExtractor:
        return DeterministicExtractor()

    def test_extract_internship(self, extractor: DeterministicExtractor) -> None:
        markdown = """
        # Software Engineering Internship
        Company: TechCorp
        Location: San Francisco, CA
        We are looking for a student intern to join our team.
        Skills: Python, JavaScript, React
        """
        metadata = {"sourceURL": "https://example.com/jobs/intern-1", "title": "Software Engineering Internship"}
        
        result = extractor.extract("https://example.com/jobs/intern-1", markdown, metadata)
        
        assert isinstance(result, ExtractionResult)
        assert result.opportunity_type == OpportunityType.INTERNSHIP
        assert "python" in [s.lower() for s in result.required_skills]
        assert result.experience_level == "student"

    def test_extract_fresher_job(self, extractor: DeterministicExtractor) -> None:
        markdown = """
        # Junior Software Engineer
        Company: StartupInc
        Entry level position for fresh graduates.
        Required: Java, Spring Boot, SQL
        """
        metadata = {"sourceURL": "https://example.com/jobs/fresher-1", "title": "Junior Software Engineer"}
        
        result = extractor.extract("https://example.com/jobs/fresher-1", markdown, {})
        
        assert result.opportunity_type == OpportunityType.FRESHER_JOB
        assert "java" in [s.lower() for s in result.required_skills]
        assert result.experience_level == "fresher"

    def test_extract_full_time_job(self, extractor: DeterministicExtractor) -> None:
        markdown = """
        # Senior Software Engineer
        Company: BigTech
        Full-time permanent position.
        Salary: $120,000 - $150,000
        Skills: Python, AWS, Kubernetes
        """
        metadata = {"sourceURL": "https://example.com/jobs/senior-1", "title": "Senior Software Engineer"}
        
        result = extractor.extract("https://example.com/jobs/senior-1", markdown, {})
        
        assert result.opportunity_type == OpportunityType.FULL_TIME_JOB
        assert result.salary_min == 120000
        assert result.salary_max == 150000
        assert result.salary_currency == "USD"

    def test_extract_freelance_project(self, extractor: DeterministicExtractor) -> None:
        markdown = """
        # Freelance Web Developer
        Contract position for 3 months.
        Skills: React, TypeScript, Node.js
        """
        metadata = {"sourceURL": "https://example.com/jobs/freelance-1", "title": "Freelance Web Developer"}
        
        result = extractor.extract("https://example.com/jobs/freelance-1", markdown, {})
        
        assert result.opportunity_type == OpportunityType.FREELANCE_PROJECT
        assert result.employment_type == EmploymentType.FREELANCE

    def test_extract_skills(self, extractor: DeterministicExtractor) -> None:
        markdown = """
        # Developer Position
        Required skills: Python, JavaScript, React, AWS, Docker, Kubernetes, SQL, Git
        """
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        skills_lower = [s.lower() for s in result.required_skills]
        assert "python" in skills_lower
        assert "javascript" in skills_lower
        assert "react" in skills_lower
        assert "aws" in skills_lower
        assert "docker" in skills_lower

    def test_extract_salary_range(self, extractor: DeterministicExtractor) -> None:
        markdown = "Salary: $100,000 - $130,000 per year"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.salary_min == 100000
        assert result.salary_max == 130000
        assert result.salary_currency == "USD"

    def test_extract_salary_single(self, extractor: DeterministicExtractor) -> None:
        markdown = "Salary: $120,000 per year"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.salary_min == 120000
        assert result.salary_max == 120000

    def test_extract_eur_salary(self, extractor: DeterministicExtractor) -> None:
        markdown = "Salary: €60,000 - €80,000"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.salary_currency == "EUR"
        assert result.salary_min == 60000
        assert result.salary_max == 80000

    def test_extract_remote_only(self, extractor: DeterministicExtractor) -> None:
        markdown = "Fully remote position. Work from anywhere."
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.remote_preference == "remote_only"

    def test_extract_hybrid(self, extractor: DeterministicExtractor) -> None:
        markdown = "Hybrid work model - 3 days in office."
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.remote_preference == "hybrid"

    def test_extract_onsite(self, extractor: DeterministicExtractor) -> None:
        markdown = "Onsite position in our New York office."
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.remote_preference == "onsite_only"

    def test_extract_application_url(self, extractor: DeterministicExtractor) -> None:
        markdown = "Apply here: https://company.com/apply/123"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.application_url == "https://company.com/apply/123"

    def test_extract_deadline(self, extractor: DeterministicExtractor) -> None:
        markdown = "Apply by: 12/31/2024"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.application_deadline is not None

    def test_extract_employment_type_full_time(self, extractor: DeterministicExtractor) -> None:
        markdown = "Full-time permanent position"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.employment_type == EmploymentType.FULL_TIME

    def test_extract_employment_type_contract(self, extractor: DeterministicExtractor) -> None:
        markdown = "Contract position for 6 months"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.employment_type == EmploymentType.CONTRACT

    def test_confidence_score(self, extractor: DeterministicExtractor) -> None:
        markdown = "# Software Engineer\nCompany: TestCorp"
        metadata = {}
        
        result = extractor.extract("https://example.com/job", markdown, {})
        
        assert result.confidence == 0.6