'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchOpportunityMatch } from '@/lib/matching';
import type { MatchDetail } from '@/types';
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

interface MatchDetailProps {
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

export default function MatchDetail({ opportunityId, onClose }: MatchDetailProps) {
  const [match, setMatch] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMatch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/matching/${opportunityId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('supabase_access_token')}`,
        },
      });
      if (!response.ok) {
        throw new Error('Failed to load match');
      }
      const matchData = await response.json();
      setMatch(matchData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load match');
    } finally {
      setIsLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    loadMatch();
  }, [loadMatch]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-700';
    if (score >= 60) return 'bg-yellow-100 text-yellow-700';
    if (score >= 40) return 'bg-orange-100 text-orange-700';
    return 'bg-red-100 text-red-700';
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading match details...</p>
        </div>
      </div>
    );
  }

  if (error && !match) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-md mx-4">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={onClose} className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Close</button>
        </div>
      </div>
    );
  }

  if (!match) return null;

  const m = match;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between p-6 border-b border-slate-200 sticky top-0 bg-white/95 backdrop-blur z-10">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Match Details</h2>
            <p className="text-slate-600 mt-1">Detailed match analysis</p>
          </div>
          <button onClick={onClose} className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50">
            Close
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[calc(90vh-200px)] overflow-y-auto">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex flex-wrap gap-2 mb-3">
                {m.factor_scores && (
                  <>
                    <span className={`px-3 py-1 text-sm rounded-full ${getScoreColor(m.overall_score)}`}>
                      {m.overall_score.toFixed(0)}% Match
                    </span>
                    <span className="px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded-full">
                      Skills: {m.factor_scores.skills?.toFixed(0)}%
                    </span>
                    <span className="px-3 py-1 text-sm bg-emerald-100 text-emerald-700 rounded-full">
                      Experience: {m.factor_scores.experience?.toFixed(0)}%
                    </span>
                    <span className="px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded-full">
                      Role: {m.factor_scores.role?.toFixed(0)}%
                    </span>
                    <span className="px-3 py-1 text-sm bg-emerald-100 text-emerald-700 rounded-full">
                      Location: {m.factor_scores.location?.toFixed(0)}%
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-medium text-slate-900 mb-2">Overall Score</h4>
                <div className="w-full h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getScoreColor(m.overall_score)}`}
                    style={{ width: `${m.overall_score}%` }}
                  />
                </div>
                <p className="text-2xl font-bold text-slate-900 mt-1">{m.overall_score?.toFixed(1) || 0}%</p>
                <p className="text-sm text-slate-500">Overall match score</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-medium text-slate-900 mb-2">Confidence</h4>
                <div className="w-full h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${(m.explanation?.confidence || 0) * 100}%` }}
                  />
                </div>
                <p className="text-2xl font-bold text-slate-900 mt-1">{(m.explanation?.confidence || 0) * 100}%</p>
                <p className="text-sm text-slate-500">Data completeness</p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <h4 className="font-medium text-slate-900 mb-4">Factor Scores</h4>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {m.factor_scores && Object.entries(m.factor_scores).map(([key, value]: [string, unknown]) => {
                  const numValue = typeof value === 'number' ? value : 0;
                  return (
                    <div key={key} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium capitalize text-slate-700">{key}</span>
                        <span className={`text-lg font-bold ${getScoreColor(numValue)}`}>
                          {numValue.toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${getScoreColor(numValue)}`}
                          style={{ width: `${numValue}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <h4 className="font-medium text-slate-900 mb-4">Why This Match?</h4>
              <div className="space-y-3">
                {m.explanation?.positive_reasons && m.explanation.positive_reasons.length > 0 && (
                  <div>
                    <h5 className="font-medium text-green-700 mb-2">+ Strengths</h5>
                    <ul className="space-y-1 text-sm text-slate-600">
                      {m.explanation.positive_reasons.map((reason: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-green-500">+</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {m.explanation?.missing_requirements && m.explanation.missing_requirements.length > 0 && (
                  <div>
                    <h5 className="font-medium text-orange-700 mb-2">! Missing Requirements</h5>
                    <ul className="space-y-1 text-sm text-slate-600">
                      {m.explanation.missing_requirements.map((req: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-orange-500">!</span>
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {m.explanation?.potential_mismatches && m.explanation.potential_mismatches.length > 0 && (
                  <div>
                    <h5 className="font-medium text-red-700 mb-2">x Potential Mismatches</h5>
                    <ul className="space-y-1 text-sm text-slate-600">
                      {m.explanation.potential_mismatches.map((mismatch: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-red-500">x</span>
                          <span>{mismatch}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(!m.explanation?.positive_reasons?.length && !m.explanation?.missing_requirements?.length && !m.explanation?.potential_mismatches?.length) && (
                  <p className="text-slate-500 text-sm">No detailed explanation available</p>
                )}
              </div>
            </div>

            {match?.skills_detail && (
              <div className="pt-4 border-t border-slate-200">
                <h4 className="font-medium text-slate-900 mb-3">Skills Analysis</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Matched Skills ({match.skills_detail.matched_skills.length})</p>
                    <div className="flex flex-wrap gap-1">
                      {match.skills_detail.matched_skills.slice(0, 10).map((skill: string) => (
                        <span key={skill} className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">{skill}</span>
                      ))}
                      {match.skills_detail.matched_skills.length > 10 && (
                        <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-500 rounded">+{match.skills_detail.matched_skills.length - 10}</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Missing Required ({match.skills_detail.missing_required_skills.length})</p>
                    <div className="flex flex-wrap gap-1">
                      {match.skills_detail.missing_required_skills.slice(0, 10).map((skill: string) => (
                        <span key={skill} className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">{skill}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {match?.experience_detail && (
              <div className="pt-4 border-t border-slate-200">
                <h4 className="font-medium text-slate-900 mb-3">Experience Match</h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Your Level</p>
                    <p className="text-lg font-medium capitalize">{match.experience_detail.user_level || 'Not specified'}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Required Level</p>
                    <p className="text-lg font-medium capitalize">{match.experience_detail.required_level || 'Not specified'}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Match Score</p>
                    <p className="text-lg font-bold text-emerald-600">{match.experience_detail.match_score.toFixed(0)}%</p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">{match.experience_detail.match_explanation}</p>
                {match.experience_detail.is_overqualified && (
                  <p className="mt-2 text-sm text-emerald-600">+ Overqualified - may be beneficial</p>
                )}
                {match.experience_detail.is_underqualified && (
                  <p className="mt-2 text-sm text-orange-600">! Underqualified - may need training</p>
                )}
              </div>
            )}

            {match?.role_detail && (
              <div className="pt-4 border-t border-slate-200">
                <h4 className="font-medium text-slate-900 mb-3">Role & Type Match</h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className={`p-4 rounded-lg ${match.role_detail.is_type_match ? 'bg-green-50' : 'bg-red-50'}`}>
                    <p className="text-sm text-slate-500">Opportunity Type Match</p>
                    <p className="text-lg font-bold">{match.role_detail.is_type_match ? 'Yes' : 'No'}</p>
                  </div>
                  <div className={`p-4 rounded-lg ${match.role_detail.is_role_match ? 'bg-green-50' : 'bg-red-50'}`}>
                    <p className="text-sm text-slate-500">Role Match</p>
                    <p className="text-lg font-bold">{match.role_detail.is_role_match ? 'Yes' : 'No'}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Match Score</p>
                    <p className="text-lg font-bold text-emerald-600">{match.role_detail.match_score.toFixed(0)}%</p>
                  </div>
                </div>
                {match.role_detail.matched_roles.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm text-slate-500 mb-2">Matched Roles</p>
                    <div className="flex flex-wrap gap-2">
                      {match.role_detail.matched_roles.map((role: string) => (
                        <span key={role} className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded">{role}</span>
                      ))}
                    </div>
                  </div>
                )}
                <p className="mt-3 text-sm text-slate-600">{match.role_detail.match_explanation}</p>
              </div>
            )}

            {match?.location_detail && (
              <div className="pt-4 border-t border-slate-200">
                <h4 className="font-medium text-slate-900 mb-3">Location & Remote Match</h4>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className={`p-4 rounded-lg ${match.location_detail.is_location_match ? 'bg-green-50' : match.location_detail.location_match_type === 'remote' ? 'bg-blue-50' : 'bg-slate-50'}`}>
                    <p className="text-sm text-slate-500">Location Match</p>
                    <p className="text-lg font-bold capitalize">{match.location_detail.location_match_type}</p>
                  </div>
                  <div className={`p-4 rounded-lg ${match.location_detail.is_remote_compatible ? 'bg-green-50' : 'bg-red-50'}`}>
                    <p className="text-sm text-slate-500">Remote Compatible</p>
                    <p className="text-lg font-bold">{match.location_detail.is_remote_compatible ? 'Yes' : 'No'}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Match Score</p>
                    <p className="text-lg font-bold text-emerald-600">{match.location_detail.match_score.toFixed(0)}%</p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">{match.location_detail.match_explanation}</p>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}