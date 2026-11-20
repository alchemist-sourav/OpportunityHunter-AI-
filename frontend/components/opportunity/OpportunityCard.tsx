'use client';

import { useState } from 'react';
import type { Opportunity, OpportunityListItem, VerificationStatus } from '@/types';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

const VERIFICATION_COLORS: Record<VerificationStatus, string> = {
  unverified: 'bg-yellow-100 text-yellow-800',
  active: 'bg-green-100 text-green-800',
  expired: 'bg-orange-100 text-orange-800',
  closed: 'bg-red-100 text-red-800',
  inaccessible: 'bg-slate-100 text-slate-800',
  uncertain: 'bg-blue-100 text-blue-800',
};

const TYPE_LABELS: Record<string, string> = {
  internship: 'Internship',
  fresher_job: 'Fresher Job',
  full_time_job: 'Full-time',
  freelance_project: 'Freelance',
};

const REMOTE_LABELS: Record<string, string> = {
  remote_only: 'Remote',
  hybrid: 'Hybrid',
  onsite_only: 'Onsite',
  no_preference: 'Any',
};

interface OpportunityCardProps {
  opportunity: OpportunityListItem | Opportunity;
  onClick?: () => void;
  onVerify?: () => void;
  isVerifying?: boolean;
}

const formatSalary = (min: number | null, max: number | null, currency: string | null) => {
  if (!min && !max) return null;
  const c = currency || 'USD';
  if (min && max) return `${c} ${min.toLocaleString()} - ${max.toLocaleString()}`;
  if (min) return `${c} ${min.toLocaleString()}+`;
  if (max) return `${c} ${max.toLocaleString()}+`;
  return null;
}

interface OpportunityWithDetails extends OpportunityListItem {
  description?: string;
  required_skills?: string[];
  application_url?: string;
}

const isFullOpportunity = (opp: OpportunityListItem | Opportunity): opp is Opportunity => {
  return 'description' in opp;
};

export default function OpportunityCard({ opportunity, onClick, onVerify, isVerifying = false }: OpportunityCardProps) {
  const [expanded, setExpanded] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpanded(!expanded);
  };

  const handleVerify = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onVerify) await onVerify();
  };

  const isFullOpportunity = (opp: OpportunityListItem | Opportunity): opp is Opportunity => {
    return 'description' in opp;
  };

  const formatSalary = (min: number | null, max: number | null, currency: string | null) => {
    if (!min && !max) return null;
    const c = currency || 'USD';
    if (min && max) return `${c} ${min.toLocaleString()} - ${max.toLocaleString()}`;
    if (min) return `${c} ${min.toLocaleString()}+`;
    if (max) return `${c} ${max.toLocaleString()}+`;
    return null;
  };

  const getOpportunityTypeLabel = (opp: OpportunityListItem | Opportunity): string => {
    const type = opp.opportunity_type;
    return type ? TYPE_LABELS[type] || type : '';
  };

  return (
    <Card
      title={
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-semibold text-slate-900 flex-1 cursor-pointer" onClick={onClick}>
            {opportunity.title || 'Untitled Position'}
          </h3>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${VERIFICATION_COLORS[opportunity.verification_status] || 'bg-slate-100 text-slate-800'}`}>
            {opportunity.verification_status}
          </span>
        </div>
      }
    >
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {opportunity.opportunity_type && (
            <span className="px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded">
              {TYPE_LABELS[opportunity.opportunity_type] || opportunity.opportunity_type}
            </span>
          )}
          {opportunity.remote_preference && (
            <span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded">
              {REMOTE_LABELS[opportunity.remote_preference] || opportunity.remote_preference}
            </span>
          )}
          {opportunity.source_domain && (
            <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded">
              {opportunity.source_domain}
            </span>
          )}
        </div>

        <div className="flex items-center gap-4 text-sm text-slate-600">
          {opportunity.company_name && (
            <span className="font-medium">{opportunity.company_name}</span>
          )}
          {opportunity.location && (
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {opportunity.location}
            </span>
          )}
          {formatSalary(opportunity.salary_min, opportunity.salary_max, opportunity.salary_currency) && (
            <span className="font-medium text-emerald-600">
              {formatSalary(opportunity.salary_min, opportunity.salary_max, opportunity.salary_currency)}
            </span>
          )}
        </div>

        {isFullOpportunity(opportunity) && opportunity.description && expanded && (
          <div className="pt-2 border-t border-slate-200">
            <p className="text-sm text-slate-600 line-clamp-4">{opportunity.description}</p>
          </div>
        )}

        {isFullOpportunity(opportunity) && opportunity.required_skills && opportunity.required_skills.length > 0 && expanded && (
          <div className="pt-2">
            <p className="text-xs font-medium text-slate-500 mb-1">Skills</p>
            <div className="flex flex-wrap gap-1">
              {opportunity.required_skills.slice(0, 10).map((skill) => (
                <span key={skill} className="px-2 py-0.5 text-xs bg-slate-100 text-slate-700 rounded">
                  {skill}
                </span>
              ))}
              {opportunity.required_skills.length > 10 && (
                <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-500 rounded">
                  +{opportunity.required_skills.length - 10} more
                </span>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-slate-200">
          <div className="flex items-center gap-2">
            <button
              onClick={handleClick}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
            {isFullOpportunity(opportunity) && opportunity.application_url && (
              <a
                href={opportunity.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Apply
              </a>
            )}
          </div>
          <button
            onClick={handleVerify}
            disabled={isVerifying || opportunity.verification_status === 'active'}
            className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isVerifying ? 'Verifying...' : 'Verify'}
          </button>
        </div>
      </div>
    </Card>
  );
}