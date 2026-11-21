/**
 * StageStepper component for visualizing Ojas agent workflow progression:
 * Index → Plan → Generate → Check → Test → Fix → Done.
 */

import React from 'react';
import { Check } from 'lucide-react';

export const STAGES = [
  'Index',
  'Plan',
  'Generate',
  'Check',
  'Test',
  'Fix',
  'Done',
];

interface StageStepperProps {
  currentStageIndex: number;
  isRunActive: boolean;
}

export const StageStepper: React.FC<StageStepperProps> = ({
  currentStageIndex,
  isRunActive,
}) => {
  return (
    <div className="flex flex-col gap-1 select-none">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
          Pipeline Stages
        </span>
        {isRunActive && (
          <span className="text-[10px] text-sky-400 font-mono animate-pulse">
            In Progress
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        {STAGES.map((stage, idx) => {
          const isCompleted = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex && isRunActive;

          return (
            <div
              key={stage}
              className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors ${
                isCurrent
                  ? 'bg-sky-950/70 border border-sky-800/80 text-sky-300 font-medium'
                  : isCompleted
                    ? 'text-emerald-400 bg-neutral-950/40 border border-emerald-950/50'
                    : 'text-neutral-500 bg-neutral-950/20 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`flex items-center justify-center w-4 h-4 rounded-full text-[10px] ${
                    isCurrent
                      ? 'bg-sky-500 text-black font-bold animate-pulse'
                      : isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-neutral-800 text-neutral-500'
                  }`}
                >
                  {isCompleted ? <Check className="w-3 h-3 stroke-[2.5]" /> : idx + 1}
                </span>
                <span>{stage}</span>
              </div>

              {isCurrent && (
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
