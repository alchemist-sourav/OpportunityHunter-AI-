'use client';

import { useState } from 'react';
import type { ApplicationStatus, ApplicationFormData } from '@/types';
import Card from '@/components/ui/card';
import Button from '@/components/shared/button';

interface ApplicationFormProps {
  initialStatus: ApplicationStatus;
  initialNotes: string;
  initialDeadline: string;
  onSubmit: (data: ApplicationFormData) => void;
  onClose: () => void;
}

export default function ApplicationForm({ initialStatus, initialNotes, initialDeadline, onSubmit, onClose }: ApplicationFormProps) {
  const [status, setStatus] = useState(initialStatus);
  const [notes, setNotes] = useState(initialNotes);
  const [deadline, setDeadline] = useState(initialDeadline);

  const handleSubmit = () => {
    onSubmit({ status, notes, deadline: deadline || null });
    onClose();
  };

  return (
    <Card title="Application Form">
      <form onSubmit={handleSubmit} className="space-y-4 p-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ApplicationStatus)}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="interested">Interested</option>
            <option value="saved">Saved</option>
            <option value="applied">Applied</option>
            <option value="assessment">Assessment</option>
            <option value="interview">Interview</option>
            <option value="offer">Offer</option>
            <option value="rejected">Rejected</option>
            <option value="withdrawn">Withdrawn</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes about this application..."
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 min-h[60px]"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Application Deadline</label>
          <input
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-3">
          <Button type="button" onClick={onClose} variant="secondary">
            Cancel
          </Button>
          <Button type="submit">Save</Button>
        </div>
      </form>
    </Card>
  );
}