type SupabaseAuthResponse = {
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
  expires_at?: number;
  user?: { id: string; email?: string; user_metadata?: Record<string, unknown> };
  msg?: string;
  message?: string;
  error_description?: string;
};

const SESSION_KEY = "opportunity_hunter_supabase_session";

function config() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error("Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.");
  }
  return { url: url.replace(/\/$/, ""), key };
}

function readSession(): SupabaseAuthResponse | null {
  if (typeof window === "undefined") return null;
  const value = window.sessionStorage.getItem(SESSION_KEY);
  if (!value) return null;
  try { return JSON.parse(value) as SupabaseAuthResponse; } catch { return null; }
}

function writeSession(session: SupabaseAuthResponse | null) {
  if (typeof window === "undefined") return;
  if (session?.access_token && session.refresh_token) {
    const stored = { ...session, expires_at: session.expires_at ?? Math.floor(Date.now() / 1000) + (session.expires_in ?? 3600) };
    window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(stored));
  } else {
    window.sessionStorage.removeItem(SESSION_KEY);
  }
}

async function authRequest(path: string, body: Record<string, unknown>) {
  const { url, key } = config();
  const response = await fetch(`${url}/auth/v1/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: key },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const data = await response.json().catch(() => ({})) as SupabaseAuthResponse;
  if (!response.ok) {
    throw new Error(data.msg || data.message || data.error_description || "Authentication request failed.");
  }
  return data;
}

export async function signInWithPassword(email: string, password: string) {
  const data = await authRequest("token?grant_type=password", { email, password });
  if (!data.access_token || !data.refresh_token) throw new Error("Supabase did not return a valid session.");
  writeSession(data);
  return data;
}

export async function signUp(email: string, password: string, fullName: string) {
  const data = await authRequest("signup", {
    email,
    password,
    data: { full_name: fullName },
  });
  if (data.access_token && data.refresh_token) writeSession(data);
  return data;
}

export async function signOut() {
  const token = readSession()?.access_token;
  try {
    if (token) {
      const { url, key } = config();
      await fetch(`${url}/auth/v1/logout`, {
        method: "POST",
        headers: { apikey: key, Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
    }
  } finally {
    writeSession(null);
  }
}

export async function getAccessToken(): Promise<string | null> {
  const session = readSession();
  if (!session?.access_token || !session.refresh_token) return null;
  // Refresh shortly before expiry; Supabase returns expires_in in seconds.
  const expiresAt = Number(session.expires_at ?? 0);
  if (!expiresAt || expiresAt * 1000 > Date.now() + 60_000) return session.access_token;
  const refreshed = await authRequest("token?grant_type=refresh_token", {
    refresh_token: session.refresh_token,
  });
  if (!refreshed.access_token || !refreshed.refresh_token) {
    writeSession(null);
    return null;
  }
  writeSession(refreshed);
  return refreshed.access_token;
}

export async function authenticatedFetch(input: string, init: RequestInit = {}) {
  const token = await getAccessToken();
  if (!token) throw new Error("Your session has expired. Please log in again.");
  return fetch(input, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
}
