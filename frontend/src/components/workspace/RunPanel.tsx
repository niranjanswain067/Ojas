/**
 * RunPanel component for Ojas Workspace.
 * Right panel containing prompt input, agent execution triggers (Plan, Develop, Test, Fix loop),
 * execution status block, and visual stage stepper.
 */

import React, { useState } from 'react';
import { Play, FileText, Bug, Wrench, Square, Sparkles } from 'lucide-react';

interface RunPanelProps {
  onRunPlan?: (prompt: string) => void;
  onRunDevelop?: (prompt: string) => void;
  onRunTest?: () => void;
  onRunFixLoop?: () => void;
  onStopRun?: () => void;
  isRunActive?: boolean;
}

const STAGES = [
  'Index',
  'Plan',
  'Generate',
  'Check',
  'Test',
  'Fix',
  'Done',
];

export const RunPanel: React.FC<RunPanelProps> = ({
  onRunPlan,
  onRunDevelop,
  onRunTest,
  onRunFixLoop,
  onStopRun,
  isRunActive = false,
}) => {
  const [prompt, setPrompt] = useState('');
  const [currentStageIndex] = useState(0);

  return (
    <aside className="flex flex-col h-full bg-neutral-900 border-l border-neutral-800 text-neutral-200 p-3 overflow-y-auto select-none">
      {/* Panel Title */}
      <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-neutral-300">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>Agent Execution</span>
        </div>
        {isRunActive ? (
          <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Running
          </span>
        ) : (
          <span className="text-[11px] text-neutral-500">Idle</span>
        )}
      </div>

      {/* Prompt Input Box */}
      <div className="mt-3">
        <label htmlFor="prompt-input" className="block text-xs font-medium text-neutral-400 mb-1">
          Task Prompt
        </label>
        <textarea
          id="prompt-input"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what to build or modify (e.g. Build a library book checkout service with tests)..."
          disabled={isRunActive}
          className="w-full p-2.5 text-xs bg-neutral-950 border border-neutral-800 rounded-md text-white placeholder-neutral-500 focus:outline-none focus:border-sky-500 resize-none disabled:opacity-50"
        />
      </div>

      {/* Action Buttons Grid */}
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => onRunPlan && onRunPlan(prompt)}
          disabled={isRunActive || !prompt.trim()}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-white rounded transition-colors disabled:opacity-40"
        >
          <FileText className="w-3.5 h-3.5 text-amber-400" />
          <span>Plan</span>
        </button>

        <button
          type="button"
          onClick={() => onRunDevelop && onRunDevelop(prompt)}
          disabled={isRunActive || !prompt.trim()}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors disabled:opacity-40"
        >
          <Play className="w-3.5 h-3.5 text-white" />
          <span>Develop</span>
        </button>

        <button
          type="button"
          onClick={() => onRunTest && onRunTest()}
          disabled={isRunActive}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-white rounded transition-colors disabled:opacity-40"
        >
          <Bug className="w-3.5 h-3.5 text-emerald-400" />
          <span>Test</span>
        </button>

        <button
          type="button"
          onClick={() => onRunFixLoop && onRunFixLoop()}
          disabled={isRunActive}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-white rounded transition-colors disabled:opacity-40"
        >
          <Wrench className="w-3.5 h-3.5 text-rose-400" />
          <span>Fix Loop</span>
        </button>
      </div>

      {/* Execution Status Block */}
      <div className="mt-4 p-3 bg-neutral-950/80 rounded-lg border border-neutral-800 text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-neutral-400 font-medium">Status</span>
          <span className="text-neutral-200 font-semibold">
            {isRunActive ? 'Generating Code' : 'Idle'}
          </span>
        </div>
        <div className="flex items-center justify-between text-neutral-400 text-[11px]">
          <span>Iteration</span>
          <span className="font-mono text-neutral-300">0 / 5</span>
        </div>
        <div className="flex items-center justify-between text-neutral-400 text-[11px] mt-1">
          <span>Active File</span>
          <span className="font-mono text-neutral-300">—</span>
        </div>

        {isRunActive && (
          <button
            type="button"
            onClick={onStopRun}
            className="w-full mt-3 flex items-center justify-center gap-1.5 py-1 text-xs font-medium text-rose-300 bg-rose-950/60 border border-rose-800/80 hover:bg-rose-900/60 rounded transition-colors"
          >
            <Square className="w-3 h-3 fill-current" />
            <span>Stop Run</span>
          </button>
        )}
      </div>

      {/* Stage Stepper */}
      <div className="mt-4">
        <span className="block text-[11px] font-semibold uppercase tracking-wider text-neutral-400 mb-2">
          Pipeline Stages
        </span>
        <div className="flex flex-col gap-1.5">
          {STAGES.map((stage, idx) => {
            const isCompleted = idx < currentStageIndex;
            const isCurrent = idx === currentStageIndex && isRunActive;
            return (
              <div
                key={stage}
                className={`flex items-center gap-2 px-2.5 py-1 rounded text-xs transition-colors ${
                  isCurrent
                    ? 'bg-sky-950/80 text-sky-300 border border-sky-800/60 font-medium'
                    : isCompleted
                      ? 'text-emerald-400'
                      : 'text-neutral-400'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isCurrent
                      ? 'bg-sky-400 animate-pulse'
                      : isCompleted
                        ? 'bg-emerald-400'
                        : 'bg-neutral-600'
                  }`}
                />
                <span>{stage}</span>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
