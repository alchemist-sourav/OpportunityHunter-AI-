'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { startDiscoverySearch, getDiscoveryJob, cancelDiscoveryJob, getDiscoveryHistory } from '@/lib/discovery';
import { extractFromDiscoveryJob, batchVerifyOpportunities } from '@/lib/opportunity';
import type { DiscoveryJob, DiscoverySearchRequest, DiscoveryHistoryResponse } from '@/types';
import { DiscoveryForm, DiscoveryStatus, DiscoveryResults, DiscoveryHistory } from '@/components/discovery';
import { OpportunityList } from '@/components/opportunity';
import { Recommendations } from '@/components/matching';

export default function OpportunitiesPage() {
  const [activeTab, setActiveTab] = useState<'discovery' | 'recommendations'>('discovery');
  
  // Discovery state
  const [currentJob, setCurrentJob] = useState<any>(null);
  const [history, setHistory] = useState<DiscoveryHistoryResponse>({ total: 0, items: [] });
  const [historyPage, setHistoryPage] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showOpportunities, setShowOpportunities] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<string | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [extractedOpportunityIds, setExtractedOpportunityIds] = useState<string[]>([]);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => { if (pollTimer.current) clearTimeout(pollTimer.current); }, []);

  const loadHistory = useCallback(async () => {
    try {
      const data = await getDiscoveryHistory(20, historyPage * 20);
      setHistory(prev => ({
        total: data.total,
        items: historyPage === 0 ? data.items : [...prev.items, ...data.items],
      }));
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }, [historyPage]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleSearch = async (payload: any) => {
    setIsSearching(true);
    setError(null);
    setShowResults(false);
    setShowOpportunities(false);
    setCurrentJob(null);

    try {
      const job = await startDiscoverySearch(payload);
      setCurrentJob(job);
      setShowResults(true);
      pollJobStatus(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start discovery');
    } finally {
      setIsSearching(false);
    }
  };

  const pollJobStatus = (jobId: string) => {
    setIsPolling(true);
    
    const poll = async () => {
      try {
        const job = await getDiscoveryJob(jobId);
        setCurrentJob(job);
        
        if (job.status === 'running' || job.status === 'pending') {
          pollTimer.current = setTimeout(poll, 3000);
        } else {
          setIsPolling(false);
          loadHistory();
        }
      } catch (err) {
        console.error('Polling error:', err);
        setIsPolling(false);
      }
    };

    poll();
  };

  const handleExtract = async () => {
    if (!currentJob) return;
    setIsExtracting(true);
    setExtractError(null);
    try {
      const result = await extractFromDiscoveryJob({
        job_id: currentJob.id,
        result_indices: undefined,
      });
      if (result.errors.length > 0) {
        setExtractError(result.errors.join('; '));
      }
      setExtractedOpportunityIds([...result.created, ...result.updated]);
      setShowOpportunities(true);
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Failed to extract opportunities');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleVerify = async () => {
    if (extractedOpportunityIds.length === 0) {
      setExtractError('Extract opportunities before verifying them.');
      return;
    }
    try {
      const result = await batchVerifyOpportunities({ opportunity_ids: extractedOpportunityIds });
      if (result.errors.length > 0) setExtractError(result.errors.join('; '));
      else setExtractError(null);
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  const handleCancel = async () => {
    if (!currentJob) return;
    
    try {
      await cancelDiscoveryJob(currentJob.id);
      const updatedJob = await getDiscoveryJob(currentJob.id);
      setCurrentJob(updatedJob);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  const handleRefresh = async () => {
    if (!currentJob) return;
    
    try {
      const job = await getDiscoveryJob(currentJob.id);
      setCurrentJob(job);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh job');
    }
  };

  const loadMoreHistory = () => {
    setHistoryPage(prev => prev + 1);
  };

  const openOpportunityDetail = (opportunityId: string) => {
    setSelectedOpportunity(opportunityId);
  };

  const closeOpportunityDetail = () => {
    setSelectedOpportunity(null);
  };

  // Render functions to simplify JSX
  const renderDiscoveryTab = () => (
    <div>
      <DiscoveryForm onSearch={handleSearch} isLoading={isSearching} />

      {currentJob && (
        <div>
          <DiscoveryStatus
            job={currentJob}
            onCancel={handleCancel}
            onRefresh={handleRefresh}
          />
          
          <div className="flex flex-wrap gap-3 mt-4">
            <button
              onClick={handleExtract}
              disabled={isExtracting || currentJob.status !== 'completed' || !currentJob.results?.length}
              className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isExtracting ? 'Extracting...' : 'Extract Opportunities'}
            </button>
            <button
              onClick={handleVerify}
              disabled={extractedOpportunityIds.length === 0}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Verify Opportunities
            </button>
            <button
              onClick={() => setShowOpportunities(!showOpportunities)}
              className="px-4 py-2 text-sm border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
            >
              {showOpportunities ? 'Hide' : 'Show'} Opportunities
            </button>
          </div>

          {extractError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
              {extractError}
            </div>
          )}

          {showResults && currentJob.results.length > 0 && (
            <DiscoveryResults results={currentJob.results} keywords={currentJob.keywords} />
          )}
        </div>
      )}
    </div>
  );

  const renderRecommendationsTab = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
        <p className="text-slate-600 mt-1">
          Personalized opportunity matches based on your profile
        </p>
      </div>
      <Recommendations />
    </div>
  );

  const renderError = () => (
    (error || extractError) && (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800" role="alert">
        {error || extractError}
        <button
          onClick={() => { setError(null); setExtractError(null); }}
          className="ml-4 text-red-600 hover:text-red-800 underline"
        >
          Dismiss
        </button>
      </div>
    )
  );

  const renderTabs = () => (
    <div className="border-b border-slate-200 mb-6">
      <nav className="flex gap-4" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'discovery'}
          onClick={() => setActiveTab('discovery')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'discovery'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Discovery
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'recommendations'}
          onClick={() => setActiveTab('recommendations')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'recommendations'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Recommendations
        </button>
      </nav>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Opportunities</h1>
            <p className="text-slate-600 mt-1">
              Discover and match with opportunities tailored to your profile
            </p>
          </div>
        </div>

        <div className="border-b border-slate-200 mb-6">
          <nav className="flex gap-4" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'discovery'}
              onClick={() => setActiveTab('discovery')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'discovery'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
        >
          Discovery
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'recommendations'}
          onClick={() => setActiveTab('recommendations')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'recommendations'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Recommendations
        </button>
      </nav>
    </div>
  </div>

  {renderError()}

  {activeTab === 'discovery' && renderDiscoveryTab()}



  <div className="mt-8">
    {showOpportunities && (
      <OpportunityList />
    )}
  </div>

  <DiscoveryHistory
    items={history.items}
    total={history.total}
    onLoadMore={loadMoreHistory}
    hasMore={history.items.length < history.total}
    isLoading={isPolling}
  />

  {activeTab === 'recommendations' && (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
        <p className="text-slate-600 mt-1">
          Personalized opportunity matches based on your profile
        </p>
      </div>
      <Recommendations />
    </div>
  )}
</div>
  );
}