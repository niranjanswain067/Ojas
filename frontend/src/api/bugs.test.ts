import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as client from './client';
import { listBugs, getBugDetail, updateBugStatus } from './bugs';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
}));

describe('bugs API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls listBugs with project ID and optional filters', async () => {
    const mockList = { bugs: [], total: 0 };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockList);

    const res = await listBugs('proj-1', 'run-1', 'open');
    expect(client.apiGet).toHaveBeenCalledWith(
      '/projects/proj-1/bugs',
      { run_id: 'run-1', status: 'open' }
    );
    expect(res).toEqual(mockList);
  });

  it('calls getBugDetail with bug ID', async () => {
    const mockBug = {
      id: 'bug-1',
      project_id: 'proj-1',
      run_id: 'run-1',
      bug_id: 'B-001',
      severity: 'high' as const,
      expected_result: '5',
      actual_result: '4',
      probable_cause: 'Off-by-one',
      iteration: 1,
      status: 'open' as const,
      created_at: '2026-11-21T00:00:00',
      updated_at: '2026-11-21T00:00:00',
    };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockBug);

    const res = await getBugDetail('bug-1');
    expect(client.apiGet).toHaveBeenCalledWith('/bugs/bug-1');
    expect(res).toEqual(mockBug);
  });

  it('calls updateBugStatus with status and fix description', async () => {
    const mockUpdated = {
      id: 'bug-1',
      project_id: 'proj-1',
      run_id: 'run-1',
      bug_id: 'B-001',
      severity: 'high' as const,
      expected_result: '5',
      actual_result: '4',
      probable_cause: 'Off-by-one',
      iteration: 1,
      status: 'fixed' as const,
      fix_description: 'Corrected boundary check',
      created_at: '2026-11-21T00:00:00',
      updated_at: '2026-11-21T00:01:00',
    };
    vi.mocked(client.apiPatch).mockResolvedValueOnce(mockUpdated);

    const res = await updateBugStatus('bug-1', 'fixed', 'Corrected boundary check');
    expect(client.apiPatch).toHaveBeenCalledWith(
      '/bugs/bug-1',
      { status: 'fixed', fix_description: 'Corrected boundary check' }
    );
    expect(res).toEqual(mockUpdated);
  });
});
