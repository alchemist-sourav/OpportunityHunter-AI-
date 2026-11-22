"use client";

import { FormEvent, useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { authenticatedFetch } from "@/lib/supabase-auth";

type Profile = {
  full_name: string | null;
  skills: string[];
  experience_level: string;
  preferred_job_roles: string[];
  preferred_opportunity_types: string[];
  preferred_locations: string[];
  remote_preference: string;
};

const emptyProfile: Profile = {
  full_name: "", skills: [], experience_level: "fresher",
  preferred_job_roles: [], preferred_opportunity_types: ["internship", "fresher_job"],
  preferred_locations: [], remote_preference: "no_preference",
};

const inputClass = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";
const labelClass = "block text-sm font-medium text-slate-700";

export default function ProfileEditor() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [exists, setExists] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    authenticatedFetch(`${API_BASE_URL}/api/v1/profile`)
      .then(async response => {
        if (response.status === 404) return null;
        if (!response.ok) throw new Error("Could not load your profile.");
        return response.json() as Promise<Profile>;
      })
      .then(data => { if (active && data) { setProfile(data); setExists(true); } })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : "Profile loading failed."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile(current => ({ ...current, [key]: value }));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(""); setMessage("");
    const payload = {
      ...profile,
      full_name: profile.full_name?.trim() || "",
      skills: profile.skills,
      preferred_job_roles: profile.preferred_job_roles,
      preferred_opportunity_types: profile.preferred_opportunity_types,
      preferred_locations: profile.preferred_locations,
    };
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/profile`, {
        method: exists ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error?.message || "Could not save your profile.");
      }
      setProfile(await response.json() as Profile); setExists(true); setMessage("Profile saved successfully.");
    } catch (e) { setError(e instanceof Error ? e.message : "Profile save failed."); }
    finally { setSaving(false); }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading your profile…</p>;

  return <form onSubmit={save} className="space-y-6">
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Personal information</h2>
      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <label className={labelClass}>Full name<input required maxLength={255} className={inputClass} value={profile.full_name ?? ""} onChange={e => update("full_name", e.target.value)} /></label>
        <label className={labelClass}>Experience level<select className={inputClass} value={profile.experience_level} onChange={e => update("experience_level", e.target.value)}><option value="student">Student</option><option value="fresher">Fresher</option><option value="junior">Junior</option><option value="experienced">Experienced</option></select></label>
        <label className={labelClass}>Remote preference<select className={inputClass} value={profile.remote_preference} onChange={e => update("remote_preference", e.target.value)}><option value="no_preference">No preference</option><option value="remote_only">Remote only</option><option value="hybrid">Hybrid</option><option value="onsite_only">On-site only</option></select></label>
        <label className={labelClass}>Skills <span className="font-normal text-slate-400">(comma-separated)</span><input className={inputClass} value={profile.skills.join(", ")} onChange={e => update("skills", e.target.value.split(",").map(v => v.trim()).filter(Boolean))} placeholder="Python, React, SQL" /></label>
        <label className={labelClass}>Preferred roles <span className="font-normal text-slate-400">(comma-separated)</span><input className={inputClass} value={profile.preferred_job_roles.join(", ")} onChange={e => update("preferred_job_roles", e.target.value.split(",").map(v => v.trim()).filter(Boolean))} placeholder="AI Engineer, ML Engineer" /></label>
        <label className={labelClass}>Preferred locations <span className="font-normal text-slate-400">(comma-separated)</span><input className={inputClass} value={profile.preferred_locations.join(", ")} onChange={e => update("preferred_locations", e.target.value.split(",").map(v => v.trim()).filter(Boolean))} placeholder="Remote, Bengaluru, Kochi" /></label>
      </div>
      <div className="mt-5">
        <p className={labelClass}>Opportunity types</p>
        <div className="mt-3 flex flex-wrap gap-3">
          {(["internship", "fresher_job", "full_time_job", "freelance_project"] as const).map(type => <label key={type} className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={profile.preferred_opportunity_types.includes(type)} onChange={e => update("preferred_opportunity_types", e.target.checked ? [...profile.preferred_opportunity_types, type] : profile.preferred_opportunity_types.filter(v => v !== type))} />{type.replaceAll("_", " ")}</label>)}
        </div>
      </div>
    </section>
    {error && <p role="alert" className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
    {message && <p role="status" className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p>}
    <button disabled={saving} className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">{saving ? "Saving…" : "Save profile"}</button>
  </form>;
}
