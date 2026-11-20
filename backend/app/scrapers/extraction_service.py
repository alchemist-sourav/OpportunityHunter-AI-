from __future__ import annotations

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.core.config import get_settings
from app.models.opportunity_models import EmploymentType, OpportunityType, VerificationStatus

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    title: str | None
    company_name: str | None
    description: str | None
    opportunity_type: OpportunityType | None
    required_skills: list[str]
    experience_level: str | None
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    application_url: str | None
    application_deadline: datetime | None
    employment_type: EmploymentType | None
    confidence: float
    raw_extracted: dict[str, Any]


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, url: str, markdown: str, metadata: dict[str, Any]) -> ExtractionResult:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class DeterministicExtractor(BaseExtractor):
    def name(self) -> str:
        return "deterministic"

    def extract(self, url: str, markdown: str, metadata: dict[str, Any]) -> ExtractionResult:
        title = self._extract_title(markdown, metadata)
        company_name = self._extract_company(markdown, metadata, url)
        description = self._extract_description(markdown)
        opportunity_type = self._extract_opportunity_type(markdown, url)
        required_skills = self._extract_skills(markdown)
        experience_level = self._extract_experience_level(markdown)
        location = self._extract_location(markdown, metadata)
        remote_preference = self._extract_remote_preference(markdown)
        salary_min, salary_max, salary_currency = self._extract_salary(markdown)
        application_url = self._extract_application_url(markdown, url)
        application_deadline = self._extract_deadline(markdown)
        employment_type = self._extract_employment_type(markdown, url)

        return ExtractionResult(
            title=title,
            company_name=company_name,
            description=description,
            opportunity_type=opportunity_type,
            required_skills=required_skills,
            experience_level=experience_level,
            location=location,
            remote_preference=remote_preference,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            application_url=application_url,
            application_deadline=application_deadline,
            employment_type=employment_type,
            confidence=0.6,
            raw_extracted={},
        )

    def _extract_title(self, markdown: str, metadata: dict[str, Any]) -> str | None:
        if metadata.get("title"):
            return metadata["title"][:500]
        lines = markdown.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()[:500]
            if line.startswith("## "):
                return line[3:].strip()[:500]
        return None

    def _extract_company(self, markdown: str, metadata: dict[str, Any], url: str) -> str | None:
        if metadata.get("ogSiteName"):
            return metadata["ogSiteName"][:255]
        domain = urlparse(url).netloc
        return domain.replace("www.", "")[:255]

    def _extract_description(self, markdown: str) -> str | None:
        content = markdown.strip()
        if len(content) > 100:
            return content[:5000]
        return content if content else None

    def _extract_opportunity_type(self, markdown: str, url: str) -> OpportunityType | None:
        text = (markdown + " " + url).lower()
        if any(kw in text for kw in ["intern", "internship"]):
            return OpportunityType.INTERNSHIP
        if any(kw in text for kw in ["fresher", "entry level", "entry-level", "new grad", "recent graduate"]):
            return OpportunityType.FRESHER_JOB
        if any(kw in text for kw in ["full time", "full-time", "permanent", "salary"]):
            return OpportunityType.FULL_TIME_JOB
        if any(kw in text for kw in ["freelance", "gig", "project-based"]):
            return OpportunityType.FREELANCE_PROJECT
        if "contract" in text and "contractor" not in text:
            return OpportunityType.FREELANCE_PROJECT
        return None

    def _extract_skills(self, markdown: str) -> list[str]:
        skills_keywords = [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#", "ruby", "php",
            "react", "vue", "angular", "svelte", "next.js", "node.js", "django", "flask", "fastapi",
            "spring", "express", "rails", "laravel",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
            "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
            "git", "ci/cd", "jenkins", "github actions", "gitlab ci",
            "machine learning", "ml", "ai", "deep learning", "nlp", "computer vision",
            "data analysis", "pandas", "numpy", "tableau", "power bi",
            "rest", "graphql", "grpc", "microservices", "api design",
            "agile", "scrum", "kanban", "jira", "confluence",
        ]
        text = markdown.lower()
        found = []
        for skill in skills_keywords:
            if skill in text:
                found.append(skill.title() if " " not in skill else skill.upper() if skill.isupper() else skill)
        return found[:50]

    def _extract_experience_level(self, markdown: str) -> str | None:
        text = markdown.lower()
        if any(kw in text for kw in ["fresher", "entry level", "entry-level", "0-1", "0 to 1", "new grad", "recent graduate"]):
            return "fresher"
        if any(kw in text for kw in ["student", "university", "college", "degree", "graduat"]):
            return "student"
        if any(kw in text for kw in ["junior", "1-2", "1 to 2", "2-3", "2 to 3"]):
            return "junior"
        if any(kw in text for kw in ["senior", "lead", "principal", "staff", "5+", "7+", "10+", "expert"]):
            return "experienced"
        return None

    def _extract_location(self, markdown: str, metadata: dict[str, Any]) -> str | None:
        location_patterns = [
            r"(?:location|based in|office in)\s*[:\-]\s*([^,\n]+)",
            r"(?:remote|hybrid|onsite)\s*(?:in|at|from)\s+([^,\n]+)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:255]
        return None

    def _extract_remote_preference(self, markdown: str) -> str | None:
        text = markdown.lower()
        if "remote only" in text or "fully remote" in text or "work from anywhere" in text:
            return "remote_only"
        if "hybrid" in text:
            return "hybrid"
        if "onsite" in text or "on-site" in text or "office" in text:
            return "onsite_only"
        return None

    def _extract_salary(self, markdown: str) -> tuple[int | None, int | None, str | None]:
        text = markdown
        currency = "USD"
        if "€" in text or "eur" in text.lower():
            currency = "EUR"
        elif "£" in text or "gbp" in text.lower():
            currency = "GBP"
        elif "₹" in text or "inr" in text.lower():
            currency = "INR"

        salary_patterns = [
            r"(?:salary|compensation|pay)\s*[:\-]\s*[\$€£₹]?(\d[\d,]*)\s*[-–to]\s*[\$€£₹]?(\d[\d,]*)",
            r"[\$€£₹](\d[\d,]*)\s*[-–to]\s*[\$€£₹](\d[\d,]*)",
            r"(?:salary|compensation|pay)\s*[:\-]\s*[\$€£₹]?(\d[\d,]*)",
            r"[\$€£₹](\d[\d,]*)\s*(?:per year|/year|annual)",
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        min_val = int(groups[0].replace(",", ""))
                        max_val = int(groups[1].replace(",", ""))
                        return min_val, max_val, currency
                    except ValueError:
                        pass
                elif len(groups) == 1:
                    try:
                        val = int(groups[0].replace(",", ""))
                        return val, val, currency
                    except ValueError:
                        pass
        return None, None, currency

    def _extract_application_url(self, markdown: str, source_url: str) -> str | None:
        url_pattern = r'https?://[^\s\)\]\}]+'
        urls = re.findall(url_pattern, markdown)
        for url in urls:
            if any(kw in url.lower() for kw in ["apply", "application", "career", "job", "hiring"]):
                return url
        return source_url if source_url else None

    def _extract_deadline(self, markdown: str) -> datetime | None:
        date_patterns = [
            r"(?:deadline|apply by|closes?|closing date)\s*[:\-]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            r"(?:deadline|apply by|closes?|closing date)\s*[:\-]\s*(\w+\s+\d{1,2},?\s+\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y"):
                    try:
                        return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
        return None

    def _extract_employment_type(self, markdown: str, url: str) -> EmploymentType | None:
        text = (markdown + " " + url).lower()
        if any(kw in text for kw in ["full time", "full-time", "permanent"]):
            return EmploymentType.FULL_TIME
        if any(kw in text for kw in ["part time", "part-time"]):
            return EmploymentType.PART_TIME
        if any(kw in text for kw in ["freelance", "gig"]):
            return EmploymentType.FREELANCE
        if any(kw in text for kw in ["contract", "contractor"]):
            return EmploymentType.CONTRACT
        if any(kw in text for kw in ["temporary", "temp", "seasonal"]):
            return EmploymentType.TEMPORARY
        if "intern" in text:
            return EmploymentType.INTERNSHIP
        return EmploymentType.UNKNOWN


class LLMExtractor(BaseExtractor):
    def __init__(self) -> None:
        self._client = None
        self._model = None

    def name(self) -> str:
        return "llm"

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                settings = get_settings()
                if settings.openai_api_key:
                    self._client = OpenAI(api_key=settings.openai_api_key)
                    self._model = getattr(settings, "openai_model", "gpt-4o-mini")
            except ImportError:
                logger.warning("openai package not installed, LLM extraction unavailable")
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)
        return self._client

    def extract(self, url: str, markdown: str, metadata: dict[str, Any]) -> ExtractionResult:
        client = self._get_client()
        if not client:
            logger.info("LLM extractor unavailable, falling back to deterministic")
            return DeterministicExtractor().extract(url, markdown, metadata)

        prompt = self._build_prompt(url, markdown[:8000], metadata)
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                return self._parse_llm_result(data, url)
        except Exception as e:
            logger.warning("LLM extraction failed: %s, falling back to deterministic", e)
        return DeterministicExtractor().extract(url, markdown, metadata)

    def _system_prompt(self) -> str:
        return """You are an expert at extracting structured job opportunity data from web page content.
Extract the following fields as JSON. If a field cannot be determined, use null.
Never invent values - only extract what is explicitly stated in the content.

Fields:
- title: Job title (string)
- company_name: Company name (string)
- description: Job description (string)
- opportunity_type: One of "internship", "fresher_job", "full_time_job", "freelance_project"
- required_skills: Array of skill strings
- experience_level: One of "student", "fresher", "junior", "experienced"
- location: Location string (city, state, country, or "Remote")
- remote_preference: One of "remote_only", "hybrid", "onsite_only", "no_preference"
- salary_min: Minimum annual salary in base units (integer)
- salary_max: Maximum annual salary in base units (integer)
- salary_currency: 3-letter currency code (USD, EUR, GBP, INR, etc.)
- application_url: Direct link to apply (string)
- application_deadline: ISO 8601 datetime string (YYYY-MM-DDTHH:MM:SSZ)
- employment_type: One of "full_time", "part_time", "contract", "temporary", "internship", "freelance", "unknown"

Return only valid JSON."""

    def _build_prompt(self, url: str, markdown: str, metadata: dict[str, Any]) -> str:
        return f"""Source URL: {url}
Page Title: {metadata.get('title', 'N/A')}
Source Domain: {metadata.get('sourceURL', url)}

Page Content (truncated):
{markdown}"""

    def _parse_llm_result(self, data: dict[str, Any], url: str) -> ExtractionResult:
        def safe_enum(enum_cls, value):
            if value is None:
                return None
            try:
                return enum_cls(value)
            except ValueError:
                return None

        def parse_datetime(value):
            if not value:
                return None
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return None

        return ExtractionResult(
            title=data.get("title"),
            company_name=data.get("company_name"),
            description=data.get("description"),
            opportunity_type=safe_enum(OpportunityType, data.get("opportunity_type")),
            required_skills=data.get("required_skills") or [],
            experience_level=data.get("experience_level"),
            location=data.get("location"),
            remote_preference=data.get("remote_preference"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=data.get("salary_currency"),
            application_url=data.get("application_url"),
            application_deadline=parse_datetime(data.get("application_deadline")),
            employment_type=safe_enum(EmploymentType, data.get("employment_type")),
            confidence=0.85,
            raw_extracted=data,
        )


class ExtractionService:
    def __init__(self) -> None:
        self._deterministic = DeterministicExtractor()
        self._llm = LLMExtractor()
        self._use_llm = getattr(get_settings(), "enable_llm_extraction", False)

    def extract(self, url: str, markdown: str, metadata: dict[str, Any]) -> ExtractionResult:
        if self._use_llm:
            return self._llm.extract(url, markdown, metadata)
        return self._deterministic.extract(url, markdown, metadata)