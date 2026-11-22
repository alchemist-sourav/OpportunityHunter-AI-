"use client";

import { FormEvent, useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { authenticatedFetch } from "@/lib/supabase-auth";

type CredentialStatus = { provider: string; configured: boolean; algorithm?: string | null; updated_at?: string | null };

export default function FirecrawlSettings() {
  const [status, setStatus] = useState<CredentialStatus | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadStatus() {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/credentials/firecrawl/status`);
    if (!response.ok) throw new Error("Unable to load Firecrawl credential status.");
    setStatus(await response.json() as CredentialStatus);
  }

  useEffect(() => {
    let active = true;
    authenticatedFetch(`${API_BASE_URL}/api/v1/credentials/firecrawl/status`)
      .then(async response => {
        if (!response.ok) throw new Error("Unable to load Firecrawl credential status.");
        return response.json() as Promise<CredentialStatus>;
      })
      .then(data => { if (active) setStatus(data); })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : "Settings could not be loaded."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/credentials/firecrawl`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey.trim() }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.error?.message || "Unable to save Firecrawl API key.");
      setApiKey(""); await loadStatus(); setNotice("Firecrawl API key saved securely.");
    } catch (e) { setError(e instanceof Error ? e.message : "Credential update failed."); }
    finally { setSaving(false); }
  }

  async function remove() {
    if (!window.confirm("Remove your saved Firecrawl API key?")) return;
    setSaving(true); setError(""); setNotice("");
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/credentials/firecrawl`, { method: "DELETE" });
      if (!response.ok) throw new Error("Unable to remove Firecrawl API key.");
      setStatus({ provider: "firecrawl", configured: false }); setNotice("Firecrawl API key removed.");
    } catch (e) { setError(e instanceof Error ? e.message : "Credential removal failed."); }
    finally { setSaving(false); }
  }

  return <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Integrations</p><h2 className="mt-1 text-xl font-semibold text-slate-950">Firecrawl</h2><p className="mt-1 max-w-xl text-sm text-slate-500">Connect your Firecrawl API key to discover opportunities from supported sources. Your key is encrypted on the backend and never returned to the browser.</p></div>
      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${status?.configured ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{loading ? "Checking…" : status?.configured ? "Connected" : "Not connected"}</span>
    </div>
    <form onSubmit={save} className="mt-6 space-y-3">
      <label htmlFor="firecrawl-key" className="block text-sm font-medium text-slate-700">Firecrawl API key</label>
      <input id="firecrawl-key" type="password" autoComplete="new-password" minLength={16} maxLength={255} required value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder={status?.configured ? "Enter a new key to replace the saved key" : "fc-…"} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
      <div className="flex flex-wrap gap-3"><button disabled={saving || loading || !apiKey.trim()} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">{saving ? "Saving…" : "Save API key"}</button>{status?.configured && <button type="button" disabled={saving} onClick={remove} className="rounded-lg border border-rose-200 px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50">Remove key</button>}</div>
    </form>
    {status?.updated_at && <p className="mt-3 text-xs text-slate-500">Last updated: {new Date(status.updated_at).toLocaleString()}</p>}
    {error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
    {notice && <p role="status" className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>}
  </section>;
}
