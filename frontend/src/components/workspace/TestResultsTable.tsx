/**
 * TestResultsTable component for BottomPanel in Ojas Workspace.
 * Renders per-test execution results with TC-IDs, pass/fail status, duration,
 * error traceback preview, and row selection callback.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, XCircle, AlertCircle, Clock } from 'lucide-react';

import { getTestResults, type TestResult } from '../../api/tests';
import { useRunStore } from '../../store/runStore';

interface TestResultsTableProps {
  projectId: string;
  onSelectTest?: (testName: string) => void;
}

export const TestResultsTable: React.FC<TestResultsTableProps> = ({
  projectId,
  onSelectTest,
}) => {
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');
  const storeResults = useRunStore((s) => s.testResults);

  const { data: apiData, isLoading } = useQuery({
    queryKey: ['test-results', projectId],
    queryFn: () => getTestResults(projectId),
    enabled: Boolean(projectId) && storeResults.length === 0,
  });

  const allResults: TestResult[] = storeResults.length > 0 ? storeResults : apiData?.results || [];

  const filtered = allResults.filter((r) => {
    if (filter === 'passed') return r.result === 'passed';
    if (filter === 'failed') return r.result === 'failed' || r.result === 'error';
    return true;
  });

  const passedCount = allResults.filter((r) => r.result === 'passed').length;
  const failedCount = allResults.filter((r) => r.result === 'failed' || r.result === 'error').length;

  const renderStatusBadge = (res: TestResult) => {
    switch (res.result) {
      case 'passed':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">
            <CheckCircle2 className="w-3 h-3" />
            PASSED
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-900/50">
            <XCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      case 'error':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-900/50">
            <AlertCircle className="w-3 h-3" />
            ERROR
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-neutral-400 bg-neutral-900 px-2 py-0.5 rounded">
            <Clock className="w-3 h-3" />
            SKIPPED
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden text-xs font-mono">
      {/* Controls & Summary Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-neutral-900/80 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <span className="text-neutral-400 font-sans text-xs font-semibold">Results:</span>
          <span className="text-emerald-400 font-medium">{passedCount} passed</span>
          <span className="text-neutral-600">•</span>
          <span className="text-rose-400 font-medium">{failedCount} failed</span>
          <span className="text-neutral-600">•</span>
          <span className="text-neutral-400 font-medium">{allResults.length} total</span>
        </div>

        <div className="flex items-center gap-1 bg-neutral-950 p-0.5 rounded border border-neutral-800">
          {(['all', 'passed', 'failed'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setFilter(mode)}
              className={`px-2 py-0.5 text-[10px] rounded capitalize transition-colors ${
                filter === mode
                  ? 'bg-neutral-800 text-white font-medium'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Results Table */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && allResults.length === 0 ? (
          <div className="p-6 text-center text-neutral-500 font-sans">Loading test results...</div>
        ) : filtered.length === 0 ? (
          <div className="p-6 text-center text-neutral-500 font-sans select-none">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 opacity-30 text-emerald-400" />
            <p className="text-neutral-400 font-medium">No test results to display</p>
            <p className="text-[11px] text-neutral-500 mt-0.5">Run tests from the Run panel to view results.</p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-950/70 text-[10px] font-sans text-neutral-400 uppercase tracking-wider sticky top-0">
                <th className="py-1.5 px-3 w-20">TC-ID</th>
                <th className="py-1.5 px-3">Test Case</th>
                <th className="py-1.5 px-3 w-28">Status</th>
                <th className="py-1.5 px-3 w-20 text-right">Time</th>
                <th className="py-1.5 px-3">Failure Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {filtered.map((res: TestResult, idx) => (
                <tr
                  key={res.id || idx}
                  onClick={() => onSelectTest?.(res.tc_id)}
                  className="hover:bg-neutral-900/60 transition-colors cursor-pointer group"
                >
                  <td className="py-2 px-3 font-semibold text-sky-400 whitespace-nowrap">
                    {res.tc_id}
                  </td>
                  <td className="py-2 px-3 text-neutral-200 group-hover:text-white max-w-xs truncate">
                    {res.tc_id}
                  </td>
                  <td className="py-2 px-3 whitespace-nowrap">{renderStatusBadge(res)}</td>
                  <td className="py-2 px-3 text-right text-neutral-400 whitespace-nowrap">
                    {res.duration_ms ? `${res.duration_ms}ms` : '-'}
                  </td>
                  <td className="py-2 px-3 text-neutral-400 max-w-md truncate">
                    {res.error_message ? (
                      <span className="text-rose-300 font-mono text-[11px] bg-rose-950/30 px-1 py-0.5 rounded">
                        {res.error_message}
                      </span>
                    ) : (
                      <span className="text-neutral-600">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
