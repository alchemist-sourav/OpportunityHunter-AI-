'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchOpportunities } from '@/lib/opportunity';
import type { OpportunityListResponse, OpportunityListItem, VerificationStatus, OpportunityType } from '@/types';
import OpportunityCard from './OpportunityCard';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

const VERIFICATION_STATUSES: VerificationStatus[] = ['unverified', 'active', 'expired', 'closed', 'inaccessible', 'uncertain'];
const OPPORTUNITY_TYPES: OpportunityType[] = ['internship', 'fresher_job', 'full_time_job', 'freelance_project'];

export default function OpportunityList() {
  const [opportunities, setOpportunities] = useState<OpportunityListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [limit] = useState(20);

  const [filters, setFilters] = useState({
    category: '',
    verification_status: '',
    source_domain: '',
    location: '',
    remote_preference: '',
    skills: '',
    search: '',
  });

  const loadOpportunities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchOpportunities({
        ...filters,
        limit,
        offset: page * limit,
        category: filters.category || undefined,
        verification_status: filters.verification_status || undefined,
        source_domain: filters.source_domain || undefined,
        location: filters.location || undefined,
        remote_preference: filters.remote_preference || undefined,
        skills: filters.skills || undefined,
        search: filters.search || undefined,
      });
      setOpportunities(page === 0 ? data.items : [...opportunities, ...data.items]);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load opportunities');
    } finally {
      setIsLoading(false);
    }
  }, [filters, page, limit, opportunities]);

  useEffect(() => {
    loadOpportunities();
  }, [loadOpportunities]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
  };

  const loadMore = () => {
    if (!isLoading && opportunities.length < total) {
      setPage(prev => prev + 1);
    }
  };

  const clearFilters = () => {
    setFilters({
      category: '',
      verification_status: '',
      source_domain: '',
      location: '',
      remote_preference: '',
      skills: '',
      search: '',
    });
    setPage(0);
  };

  return (
    <div className="space-y-6">
      <Card title="Filters">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Search</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Title, company, description..."
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                {OPPORTUNITY_TYPES.map(t => (
                  <option key={t} value={t}>{t.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Verification</label>
              <select
                value={filters.verification_status}
                onChange={(e) => setFilters(prev => ({ ...prev, verification_status: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                {VERIFICATION_STATUSES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
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
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
            <div className="flex items-end">
              <Button type="submit" className="w-full md:w-auto" variant="primary">
                Search
              </Button>
            </div>
            <div className="flex items-end">
              <Button type="button" onClick={clearFilters} variant="secondary" className="w-full md:w-auto">
                Clear
              </Button>
            </div>
          </div>
        </form>
      </Card>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800" role="alert">
          {error}
        </div>
      )}

      <Card title={`Opportunities (${total})`}>
        {isLoading && opportunities.length === 0 ? (
          <div className="text-center py-8 text-slate-500">Loading opportunities...</div>
        ) : opportunities.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No opportunities found. Try adjusting your filters.
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {opportunities.map((opp) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))}
            </div>
            {(opportunities.length < total || isLoading) && (
              <div className="mt-4 text-center">
                <Button
                  onClick={loadMore}
                  disabled={isLoading || opportunities.length >= total}
                  variant="secondary"
                >
                  {isLoading ? 'Loading...' : 'Load More'}
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}