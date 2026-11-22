import FirecrawlSettings from "@/components/settings/firecrawl-settings";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Workspace</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Settings</h1>
        <p className="mt-2 text-slate-600">Manage integrations used by your opportunity discovery workspace.</p>
      </div>
      <FirecrawlSettings />
    </div>
  );
}
