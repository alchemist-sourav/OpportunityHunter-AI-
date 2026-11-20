from app.matching.normalizer import (
    normalize_skill,
    normalize_skills,
    get_skill_category,
    categorize_skills,
    extract_skill_tokens,
    SKILL_ALIASES,
    SKILL_CATEGORIES,
)

from app.matching.skill_matcher import (
    match_skills,
    SkillMatchResult,
    calculate_skill_match_score,
    get_missing_skills_summary,
)

from app.matching.experience_matcher import (
    match_experience,
    ExperienceMatchResult,
    calculate_experience_match_score,
    get_experience_match_explanation,
)

from app.matching.location_matcher import (
    match_location,
    calculate_location_match_score,
    get_location_match_explanation,
)

from app.matching.role_matcher import (
    match_roles_and_type,
    calculate_role_match_score,
    get_role_match_explanation,
    OPPORTUNITY_TYPE_ROLE_MAP,
)

from app.matching.scoring import (
    MatchingConfig,
    DEFAULT_CONFIG,
    ScoringEngine,
    MatchExplanation,
    MatchResult,
    calculate_skill_match_score,
    calculate_experience_match_score,
    calculate_salary_match_score,
)

from app.matching.matching_service import MatchingService, get_matching_service

__all__ = [
    # Normalizer
    "normalize_skill",
    "normalize_skills",
    "get_skill_category",
    "categorize_skills",
    "extract_skill_tokens",
    "SKILL_ALIASES",
    "SKILL_CATEGORIES",
    
    # Skill matcher
    "match_skills",
    "SkillMatchResult",
    "calculate_skill_match_score",
    "get_missing_skills_summary",
    
    # Experience matcher
    "match_experience",
    "ExperienceMatchResult",
    "calculate_experience_match_score",
    "get_experience_match_explanation",
    
    # Location matcher
    "match_location",
    "calculate_location_match_score",
    "get_location_match_explanation",
    
    # Role matcher
    "match_roles_and_type",
    "calculate_role_match_score",
    "get_role_match_explanation",
    "OPPORTUNITY_TYPE_ROLE_MAP",
    
    # Scoring
    "MatchingConfig",
    "DEFAULT_CONFIG",
    "ScoringEngine",
    "MatchExplanation",
    "MatchResult",
    "calculate_skill_match_score",
    "calculate_experience_match_score",
    "calculate_salary_match_score",
    
    # Service
    "MatchingService",
    "get_matching_service",
]