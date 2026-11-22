'use client';

import { useState, useEffect, useCallback } from 'react';
import type { ApplicationListResponse, ApplicationListItem, ApplicationStatus, OpportunitySummary } from '@/types';
import { fetchApplications, updateApplicationStatus } from '@/lib/application';
import ApplicationCard from './ApplicationCard';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

export default function ApplicationTracker() {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingApplication, setEditingApplication] = useState<ApplicationListItem | null>(null);
  const [formData, setFormData] = useState<{ status: ApplicationStatus; notes: string; deadline: string }>({
    status: 'interested',
    notes: '',
    deadline: '',
  });
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const loadApplications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchApplications({
        limit: 50,
        offset: 0,
      });
      setApplications(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  const loadMore = async () => {
    if (isLoadingMore || applications.length >= total) return;
    setIsLoadingMore(true);
    try {
      const data = await fetchApplications({ limit: 50, offset: applications.length });
      setApplications(prev => [...prev, ...data.items]);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more applications');
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleStatusChange = async (applicationId: string, newStatus: ApplicationStatus) => {
    try {
      await updateApplicationStatus(applicationId, newStatus);
      setApplications(prev => prev.map(app => app.id === applicationId ? { ...app, status: newStatus } : app));
    } catch (err) {
      // Error handled below
    }
  };

  const openForm = (application?: ApplicationListItem) => {
    const status = application ? application.status || 'interested' : 'interested';
    const notes = application?.notes || '';
    const deadline = application?.deadline || '';
    setEditingApplication(application || null);
    setFormData({
      status,
      notes,
      deadline: deadline || '',
    });
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingApplication(null);
    setFormData({
      status: 'interested',
      notes: '',
      deadline: '',
    });
  };

  if (isLoading && applications.length === 0) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <p className="text-slate-500">Loading applications...</p>
      </div>
    );
  }

  if (applications.length === 0) {
    return (
      <div className="min-h-screen p-6 text-center">
        <p className="text-slate-500">No applications yet.</p>
        <p className="text-slate-400 mt-2">Save opportunities to track your application progress.</p>
        <Button onClick={loadApplications} className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded">
          Discover Opportunities
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <Card title={`My Applications (${total})`}>
        <div className="space-y-3">
          {applications.map((app) => (
            <ApplicationCard
              key={app.id}
              application={app}
              onStatusChange={(newStatus) => handleStatusChange(app.id, newStatus)}
              onDelete={() => setDeleteId(app.id)}
            />
          ))}
          {(applications.length < total || isLoading) && (
            <div className="mt-4 text-center">
              <Button onClick={loadMore} disabled={isLoadingMore} variant="secondary">
                {isLoadingMore ? 'Loading...' : 'Load More'}
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}