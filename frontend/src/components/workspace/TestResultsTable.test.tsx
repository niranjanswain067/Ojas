import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestResultsTable } from './TestResultsTable';
import * as testsApi from '../../api/tests';
import { useRunStore } from '../../store/runStore';

vi.mock('../../api/tests', () => ({
  getTestResults: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('TestResultsTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useRunStore.getState().reset();
  });

  it('renders empty message when no results exist', async () => {
    vi.mocked(testsApi.getTestResults).mockResolvedValueOnce({
      results: [],
      total: 0,
    });

    renderWithClient(<TestResultsTable projectId="proj-1" />);

    expect(await screen.findByText(/No test results to display/i)).toBeInTheDocument();
  });

  it('renders test results and allows filtering by passed and failed', async () => {
    const mockResults: testsApi.TestResult[] = [
      {
        id: 'res-1',
        run_id: 'run-1',
        test_case_id: 'tc-1',
        tc_id: 'TC-001',
        iteration: 1,
        result: 'passed',
        duration_ms: 12,
        created_at: '2026-11-21T00:00:00',
      },
      {
        id: 'res-2',
        run_id: 'run-1',
        test_case_id: 'tc-2',
        tc_id: 'TC-002',
        iteration: 1,
        result: 'failed',
        duration_ms: 25,
        error_message: 'AssertionError: expected 5 but got 4',
        created_at: '2026-11-21T00:00:00',
      },
    ];

    vi.mocked(testsApi.getTestResults).mockResolvedValueOnce({
      results: mockResults,
      total: 2,
    });

    renderWithClient(<TestResultsTable projectId="proj-1" />);

    expect(await screen.findAllByText('TC-001')).not.toHaveLength(0);
    expect(screen.getAllByText('TC-002')).not.toHaveLength(0);
    expect(screen.getByText('PASSED')).toBeInTheDocument();
    expect(screen.getByText('FAILED')).toBeInTheDocument();
    expect(screen.getByText(/AssertionError: expected 5 but got 4/i)).toBeInTheDocument();

    // Filter to passed only
    const passedFilterBtn = screen.getByRole('button', { name: /passed/i });
    fireEvent.click(passedFilterBtn);

    expect(screen.getAllByText('TC-001')).not.toHaveLength(0);
    expect(screen.queryByText('TC-002')).not.toBeInTheDocument();

    // Filter to failed only
    const failedFilterBtn = screen.getByRole('button', { name: /failed/i });
    fireEvent.click(failedFilterBtn);

    expect(screen.queryByText('TC-001')).not.toBeInTheDocument();
    expect(screen.getAllByText('TC-002')).not.toHaveLength(0);
  });
});
