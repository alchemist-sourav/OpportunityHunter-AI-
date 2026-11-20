export type OpportunityType = 'internship' | 'fresher_job' | 'full_time_job' | 'freelance_project';
export type VerificationStatus = 'unverified' | 'active' | 'expired' | 'closed' | 'inaccessible' | 'uncertain';
export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'temporary' | 'internship' | 'freelance' | 'unknown';
export type ExperienceLevel = 'student' | 'fresher' | 'junior' | 'experienced';
export type RemotePreference = 'remote_only' | 'hybrid' | 'onsite_only' | 'no_preference';

export interface Opportunity {
  id: string;
  fingerprint: string;
  title: string | null;
  company_name: string | null;
  description: string | null;
  opportunity_type: OpportunityType | null;
  required_skills: string[];
  experience_level: ExperienceLevel | null;
  location: string | null;
  remote_preference: RemotePreference | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  application_url: string | null;
  source_url: string;
  source_domain: string;
  application_deadline: string | null;
  employment_type: EmploymentType | null;
  verification_status: VerificationStatus;
  last_verified_at: string | null;
  verification_evidence: string | null;
  verification_failure_reason: string | null;
  is_public: boolean;
  extracted_at: string;
  created_at: string;
  updated_at: string;
  sources: OpportunitySource[];
}

export interface OpportunitySource {
  id: number;
  discovery_job_id: string;
  user_id: string;
  source_url: string;
  source_domain: string;
  extracted_at: string;
}

export interface OpportunityListItem {
  id: string;
  title: string | null;
  company_name: string | null;
  opportunity_type: OpportunityType | null;
  location: string | null;
  remote_preference: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  verification_status: VerificationStatus;
  source_domain: string;
  created_at: string;
}

export interface OpportunityListResponse {
  total: number;
  items: OpportunityListItem[];
  limit: number;
  offset: number;
}

export interface OpportunityExtractRequest {
  job_id: string;
  result_indices?: number[];
}

export interface OpportunityExtractResponse {
  created: string[];
  updated: string[];
  skipped: Array<Record<string, any>>;
  errors: string[];
}

export interface OpportunityVerifyRequest {
  opportunity_ids?: string[];
}

export interface OpportunityVerifyResponse {
  verified: Record<string, VerificationStatus>;
  errors: string[];
}

export interface OpportunitySourcesResponse {
  opportunity_id: string;
  sources: OpportunitySource[];
}