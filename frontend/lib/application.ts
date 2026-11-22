import type { ApplicationListResponse, ApplicationListItem } from '@/types';
import { authenticatedFetch } from '@/lib/supabase-auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export { API_BASE_URL };

export async function fetchApplications(params: {
  limit?: number;
  offset?: number;
}): Promise<ApplicationListResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) {
    searchParams.append('limit', String(params.limit));
  }
  if (params.offset !== undefined) {
    searchParams.append('offset', String(params.offset));
  }
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/applications?${searchParams.toString()}`, {
    credentials: "include",
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Unknown error' } }));
    throw new Error(error.error?.message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<ApplicationListResponse>;
}

export async function fetchApplication(opportunityId: string): Promise<ApplicationListItem> {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/applications/${opportunityId}`, {
    credentials: "include",
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Unknown error' } }));
    throw new Error(error.error?.message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<ApplicationListItem>;
}

export async function updateApplicationStatus(
  applicationId: string,
  status: string
): Promise<ApplicationListItem> {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/applications/${applicationId}`, {
    method: 'PATCH',
    credentials: "include",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Unknown error' } }));
    throw new Error(error.error?.message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<ApplicationListItem>;
}