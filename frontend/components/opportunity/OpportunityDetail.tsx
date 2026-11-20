'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchOpportunity, verifyOpportunity, fetchOpportunitySources } from '@/lib/opportunity';
import type { Opportunity, OpportunitySource } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

const VERIFICATION_COLORS: Record<string, string> = {
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

const EMPLOYMENT_LABELS: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  contract: 'Contract',
  temporary: 'Temporary',
  internship: 'Internship',
  freelance: 'Freelance',
  unknown: 'Unknown',
};

interface OpportunityDetailProps {
  opportunityId: string;
  onClose: () => void;
}

const formatSalary = (min: number | null, max: number | null, currency: string | null) => {
  if (!min && !max) return 'Not specified';
  const c = currency || 'USD';
  if (min && max) return `${c} ${min.toLocaleString()} - ${max.toLocaleString()}`;
  if (min) return `${c} ${min.toLocaleString()}+`;
  if (max) return `${c} ${max.toLocaleString()}+`;
  return 'Not specified';
}

export default function OpportunityDetail({ opportunityId, onClose }: OpportunityDetailProps) {
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [sources, setSources] = useState<OpportunitySource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(false);

  const loadOpportunity = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [opp, srcs] = await Promise.all([
        fetchOpportunity(opportunityId),
        fetchOpportunitySources(opportunityId),
      ]);
      setOpportunity(opp);
      setSources(srcs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load opportunity');
    } finally {
      setIsLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    loadOpportunity();
  }, [loadOpportunity]);

  const handleVerify = useCallback(async () => {
    if (!opportunity) return;
    setIsVerifying(true);
    try {
      const result = await verifyOpportunity(opportunityId);
      if (result.verified[opportunityId]) {
        setOpportunity(prev => prev ? { ...prev, verification_status: result.verified[opportunityId] } : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setIsVerifying(false);
    }
  }, [opportunityId]);

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading opportunity...</p>
        </div>
      </div>
    );
  }

  if (error && !opportunity) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-md mx-4">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    );
  }

  if (!opportunity) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between p-6 border-b border-slate-200 sticky top-0 bg-white/95 backdrop-blur z-10">
          <div>
            <h2 className="text-xl font-bold text-slate-900">{opportunity.title || 'Untitled Position'}</h2>
            <p className="text-slate-600 mt-1">{opportunity.company_name || 'Unknown Company'}</p>
          </div>
          <Button variant="secondary" onClick={onClose} className="shrink-0">
            Close
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
              {error}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {opportunity.opportunity_type && (
              <span className="px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded-full">
                {TYPE_LABELS[opportunity.opportunity_type] || opportunity.opportunity_type}
              </span>
            )}
            <span className={`px-3 py-1 text-sm rounded-full ${VERIFICATION_COLORS[opportunity.verification_status] || 'bg-slate-100 text-slate-800'}`}>
              {opportunity.verification_status}
            </span>
            {opportunity.source_domain && (
              <span className="px-3 py-1 text-sm bg-slate-100 text-slate-600 rounded-full">
                {opportunity.source_domain}
              </span>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-slate-500">Salary</p>
              <p className="text-lg font-medium text-emerald-600">
                {formatSalary(opportunity.salary_min, opportunity.salary_max, opportunity.salary_currency)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Location</p>
              <p className="text-lg font-medium">{opportunity.location || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Remote Preference</p>
              <p className="text-lg font-medium capitalize">{opportunity.remote_preference || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Employment Type</p>
              <p className="text-lg font-medium">{opportunity.employment_type ? EMPLOYMENT_LABELS[opportunity.employment_type] || opportunity.employment_type : 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Application Deadline</p>
              <p className="text-lg font-medium">{opportunity.application_deadline ? formatDistanceToNow(new Date(opportunity.application_deadline), { addSuffix: true }) : 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Source</p>
              <a href={opportunity.source_url} target="_blank" rel="noopener noreferrer" className="text-lg font-medium text-blue-600 hover:underline truncate block">
                {opportunity.source_domain}
              </a>
            </div>
            <div>
              <p className="text-sm text-slate-500">Apply Link</p>
              {opportunity.application_url ? (
                <a href={opportunity.application_url} target="_blank" rel="noopener noreferrer" className="text-lg font-medium text-blue-600 hover:underline truncate block">
                  Apply Now
                </a>
              ) : (
                <p className="text-lg font-medium text-slate-500">Not available</p>
              )}
            </div>
          </div>

          {opportunity.description && (
            <div>
              <p className="text-sm text-slate-500 mb-2">Description</p>
              <p className="text-slate-700 whitespace-pre-wrap">{opportunity.description}</p>
            </div>
          )}

          {opportunity.required_skills && opportunity.required_skills.length > 0 && (
            <div>
              <p className="text-sm text-slate-500 mb-2">Required Skills</p>
              <div className="flex flex-wrap gap-2">
                {opportunity.required_skills.map((skill: string) => (
                  <span key={skill} className="px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded-full">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-slate-200">
            <p className="text-sm text-slate-500 mb-2">Verification</p>
            <div className="flex items-center gap-4">
              <span className={`px-3 py-1 text-sm rounded-full ${VERIFICATION_COLORS[opportunity.verification_status] || 'bg-slate-100 text-slate-800'}`}>
                {opportunity.verification_status}
              </span>
              {opportunity.last_verified_at && (
                <span className="text-sm text-slate-500">
                  Last checked: {formatDistanceToNow(new Date(opportunity.last_verified_at), { addSuffix: true })}
                </span>
              )}
              <Button
                onClick={handleVerify}
                disabled={isVerifying || opportunity.verification_status === 'active'}
                variant="primary"
              >
                {isVerifying ? 'Verifying...' : 'Verify Now'}
              </Button>
            </div>
            {opportunity.verification_evidence && (
              <p className="mt-2 text-sm text-slate-600 bg-slate-50 p-3 rounded-lg">
                {opportunity.verification_evidence}
              </p>
            )}
            {opportunity.verification_failure_reason && (
              <p className="mt-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg">
                {opportunity.verification_failure_reason}
              </p>
            )}
          </div>

          {sources.length > 0 && (
            <div className="pt-4 border-t border-slate-200">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-slate-500">Sources ({sources.length})</p>
                <Button variant="secondary" onClick={() => setShowSources(!showSources)}>
                  {showSources ? 'Hide' : 'Show'} Sources
                </Button>
              </div>
              {showSources && (
                <div className="space-y-2">
                  {sources.map((source) => (
                    <div key={source.id} className="p-3 bg-slate-50 rounded-lg text-sm">
                      <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {source.source_domain}
                      </a>
                      <p className="text-slate-500">Extracted {formatDistanceToNow(new Date(source.extracted_at), { addSuffix: true })}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}