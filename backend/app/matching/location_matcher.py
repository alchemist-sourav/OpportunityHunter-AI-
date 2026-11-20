from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from app.matching.normalizer import normalize_skill


@dataclass
class LocationMatchResult:
    """Result of location and remote preference matching."""
    user_locations: list[str]
    opportunity_location: str | None
    user_remote_preference: str | None
    opportunity_remote_preference: str | None
    is_location_match: bool
    is_remote_compatible: bool
    match_score: float
    match_explanation: str
    location_match_type: str  # "exact", "remote", "partial", "none"


REMOTE_PREFERENCES = ["remote_only", "hybrid", "onsite_only", "no_preference"]


def normalize_location(location: str | None) -> str | None:
    """Normalize a location string."""
    if not location:
        return None
    loc = location.strip().lower()
    # Remove extra whitespace
    import re
    loc = " ".join(loc.split())
    return loc


def normalize_locations(locations: list[str]) -> list[str]:
    """Normalize a list of locations."""
    normalized = []
    seen = set()
    for loc in locations:
        norm = normalize_location(loc)
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    return normalized


def get_remote_preference_rank(preference: str | None) -> int:
    """Get numeric rank for remote preference (higher = more remote)."""
    if not preference:
        return 1  # no_preference default
    pref = preference.lower().strip()
    ranks = {
        "remote_only": 4,
        "hybrid": 3,
        "no_preference": 2,
        "onsite_only": 1,
    }
    return ranks.get(pref.lower(), 2)


def match_location(
    user_locations: list[str],
    user_remote_preference: str | None,
    opportunity_location: str | None,
    opportunity_remote_preference: str | None,
) -> Any:
    """
    Match user location preferences against opportunity location and remote policy.
    
    Returns:
        LocationMatchResult with match details
    """
    from dataclasses import dataclass
    
    @dataclass
    class LocationMatchResult:
        user_locations: list[str]
        opportunity_location: str | None
        user_remote_preference: str | None
        opportunity_remote_preference: str | None
        is_location_match: bool
        is_remote_compatible: bool
        match_score: float
        match_explanation: str
        location_match_type: str
    
    user_locs = [loc.lower().strip() for loc in user_locations if loc]
    opp_loc = normalize_location(opportunity_location) if opportunity_location else None
    
    # Normalize remote preferences
    user_remote = (user_remote_preference or "no_preference").lower()
    opp_remote = (opportunity_remote_preference or "no_preference").lower()
    
    # Check location match
    is_location_match = False
    location_match_type = "none"
    
    if opp_loc:
        for user_loc in [loc.lower() for loc in user_locations if loc]:
            if user_loc == opp_loc:
                return {
                    "user_locations": user_locations,
                    "opportunity_location": opportunity_location,
                    "user_remote_preference": user_remote_preference,
                    "opportunity_remote_preference": opportunity_remote_preference,
                    "is_location_match": True,
                    "is_remote_compatible": True,
                    "match_score": 100.0,
                    "match_explanation": f"Exact location match: {opportunity_location}",
                    "location_match_type": "exact",
                }
            # Check partial match (city in city, etc.)
            if user_loc in opp_loc or opp_loc in user_loc:
                return {
                    "user_locations": user_locations,
                    "opportunity_location": opportunity_location,
                    "user_remote_preference": user_remote_preference,
                    "opportunity_remote_preference": opportunity_remote_preference,
                    "is_location_match": True,
                    "is_remote_compatible": True,
                    "match_score": 80.0,
                    "match_explanation": f"Partial location match: {opportunity_location}",
                    "location_match_type": "partial",
                }
    
    # No exact/partial location match, check remote compatibility
    user_remote_rank = get_remote_preference_rank(user_remote_preference)
    opp_remote_rank = get_remote_preference_rank(opportunity_remote_preference)
    
    # Remote compatibility: user preference should be >= opportunity requirement
    # (e.g., user wants remote_only, job is hybrid -> compatible)
    # User rank >= job rank means user is OK with the job's remote level
    is_remote_compatible = True
    remote_score = 100.0
    remote_explanation = ""
    
    if user_remote_preference == "remote_only" and opp_remote != "remote_only":
        is_remote_compatible = False
        remote_score = 0.0
        remote_explanation = "User requires remote-only but opportunity is not remote-only"
    elif user_remote_preference == "hybrid" and opp_remote == "onsite_only":
        is_remote_compatible = False
        remote_score = 20.0
        remote_explanation = "User prefers hybrid but opportunity is onsite-only"
    elif user_remote_preference == "onsite_only" and opp_remote == "remote_only":
        is_remote_compatible = False
        remote_score = 10.0
        remote_explanation = "User prefers onsite but opportunity is remote-only"
    else:
        # Compatible - calculate score based on alignment
        if user_remote_preference == opportunity_remote_preference:
            remote_explanation = f"Remote preference matches: {user_remote_preference}"
        elif user_remote_preference == "no_preference":
            remote_explanation = f"No remote preference, compatible with {opportunity_remote_preference}"
        else:
            remote_explanation = f"Remote preference compatible: user wants {user_remote_preference}, job offers {opportunity_remote_preference}"
    
    if not is_remote_compatible:
        return {
            "user_locations": user_locations,
            "opportunity_location": opportunity_location,
            "user_remote_preference": user_remote_preference,
            "opportunity_remote_preference": opportunity_remote_preference,
            "is_location_match": False,
            "is_remote_compatible": False,
            "match_score": 0.0,
            "match_explanation": remote_explanation or "Remote preference incompatible",
            "location_match_type": "incompatible",
        }
    
    # If we have a location but no match, and remote is compatible
    if opp_loc:
        return {
            "user_locations": user_locations,
            "opportunity_location": opportunity_location,
            "user_remote_preference": user_remote_preference,
            "opportunity_remote_preference": opportunity_remote_preference,
            "is_location_match": False,
            "is_remote_compatible": True,
            "match_score": 60.0,
            "match_explanation": f"Location differs ({opportunity_location}) but remote work compatible",
            "location_match_type": "remote",
        }
    
    # No location specified on opportunity, but remote is compatible
    return {
        "user_locations": user_locations,
        "opportunity_location": opportunity_location,
        "user_remote_preference": user_remote_preference,
        "opportunity_remote_preference": opportunity_remote_preference,
        "is_location_match": False,
        "is_remote_compatible": True,
        "match_score": 90.0,
        "match_explanation": "No specific location required, remote work compatible",
        "location_match_type": "remote",
    }


def calculate_location_match_score(result: dict) -> float:
    """Calculate location match score from result."""
    return result.get("match_score", 0.0)


def get_location_match_explanation(result: dict) -> str:
    """Get the explanation for location match."""
    return result.get("match_explanation", "")