/**
 * IterationStatus component for RunPanel.
 * Displays current Fix Loop iteration progress, active limits, and failing test counter.
 */

import React from 'react';
import { RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

interface IterationStatusProps {
  iteration: number;
  iterationLimit: number;
  failingCount: number;
  isActive: boolean;
}

export const IterationStatus: React.FC<IterationStatusProps> = ({
  iteration,
  iterationLimit,
  failingCount,
  isActive,
}) => {
  if (iteration <= 0) return null;

  const percent = Math.min(100, Math.round((iteration / iterationLimit) * 100));

  return (
    <div className="flex flex-col gap-2 p-3 bg-neutral-900 border border-neutral-800 rounded-lg select-none text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-semibold text-neutral-200">
          <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${isActive ? 'animate-spin' : ''}`} />
          <span>Fix Loop Progress</span>
        </div>
        <span className="font-mono text-sky-400 font-bold">
          Iteration {iteration} of {iterationLimit}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-neutral-800 h-1.5 rounded-full overflow-hidden">
        <div
          className="bg-sky-500 h-full transition-all duration-300 rounded-full"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Stats summary */}
      <div className="flex items-center justify-between text-[11px] text-neutral-400">
        <div className="flex items-center gap-1">
          {failingCount > 0 ? (
            <>
              <AlertCircle className="w-3 h-3 text-rose-400" />
              <span className="text-rose-400 font-medium">{failingCount} test(s) failing</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-medium">All tests passing</span>
            </>
          )}
        </div>
        <span className="text-neutral-500">Max limit: {iterationLimit}</span>
      </div>
    </div>
  );
};
