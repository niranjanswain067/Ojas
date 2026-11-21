/**
 * BugList component for BottomPanel in Ojas Workspace.
 * Renders structured bug reports produced by the Testing Agent.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bug, CheckCircle, ExternalLink, Filter } from 'lucide-react';

import { listBugs, type BugReport, type BugSeverity } from '../../api/bugs';
import { useRunStore } from '../../store/runStore';

interface BugListProps {
  projectId: string;
  onSelectBug?: (filePath: string, functionName?: string | null) => void;
}

export const BugList: React.FC<BugListProps> = ({ projectId, onSelectBug }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const storeBugs = useRunStore((s) => s.bugReports);

  const { data: apiData, isLoading } = useQuery({
    queryKey: ['bugs', projectId],
    queryFn: () => listBugs(projectId),
    enabled: Boolean(projectId) && storeBugs.length === 0,
  });

  const allBugs: BugReport[] = storeBugs.length > 0 ? storeBugs : apiData?.bugs || [];

  const filtered = allBugs.filter((b) => {
    if (filterSeverity === 'all') return true;
    return b.severity.toLowerCase() === filterSeverity.toLowerCase();
  });

  const renderSeverityBadge = (severity: BugSeverity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-950 text-purple-300 border border-purple-800">
            CRITICAL
          </span>
        );
      case 'high':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-950 text-rose-300 border border-rose-800">
            HIGH
          </span>
        );
      case 'medium':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-950 text-amber-300 border border-amber-800">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-sky-950 text-sky-300 border border-sky-800">
            LOW
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden text-xs">
      {/* Header Controls */}
      <div className="flex items-center justify-between px-3 py-2 bg-neutral-900/80 border-b border-neutral-800 select-none">
        <div className="flex items-center gap-2">
          <Bug className="w-3.5 h-3.5 text-rose-400" />
          <span className="font-semibold text-neutral-300">
            Diagnosed Bugs ({allBugs.length})
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Filter className="w-3 h-3 text-neutral-500 mr-1" />
          {['all', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setFilterSeverity(sev)}
              className={`px-2 py-0.5 text-[10px] rounded uppercase font-medium transition-colors ${
                filterSeverity === sev
                  ? 'bg-neutral-800 text-white'
                  : 'text-neutral-400 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Bug Report Cards */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5">
        {isLoading && allBugs.length === 0 ? (
          <div className="p-6 text-center text-neutral-500">Loading bug reports...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-neutral-500 select-none">
            <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30 text-emerald-400" />
            <p className="font-medium text-neutral-300">No bugs recorded</p>
            <p className="text-[11px] text-neutral-500 mt-1">
              Test runs and fix loops will automatically record diagnostic bug reports here when failures occur.
            </p>
          </div>
        ) : (
          filtered.map((bug: BugReport) => (
            <div
              key={bug.id || bug.bug_id}
              className="flex flex-col bg-neutral-900 border border-neutral-800 rounded-lg p-3 hover:border-neutral-700 transition-colors shadow-sm"
            >
              {/* Card Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-rose-950/70 text-rose-300 border border-rose-800/80">
                    {bug.bug_id}
                  </span>
                  {renderSeverityBadge(bug.severity)}
                  {bug.req_id && (
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-900/60">
                      {bug.req_id}
                    </span>
                  )}
                  {bug.tc_id && (
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-900/60">
                      {bug.tc_id}
                    </span>
                  )}
                </div>

                {bug.file_path && (
                  <button
                    type="button"
                    onClick={() => onSelectBug?.(bug.file_path!, bug.function_name)}
                    className="flex items-center gap-1 text-[11px] font-mono text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    <span>
                      {bug.file_path}
                      {bug.function_name ? `:${bug.function_name}` : ''}
                    </span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>

              {/* Probable Cause */}
              {bug.probable_cause && (
                <div className="mb-2 bg-neutral-950/80 p-2 rounded border border-neutral-800/80 font-mono text-[11px] text-neutral-300">
                  <span className="text-neutral-500 block text-[10px] uppercase font-sans font-semibold mb-0.5">
                    Probable Cause:
                  </span>
                  {bug.probable_cause}
                </div>
              )}

              {/* Expected vs Actual */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="bg-emerald-950/20 border border-emerald-900/30 p-2 rounded text-emerald-300">
                  <span className="text-[10px] text-emerald-500 font-sans uppercase font-bold block mb-0.5">
                    Expected:
                  </span>
                  <div className="truncate">{bug.expected_result}</div>
                </div>

                <div className="bg-rose-950/20 border border-rose-900/30 p-2 rounded text-rose-300">
                  <span className="text-[10px] text-rose-500 font-sans uppercase font-bold block mb-0.5">
                    Actual:
                  </span>
                  <div className="truncate">{bug.actual_result}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
