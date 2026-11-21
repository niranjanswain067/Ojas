/**
 * Zustand store for tracking current execution run state, stage stepper,
 * live SSE event stream, plan review modal, and execution logs.
 */

import { create } from 'zustand';

export type RunStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type RunType = 'plan' | 'develop' | 'test' | 'fix_loop' | null;

export interface LogEntry {
  timestamp: string;
  message: string;
  level?: 'info' | 'warn' | 'error';
}

export interface RunState {
  activeRunId: string | null;
  runType: RunType;
  status: RunStatus;
  currentStage: string;
  currentStageIndex: number;
  activeFile: string | null;
  iteration: number;
  iterationLimit: number;
  planText: string | null;
  isPlanReviewOpen: boolean;
  logs: LogEntry[];
  filesGenerated: string[];
  error: string | null;

  // Actions
  startRun: (runId: string, runType: RunType, prompt?: string) => void;
  setStage: (stage: string, stageIndex?: number) => void;
  setActiveFile: (filePath: string | null) => void;
  setPlan: (planText: string | null) => void;
  setPlanReviewOpen: (isOpen: boolean) => void;
  addLog: (message: string, level?: 'info' | 'warn' | 'error') => void;
  addGeneratedFile: (filePath: string) => void;
  completeRun: (status: RunStatus, error?: string) => void;
  reset: () => void;
}

const STAGE_ORDER: Record<string, number> = {
  idle: 0,
  index: 0,
  indexing: 0,
  plan: 1,
  planning: 1,
  generate: 2,
  generating: 2,
  check: 3,
  checking: 3,
  test: 4,
  testing: 4,
  fix: 5,
  fixing: 5,
  done: 6,
  completed: 6,
};

function formatTimestamp(): string {
  const d = new Date();
  return d.toTimeString().split(' ')[0];
}

export const useRunStore = create<RunState>((set) => ({
  activeRunId: null,
  runType: null,
  status: 'idle',
  currentStage: 'Idle',
  currentStageIndex: 0,
  activeFile: null,
  iteration: 0,
  iterationLimit: 5,
  planText: null,
  isPlanReviewOpen: false,
  logs: [
    {
      timestamp: formatTimestamp(),
      message: 'Workspace initialized. Ready for execution.',
      level: 'info',
    },
  ],
  filesGenerated: [],
  error: null,

  startRun: (runId: string, runType: RunType, prompt?: string) =>
    set((state) => ({
      activeRunId: runId,
      runType,
      status: 'running',
      currentStage: runType === 'plan' ? 'Plan' : 'Generate',
      currentStageIndex: runType === 'plan' ? 1 : 2,
      activeFile: null,
      error: null,
      logs: [
        ...state.logs,
        {
          timestamp: formatTimestamp(),
          message: `Started ${runType} run [${runId}]${prompt ? `: "${prompt.slice(0, 60)}..."` : ''}`,
          level: 'info',
        },
      ],
    })),

  setStage: (stage: string, stageIndex?: number) =>
    set((state) => {
      const normalized = stage.toLowerCase();
      const idx = stageIndex !== undefined ? stageIndex : (STAGE_ORDER[normalized] ?? state.currentStageIndex);
      const displayStage = stage ? stage.charAt(0).toUpperCase() + stage.slice(1) : stage;
      return {
        currentStage: displayStage,
        currentStageIndex: idx,
      };
    }),

  setActiveFile: (filePath: string | null) => set({ activeFile: filePath }),

  setPlan: (planText: string | null) =>
    set({
      planText,
      isPlanReviewOpen: Boolean(planText),
    }),

  setPlanReviewOpen: (isOpen: boolean) => set({ isPlanReviewOpen: isOpen }),

  addLog: (message: string, level: 'info' | 'warn' | 'error' = 'info') =>
    set((state) => ({
      logs: [
        ...state.logs,
        {
          timestamp: formatTimestamp(),
          message,
          level,
        },
      ],
    })),

  addGeneratedFile: (filePath: string) =>
    set((state) => {
      if (state.filesGenerated.includes(filePath)) return state;
      return { filesGenerated: [...state.filesGenerated, filePath] };
    }),

  completeRun: (status: RunStatus, error?: string) =>
    set((state) => ({
      status,
      currentStage: status === 'completed' ? 'Done' : state.currentStage,
      currentStageIndex: status === 'completed' ? 6 : state.currentStageIndex,
      error: error || null,
      logs: [
        ...state.logs,
        {
          timestamp: formatTimestamp(),
          message: `Run ${state.activeRunId} ended with status: ${status}${error ? ` (${error})` : ''}`,
          level: status === 'failed' ? 'error' : 'info',
        },
      ],
    })),

  reset: () =>
    set({
      activeRunId: null,
      runType: null,
      status: 'idle',
      currentStage: 'Idle',
      currentStageIndex: 0,
      activeFile: null,
      error: null,
    }),
}));
