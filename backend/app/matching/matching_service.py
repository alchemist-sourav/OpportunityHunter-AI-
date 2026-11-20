from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.engine import get_session_factory
from app.models.discovery_models import DiscoveryJob
from app.models.opportunity_models import Opportunity, OpportunityType
from app.models.user_models import UserProfile
from app.scrapers.discovery_service import run_discovery_job
from app.matching.experience_matcher import match_experience
from app.matching.location_matcher import match_location
from app.matching.normalizer import normalize_skills
from app.matching.role_matcher import match_roles_and_type
from app.matching.scoring import (
    DEFAULT_CONFIG,
    MatchExplanation,
    MatchResult,
    MatchingConfig,
    ScoringEngine,
    calculate_salary_match_score,
)
from app.matching.skill_matcher import match_skills
from app.scrapers.deduplication_service import DuplicateDetector

logger = logging.getLogger(__name__)


class MatchingService:
    """Main service for matching user profiles to opportunities."""
    
    def __init__(
        self,
        session_factory: Callable[[], Session] | None = None,
        scoring_config: MatchingConfig | None = None,
    ) -> None:
        self.session_factory = session_factory or get_session_factory
        self.scoring_engine = ScoringEngine(scoring_config) if scoring_config else DEFAULT_CONFIG
        self.config = get_settings()
    
    def get_user_profile(self, session: Session, user_id: str) -> UserProfile | None:
        """Get user profile by ID."""
        return session.get(UserProfile, user_id)
    
    def get_opportunities_for_matching(
        self,
        session: Session,
        user_id: str,
        filters: dict | None = None,
        limit: int = 100,
    ) -> list[Opportunity]:
        """Get opportunities that are candidates for matching."""
        from app.models.opportunity_models import Opportunity
        
        stmt = select(Opportunity).where(
            Opportunity.is_public == True,
            Opportunity.verification_status == "active",
        )
        
        # Apply optional filters
        filters = filters or {}
        if filters.get("opportunity_type"):
            stmt = stmt.where(Opportunity.opportunity_type == filters["opportunity_type"])
        if filters.get("location"):
            stmt = stmt.where(Opportunity.location.ilike(f"%{filters['location']}%"))
        if filters.get("remote_preference"):
            stmt = stmt.where(Opportunity.remote_preference == filters["remote_preference"])
        
        stmt = stmt.order_by(desc(Opportunity.created_at)).limit(limit)
        return list(session.scalars(stmt).all())
    
    def match_user_to_opportunity(
        self,
        user: UserProfile,
        opportunity: Opportunity,
    ) -> MatchResult:
        """
        Match a single user profile to a single opportunity.
        
        Returns a detailed MatchResult with scores and explanation.
        """
        # Skill matching
        user_skills = normalize_skills(user.skills or [])
        opp_skills = normalize_skills(opportunity.required_skills or [])
        skills_result = match_skills(user_skills, opp_skills)
        
        # Experience matching
        exp_result = match_experience(
            user.experience_level,
            opportunity.experience_level,
        )
        
        # Role matching
        role_result = match_roles_and_type(
            user_preferred_roles=user.preferred_job_roles or [],
            user_preferred_types=user.preferred_opportunity_types or [],
            opportunity_type=opportunity.opportunity_type.value if opportunity.opportunity_type else None,
        )
        
        # Location matching
        location_result = match_location(
            user_locations=user.preferred_locations or [],
            user_remote_preference=user.remote_preference,
            opportunity_location=opportunity.location,
            opportunity_remote_preference=opportunity.remote_preference,
        )
        
        # Salary matching
        salary_result = calculate_salary_match_score(
            user_min=user.salary_min,
            user_max=user.salary_max,
            user_currency=user.salary_currency,
            opp_min=opportunity.salary_min,
            opp_max=opportunity.salary_max,
            opp_currency=opportunity.salary_currency,
        )
        
        # Calculate overall score using ScoringEngine
        config = MatchingConfig()
        engine = ScoringEngine(config)
        
        overall_score, factor_scores, explanation = engine.calculate_score(
            skills_result=skills_result,
            experience_result=exp_result,
            role_result=role_result,
            location_result=location_result,
            salary_result=salary_result,
        )
        
        # Build skills_detail from skills_result
        skills_detail = SkillMatchDetail(
            matched_skills=skills_result.matched_skills,
            missing_required_skills=skills_result.missing_required_skills,
            missing_preferred_skills=skills_result.missing_preferred_skills,
            extra_skills=skills_result.extra_skills,
            required_coverage=skills_result.required_coverage,
            preferred_coverage=skills_result.preferred_coverage,
            exact_matches=skills_result.exact_matches,
            partial_matches=skills_result.partial_matches,
            match_explanation=skills_result.match_explanation,
        )
        
        # Build experience_detail from exp_result
        experience_detail = ExperienceMatchDetail(
            user_level=exp_result.user_level,
            required_level=exp_result.required_level,
            is_compatible=exp_result.is_compatible,
            level_difference=exp_result.level_difference,
            match_score=exp_result.match_score,
            match_explanation=exp_result.match_explanation,
            is_overqualified=exp_result.is_overqualified,
            is_underqualified=exp_result.is_underqualified,
        )
        
        # Build role_detail from role_result
        role_detail = RoleMatchDetail(
            is_type_match=role_result.get("is_type_match", False),
            is_role_match=role_result.get("is_role_match", False),
            match_score=role_result.get("match_score", 0.0),
            match_explanation=role_result.get("match_explanation", ""),
            matched_roles=role_result.get("matched_roles", []),
        )
        
        # Build location_detail from location_result
        location_detail = LocationMatchDetail(
            user_locations=user.preferred_locations or [],
            opportunity_location=opportunity.location,
            user_remote_preference=user.remote_preference,
            opportunity_remote_preference=opportunity.remote_preference,
            is_location_match=location_result.get("is_location_match", False),
            is_remote_compatible=location_result.get("is_remote_compatible", False),
            match_score=location_result.get("match_score", 0.0),
            match_explanation=location_result.get("match_explanation", ""),
            location_match_type=location_result.get("location_match_type", "none"),
        )
        
        return MatchResult(
            opportunity_id=opportunity.id,
            user_id=user.id,
            overall_score=overall_score,
            skills_score=factor_scores.get("skills", 0.0),
            experience_score=factor_scores.get("experience", 0.0),
            role_score=factor_scores.get("role", 0.0),
            location_score=factor_scores.get("location", 0.0),
            type_score=factor_scores.get("type", 0.0),
            salary_score=factor_scores.get("salary", 0.0),
            explanation=explanation,
            skills_detail=skills_detail,
            experience_detail=experience_detail,
            role_detail=role_detail,
            location_detail=location_detail,
        )
    
    def get_recommendations(
        self,
        user_id: str,
        limit: int = 20,
        min_score: float = 0,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Get ranked opportunity recommendations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            min_score: Minimum match score (0-100)
            filters: Additional filters
        
        Returns:
            List of scored opportunities sorted by match score
        """
        with self.session_factory() as session:
            user = self.get_user_profile(session, user_id)
            if not user:
                return []
            
            opportunities = self.get_opportunities_for_matching(
                session, user_id, filters, limit * 3  # Get more for filtering
            )
            
            scored = []
            for opp in opportunities:
                match = self.match_user_to_opportunity(user, opp)
                if match.overall_score >= min_score:
                    scored.append({
                        "opportunity_id": opp.id,
                        "title": opp.title,
                        "company_name": opp.company_name,
                        "opportunity_type": opp.opportunity_type.value if opp.opportunity_type else None,
                        "location": opp.location,
                        "remote_preference": opp.remote_preference,
                        "salary_min": opp.salary_min,
                        "salary_max": opp.salary_max,
                        "salary_currency": opp.salary_currency,
                        "verification_status": opp.verification_status,
                        "source_domain": opp.source_domain,
                        "match_score": match.overall_score,
                        "factor_scores": match.factor_scores,
                        "explanation": match.explanation.to_dict(),
                    })
            
            # Sort by score descending
            scored.sort(key=lambda x: x["match_score"], reverse=True)
            return scored[:limit]
    
    def get_detailed_match(
        self,
        user_id: str,
        opportunity_id: str,
    ) -> dict | None:
        """Get detailed match explanation for a specific opportunity."""
        with self.session_factory() as session:
            user = self.get_user_profile(session, user_id)
            if not user:
                return None
            
            opp = session.get(Opportunity, opportunity_id)
            if not opp:
                return None
            
            match = self.match_user_to_opportunity(user, opp)
            return match.to_dict()
    
    def recalculate_all_for_user(self, user_id: str) -> int:
        """Recalculate all matches for a user (useful after profile update)."""
        with self.session_factory() as session:
            user = self.get_user_profile(session, user_id)
            if not user:
                return 0
            
            # Get all active opportunities
            opps = self.get_opportunities_for_matching(session, user_id, limit=1000)
            
            count = 0
            for opp in opps:
                match = self.match_user_to_opportunity(user, opp)
                # Could persist here if we add a recommendations table
                count += 1
            
            return count


def get_matching_service() -> MatchingService:
    """Factory function to create a MatchingService instance."""
    return MatchingService()