'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchRecommendations } from '@/lib/matching';
import type { RecommendationItem, MatchingRecommendationsResponse, MatchingRecommendationsRequest } from '@/types';
import OpportunityCard from '@/components/opportunity/OpportunityCard';
import Button from '@/components/shared/button';

const VERIFICATION_STATUSES = ['unverified', 'active', 'expired', 'closed', 'inaccessible', 'uncertain'];
const OPPORTUNITY_TYPES = ['internship', 'fresher_job', 'full_time_job', 'freelance_project'];

export default function MatchingRecommendations() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [limit] = useState(20);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const [filters, setFilters] = useState<{
    min_score: number;
    opportunity_type: string;
    location: string;
    remote_preference: string;
    skills: string;
    min_salary: number | null;
    max_salary: number | null;
  }>({
    min_score: 0,
    opportunity_type: '',
    location: '',
    remote_preference: '',
    skills: '',
    min_salary: null,
    max_salary: null,
  });

  const loadRecommendations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        min_score: filters.min_score,
        limit: 20,
        offset: page * 20,
        opportunity_type: filters.opportunity_type || undefined,
        location: filters.location || undefined,
        remote_preference: filters.remote_preference || undefined,
        skills: filters.skills || undefined,
        min_salary: filters.min_salary || undefined,
        max_salary: filters.max_salary || undefined,
      };
      const data = await fetchRecommendations(params);
      setRecommendations(page === 0 ? data.items : [...recommendations, ...data.items]);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setIsLoading(false);
    }
  }, [filters, page, recommendations]);

  useEffect(() => {
    loadRecommendations();
  }, [loadRecommendations]);

  const handleFilterChange = (key: string, value: string | number) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
  };

  const loadMore = () => {
    if (!isLoading && recommendations.length < total) {
      setPage(prev => prev + 1);
    }
  };

  const clearFilters = () => {
    setFilters({
      min_score: 0,
      opportunity_type: '',
      location: '',
      remote_preference: '',
      skills: '',
      min_salary: null,
      max_salary: null,
    });
    setPage(0);
  };

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    try {
      const result = await fetch('/api/v1/matching/recalculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('supabase_access_token')}`,
        },
      });
      if (result.ok) {
        const data = await result.json();
        alert(`Recalculated ${data.recalculated_count} matches`);
        setPage(0);
        loadRecommendations();
      } else {
        throw new Error('Failed to recalculate');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to recalculate');
    } finally {
      setIsRecalculating(false);
    }
  };

  const VERIFICATION_STATUSES = ['unverified', 'active', 'expired', 'closed', 'inaccessible', 'uncertain'];
  const OPPORTUNITY_TYPES = ['internship', 'fresher_job', 'full_time_job', 'freelance_project'];
  const REMOTE_PREFERENCES = ['remote_only', 'hybrid', 'onsite_only', 'no_preference'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
          <p className="text-slate-600 mt-1">
            Personalized opportunity matches based on your profile
          </p>
        </div>
        <button
          onClick={handleRecalculate}
          disabled={isRecalculating}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isRecalculating ? 'Recalculating...' : 'Recalculate Matches'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800" role="alert">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Min Score</label>
              <input
                type="number"
                value={filters.min_score}
                onChange={(e) => setFilters(prev => ({ ...prev, min_score: parseFloat(e.target.value) || 0 }))}
                min={0}
                max={100}
                step={1}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                value={filters.opportunity_type}
                onChange={(e) => setFilters(prev => ({ ...prev, opportunity_type: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="internship">Internship</option>
                <option value="fresher_job">Fresher Job</option>
                <option value="full_time_job">Full-time Job</option>
                <option value="freelance_project">Freelance Project</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
              <input
                type="text"
                value={filters.location}
                onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value }))}
                placeholder="City, state, country..."
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Remote</label>
              <select
                value={filters.remote_preference}
                onChange={(e) => setFilters(prev => ({ ...prev, remote_preference: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="remote_only">Remote Only</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite_only">Onsite Only</option>
                <option value="no_preference">No Preference</option>
              </select>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Skills</label>
              <input
                type="text"
                value={filters.skills}
                onChange={(e) => setFilters(prev => ({ ...prev, skills: e.target.value }))}
                placeholder="Comma-separated skills"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Min Salary</label>
              <input
                type="number"
                value={filters.min_salary || ''}
                onChange={(e) => setFilters(prev => ({ ...prev, min_salary: e.target.value ? parseInt(e.target.value) : null }))}
                placeholder="USD"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Salary</label>
              <input
                type="number"
                value={filters.max_salary || ''}
                onChange={(e) => setFilters(prev => ({ ...prev, max_salary: e.target.value ? parseInt(e.target.value) : null }))}
                placeholder="USD"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button type="submit" className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 w-full md:w-auto">
                Search
              </button>
            </div>
          </div>
          <div className="flex items-end">
            <Button type="button" onClick={clearFilters} variant="secondary" className="w-full md:w-auto">
              Clear Filters
            </Button>
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800" role="alert">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-3">
        {isLoading && recommendations.length === 0 ? (
          <div className="text-center py-8 text-slate-500">Loading recommendations...</div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No recommendations found. Try adjusting your filters or updating your profile.
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {recommendations.map((opp) => (
                <div key={opp.opportunity_id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex flex-wrap gap-2 mb-2">
                        {opp.opportunity_type && (
                          <span className="px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded">
                            {opp.opportunity_type.replace('_', ' ')}
                          </span>
                        )}
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          opp.verification_status === 'active' ? 'bg-green-100 text-green-700' :
                          opp.verification_status === 'unverified' ? 'bg-yellow-100 text-yellow-700' :
                          opp.verification_status === 'expired' ? 'bg-orange-100 text-orange-700' :
                          opp.verification_status === 'closed' ? 'bg-red-100 text-red-700' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {opp.verification_status}
                        </span>
                        {opp.source_domain && (
                          <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded">
                            {opp.source_domain}
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">{opp.title || 'Untitled Position'}</h3>
                      <p className="text-slate-600 mb-2">{opp.company_name || 'Unknown Company'}</p>
                      <div className="flex flex-wrap gap-3 text-sm text-slate-600">
                        {opp.location && (
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            {opp.location}
                          </span>
                        )}
                        {opp.remote_preference && (
                          <span className="flex items-center gap-1">
                            <span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded">
                              {opp.remote_preference.replace('_', ' ')}
                            </span>
                          </span>
                        )}
                        {opp.salary_min || opp.salary_max ? (
                          <span className="font-medium text-emerald-600">
                            {(opp.salary_min && opp.salary_max) ? `$${opp.salary_min.toLocaleString()} - $${opp.salary_max.toLocaleString()}` :
                             opp.salary_min ? `$${opp.salary_min.toLocaleString()}+` :
                             `$${opp.salary_max.toLocaleString()}`}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                          opp.match_score >= 80 ? 'bg-green-100 text-green-700' :
                          opp.match_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                          opp.match_score >= 40 ? 'bg-orange-100 text-orange-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {opp.match_score.toFixed(0)}% Match
                        </span>
                        <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              opp.match_score >= 80 ? 'bg-green-500' :
                              opp.match_score >= 60 ? 'bg-yellow-500' :
                              opp.match_score >= 40 ? 'bg-orange-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${opp.match_score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-200 flex flex-wrap gap-2">
                    <button className="px-4 py-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium">
                      View Details
                    </button>
                    <a
                      href={opp.application_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Apply
                    </a>
                  </div>
                </div>
              ))}
            </div>
            {(recommendations.length < total || isLoading) && (
              <div className="mt-4 text-center">
                <button
                  onClick={() => setPage(prev => prev + 1)}
                  disabled={isLoading || recommendations.length >= total}
                  className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}