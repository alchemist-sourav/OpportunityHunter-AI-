export type ApplicationStatus = 'interested' | 'saved' | 'applied' | 'assessment' | 'interview' | 'offer' | 'rejected' | 'withdrawn';

export interface Application {
  id: string;
  user_id: string;
  opportunity_id: string;
  status: ApplicationStatus;
  applied_date: string | null;
  deadline: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  opportunity?: OpportunitySummary;
}

export interface OpportunitySummary {
  id: string;
  title: string | null;
  company_name: string | null;
  opportunity_type: string | null;
  location: string | null;
  remote_preference: string | null;
  verification_status: string;
  source_domain: string;
}

export interface ApplicationFormData {
  status: ApplicationStatus;
  notes: string;
  deadline: string | null;
}

export interface ApplicationListItem {
  id: string;
  opportunity_id: string;
  status: ApplicationStatus;
  applied_date: string | null;
  deadline: string | null;
  notes: string | null;
  created_at: string;
  opportunity: OpportunitySummary | null;
}

export interface ApplicationListResponse {
  total: number;
  items: ApplicationListItem[];
  limit: number;
  offset: number;
}