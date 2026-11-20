'use client';

import type { DiscoveryJob, DiscoveryResult } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import Card from '@/components/ui/card';

interface DiscoveryStatusProps {
  job: DiscoveryJob;
  onCancel?: () => void;
  onRefresh?: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-slate-100 text-slate-800',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

export default function DiscoveryStatus({ job, onCancel, onRefresh }: DiscoveryStatusProps) {
  const isActive = job.status === 'pending' || job.status === 'running';
  const isCancellable = job.status === 'pending' || job.status === 'running';

  const getProgress = () => {
    if (job.total_pages === 0) return 0;
    return Math.round((job.completed_pages / job.total_pages) * 100);
  };

  return (
    <Card title="Discovery Status">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[job.status] || 'bg-slate-100 text-slate-800'}`}>
            {STATUS_LABELS[job.status] || job.status}
          </span>
          <span className="text-sm text-slate-500">
            Started {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
          </span>
        </div>

        {isActive && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Progress</span>
              <span className="font-medium">{getProgress()}%</span>
            </div>
            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${getProgress()}%` }}
              />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-slate-600">
              <div>Pages: {job.completed_pages} / {job.total_pages}</div>
              <div>Results: {job.result_count}</div>
              <div>Credits: {job.credits_used}</div>
            </div>
          </div>
        )}

        {!isActive && job.status !== 'pending' && (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-slate-500">Total Pages</p>
              <p className="font-semibold">{job.total_pages}</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-slate-500">Completed</p>
              <p className="font-semibold">{job.completed_pages}</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-slate-500">Results Found</p>
              <p className="font-semibold">{job.result_count}</p>
            </div>
          </div>
        )}

        {job.error_message && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            <strong>Error:</strong> {job.error_message}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isActive}
              className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Refresh
            </button>
          )}
          {isCancellable && onCancel && (
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </Card>
  );
}