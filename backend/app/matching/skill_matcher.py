from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.matching.normalizer import normalize_skill, normalize_skills


@dataclass
class SkillMatchResult:
    """Result of skill matching between user skills and required skills."""
    matched_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    extra_skills: list[str]
    required_coverage: float
    preferred_coverage: float
    exact_matches: list[str]
    partial_matches: list[str]
    match_explanation: str


def _fuzzy_match(skill1: str, skill2: str) -> bool:
    """Check if two skills match with fuzzy matching."""
    if skill1 == skill2:
        return True
    # Check if one is a substring of the other (for compound skills)
    if skill1 in skill2 or skill2 in skill1:
        return True
    return False


def match_skills(
    user_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> SkillMatchResult:
    """
    Match user skills against required and preferred skills.
    
    Args:
        user_skills: List of user's skills (will be normalized)
        required_skills: List of required skills for the opportunity
        preferred_skills: Optional list of preferred/nice-to-have skills
    
    Returns:
        SkillMatchResult with matched, missing, and extra skills
    """
    user_norm = set(normalize_skills(user_skills))
    required_norm = set(normalize_skills(required_skills))
    preferred_norm = set(normalize_skills(preferred_skills or []))
    
    # Exact matches
    exact_matches = user_norm & required_norm
    
    # Partial matches (fuzzy matching for remaining required skills)
    unmatched_required = required_norm - exact_matches
    partial_matches = set()
    for req_skill in unmatched_required:
        for user_skill in user_skills:
            if _fuzzy_match(normalize_skill(req_skill), normalize_skill(user_skill)):
                partial_matches.add(req_skill)
                break
    
    all_matched = exact_matches | partial_matches
    
    # Missing skills
    missing_required = list(required_norm - all_matched)
    missing_preferred = list(preferred_norm - user_norm) if preferred_norm else []
    
    # Extra skills (user has but not required/preferred)
    all_opportunity_skills = required_norm | (preferred_norm or set())
    extra_skills = list(user_norm - all_opportunity_skills)
    
    # Coverage calculations
    required_coverage = 0.0
    if required_norm:
        required_coverage = len(exact_matches | partial_matches) / len(required_norm)
    
    preferred_coverage = 0.0
    if preferred_norm:
        preferred_coverage = len(user_norm & preferred_norm) / len(preferred_norm)
    
    # Build explanation
    explanation_parts = []
    if exact_matches:
        explanation_parts.append(f"Exact match on {len(exact_matches)} required skill(s): {', '.join(sorted(exact_matches))}")
    if partial_matches:
        explanation_parts.append(f"Partial match on {len(partial_matches)} required skill(s): {', '.join(sorted(partial_matches))}")
    if missing_required:
        explanation_parts.append(f"Missing {len(missing_required)} required skill(s): {', '.join(sorted(missing_required))}")
    if missing_preferred:
        explanation_parts.append(f"Missing {len(missing_preferred)} preferred skill(s): {', '.join(sorted(missing_preferred))}")
    if not required_norm:
        explanation_parts.append("No specific skills required")
    
    match_explanation = "; ".join(explanation_parts) if explanation_parts else "No skill comparison possible"
    
    return SkillMatchResult(
        matched_skills=sorted(exact_matches | partial_matches),
        missing_required_skills=sorted(missing_required),
        missing_preferred_skills=sorted(missing_preferred),
        extra_skills=sorted(extra_skills),
        required_coverage=round(required_coverage, 3),
        preferred_coverage=round(preferred_coverage, 3),
        exact_matches=sorted(exact_matches),
        partial_matches=sorted(partial_matches),
        match_explanation=match_explanation,
    )


def calculate_skill_match_score(skill_result: Any) -> float:
    """
    Calculate a skill match score from 0-100 based on coverage.
    Weights: required coverage 70%, preferred coverage 30%
    """
    required_weight = 0.7
    preferred_weight = 0.3
    
    score = (
        skill_result.required_coverage * required_weight +
        skill_result.preferred_coverage * preferred_weight
    ) * 100
    
    return round(min(score, 100), 1)


def get_missing_skills_summary(skill_result: Any) -> dict[str, Any]:
    """Get a summary of missing skills for display."""
    return {
        "required": skill_result.missing_required_skills,
        "preferred": skill_result.missing_preferred_skills,
        "total_missing": len(skill_result.missing_required_skills) + len(skill_result.missing_preferred_skills),
    }