'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchPublicOpportunities, fetchPublicOpportunity } from '@/lib/public_opportunity';
import type {
  OpportunityListItem,
  OpportunityListResponse,
} from '@/types';
import OpportunityCard from '@/components/opportunity/OpportunityCard';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

const VERIFICATION_STATUSES = ['unverified', 'active', 'expired', 'closed', 'inaccessible', 'uncertain'];
const OPPORTUNITY_TYPES = ['internship', 'fresher_job', 'full_time_job', 'freelance_project'];
const REMOTE_PREFERENCES = ['remote_only', 'hybrid', 'onsite_only', 'no_preference'];
const EXPERIENCE_LEVELS = ['student', 'fresher', 'junior', 'experienced'];

interface PublicExplorerFilters {
  category: string;
  verification_status: string;
  location: string;
  remote_preference: string;
  experience_level: string;
  skills: string;
  search: string;
  min_salary: number | null;
  max_salary: number | null;
}

const initialFilters: PublicExplorerFilters = {
  category: '',
  verification_status: '',
  location: '',
  remote_preference: 'no_preference',
  experience_level: '',
  skills: '',
  search: '',
  min_salary: null,
  max_salary: null,
};

export default function PublicExplorerPage() {
  const [opportunities, setOpportunities] = useState<OpportunityListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [limit] = useState(20);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);

  const [filters, setFilters] = useState<PublicExplorerFilters>(initialFilters);

  // Parse initial search params or use defaults
  useEffect(() => {
    const params = {
      category: initialFilters.category,
      verification_status: initialFilters.verification_status,
      location: initialFilters.location,
      remote_preference: initialFilters.remote_preference,
      experience_level: initialFilters.experience_level,
      skills: initialFilters.skills,
      search: initialFilters.search,
      min_salary: initialFilters.min_salary,
      max_salary: initialFilters.max_salary,
    };
    setPage(0);
    loadOpportunities(params);
  }, []);

  const loadOpportunities = useCallback(async (params: {
    category?: string;
    verification_status?: string;
    location?: string;
    remote_preference?: string;
    experience_level?: string;
    skills?: string;
    search?: string;
    min_salary?: number | null;
    max_salary?: number | null;
  }) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchPublicOpportunities({
        category: params.category,
        verification_status: params.verification_status,
        location: params.location,
        remote_preference: params.remote_preference,
        experience_level: params.experience_level,
        skills: params.skills,
        search: params.search,
        limit,
        offset: page * limit,
      });
      setOpportunities(page === 0 ? data.items : [...opportunities, ...data.items]);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load opportunities');
    } finally {
      setIsLoading(false);
    }
  }, [page, limit]);

  const handleFilterChange = (key: keyof PublicExplorerFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(0);
    loadOpportunities({
      category: filters.category,
      verification_status: filters.verification_status,
      location: filters.location,
      remote_preference: filters.remote_preference,
      experience_level: filters.experience_level,
      skills: filters.skills,
      search: filters.search,
      min_salary: filters.min_salary,
      max_salary: filters.max_salary,
    });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
  };

  const loadMore = () => {
    if (!isLoading && opportunities.length < total) {
      setPage(prev => prev + 1);
      loadOpportunities({
        category: filters.category,
        verification_status: filters.verification_status,
        location: filters.location,
        remote_preference: filters.remote_preference,
        experience_level: filters.experience_level,
        skills: filters.skills,
        search: filters.search,
        min_salary: filters.min_salary,
        max_salary: filters.max_salary,
      });
    }
  };

  const clearFilters = () => {
    setFilters({
      category: '',
      verification_status: '',
      location: '',
      remote_preference: 'no_preference',
      experience_level: '',
      skills: '',
      search: '',
      min_salary: null,
      max_salary: null,
    });
    setPage(0);
    loadOpportunities({
      category: filters.category,
      verification_status: filters.verification_status,
      location: filters.location,
      remote_preference: filters.remote_preference,
      experience_level: filters.experience_level,
      skills: filters.skills,
      search: filters.search,
      min_salary: filters.min_salary,
      max_salary: filters.max_salary,
    });
  };

  const handleViewDetail = (opportunityId: string) => {
    setShowLoginPrompt(true);
  };

  const handleLoginClick = () => {
    setShowLoginPrompt(false);
    window.location.href = '/login';
  };

  const renderHeader = () => (
    <header className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Public Opportunity Explorer</h1>
          <p className="text-slate-500">Discover opportunities from companies worldwide</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => setShowLoginPrompt(true)}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-2L12 3v14z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v7l-5-5L12 5zm7 4h5l-5 5-5-5zm5-9v5c0 .65-.12 1.28-.34 1.88a2.11 2.11 0 0 1-.68 0C21.3 9.12 21 8.55 21 8v-5c0-.65-.13-1.28-.35-1.88a2.18 2.18 0 0 1-.68 0z" />
            </svg>
            Save Opportunities
          </Button>
          {showLoginPrompt && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg p-6 border border-slate-200">
              <h3 className="font-medium text-slate-900 mb-4">Log in to save opportunities</h3>
              <p className="text-slate-500 mb-6">
                Create a free account to save your favorite opportunities and get personalized recommendations.
              </p>
              <div className="space-y-4">
<Button
              variant="secondary"
              className="w-full px-4 py-2 text-sm rounded-lg hover:bg-slate-50 transition-colors"
            >
              <a href="/login" className="text-indigo-600 font-medium">
                Sign In
              </a>
            </Button>
            <Button
              variant="primary"
              className="w-full px-4 py-2 text-sm rounded-lg hover:bg-indigo-100 transition-colors"
            >
              <a href="/register" className="text-white">
                Sign Up
              </a>
            </Button>
              </div>
              <button
                onClick={() => setShowLoginPrompt(false)}
                className="w-full text-sm text-slate-500 hover:text-slate-700 mt-4"
              >
                Skip for now
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );

  const renderFilters = () => (
    <Card title="Filters">
      <form onSubmit={handleSearch} className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {OPPORTUNITY_TYPES.map(t => (
                <option key={t} value={t}>
                  {t.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Verification Status</label>
            <select
              value={filters.verification_status}
              onChange={(e) => handleFilterChange('verification_status', e.target.value)}
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
              onChange={(e) => handleFilterChange('location', e.target.value)}
              placeholder="City, state, country..."
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Remote</label>
            <select
              value={filters.remote_preference}
              onChange={(e) => handleFilterChange('remote_preference', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              {REMOTE_PREFERENCES.map(p => (
                <option key={p} value={p}>{p.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Experience Level</label>
            <select
              value={filters.experience_level}
              onChange={(e) => handleFilterChange('experience_level', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              {EXPERIENCE_LEVELS.map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Skills</label>
            <input
              type="text"
              value={filters.skills}
              onChange={(e) => handleFilterChange('skills', e.target.value)}
              placeholder="Comma-separated skills (e.g., python, javascript, react)"
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Search</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Title, company, or description..."
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Min Salary (USD)</label>
            <input
              type="number"
              value={filters.min_salary || ''}
              onChange={(e) => handleFilterChange('min_salary', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              min={0}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Max Salary (USD)</label>
            <input
              type="number"
              value={filters.max_salary || ''}
              onChange={(e) => handleFilterChange('max_salary', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              min={0}
            />
          </div>
        </div>
        <div className="flex items-end">
          <Button type="submit" className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 w-full md:w-auto">
            Apply Filters
          </Button>
          <Button
            type="button"
            onClick={clearFilters}
            variant="secondary"
            className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors w-full md:w-auto"
          >
            Clear Filters
          </Button>
        </div>
      </form>
    </Card>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {renderHeader()}

      <main className="max-w-7xl mx-auto p-6">
        {renderFilters()}

        <div className="mt-8">
          <Card title={`Opportunities (${total})`}>
            {isLoading && opportunities.length === 0 ? (
              <div className="text-center py-8 text-slate-500">Loading opportunities...</div>
            ) : opportunities.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>No opportunities found.</p>
                <p className="text-slate-500 mt-2">Try adjusting your filters or search above.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {opportunities.map((opp) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    onClick={() => handleViewDetail(opp.id)}
                    isVerifying={false}
                  />
                ))}
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
              </div>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}