'use client';

import type { DiscoveryResult } from '@/types';
import Card from '@/components/ui/card';

interface DiscoveryResultsProps {
  results: DiscoveryResult[];
  keywords: string;
}

function highlightText(text: string, keywords: string): React.ReactNode {
  if (!keywords.trim() || !text) return text;
  
  const tokens = keywords.toLowerCase().split(/\s+/).filter(t => t.length >= 2);
  if (tokens.length === 0) return text;
  
  const regex = new RegExp(`(${tokens.join('|')})`, 'gi');
  const parts = text.split(regex);
  
  return (
    <>
      {parts.map((part, i) => 
        regex.test(part) ? (
          <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark>
        ) : (
          part
        )
      )}
    </>
  );
}

export default function DiscoveryResults({ results, keywords }: DiscoveryResultsProps) {
  if (results.length === 0) {
    return (
      <Card title="Results">
        <div className="text-center py-8 text-slate-500">
          No results found. Try adjusting your search criteria.
        </div>
      </Card>
    );
  }

  const relevantResults = results.filter(r => r.relevant);
  const otherResults = results.filter(r => !r.relevant);

  return (
    <Card title={`Results (${results.length})`}>
      <div className="space-y-3">
        {relevantResults.length > 0 && (
          <>
            <h4 className="text-sm font-medium text-green-700">Relevant Matches</h4>
            <div className="space-y-2">
              {relevantResults.map((result, index) => (
                <ResultItem key={result.url} result={result} index={index} keywords={keywords} />
              ))}
            </div>
          </>
        )}
        {otherResults.length > 0 && (
          <>
            <h4 className="text-sm font-medium text-slate-500 mt-4">Other Results</h4>
            <div className="space-y-2">
              {otherResults.map((result, index) => (
                <ResultItem key={result.url} result={result} index={index} keywords={keywords} />
              ))}
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

function ResultItem({ result, index, keywords }: { result: DiscoveryResult; index: number; keywords: string }) {
  return (
    <div className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
      <div className="flex items-start gap-3">
        <span className="text-slate-400 text-sm font-mono w-6 text-right">{index + 1}.</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-blue-700 hover:text-blue-900 truncate flex-1"
            >
              {highlightText(result.title || result.url, keywords)}
            </a>
            {result.domain && (
              <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded">
                {result.domain}
              </span>
            )}
            {result.relevant && (
              <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                Relevant ({result.found_keywords})
              </span>
            )}
            {result.status_code && (
              <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded">
                {result.status_code}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 line-clamp-2">
            {highlightText(result.snippet, keywords)}
          </p>
        </div>
      </div>
    </div>
  );
}