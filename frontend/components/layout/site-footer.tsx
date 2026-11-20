import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-slate-500 md:flex-row">
        <p>© {new Date().getFullYear()} OpportunityHunter AI. Licensed under Apache-2.0.</p>
        <nav className="flex gap-6">
          <Link href="/dashboard" className="hover:text-indigo-600">
            Dashboard
          </Link>
          <Link href="/settings" className="hover:text-indigo-600">
            Settings
          </Link>
          <Link href="/login" className="hover:text-indigo-600">
            Log in
          </Link>
        </nav>
      </div>
      <p className="pb-6 text-center text-xs text-slate-400">
        Phase 1 foundation — authentication and opportunity discovery are not yet operational.
      </p>
    </footer>
  );
}
