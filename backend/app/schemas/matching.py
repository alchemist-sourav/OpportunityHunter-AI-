from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MatchExplanation(BaseModel):
    positive_reasons: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    potential_mismatches: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class MatchFactorScores(BaseModel):
    skills: float = Field(ge=0.0, le=100.0)
    experience: float = Field(ge=0.0, le=100.0)
    role: float = Field(ge=0.0, le=100.0)
    location: float = Field(ge=0.0, le=100.0)
    type: float = Field(ge=0.0, le=100.0)
    salary: float = Field(ge=0.0, le=100.0)


class MatchExplanationResponse(BaseModel):
    positive_reasons: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    potential_mismatches: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class SkillMatchDetail(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)
    required_coverage: float = Field(ge=0.0, le=1.0)
    preferred_coverage: float = Field(ge=0.0, le=1.0)
    exact_matches: list[str] = Field(default_factory=list)
    partial_matches: list[str] = Field(default_factory=list)
    match_explanation: str


class ExperienceMatchDetail(BaseModel):
    user_level: str | None
    required_level: str | None
    is_compatible: bool
    level_difference: int
    match_score: float
    match_explanation: str
    is_overqualified: bool
    is_underqualified: bool


class RoleMatchDetail(BaseModel):
    is_type_match: bool
    is_role_match: bool
    match_score: float
    match_explanation: str
    matched_roles: list[str]


class LocationMatchDetail(BaseModel):
    user_locations: list[str]
    opportunity_location: str | None
    user_remote_preference: str | None
    opportunity_remote_preference: str | None
    is_location_match: bool
    is_remote_compatible: bool
    match_score: float
    match_explanation: str
    location_match_type: str


class MatchDetailResponse(BaseModel):
    opportunity_id: str
    user_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    factor_scores: dict[str, float]
    explanation: MatchExplanationResponse
    skills_detail: SkillMatchDetail | None = None
    experience_detail: ExperienceMatchDetail | None = None
    role_detail: RoleMatchDetail | None = None
    location_detail: LocationMatchDetail | None = None
    calculated_at: datetime


class RecommendationItem(BaseModel):
    opportunity_id: str
    title: str | None
    company_name: str | None
    opportunity_type: str | None
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    verification_status: str
    source_domain: str
    match_score: float = Field(ge=0.0, le=100.0)
    factor_scores: dict[str, float]
    explanation: MatchExplanationResponse


class MatchingRecommendationsResponse(BaseModel):
    total: int
    items: list[RecommendationItem]
    limit: int
    offset: int


class MatchingRecommendationsRequest(BaseModel):
    min_score: float = Field(default=0.0, ge=0.0, le=100.0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    opportunity_type: str | None = None
    location: str | None = None
    remote_preference: str | None = None
    skills: str | None = None
    min_salary: int | None = None
    max_salary: int | None = None


class RecalculateRequest(BaseModel):
    user_id: str | None = None  # If None, use authenticated user


class MatchingRecalculateResponse(BaseModel):
    recalculated_count: int
    message: str