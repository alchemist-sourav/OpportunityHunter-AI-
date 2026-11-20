import type {
  Opportunity,
  OpportunityListItem,
  OpportunityListResponse,
  OpportunityExtractRequest,
  OpportunityExtractResponse,
  OpportunityVerifyRequest,
  OpportunityVerifyResponse,
  OpportunitySourcesResponse,
  OpportunitySource,
} from '@/types';
import { API_BASE_URL } from './api';

function getAuthHeader(): Record<string, string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('supabase_access_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/v1${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...options.headers,
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Unknown error' } }));
    throw new Error(error.error?.message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchOpportunities(params: {
  category?: string;
  verification_status?: string;
  source_domain?: string;
  location?: string;
  remote_preference?: string;
  skills?: string;
  search?: string;
  is_public?: boolean;
  limit?: number;
  offset?: number;
} = {}): Promise<OpportunityListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return fetchWithAuth<OpportunityListResponse>(`/opportunities?${searchParams.toString()}`);
}

export async function fetchOpportunity(opportunityId: string): Promise<Opportunity> {
  return fetchWithAuth<Opportunity>(`/opportunities/${opportunityId}`);
}

export async function extractFromDiscoveryJob(payload: OpportunityExtractRequest): Promise<OpportunityExtractResponse> {
  return fetchWithAuth<OpportunityExtractResponse>(`/opportunities/extract/${payload.job_id}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function verifyOpportunity(opportunityId: string): Promise<OpportunityVerifyResponse> {
  return fetchWithAuth<OpportunityVerifyResponse>(`/opportunities/${opportunityId}/verify`, {
    method: 'POST',
  });
}

export async function batchVerifyOpportunities(payload: OpportunityVerifyRequest): Promise<OpportunityVerifyResponse> {
  return fetchWithAuth<OpportunityVerifyResponse>(`/opportunities/verify/batch`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchOpportunitySources(opportunityId: string): Promise<OpportunitySource[]> {
  return fetchWithAuth<OpportunitySource[]>(`/opportunities/${opportunityId}/sources`);
}