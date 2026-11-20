import type {
  OpportunityListItem,
  OpportunityListResponse,
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

export async function fetchPublicOpportunities(params: {
  category?: string;
  verification_status?: string;
  location?: string;
  remote_preference?: string;
  experience_level?: string;
  skills?: string;
  search?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<{ total: number; items: OpportunityListItem[]; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return fetchWithAuth<{ total: number; items: OpportunityListItem[]; limit: number; offset: number }>(
    `/public/opportunities?${searchParams.toString()}`
  );
}

export async function fetchPublicOpportunity(opportunityId: string): Promise<OpportunityListItem> {
  return fetchWithAuth<OpportunityListItem>(`/public/opportunities/${opportunityId}`);
}