/**
 * RunHistory component for Ojas.
 * Displays history of past execution runs, stages, iterations, and status.
 */

import React from 'react';
import { Play, CheckCircle2, XCircle, Clock, Layers } from 'lucide-react';
import type { RunDetail } from '../../api/runs';

interface RunHistoryProps {
  runs: RunDetail[];
  onSelectRun?: (runId: string) => void;
}

export const RunHistory: React.FC<RunHistoryProps> = ({ runs, onSelectRun }) => {
  const getStatusBadge = (status: string, stopReason?: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
            <CheckCircle2 className="w-3 h-3" />
            <span>{stopReason === 'all_passed' ? 'All Passed' : 'Completed'}</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-950/60 text-rose-400 border border-rose-800/50">
            <XCircle className="w-3 h-3" />
            <span>{stopReason || 'Failed'}</span>
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-sky-950/60 text-sky-400 border border-sky-800/50 animate-pulse">
            <Play className="w-3 h-3" />
            <span>Running</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-neutral-800 text-neutral-400">
            <Clock className="w-3 h-3" />
            <span>{status}</span>
          </span>
        );
    }
  };

  const formatDuration = (started?: string, completed?: string) => {
    if (!started || !completed) return '-';
    try {
      const s = new Date(started).getTime();
      const c = new Date(completed).getTime();
      const secs = Math.max(0, Math.round((c - s) / 1000));
      return `${secs}s`;
    } catch {
      return '-';
    }
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden select-none">
      <div className="px-4 py-2.5 bg-neutral-950/80 border-b border-neutral-800">
        <h3 className="text-xs font-semibold text-white flex items-center gap-2">
          <Layers className="w-4 h-4 text-sky-400" />
          <span>Execution Runs History</span>
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-neutral-950/40 text-neutral-400 border-b border-neutral-800">
            <tr>
              <th className="py-2.5 px-3 w-28">Run ID</th>
              <th className="py-2.5 px-3">Run Type</th>
              <th className="py-2.5 px-3">Prompt / Target</th>
              <th className="py-2.5 px-3 w-24">Iterations</th>
              <th className="py-2.5 px-3 w-24">Duration</th>
              <th className="py-2.5 px-3 w-32">Status</th>
              <th className="py-2.5 px-3 w-40 text-right">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/50">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-neutral-500">
                  No execution runs found for this project.
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => onSelectRun?.(r.id)}
                  className="hover:bg-neutral-800/40 transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 px-3 font-mono font-semibold text-sky-400">
                    {r.id.slice(0, 8)}
                  </td>
                  <td className="py-2.5 px-3 capitalize text-neutral-300 font-medium">
                    {r.run_type}
                  </td>
                  <td className="py-2.5 px-3 text-neutral-400 max-w-xs truncate" title={r.prompt}>
                    {r.prompt || 'No prompt specified'}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-neutral-300">
                    {r.iteration_count}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-neutral-400">
                    {formatDuration(r.started_at, r.completed_at)}
                  </td>
                  <td className="py-2.5 px-3">
                    {getStatusBadge(r.status, r.stop_reason)}
                  </td>
                  <td className="py-2.5 px-3 text-right text-neutral-400 font-mono text-[11px]">
                    {r.created_at ? new Date(r.created_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
