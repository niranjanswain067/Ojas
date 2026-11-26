/**
 * RunPanel component for Ojas Workspace.
 * Right panel providing task prompt input, agent execution triggers (Plan, Develop, Test, Fix loop),
 * active run status display, StageStepper, cooperative stop button, and PlanReview modal.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Play, FileText, Bug, Wrench, Square, Sparkles } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

import { useRunStore } from '../../store/runStore';
import { useUIStore } from '../../store/uiStore';
import { startRun, approvePlan } from '../../api/runs';
import { subscribeRunEvents, cancelRun } from '../../api/sse';
import { StageStepper } from './StageStepper';
import { PlanReview } from './PlanReview';
import { IterationStatus } from './IterationStatus';
import { EscalationBanner } from './EscalationBanner';

interface RunPanelProps {
  projectId?: string;
}

export const RunPanel: React.FC<RunPanelProps> = ({ projectId = 'default-project' }) => {
  const queryClient = useQueryClient();

  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const {
    activeRunId,
    runType,
    status,
    currentStage,
    currentStageIndex,
    activeFile,
    iteration,
    iterationLimit,
    planText,
    isPlanReviewOpen,
    failingTestsCount,
    fixLoopStopReason,
    startRun: storeStartRun,
    setStage,
    setActiveFile,
    setPlan,
    setPlanReviewOpen,
    addLog,
    addGeneratedFile,
    addTestResult,
    addBugReport,
    setIteration,
    setFixLoopStopReason,
    appendModelOutput,
    clearModelOutput,
    completeRun,
  } = useRunStore();

  const { setBottomPanelTab } = useUIStore();

  const isRunActive = status === 'running' || status === 'queued';

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  // Connect to live SSE progress stream for a run
  const attachSseListener = (runId: string) => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
    }

    const unsub = subscribeRunEvents(runId, {
      onEvent: (event) => {
        const { event_type, data } = event;

        if (event_type === 'stage') {
          if (data?.stage) {
            setStage(data.stage);
            addLog(`Stage [${data.stage}]: ${data.message || data.status || ''}`, 'info');
          }
        } else if (event_type === 'file') {
          if (data?.path) {
            setActiveFile(data.path);
            if (data.action === 'created') {
              addGeneratedFile(data.path);
              addLog(`Created file: ${data.path} (${data.status || 'ast_ok'})`, 'info');
            } else {
              addLog(`Generating file: ${data.path}...`, 'info');
            }
          }
        } else if (event_type === 'test') {
          if (data) {
            addTestResult(data);
            addLog(`Test [${data.tc_id || ''}]: ${data.name || ''} → ${data.result || ''}`, data.result === 'passed' ? 'info' : 'warn');
          }
        } else if (event_type === 'bug') {
          if (data) {
            addBugReport(data);
            addLog(`Bug recorded [${data.bug_id}]: ${data.probable_cause || data.actual_result || ''}`, 'warn');
          }
        } else if (event_type === 'iteration') {
          if (data?.iteration) {
            setIteration(data.iteration);
            addLog(`Fix loop iteration: ${data.iteration} / ${data.limit || 5}`, 'info');
          }
        } else if (event_type === 'plan_ready') {
          if (data?.plan_text) {
            setPlan(data.plan_text);
            addLog('Development plan generated and ready for review.', 'info');
          }
        } else if (event_type === 'token') {
          if (data?.token) {
            appendModelOutput(data.token);
          }
        } else if (event_type === 'error') {
          addLog(data?.message || 'Execution error encountered', 'error');
        } else if (event_type === 'done') {
          completeRun(data?.status || 'completed', undefined, data?.stop_reason);
          addLog(`Execution completed: ${data?.status || 'done'}${data?.stop_reason ? ` (${data.stop_reason})` : ''}`, 'info');
          // Invalidate workspace files, runs, tests, and bugs query cache
          queryClient.invalidateQueries({ queryKey: ['files', projectId] });
          queryClient.invalidateQueries({ queryKey: ['runs', projectId] });
          queryClient.invalidateQueries({ queryKey: ['tests', projectId] });
          queryClient.invalidateQueries({ queryKey: ['test-results', projectId] });
          queryClient.invalidateQueries({ queryKey: ['bugs', projectId] });
        }
      },
      onError: (err) => {
        addLog(`SSE connection error: ${err}`, 'warn');
      },
    });

    unsubscribeRef.current = unsub;
  };

  // Trigger Plan run
  const handleRunPlan = async () => {
    if (!prompt.trim() || isRunActive || isSubmitting) return;

    setIsSubmitting(true);
    clearModelOutput();
    try {
      const res = await startRun(projectId, 'plan', prompt);
      storeStartRun(res.run_id, 'plan', prompt);
      attachSseListener(res.run_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to start planning run: ${msg}`, 'error');
      completeRun('failed', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trigger Develop run
  const handleRunDevelop = async () => {
    if (!prompt.trim() || isRunActive || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const res = await startRun(projectId, 'develop', prompt);
      storeStartRun(res.run_id, 'develop', prompt);
      attachSseListener(res.run_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to start development run: ${msg}`, 'error');
      completeRun('failed', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trigger Test run
  const handleRunTest = async () => {
    if (isRunActive || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const res = await startRun(projectId, 'test', prompt || 'Run test suite');
      storeStartRun(res.run_id, 'test', prompt || 'Run test suite');
      attachSseListener(res.run_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to start test execution run: ${msg}`, 'error');
      completeRun('failed', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trigger Fix Loop run
  const handleRunFixLoop = async () => {
    if (isRunActive || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const res = await startRun(projectId, 'fix_loop', prompt || 'Automated repair fix loop');
      storeStartRun(res.run_id, 'fix_loop', prompt || 'Automated repair fix loop');
      attachSseListener(res.run_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to start fix loop run: ${msg}`, 'error');
      completeRun('failed', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trigger Cooperative Run Cancellation
  const handleStopRun = async () => {
    if (!activeRunId) return;

    try {
      addLog('Requesting run cancellation...', 'warn');
      await cancelRun(activeRunId);
      completeRun('cancelled', 'User stopped run');
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to cancel run: ${msg}`, 'error');
    }
  };

  // Handle plan approval from modal
  const handleApprovePlan = async (editedPlan: string, proceed: boolean) => {
    setIsSubmitting(true);
    try {
      const res = await approvePlan(projectId, editedPlan, proceed);
      setPlanReviewOpen(false);

      if (proceed && res.run_id) {
        storeStartRun(res.run_id, 'develop', 'Approved plan execution');
        attachSseListener(res.run_id);
      } else {
        addLog('Plan approved and saved.', 'info');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog(`Failed to approve plan: ${msg}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <aside className="flex flex-col h-full bg-neutral-900 border-l border-neutral-800 text-neutral-200 p-3 overflow-y-auto select-none">
      {/* Panel Header */}
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
          <span className="text-[11px] text-neutral-500 font-medium">Idle</span>
        )}
      </div>

      {/* Task Prompt Input */}
      <div className="mt-3">
        <label htmlFor="prompt-input" className="block text-xs font-medium text-neutral-400 mb-1">
          Task Prompt
        </label>
        <textarea
          id="prompt-input"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what to build or modify (e.g. Build a calculator service with arithmetic operations)..."
          disabled={isRunActive || isSubmitting}
          className="w-full p-2.5 text-xs bg-neutral-950 border border-neutral-800 rounded-md text-white placeholder-neutral-500 focus:outline-none focus:border-sky-500 resize-none disabled:opacity-50"
        />
      </div>

      {/* Action Buttons Grid */}
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={handleRunPlan}
          disabled={isRunActive || isSubmitting || !prompt.trim()}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-white rounded transition-colors disabled:opacity-40"
        >
          <FileText className="w-3.5 h-3.5 text-amber-400" />
          <span>Plan</span>
        </button>

        <button
          type="button"
          onClick={handleRunDevelop}
          disabled={isRunActive || isSubmitting || !prompt.trim()}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors disabled:opacity-40 shadow-sm"
        >
          <Play className="w-3.5 h-3.5 text-white fill-current" />
          <span>Develop</span>
        </button>

        <button
          type="button"
          onClick={handleRunTest}
          disabled={isRunActive || isSubmitting}
          className="flex items-center justify-center gap-1.5 py-1.5 px-3 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-white rounded transition-colors disabled:opacity-40"
        >
          <Bug className="w-3.5 h-3.5 text-emerald-400" />
          <span>Test</span>
        </button>

        <button
          type="button"
          onClick={handleRunFixLoop}
          disabled={isRunActive || isSubmitting}
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
          <span className="text-neutral-200 font-semibold capitalize">
            {isRunActive ? `${runType || 'Task'} (${currentStage})` : status}
          </span>
        </div>
        <div className="flex items-center justify-between text-neutral-400 text-[11px]">
          <span>Iteration</span>
          <span className="font-mono text-neutral-300">
            {iteration} / {iterationLimit}
          </span>
        </div>
        <div className="flex items-center justify-between text-neutral-400 text-[11px] mt-1">
          <span>Active File</span>
          <span className="font-mono text-neutral-300 truncate max-w-[140px]" title={activeFile || 'None'}>
            {activeFile || '—'}
          </span>
        </div>

        {/* Iteration Status Bar & Failing count */}
        <div className="mt-2.5 pt-2 border-t border-neutral-900">
          <IterationStatus
            iteration={iteration}
            iterationLimit={iterationLimit}
            failingCount={failingTestsCount}
            isActive={isRunActive && runType === 'fix_loop'}
          />
        </div>

        {isRunActive && (
          <button
            type="button"
            onClick={handleStopRun}
            className="w-full mt-3 flex items-center justify-center gap-1.5 py-1 text-xs font-medium text-rose-300 bg-rose-950/60 border border-rose-800/80 hover:bg-rose-900/60 rounded transition-colors"
          >
            <Square className="w-3 h-3 fill-current" />
            <span>Stop Run</span>
          </button>
        )}
      </div>

      {/* Escalation Banner on repeated failure or iteration limit */}
      {fixLoopStopReason && (
        <div className="mt-3">
          <EscalationBanner
            stopReason={fixLoopStopReason}
            onViewBugs={() => setBottomPanelTab('bugs')}
            onDismiss={() => setFixLoopStopReason(null)}
          />
        </div>
      )}

      {/* Visual Stage Stepper */}
      <div className="mt-4">
        <StageStepper currentStageIndex={currentStageIndex} isRunActive={isRunActive} />
      </div>

      {/* Plan Review Modal */}
      <PlanReview
        isOpen={isPlanReviewOpen}
        planText={planText || ''}
        onApprove={handleApprovePlan}
        onClose={() => setPlanReviewOpen(false)}
        isLoading={isSubmitting}
      />
    </aside>
  );
};
