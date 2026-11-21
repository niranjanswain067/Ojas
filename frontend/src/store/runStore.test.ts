import { describe, it, expect, beforeEach } from 'vitest';
import { useRunStore } from './runStore';

describe('useRunStore', () => {
  beforeEach(() => {
    useRunStore.getState().reset();
  });

  it('initializes with default idle state', () => {
    const state = useRunStore.getState();
    expect(state.activeRunId).toBeNull();
    expect(state.status).toBe('idle');
    expect(state.currentStage).toBe('Idle');
    expect(state.currentStageIndex).toBe(0);
    expect(state.isPlanReviewOpen).toBe(false);
    expect(state.filesGenerated).toEqual([]);
    expect(state.logs.length).toBeGreaterThanOrEqual(1);
  });

  it('starts a plan run correctly', () => {
    useRunStore.getState().startRun('run-123', 'plan', 'Build backend');
    const state = useRunStore.getState();
    expect(state.activeRunId).toBe('run-123');
    expect(state.runType).toBe('plan');
    expect(state.status).toBe('running');
    expect(state.currentStage).toBe('Plan');
    expect(state.currentStageIndex).toBe(1);
    expect(state.logs.some((l) => l.message.includes('Build backend'))).toBe(true);
  });

  it('starts a develop run correctly', () => {
    useRunStore.getState().startRun('run-456', 'develop');
    const state = useRunStore.getState();
    expect(state.activeRunId).toBe('run-456');
    expect(state.runType).toBe('develop');
    expect(state.status).toBe('running');
    expect(state.currentStage).toBe('Generate');
    expect(state.currentStageIndex).toBe(2);
  });

  it('updates stage progression via setStage', () => {
    useRunStore.getState().setStage('generate');
    expect(useRunStore.getState().currentStage).toBe('Generate');
    expect(useRunStore.getState().currentStageIndex).toBe(2);

    useRunStore.getState().setStage('check');
    expect(useRunStore.getState().currentStage).toBe('Check');
    expect(useRunStore.getState().currentStageIndex).toBe(3);

    useRunStore.getState().setStage('done');
    expect(useRunStore.getState().currentStage).toBe('Done');
    expect(useRunStore.getState().currentStageIndex).toBe(6);
  });

  it('manages plan review modal and plan text', () => {
    useRunStore.getState().setPlan('{"project_name": "Test"}');
    expect(useRunStore.getState().planText).toBe('{"project_name": "Test"}');

    useRunStore.getState().setPlanReviewOpen(true);
    expect(useRunStore.getState().isPlanReviewOpen).toBe(true);

    useRunStore.getState().setPlanReviewOpen(false);
    expect(useRunStore.getState().isPlanReviewOpen).toBe(false);
  });

  it('adds logs and generated files', () => {
    useRunStore.getState().addLog('Test log message', 'warn');
    const logs = useRunStore.getState().logs;
    const lastLog = logs[logs.length - 1];
    expect(lastLog.message).toBe('Test log message');
    expect(lastLog.level).toBe('warn');

    useRunStore.getState().addGeneratedFile('app/main.py');
    expect(useRunStore.getState().filesGenerated).toContain('app/main.py');
  });

  it('completes run and sets final status', () => {
    useRunStore.getState().startRun('run-789', 'develop');
    useRunStore.getState().completeRun('completed');

    expect(useRunStore.getState().status).toBe('completed');
    expect(useRunStore.getState().activeRunId).toBe('run-789');
    expect(useRunStore.getState().currentStage).toBe('Done');
    expect(useRunStore.getState().currentStageIndex).toBe(6);
  });

  it('handles run failure with error message', () => {
    useRunStore.getState().startRun('run-fail', 'develop');
    useRunStore.getState().completeRun('failed', 'Syntax error in generated file');

    expect(useRunStore.getState().status).toBe('failed');
    expect(useRunStore.getState().error).toBe('Syntax error in generated file');
  });
});
