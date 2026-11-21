import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as client from './client';
import {
  startRun,
  listRuns,
  getRunDetail,
  getPlan,
  approvePlan,
} from './runs';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

describe('runs API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls startRun with correct URL and payload', async () => {
    const mockResponse = {
      run_id: 'run-1',
      status: 'queued',
      message: 'Run queued',
    };
    vi.mocked(client.apiPost).mockResolvedValueOnce(mockResponse);

    const res = await startRun('proj-1', 'plan', 'Build auth');
    expect(client.apiPost).toHaveBeenCalledWith('/projects/proj-1/runs', {
      run_type: 'plan',
      prompt: 'Build auth',
      plan_text: undefined,
    });
    expect(res).toEqual(mockResponse);
  });

  it('calls listRuns with project ID and limit', async () => {
    const mockList = { runs: [], total: 0 };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockList);

    const res = await listRuns('proj-1', 20);
    expect(client.apiGet).toHaveBeenCalledWith('/projects/proj-1/runs?limit=20');
    expect(res).toEqual(mockList);
  });

  it('calls getRunDetail with run ID', async () => {
    const mockDetail = {
      id: 'run-1',
      project_id: 'proj-1',
      run_type: 'develop',
      status: 'completed',
      prompt: 'Test',
      iteration_count: 1,
      iteration_limit: 5,
      tokens_generated: 100,
      created_at: '2026-11-21T00:00:00',
      steps: [],
    };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockDetail);

    const res = await getRunDetail('run-1');
    expect(client.apiGet).toHaveBeenCalledWith('/runs/run-1');
    expect(res).toEqual(mockDetail);
  });

  it('calls getPlan with project ID', async () => {
    const mockPlan = {
      project_id: 'proj-1',
      plan_text: '{"files":[]}',
      status: 'pending_approval',
    };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockPlan);

    const res = await getPlan('proj-1');
    expect(client.apiGet).toHaveBeenCalledWith('/projects/proj-1/plan');
    expect(res).toEqual(mockPlan);
  });

  it('calls approvePlan with plan text and proceed flag', async () => {
    const mockApprove = {
      run_id: 'run-dev-1',
      status: 'queued',
      message: 'Plan approved',
    };
    vi.mocked(client.apiPost).mockResolvedValueOnce(mockApprove);

    const res = await approvePlan('proj-1', '{"files":[]}', true);
    expect(client.apiPost).toHaveBeenCalledWith('/projects/proj-1/plan/approve', {
      plan_text: '{"files":[]}',
      proceed: true,
    });
    expect(res).toEqual(mockApprove);
  });
});
