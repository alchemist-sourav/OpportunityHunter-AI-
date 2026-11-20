from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.matching.experience_matcher import ExperienceMatchResult
from app.matching.location_matcher import LocationMatchResult
from app.matching.role_matcher import RoleMatchResult
from app.matching.skill_matcher import SkillMatchResult


@dataclass
class MatchingConfig:
    """Configuration for matching weights."""
    skills_weight: float = 0.40
    experience_weight: float = 0.20
    role_weight: float = 0.15
    location_weight: float = 0.10
    type_weight: float = 0.10
    salary_weight: float = 0.05
    
    def __post_init__(self):
        total = (self.skills_weight + self.experience_weight + 
                 self.role_weight + self.location_weight + 
                 self.type_weight + self.salary_weight)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


DEFAULT_CONFIG = MatchingConfig()


@dataclass
class MatchExplanation:
    """Structured explanation for a match."""
    positive_reasons: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    potential_mismatches: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1 based on data completeness
    
    def to_dict(self) -> dict:
        return {
            "positive_reasons": self.positive_reasons,
            "missing_requirements": self.missing_requirements,
            "potential_mismatches": self.potential_mismatches,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class MatchResult:
    """Complete match result for a user-opportunity pair."""
    opportunity_id: str
    user_id: str
    overall_score: float  # 0-100
    skills_score: float
    experience_score: float
    role_score: float
    location_score: float
    type_score: float
    salary_score: float
    explanation: MatchExplanation
    skills_detail: Any | None = None
    experience_detail: Any | None = None
    role_detail: Any | None = None
    location_detail: Any | None = None
    
    def to_dict(self) -> dict:
        return {
            "opportunity_id": self.opportunity_id,
            "user_id": self.user_id,
            "overall_score": round(self.overall_score, 1),
            "factor_scores": {
                "skills": round(self.skills_score, 1),
                "experience": round(self.experience_score, 1),
                "role": round(self.role_score, 1),
                "location": round(self.location_score, 1),
                "type": round(self.type_score, 1),
                "salary": round(self.salary_score, 1),
            },
            "explanation": self.explanation.to_dict(),
            "skills_detail": self.skills_detail,
            "experience_detail": self.experience_detail,
            "role_detail": self.role_detail,
            "location_detail": self.location_detail,
        }


class ScoringEngine:
    """Configurable weighted scoring engine for matching."""
    
    def __init__(self, config: MatchingConfig | None = None):
        self.config = config or DEFAULT_CONFIG
    
    def calculate_score(
        self,
        skills_result: Any | None,
        experience_result: Any | None,
        role_result: dict | None,
        location_result: dict | None,
        salary_result: dict | None = None,
    ) -> tuple[float, dict[str, float], MatchExplanation]:
        """
        Calculate overall match score and factor scores.
        
        Returns:
            (overall_score, factor_scores, explanation)
        """
        factor_scores = {}
        explanation = MatchExplanation()
        
        # Skills scoring
        if skills_result:
            skills_score = calculate_skill_match_score(skills_result)
            factor_scores["skills"] = skills_score
            if skills_result.required_coverage > 0.8:
                explanation.positive_reasons.append(f"Strong skill match ({skills_result.required_coverage:.0%} coverage)")
            elif skills_result.required_coverage > 0.5:
                explanation.positive_reasons.append(f"Moderate skill match ({skills_result.required_coverage:.0%} coverage)")
            if skills_result.missing_required_skills:
                explanation.missing_requirements.extend(
                    [f"Missing required skill: {s}" for s in skills_result.missing_required_skills]
                )
            if skills_result.missing_preferred_skills:
                explanation.missing_requirements.extend(
                    [f"Missing preferred skill: {s}" for s in skills_result.missing_preferred_skills]
                )
        else:
            factor_scores["skills"] = 50.0  # Neutral if no skills data
        
        # Experience scoring
        if experience_result:
            exp_score = calculate_experience_match_score(experience_result)
            factor_scores["experience"] = exp_score
            if experience_result.is_overqualified:
                explanation.positive_reasons.append("Overqualified for role (may be beneficial)")
            if experience_result.is_underqualified:
                explanation.potential_mismatches.append(
                    f"Underqualified: {experience_result.user_level} vs required {experience_result.required_level}"
                )
        else:
            factor_scores["experience"] = 70.0  # Neutral
        
        # Role scoring
        if role_result:
            role_score = role_result.get("match_score", 70.0)
            factor_scores["role"] = role_score
            if role_result.get("is_role_match"):
                explanation.positive_reasons.append("Role preferences align with opportunity")
            if role_result.get("is_type_match"):
                explanation.positive_reasons.append("Opportunity type matches preference")
        else:
            factor_scores["role"] = 70.0
        
        # Location scoring
        if location_result:
            loc_score = location_result.get("match_score", 50.0)
            factor_scores["location"] = loc_score
            if location_result.get("is_location_match"):
                explanation.positive_reasons.append("Location matches preference")
            elif location_result.get("location_match_type") == "remote":
                explanation.positive_reasons.append("Remote work compatible")
            if not location_result.get("is_remote_compatible"):
                explanation.potential_mismatches.append("Remote preference incompatible")
        else:
            factor_scores["location"] = 50.0
        
        # Opportunity type scoring (separate from role)
        type_score = factor_scores.get("role", 70.0)  # Reuse role score as proxy
        factor_scores["type"] = type_score
        
        # Salary scoring
        if salary_result:
            salary_score = salary_result.get("match_score", 70.0)
            factor_scores["salary"] = salary_score
        else:
            factor_scores["salary"] = 70.0  # Neutral
        
        # Calculate weighted overall score
        weights = {
            "skills": DEFAULT_CONFIG.skills_weight,
            "experience": DEFAULT_CONFIG.experience_weight,
            "role": DEFAULT_CONFIG.role_weight,
            "location": DEFAULT_CONFIG.location_weight,
            "type": DEFAULT_CONFIG.type_weight,
            "salary": DEFAULT_CONFIG.salary_weight,
        }
        
        overall_score = sum(
            factor_scores.get(factor, 50.0) * weight
            for factor, weight in weights.items()
        )
        
        # Confidence based on data completeness
        data_points = 0
        total_points = 6  # skills, experience, role, location, type, salary
        for key in ["skills", "experience", "role", "location", "type", "salary"]:
            if key in factor_scores:
                data_points += 1
        
        # Adjust confidence based on how many factors have real data
        explanation.confidence = data_points / total_points
        
        # Cap confidence
        explanation.confidence = min(max(explanation.confidence, 0.0), 1.0)
        
        overall_score = round(min(overall_score, 100), 1)
        
        return overall_score, factor_scores, explanation


def calculate_skill_match_score(skill_result: Any) -> float:
    """Calculate skill match score from SkillMatchResult."""
    if not skill_result:
        return 50.0
    required_weight = 0.7
    preferred_weight = 0.3
    score = (
        skill_result.required_coverage * 0.7 +
        skill_result.preferred_coverage * 0.3
    ) * 100
    return round(min(score, 100), 1)


def calculate_experience_match_score(result: Any) -> float:
    """Calculate experience match score."""
    return getattr(result, "match_score", 70.0)


def calculate_salary_match_score(
    user_min: int | None,
    user_max: int | None,
    user_currency: str | None,
    opp_min: int | None,
    opp_max: int | None,
    opp_currency: str | None,
) -> dict:
    """
    Calculate salary match between user expectations and opportunity.
    
    Returns dict with match_score and explanation.
    """
    # If user has no salary preference, neutral
    if user_min is None and user_max is None:
        return {
            "match_score": 70.0,
            "match_explanation": "No salary preference specified",
            "is_compatible": True,
        }
    
    # If opportunity has no salary info, neutral
    if opp_min is None and opp_max is None:
        return {
            "match_score": 50.0,
            "match_explanation": "Opportunity does not specify salary range",
            "is_compatible": True,
        }
    
    # Check currency compatibility
    if user_currency and opp_currency and user_currency != opp_currency:
        return {
            "match_score": 30.0,
            "match_explanation": f"Currency mismatch: expected {user_currency}, opportunity uses {opp_currency}",
            "is_compatible": False,
        }
    
    # Use midpoints for comparison
    user_mid = None
    if user_min is not None and user_max is not None:
        user_mid = (user_min + user_max) / 2
    elif user_min is not None:
        user_mid = user_min
    elif user_max is not None:
        user_mid = user_max
    
    opp_mid = None
    if opp_min is not None and opp_max is not None:
        opp_mid = (opp_min + opp_max) / 2
    elif opp_min is not None:
        opp_mid = opp_min
    elif opp_max is not None:
        opp_mid = opp_max
    
    if user_mid is None or opp_mid is None:
        return {
            "match_score": 50.0,
            "match_explanation": "Insufficient salary data for comparison",
            "is_compatible": True,
        }
    
    # Calculate match percentage
    ratio = opp_mid / user_mid if user_mid > 0 else 0
    
    if ratio >= 1.0:
        score = 100.0
        explanation = f"Opportunity meets or exceeds salary expectation ({ratio:.0%} of target)"
    elif ratio >= 0.8:
        score = 85.0
        explanation = f"Opportunity close to salary expectation ({ratio:.0%} of target)"
    elif ratio >= 0.6:
        score = 60.0
        explanation = f"Opportunity below salary expectation ({ratio:.0%} of target)"
    else:
        score = 30.0
        explanation = f"Opportunity significantly below salary expectation ({ratio:.0%} of target)"
    
    return {
        "match_score": round(score, 1),
        "match_explanation": explanation,
        "is_compatible": ratio >= 0.6,
        "ratio": ratio,
    }