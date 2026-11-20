'use client';

import ApplicationTracker from '@/components/application/ApplicationList';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-1">
          Your personal opportunity overview
        </p>
      </div>

      <ApplicationTracker />
    </div>
  );
}