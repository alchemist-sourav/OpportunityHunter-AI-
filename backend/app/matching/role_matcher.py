from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RoleMatchResult:
    """Result of role and opportunity type matching."""
    user_preferred_roles: list[str]
    opportunity_type: str | None
    is_type_match: bool
    is_role_match: bool
    match_score: float
    match_explanation: str
    matched_roles: list[str]


def normalize_role(role: str) -> str:
    """Normalize a role string."""
    if not role:
        return ""
    role = role.strip().lower()
    import re
    role = re.sub(r"[^\w\s+#.-]", "", role)
    return role.strip()


def normalize_roles(roles: list[str]) -> list[str]:
    """Normalize a list of roles."""
    normalized = []
    seen = set()
    for role in roles:
        norm = normalize_role(role)
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    return normalized


OPPORTUNITY_TYPE_ROLE_MAP = {
    "internship": {
        "intern", "internship", "trainee", "apprentice", "student", "co-op", "coop",
        "summer intern", "winter intern", "graduate intern",
    },
    "fresher_job": {
        "junior", "entry level", "entry-level", "fresher", "graduate", "new grad",
        "recent graduate", "associate", "entry", "beginner",
    },
    "full_time_job": {
        "senior", "lead", "principal", "staff", "principal engineer", "tech lead",
        "engineering manager", "architect", "senior engineer", "software engineer",
        "developer", "programmer", "engineer", "developer", "full stack", "backend",
        "frontend", "fullstack", "devops", "sre", "platform engineer", "data engineer",
        "ml engineer", "ai engineer", "data scientist", "analyst", "product manager",
        "project manager", "scrum master", "agile coach", "qa engineer", "test engineer",
    },
    "freelance_project": {
        "freelancer", "contractor", "consultant", "freelance", "contract", "gig",
        "project-based", "short-term", "part-time", "moonlighting",
    },
}


def match_roles_and_type(
    user_preferred_roles: list[str],
    user_preferred_types: list[str],
    opportunity_type: str | None,
) -> dict:
    """
    Match user's preferred roles and opportunity types against opportunity type.
    
    Returns dict with match details.
    """
    user_roles = [r.lower().strip() for r in user_preferred_roles if r]
    user_types = [t.lower().strip() for t in user_preferred_types if t]
    opp_type = (opportunity_type or "").lower()
    
    # Check opportunity type match
    type_match = False
    type_match_score = 0.0
    type_explanation = ""
    
    if opp_type:
        if opp_type in [t.lower() for t in user_preferred_types]:
            type_match = True
            type_score = 100.0
            type_explanation = f"Opportunity type matches preference: {opportunity_type}"
        else:
            type_match = False
            type_score = 50.0  # Not preferred but not excluded
            type_explanation = f"Opportunity type ({opportunity_type}) not in preferred types"
    else:
        type_match = False
        type_score = 70.0  # Unknown type
        type_explanation = "Opportunity type not specified"
    
    # Check role relevance
    role_match = False
    matched_roles = []
    role_score = 0.0
    role_explanation = ""
    
    if opp_type in OPPORTUNITY_TYPE_ROLE_MAP:
        type_roles = OPPORTUNITY_TYPE_ROLE_MAP[opportunity_type] if opportunity_type in OPPORTUNITY_TYPE_ROLE_MAP else set()
        
        # Also check generic role mappings
        for user_role in [r.lower() for r in user_preferred_roles if r]:
            matched = False
            for type_key, roles in OPPORTUNITY_TYPE_ROLE_MAP.items():
                if any(r in user_role.lower() or user_role.lower() in r for r in roles):
                    matched = True
                    break
            if matched:
                matched_roles.append(type_key)
        
        # Also check if user's roles contain keywords matching opportunity type
        for user_role in [r.lower() for r in user_preferred_roles if r]:
            if opp_type.replace("_", " ") in user_role or user_role in opp_type.replace("_", " "):
                matched_roles.append(user_role)
    
    if matched_roles:
        role_match = True
        role_score = 100.0
        role_explanation = f"Role matches: {', '.join(matched_roles)}"
    elif user_preferred_roles:
        role_match = False
        role_score = 30.0
        role_explanation = "Preferred roles don't align with opportunity type"
    else:
        role_match = False
        role_score = 70.0  # Neutral if no preference specified
        role_explanation = "No specific role preferences specified"
    
    # Calculate overall score
    type_weight = 0.6
    role_weight = 0.4
    
    if user_preferred_types:
        overall_score = type_score * 0.6 + (0 if not user_preferred_roles else role_score * 0.4 + 100 * 0.4)
        if not user_preferred_roles:
            overall_score = type_score
    else:
        overall_score = role_score if user_preferred_roles else 70.0
    
    # Combine explanations
    explanations = [type_explanation, role_explanation]
    explanation = "; ".join(e for e in explanations if e)
    
    return {
        "is_type_match": opp_type in [t.lower() for t in user_preferred_types] if user_preferred_types else False,
        "is_role_match": len(matched_roles) > 0,
        "match_score": round(min(overall_score, 100), 1),
        "match_explanation": explanation,
        "matched_roles": list(set(matched_roles)),
        "is_type_match": opp_type in [t.lower() for t in user_preferred_types] if user_preferred_types else False,
        "is_role_match": len(matched_roles) > 0,
    }


def calculate_role_match_score(result: dict) -> float:
    """Calculate role match score from result."""
    return result.get("match_score", 0.0)


def get_role_match_explanation(result: dict) -> str:
    """Get explanation for role match."""
    return result.get("match_explanation", "")