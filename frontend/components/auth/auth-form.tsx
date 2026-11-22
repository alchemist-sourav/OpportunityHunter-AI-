"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signInWithPassword, signUp } from "@/lib/supabase-auth";

type Props = { mode: "login" | "register" };

export default function AuthForm({ mode }: Props) {
  const router = useRouter();
  const isRegister = mode === "register";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      if (isRegister) {
        const result = await signUp(email.trim(), password, name.trim());
        if (!result.access_token) {
          setNotice("Account created. Check your email to confirm your address, then log in.");
          return;
        }
      } else {
        await signInWithPassword(email.trim(), password);
      }
      window.dispatchEvent(new Event("opportunity-hunter-auth-change"));
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to authenticate.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-md px-4 py-16 md:py-24">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50">
        <div className="mb-7">
          <p className="text-sm font-semibold text-indigo-600">OPPORTUNITYHUNTER AI</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{isRegister ? "Create your account" : "Welcome back"}</h1>
          <p className="mt-2 text-sm text-slate-500">{isRegister ? "Start finding opportunities that match your goals." : "Sign in to continue to your opportunity workspace."}</p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          {isRegister && <div><label htmlFor="name" className="mb-1 block text-sm font-medium text-slate-700">Full name</label><input id="name" autoComplete="name" required value={name} onChange={e => setName(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" /></div>}
          <div><label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">Email address</label><input id="email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" /></div>
          <div><label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">Password</label><input id="password" type="password" autoComplete={isRegister ? "new-password" : "current-password"} minLength={8} required value={password} onChange={e => setPassword(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" /><p className="mt-1 text-xs text-slate-500">Use at least 8 characters.</p></div>
          {error && <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          {notice && <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>}
          <button disabled={busy} className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">{busy ? "Please wait…" : isRegister ? "Create account" : "Log in"}</button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-600">{isRegister ? "Already have an account?" : "New to OpportunityHunter AI?"} <Link className="font-semibold text-indigo-600 hover:text-indigo-700" href={isRegister ? "/login" : "/register"}>{isRegister ? "Log in" : "Create account"}</Link></p>
      </div>
    </section>
  );
}
