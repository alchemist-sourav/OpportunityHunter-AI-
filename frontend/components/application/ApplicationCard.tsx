'use client';

import { useState } from 'react';
import type { ApplicationStatus, ApplicationListItem, OpportunitySummary } from '@/types';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

interface ApplicationCardProps {
  application: ApplicationListItem & { opportunity: OpportunitySummary };
  onStatusChange?: (status: ApplicationStatus) => void;
  onDelete?: () => void;
}

const STATUS_BADGES: Record<ApplicationStatus, string> = {
  interested: 'bg-gray-100 text-gray-800',
  saved: 'bg-blue-100 text-blue-800',
  applied: 'bg-emerald-100 text-emerald-800',
  assessment: 'bg-yellow-100 text-yellow-800',
  interview: 'bg-indigo-100 text-indigo-800',
  offer: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  withdrawn: 'bg-slate-100 text-slate-800',
};

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  interested: 'Interested',
  saved: 'Saved',
  applied: 'Applied',
  assessment: 'Assessment',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
};

const formatDeadline = (deadline: string | null) => {
  if (!deadline) return 'No deadline';
  const date = new Date(deadline);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export default function ApplicationCard({ application, onStatusChange, onDelete }: ApplicationCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card title="Application">
      <div className="px-4 py-3 border-b border-slate-200 flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded bg-slate-100 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-medium text-slate-600">
              {application.opportunity?.opportunity_type ?
                application.opportunity.opportunity_type.replace('_', ' ') : 'Opp'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-slate-900 line-clamp-2 cursor-pointer">
              {application.opportunity?.title || 'Untitled Opportunity'}
            </h3>
            <p className="text-sm text-slate-500 line-clamp-1">
              {application.opportunity?.company_name || 'Unknown Company'}
            </p>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGES[application.status] || 'bg-gray-100 text-gray-800'}`}>
            {STATUS_LABELS[application.status]}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{formatDeadline(application.deadline)}</span>
        </div>
      </div>

      {expanded && (
        <div className="px-4 py-3 border-t border-slate-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-500 mb-1">Location</p>
              <p className="text-sm text-slate-700">{application.opportunity?.location || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-1">Remote</p>
              <p className="text-sm text-slate-700 capitalize">{application.opportunity?.remote_preference || 'Not specified'}</p>
            </div>
          </div>
          {application.notes && (
            <div>
              <p className="text-sm text-slate-500 mb-1">Notes</p>
              <p className="text-sm text-slate-600 whitespace-pre-wrap max-h-40 line-clamp-3">{application.notes}</p>
            </div>
          )}
          {application.opportunity?.source_domain && (
            <div className="mt-3 pt-3 border-t border-slate-200">
              <p className="text-sm text-slate-500">Source</p>
              <a href={application.opportunity.source_domain} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                {application.opportunity.source_domain}
              </a>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}