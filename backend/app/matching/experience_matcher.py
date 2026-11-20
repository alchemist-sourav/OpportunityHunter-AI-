from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXPERIENCE_LEVELS = ["student", "fresher", "junior", "experienced"]
EXPERIENCE_RANK = {level: i for i, level in enumerate(EXPERIENCE_LEVELS)}


@dataclass
class ExperienceMatchResult:
    """Result of experience level matching."""
    user_level: str | None
    required_level: str | None
    is_compatible: bool
    level_difference: int
    match_score: float
    match_explanation: str
    is_overqualified: bool
    is_underqualified: bool


def get_experience_rank(level: str | None) -> int | None:
    """Get the numeric rank of an experience level."""
    if not level:
        return None
    level = level.lower().strip()
    return EXPERIENCE_RANK.get(level)


def match_experience(
    user_level: str | None,
    required_level: str | None,
) -> ExperienceMatchResult:
    """
    Match user experience level against required experience level.
    
    Rules:
    - If required is None, compatible (no requirement)
    - If user is None, unknown - neutral compatibility
    - Exact match = 100
    - User one level above = 90 (overqualified but acceptable)
    - User one level below = 70 (underqualified but trainable)
    - User two+ levels above = 80 (overqualified)
    - User two+ levels below = 40 (significantly underqualified)
    """
    user_rank = get_experience_rank(user_level)
    required_rank = get_experience_rank(required_level)
    
    # No requirement specified
    if required_rank is None:
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=0,
            match_score=100.0,
            match_explanation="No experience level requirement specified",
            is_overqualified=False,
            is_underqualified=False,
        )
    
    # User level unknown
    if user_rank is None:
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=0,
            match_score=70.0,  # Neutral - unknown but not rejected
            match_explanation="Experience level not specified in profile",
            is_overqualified=False,
            is_underqualified=False,
        )
    
    diff = user_rank - required_rank
    
    if diff == 0:
        # Exact match
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=0,
            match_score=100.0,
            match_explanation=f"Exact match: {user_level} level",
            is_overqualified=False,
            is_underqualified=False,
        )
    elif diff == 1:
        # One level above - overqualified but acceptable
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=1,
            match_score=90.0,
            match_explanation=f"Overqualified: {user_level} exceeds required {required_level}",
            is_overqualified=True,
            is_underqualified=False,
        )
    elif diff >= 2:
        # Significantly overqualified
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=diff,
            match_score=80.0,
            match_explanation=f"Significantly overqualified: {user_level} vs required {required_level}",
            is_overqualified=True,
            is_underqualified=False,
        )
    elif diff == -1:
        # One level below - underqualified but trainable
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=-1,
            match_score=70.0,
            match_explanation=f"Slightly underqualified: {user_level} vs required {required_level}",
            is_overqualified=False,
            is_underqualified=True,
        )
    else:
        # diff <= -2: significantly underqualified
        return ExperienceMatchResult(
            user_level=user_level,
            required_level=required_level,
            is_compatible=True,
            level_difference=diff,
            match_score=40.0,
            match_explanation=f"Underqualified: {user_level} below required {required_level}",
            is_overqualified=False,
            is_underqualified=True,
        )


def calculate_experience_match_score(result: Any) -> float:
    """Convert experience match result to a 0-100 score."""
    return result.match_score


def get_experience_match_explanation(result: Any) -> str:
    """Get the explanation for the experience match."""
    return result.match_explanation