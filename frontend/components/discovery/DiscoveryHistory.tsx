'use client';

import type { DiscoveryHistoryItem } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import Card from '@/components/ui/card';

interface DiscoveryHistoryProps {
  items: DiscoveryHistoryItem[];
  total: number;
  onLoadMore?: () => void;
  hasMore: boolean;
  isLoading?: boolean;
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

export default function DiscoveryHistory({ items, total, onLoadMore, hasMore, isLoading }: DiscoveryHistoryProps) {
  if (items.length === 0) {
    return (
      <Card title="Discovery History">
        <div className="text-center py-8 text-slate-500">
          No discovery jobs yet. Start your first search above!
        </div>
      </Card>
    );
  }

  return (
    <Card title={`Discovery History (${total})`}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="pb-2 pr-4">Category</th>
              <th className="pb-2 pr-4">Keywords</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2 pr-4">Results</th>
              <th className="pb-2 pr-4">Created</th>
              <th className="pb-2 pr-4">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50">
                <td className="py-3 pr-4">
                  <span className="capitalize">{item.category.replace('_', ' ')}</span>
                </td>
                <td className="py-3 pr-4 max-w-xs truncate">{item.keywords}</td>
                <td className="py-3 pr-4">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[item.status] || 'bg-slate-100 text-slate-800'}`}>
                    {STATUS_LABELS[item.status] || item.status}
                  </span>
                </td>
                <td className="py-3 pr-4 font-mono">{item.result_count}</td>
                <td className="py-3 pr-4 text-slate-500">
                  {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                </td>
                <td className="py-3 pr-4 text-slate-500">
                  {formatDistanceToNow(new Date(item.updated_at), { addSuffix: true })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(hasMore || isLoading) && (
        <div className="mt-4 text-center">
          <button
            onClick={onLoadMore}
            disabled={isLoading}
            className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </Card>
  );
}