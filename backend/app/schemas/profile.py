from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import ExperienceLevel, OpportunityType, RemotePreference


class ProfileCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    skills: list[str] = Field(default_factory=list, max_length=50)
    experience_level: str
    preferred_job_roles: list[str] = Field(default_factory=list, max_length=50)
    preferred_opportunity_types: list[str] = Field(default_factory=list, max_length=20)
    preferred_locations: list[str] = Field(default_factory=list, max_length=50)
    remote_preference: str

    @field_validator("experience_level")
    @classmethod
    def _valid_experience_level(cls, value: str) -> str:
        try:
            return ExperienceLevel(value).value
        except ValueError as exc:
            raise ValueError("Invalid experience_level.") from exc

    @field_validator("remote_preference")
    @classmethod
    def _valid_remote_preference(cls, value: str) -> str:
        try:
            return RemotePreference(value).value
        except ValueError as exc:
            raise ValueError("Invalid remote_preference.") from exc

    @field_validator("skills", "preferred_job_roles", "preferred_locations")
    @classmethod
    def _clean_string_list(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if len(cleaned) > 50:
            raise ValueError("At most 50 entries are allowed per list field.")
        if any(len(item) > 120 for item in cleaned):
            raise ValueError("Each entry must be 120 characters or fewer.")
        return cleaned

    @field_validator("preferred_opportunity_types")
    @classmethod
    def _clean_opportunity_types(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if len(cleaned) > 20:
            raise ValueError("At most 20 opportunity types are allowed.")
        for value in cleaned:
            try:
                OpportunityType(value)
            except ValueError as exc:
                raise ValueError(f"Invalid opportunity type '{value}'.") from exc
        return cleaned


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    skills: list[str] | None = Field(default=None, max_length=50)
    experience_level: str | None = None
    preferred_job_roles: list[str] | None = Field(default=None, max_length=50)
    preferred_opportunity_types: list[str] | None = Field(default=None, max_length=20)
    preferred_locations: list[str] | None = Field(default=None, max_length=50)
    remote_preference: str | None = None

    @field_validator("experience_level")
    @classmethod
    def _valid_experience_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return ExperienceLevel(value).value
        except ValueError as exc:
            raise ValueError("Invalid experience_level.") from exc

    @field_validator("remote_preference")
    @classmethod
    def _valid_remote_preference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return RemotePreference(value).value
        except ValueError as exc:
            raise ValueError("Invalid remote_preference.") from exc

    @field_validator("skills", "preferred_job_roles", "preferred_locations")
    @classmethod
    def _clean_string_list(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [item.strip() for item in values if item.strip()]
        if len(cleaned) > 50:
            raise ValueError("At most 50 entries are allowed per list field.")
        if any(len(item) > 120 for item in cleaned):
            raise ValueError("Each entry must be 120 characters or fewer.")
        return cleaned

    @field_validator("preferred_opportunity_types")
    @classmethod
    def _clean_opportunity_types(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [item.strip() for item in values if item.strip()]
        if len(cleaned) > 20:
            raise ValueError("At most 20 opportunity types are allowed.")
        for value in cleaned:
            try:
                OpportunityType(value)
            except ValueError as exc:
                raise ValueError(f"Invalid opportunity type '{value}'.") from exc
        return cleaned


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str | None
    skills: list[str]
    experience_level: str
    preferred_job_roles: list[str]
    preferred_opportunity_types: list[str]
    preferred_locations: list[str]
    remote_preference: str
    created_at: datetime
    updated_at: datetime
