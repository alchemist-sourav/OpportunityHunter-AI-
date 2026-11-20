export interface DiscoverySearchRequest {
  category: 'internship' | 'fresher_job' | 'full_time_job' | 'freelance_project';
  keywords: string;
  skills?: string[];
  locations?: string[];
  remote_preference?: 'remote_only' | 'hybrid' | 'onsite_only' | 'no_preference';
  experience_level?: 'student' | 'fresher' | 'junior' | 'experienced';
  max_results?: number;
  source_domains?: string[];
}

export interface DiscoveryResult {
  url: string;
  title: string | null;
  status_code: number | null;
  domain: string | null;
  snippet: string;
  relevant: boolean;
  found_keywords: number;
}

export interface DiscoveryJob {
  id: string;
  user_id: string;
  category: string;
  keywords: string;
  skills: string[];
  locations: string[];
  remote_preference: string;
  experience_level: string | null;
  max_results: number;
  source_domains: string[];
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  cancel_requested: boolean;
  total_pages: number;
  completed_pages: number;
  result_count: number;
  credits_used: number;
  error_message: string | null;
  results: DiscoveryResult[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface DiscoveryHistoryItem {
  id: string;
  category: string;
  keywords: string;
  status: string;
  result_count: number;
  created_at: string;
  updated_at: string;
}

export interface DiscoveryHistoryResponse {
  total: number;
  items: DiscoveryHistoryItem[];
}

export interface DiscoveryCancelResponse {
  id: string;
  status: string;
  cancelled: boolean;
}