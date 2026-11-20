export type MatchExplanation = {
  positive_reasons: string[];
  missing_requirements: string[];
  potential_mismatches: string[];
  confidence: number;
};

export type MatchFactorScores = {
  skills: number;
  experience: number;
  role: number;
  location: number;
  type: number;
  salary: number;
};

export type SkillMatchDetail = {
  matched_skills: string[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  extra_skills: string[];
  required_coverage: number;
  preferred_coverage: number;
  exact_matches: string[];
  partial_matches: string[];
  match_explanation: string;
};

export type ExperienceMatchDetail = {
  user_level: string | null;
  required_level: string | null;
  is_compatible: boolean;
  level_difference: number;
  match_score: number;
  match_explanation: string;
  is_overqualified: boolean;
  is_underqualified: boolean;
};

export type RoleMatchDetail = {
  is_type_match: boolean;
  is_role_match: boolean;
  match_score: number;
  match_explanation: string;
  matched_roles: string[];
};

export type LocationMatchDetail = {
  user_locations: string[];
  opportunity_location: string | null;
  user_remote_preference: string | null;
  opportunity_remote_preference: string | null;
  is_location_match: boolean;
  is_remote_compatible: boolean;
  match_score: number;
  match_explanation: string;
  location_match_type: string;
};

export type MatchDetail = {
  opportunity_id: string;
  user_id: string;
  overall_score: number;
  factor_scores: Record<string, number>;
  explanation: {
    positive_reasons: string[];
    missing_requirements: string[];
    potential_mismatches: string[];
    confidence: number;
  };
  skills_detail: SkillMatchDetail | null;
  experience_detail: ExperienceMatchDetail | null;
  role_detail: RoleMatchDetail | null;
  location_detail: LocationMatchDetail | null;
  calculated_at: string;
};

export type RecommendationItem = {
  opportunity_id: string;
  title: string | null;
  company_name: string | null;
  opportunity_type: string | null;
  location: string | null;
  remote_preference: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  verification_status: string;
  source_domain: string;
  match_score: number;
  factor_scores: Record<string, number>;
  explanation: {
    positive_reasons: string[];
    missing_requirements: string[];
    potential_mismatches: string[];
    confidence: number;
  };
};

export type MatchingRecommendationsResponse = {
  total: number;
  items: RecommendationItem[];
  limit: number;
  offset: number;
};

export type MatchingRecommendationsRequest = {
  min_score?: number;
  limit?: number;
  offset?: number;
  opportunity_type?: string;
  location?: string;
  remote_preference?: string;
  skills?: string;
  min_salary?: number;
  max_salary?: number;
};

export type MatchingRecalculateResponse = {
  recalculated_count: number;
  message: string;
};

export type MatchDetailResponse = {
  opportunity_id: string;
  user_id: string;
  overall_score: number;
  factor_scores: Record<string, number>;
  explanation: {
    positive_reasons: string[];
    missing_requirements: string[];
    potential_mismatches: string[];
    confidence: number;
  };
  skills_detail: {
    matched_skills: string[];
    missing_required_skills: string[];
    missing_preferred_skills: string[];
    extra_skills: string[];
    required_coverage: number;
    preferred_coverage: number;
    exact_matches: string[];
    partial_matches: string[];
    match_explanation: string;
  } | null;
  experience_detail: {
    user_level: string | null;
    required_level: string | null;
    is_compatible: boolean;
    level_difference: number;
    match_score: number;
    match_explanation: string;
    is_overqualified: boolean;
    is_underqualified: boolean;
  } | null;
  role_detail: {
    is_type_match: boolean;
    is_role_match: boolean;
    match_score: number;
    match_explanation: string;
    matched_roles: string[];
  } | null;
  location_detail: {
    user_locations: string[];
    opportunity_location: string | null;
    user_remote_preference: string | null;
    opportunity_remote_preference: string | null;
    is_location_match: boolean;
    is_remote_compatible: boolean;
    match_score: number;
    match_explanation: string;
    location_match_type: string;
  } | null;
  calculated_at: string;
};