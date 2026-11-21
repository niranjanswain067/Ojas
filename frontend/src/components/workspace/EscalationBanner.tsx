/**
 * EscalationBanner component for Ojas Workspace.
 * Displayed when fix loop stops due to repeated failure or iteration limit,
 * alerting the user and providing immediate links to inspect bugs.
 */

import React from 'react';
import { AlertOctagon, ArrowRight, X } from 'lucide-react';

interface EscalationBannerProps {
  stopReason: string | null;
  onViewBugs?: () => void;
  onDismiss?: () => void;
}

export const EscalationBanner: React.FC<EscalationBannerProps> = ({
  stopReason,
  onViewBugs,
  onDismiss,
}) => {
  if (!stopReason || (stopReason !== 'repeated_failure' && stopReason !== 'iteration_limit')) {
    return null;
  }

  const isRepeated = stopReason === 'repeated_failure';

  return (
    <div className="flex items-start justify-between gap-3 p-3 bg-rose-950/80 border border-rose-800 rounded-lg text-xs text-rose-200 select-none shadow-md animate-in fade-in duration-200">
      <div className="flex items-start gap-2.5">
        <AlertOctagon className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
        <div className="flex flex-col gap-1">
          <span className="font-semibold text-rose-100">
            {isRepeated ? 'Fix Loop Stopped: Repeated Failure' : 'Fix Loop Stopped: Iteration Limit'}
          </span>
          <p className="text-[11px] text-rose-300/90 leading-relaxed">
            {isRepeated
              ? 'The same test failure repeated across consecutive fix iterations. The autonomous agent has stopped to avoid repeating unsuccessful code changes. Manual intervention is recommended.'
              : 'The automated fix loop reached its maximum iteration limit without resolving all failing test cases. Inspect remaining open bug reports.'}
          </p>
          {onViewBugs && (
            <button
              type="button"
              onClick={onViewBugs}
              className="inline-flex items-center gap-1 mt-1 text-[11px] font-medium text-rose-200 hover:text-white underline underline-offset-2"
            >
              <span>View diagnosed bug reports</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="p-1 text-rose-400 hover:text-white rounded hover:bg-rose-900/60 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};
