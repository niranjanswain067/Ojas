import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as client from './client';
import { uploadTests, listTests, getTestResults, getRunTestResults } from './tests';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

describe('tests API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls uploadTests with multipart form data', async () => {
    const mockResponse = {
      message: 'Tests uploaded',
      file_path: 'tests/test_calc.py',
      test_cases: [
        {
          id: 'tc-1',
          project_id: 'proj-1',
          tc_id: 'TC-001',
          name: 'test_add',
          file_path: 'tests/test_calc.py',
          function_name: 'test_add',
          linked_req_ids: ['REQ-001'],
          source: 'user_uploaded',
          status: 'not_run' as const,
          created_at: '2026-11-21T00:00:00',
          updated_at: '2026-11-21T00:00:00',
        },
      ],
      total_extracted: 1,
    };

    vi.mocked(client.apiPost).mockResolvedValueOnce(mockResponse);

    const file = new File(['def test_add(): pass'], 'test_calc.py', { type: 'text/x-python' });
    const res = await uploadTests('proj-1', file);

    expect(client.apiPost).toHaveBeenCalledWith(
      '/projects/proj-1/tests',
      expect.any(FormData)
    );
    expect(res).toEqual(mockResponse);
  });

  it('calls listTests with project ID', async () => {
    const mockList = { test_cases: [], total: 0 };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockList);

    const res = await listTests('proj-1');
    expect(client.apiGet).toHaveBeenCalledWith('/projects/proj-1/tests');
    expect(res).toEqual(mockList);
  });

  it('calls getTestResults with project ID', async () => {
    const mockResults = { results: [], total: 0 };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockResults);

    const res = await getTestResults('proj-1');
    expect(client.apiGet).toHaveBeenCalledWith('/projects/proj-1/tests/results');
    expect(res).toEqual(mockResults);
  });

  it('calls getRunTestResults with run ID', async () => {
    const mockResults = { results: [], total: 0 };
    vi.mocked(client.apiGet).mockResolvedValueOnce(mockResults);

    const res = await getRunTestResults('run-123');
    expect(client.apiGet).toHaveBeenCalledWith('/runs/run-123/test-results');
    expect(res).toEqual(mockResults);
  });
});
