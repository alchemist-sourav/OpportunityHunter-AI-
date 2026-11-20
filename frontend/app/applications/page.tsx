'use client';

import { useEffect } from 'react';
import ApplicationTracker from '@/components/application/ApplicationList';
import Button from '@/components/shared/button';

export default function ApplicationsPage() {
  useEffect(() => {
    // Application tracker loads its own data
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Application Tracker</h1>
            <p className="text-slate-500">Track your application progress and stay on top of deadlines</p>
          </div>
          <Button
            onClick={() => {}}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            New Application
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        <ApplicationTracker />
      </main>
    </div>
  );
}