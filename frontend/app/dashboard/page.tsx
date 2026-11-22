'use client';

import AuthGate from '@/components/auth/auth-gate';
import ApplicationTracker from '@/components/application/ApplicationList';

export default function DashboardPage() {
  return (
    <AuthGate>
      <div className="space-y-6 px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-slate-600">Your personal opportunity overview</p>
        </div>
        <ApplicationTracker />
      </div>
    </AuthGate>
  );
}
