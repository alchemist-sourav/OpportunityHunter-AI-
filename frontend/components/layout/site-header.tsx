"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAccessToken, signOut } from "@/lib/supabase-auth";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/profile", label: "Profile" },
  { href: "/settings", label: "Settings" },
];

export default function SiteHeader() {
  const [open, setOpen] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const sync = () => { getAccessToken().then(token => setAuthenticated(Boolean(token))).catch(() => setAuthenticated(false)); };
    sync();
    window.addEventListener("opportunity-hunter-auth-change", sync);
    return () => window.removeEventListener("opportunity-hunter-auth-change", sync);
  }, []);

  async function handleSignOut() {
    await signOut();
    setAuthenticated(false);
    window.dispatchEvent(new Event("opportunity-hunter-auth-change"));
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-slate-900">
          OpportunityHunter <span className="text-indigo-600">AI</span>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-slate-600 md:flex">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-indigo-600">
              {link.label}
            </Link>
          ))}
          {authenticated ? (
            <>
              <Link href="/dashboard" className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700">Open workspace</Link>
              <button type="button" onClick={handleSignOut} className="text-sm font-medium text-slate-600 hover:text-rose-600">Sign out</button>
            </>
          ) : (
            <Link href="/login" className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700">Log in</Link>
          )}
        </nav>
        <button
          type="button"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 md:hidden"
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>
      {open ? (
        <nav className="border-t border-slate-200 bg-white md:hidden">
          <ul className="space-y-1 px-4 py-3">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  {link.label}
                </Link>
              </li>
            ))}
            <li>
              {authenticated ? (
                <button type="button" onClick={handleSignOut} className="block w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-rose-600 hover:bg-slate-50">Sign out</button>
              ) : (
                <Link href="/login" onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2 text-sm font-medium text-indigo-600 hover:bg-slate-50">Log in</Link>
              )}
            </li>
          </ul>
        </nav>
      ) : null}
    </header>
  );
}
