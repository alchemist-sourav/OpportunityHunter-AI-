import type {
  MatchingRecommendationsResponse,
  MatchingRecommendationsRequest,
  MatchDetail,
  MatchingRecalculateResponse,
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

export async function fetchRecommendations(params: MatchingRecommendationsRequest = {}): Promise<{ total: number; items: any[]; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return fetchWithAuth(`/matching/recommendations?${searchParams.toString()}`);
}

export async function fetchOpportunityMatch(opportunityId: string): Promise<any> {
  return fetchWithAuth(`/matching/${opportunityId}`);
}

export async function recalculateMatches(): Promise<{ recalculated_count: number; message: string }> {
  return fetchWithAuth(`/matching/recalculate`, {
    method: 'POST',
  });
}