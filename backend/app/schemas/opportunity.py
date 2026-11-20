from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.opportunity_models import EmploymentType, OpportunityType, VerificationStatus
from app.schemas.enums import ExperienceLevel, RemotePreference


class OpportunityBase(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    company_name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    opportunity_type: OpportunityType | None = None
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    experience_level: ExperienceLevel | None = None
    location: str | None = Field(default=None, max_length=255)
    remote_preference: RemotePreference | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    application_url: str | None = None
    source_url: str
    source_domain: str = Field(max_length=255)
    application_deadline: datetime | None = None
    employment_type: EmploymentType | None = None

    @field_validator("salary_currency")
    @classmethod
    def _validate_currency(cls, v: str | None) -> str | None:
        if v is not None and len(v) != 3:
            raise ValueError("Currency must be 3-letter ISO code")
        return v.upper() if v else v

    @field_validator("salary_max")
    @classmethod
    def _validate_salary_range(cls, v: int | None, info) -> int | None:
        if v is not None and info.data.get("salary_min") is not None:
            if v < info.data["salary_min"]:
                raise ValueError("salary_max must be >= salary_min")
        return v


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    company_name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    opportunity_type: OpportunityType | None = None
    required_skills: list[str] | None = Field(default=None, max_length=50)
    experience_level: ExperienceLevel | None = None
    location: str | None = Field(default=None, max_length=255)
    remote_preference: RemotePreference | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    application_url: str | None = None
    application_deadline: datetime | None = None
    employment_type: EmploymentType | None = None
    verification_status: VerificationStatus | None = None

    @field_validator("salary_currency")
    @classmethod
    def _validate_currency(cls, v: str | None) -> str | None:
        if v is not None and len(v) != 3:
            raise ValueError("Currency must be 3-letter ISO code")
        return v.upper() if v else v


class OpportunitySourceResponse(BaseModel):
    id: int
    discovery_job_id: str
    user_id: str
    source_url: str
    source_domain: str
    extracted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityResponse(BaseModel):
    id: str
    fingerprint: str
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
    source_url: str
    source_domain: str
    application_deadline: datetime | None
    employment_type: EmploymentType | None
    verification_status: VerificationStatus
    last_verified_at: datetime | None
    verification_evidence: str | None
    verification_failure_reason: str | None
    is_public: bool
    extracted_at: datetime
    created_at: datetime
    updated_at: datetime
    sources: list[OpportunitySourceResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OpportunityListItem(BaseModel):
    id: str
    title: str | None
    company_name: str | None
    opportunity_type: OpportunityType | None
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    verification_status: VerificationStatus
    source_domain: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityListResponse(BaseModel):
    total: int
    items: list[OpportunityListItem]
    limit: int
    offset: int


class OpportunityExtractRequest(BaseModel):
    job_id: str
    result_indices: list[int] | None = Field(default=None, description="Specific result indices to extract; None means all")


class OpportunityExtractResponse(BaseModel):
    created: list[str]
    updated: list[str]
    skipped: list[dict[str, Any]]
    errors: list[str]


class OpportunityVerifyRequest(BaseModel):
    opportunity_ids: list[str] | None = Field(default=None, description="Specific opportunity IDs; None means all unverified")


class OpportunityVerifyResponse(BaseModel):
    verified: dict[str, str]
    errors: list[str]


class OpportunitySourcesResponse(BaseModel):
    opportunity_id: str
    sources: list[OpportunitySourceResponse]