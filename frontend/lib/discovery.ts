import type { DiscoverySearchRequest, DiscoveryJob, DiscoveryHistoryResponse, DiscoveryCancelResponse } from '@/types';
import { API_BASE_URL } from './api';
import { authenticatedFetch } from './supabase-auth';

function getAuthHeader(): Record<string, string> {
  // In a real app, this would come from Supabase auth session
  // For now, we'll use a stored token or environment variable
  const token = typeof window !== 'undefined' ? localStorage.getItem('supabase_access_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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

export async function startDiscoverySearch(payload: DiscoverySearchRequest): Promise<DiscoveryJob> {
  return fetchWithAuth<DiscoveryJob>('/discovery/search', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getDiscoveryJob(jobId: string): Promise<DiscoveryJob> {
  return fetchWithAuth<DiscoveryJob>(`/discovery/${jobId}`);
}

export async function cancelDiscoveryJob(jobId: string): Promise<DiscoveryCancelResponse> {
  return fetchWithAuth<DiscoveryCancelResponse>(`/discovery/${jobId}/cancel`, {
    method: 'POST',
  });
}

export async function getDiscoveryHistory(limit = 20, offset = 0): Promise<DiscoveryHistoryResponse> {
  return fetchWithAuth<DiscoveryHistoryResponse>(`/discovery?limit=${limit}&offset=${offset}`);
}