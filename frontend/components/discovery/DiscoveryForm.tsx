'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { DiscoverySearchRequest } from '@/types';
import Button from '@/components/shared/button';

interface DiscoveryFormProps {
  onSearch: (payload: DiscoverySearchRequest) => void;
  isLoading?: boolean;
}

const CATEGORIES = [
  { value: 'internship', label: 'Internship' },
  { value: 'fresher_job', label: 'Fresher Job' },
  { value: 'full_time_job', label: 'Full-time Job' },
  { value: 'freelance_project', label: 'Freelance Project' },
] as const;

const EXPERIENCE_LEVELS = [
  { value: 'student', label: 'Student' },
  { value: 'fresher', label: 'Fresher' },
  { value: 'junior', label: 'Junior' },
  { value: 'experienced', label: 'Experienced' },
] as const;

const REMOTE_PREFERENCES = [
  { value: 'remote_only', label: 'Remote Only' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite_only', label: 'Onsite Only' },
  { value: 'no_preference', label: 'No Preference' },
] as const;

const COMMON_SKILLS = [
  'Python', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'SQL', 'AWS', 'Docker',
  'Kubernetes', 'Machine Learning', 'Data Analysis', 'REST APIs', 'GraphQL',
  'PostgreSQL', 'MongoDB', 'Redis', 'Git', 'CI/CD', 'Linux',
] as const;

const COMMON_LOCATIONS = [
  'Remote', 'San Francisco', 'New York', 'Seattle', 'Austin', 'Boston',
  'London', 'Berlin', 'Toronto', 'Bangalore', 'Singapore', 'Sydney',
] as const;

export default function DiscoveryForm({ onSearch, isLoading = false }: DiscoveryFormProps) {
  const [category, setCategory] = useState<DiscoverySearchRequest['category']>('full_time_job');
  const [keywords, setKeywords] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [remotePreference, setRemotePreference] = useState<DiscoverySearchRequest['remote_preference']>('no_preference');
  const [experienceLevel, setExperienceLevel] = useState<DiscoverySearchRequest['experience_level']>();
  const [maxResults, setMaxResults] = useState(20);
  const [sourceDomains, setSourceDomains] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  const router = useRouter();

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!keywords.trim()) {
      newErrors.keywords = 'Keywords are required';
    }
    if (keywords.trim().length > 300) {
      newErrors.keywords = 'Keywords must be 300 characters or less';
    }
    if (skills.length > 20) {
      newErrors.skills = 'Maximum 20 skills allowed';
    }
    if (locations.length > 10) {
      newErrors.locations = 'Maximum 10 locations allowed';
    }
    if (maxResults < 1 || maxResults > 100) {
      newErrors.maxResults = 'Max results must be between 1 and 100';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const payload: DiscoverySearchRequest = {
      category,
      keywords: keywords.trim(),
      skills,
      locations,
      remote_preference: remotePreference,
      experience_level: experienceLevel,
      max_results: maxResults,
      source_domains: sourceDomains,
    };

    onSearch(payload);
  };

  const addItem = (current: string[], newItem: string, max: number) => {
    const trimmed = newItem.trim();
    if (trimmed && !current.includes(trimmed) && current.length < max) {
      return [...current, trimmed];
    }
    return current;
  };

  const removeItem = (current: string[], item: string) => current.filter((i) => i !== item);

  const renderMultiSelect = (
    label: string,
    value: string[],
    onChange: (value: string[]) => void,
    suggestions: readonly string[],
    max: number,
    placeholder: string,
    error?: string,
  ) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-700">{label}</label>
      <div className="flex flex-wrap gap-2">
        {value.map((item) => (
          <span key={item} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
            {item}
            <button
              type="button"
              onClick={() => onChange(removeItem(value, item))}
              className="ml-1.5 text-slate-500 hover:text-slate-700"
              aria-label={`Remove ${item}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              onChange(addItem(value, e.currentTarget.value, max));
              e.currentTarget.value = '';
            }
          }}
          className="flex-1 min-w-[150px] px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          list={`${label.toLowerCase().replace(/\s+/g, '-')}-suggestions`}
        />
        <datalist id={`${label.toLowerCase().replace(/\s+/g, '-')}-suggestions`}>
          {suggestions.map((s) => <option key={s} value={s} />)}
        </datalist>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Opportunity Category <span className="text-red-500">*</span>
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as DiscoverySearchRequest['category'])}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Experience Level
          </label>
          <select
            value={experienceLevel || ''}
            onChange={(e) => {
              const value = e.target.value;
              setExperienceLevel((value || undefined) as DiscoverySearchRequest['experience_level']);
            }}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Any</option>
            {EXPERIENCE_LEVELS.map((e) => (
              <option key={e.value} value={e.value}>
                {e.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Keywords / Job Title <span className="text-red-500">*</span>
        </label>
        <textarea
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          rows={2}
          placeholder="e.g., software engineer, machine learning, react developer..."
          className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          maxLength={300}
        />
        <p className="mt-1 text-xs text-slate-500">{keywords.length}/300 characters</p>
        {errors.keywords && <p className="mt-1 text-sm text-red-600">{errors.keywords}</p>}
      </div>

      {renderMultiSelect('Skills', skills, setSkills, COMMON_SKILLS, 20, 'Add skill (press Enter)', errors.skills)}
      {renderMultiSelect('Preferred Locations', locations, setLocations, COMMON_LOCATIONS, 10, 'Add location (press Enter)', errors.locations)}

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Remote Preference</label>
        <div className="flex flex-wrap gap-3">
          {REMOTE_PREFERENCES.map((r) => (
            <label key={r.value} className="inline-flex items-center">
              <input
                type="radio"
                name="remote_preference"
                value={r.value}
                checked={remotePreference === r.value}
                onChange={() => setRemotePreference(r.value)}
                className="sr-only peer"
              />
              <span className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg cursor-pointer peer-checked:bg-blue-600 peer-checked:text-white peer-checked:border-blue-600 transition-colors">
                {r.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        {showAdvanced ? 'Hide' : 'Show'} Advanced Options
      </button>

      {showAdvanced && (
        <div className="space-y-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Max Results
              </label>
              <input
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(Math.min(100, Math.max(1, parseInt(e.target.value) || 1)))}
                min={1}
                max={100}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {errors.maxResults && <p className="mt-1 text-sm text-red-600">{errors.maxResults}</p>}
            </div>
            <div>
              {renderMultiSelect('Source Domains', sourceDomains, setSourceDomains, [], 20, 'Add domain (press Enter)', errors.sourceDomains)}
            </div>
          </div>
        </div>
      )}

      <div className="pt-4 border-t border-slate-200">
        <Button type="submit" disabled={isLoading} className="w-full md:w-auto">
          {isLoading ? 'Searching...' : 'Start Discovery'}
        </Button>
      </div>
    </form>
  );
}