import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestsPanel } from './TestsPanel';
import * as testsApi from '../../api/tests';

vi.mock('../../api/tests', () => ({
  listTests: vi.fn(),
  uploadTests: vi.fn(),
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

describe('TestsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dropzone and empty state when no tests exist', async () => {
    vi.mocked(testsApi.listTests).mockResolvedValueOnce({
      test_cases: [],
      total: 0,
    });

    renderWithClient(<TestsPanel projectId="proj-1" />);

    expect(screen.getByText(/Test Cases \(/i)).toBeInTheDocument();
    expect(screen.getByText(/Drop pytest file or click to upload/i)).toBeInTheDocument();
    expect(await screen.findByText(/No test cases uploaded/i)).toBeInTheDocument();
  });

  it('renders test cases with TC-IDs and triggers onSelectTest when clicked', async () => {
    const mockCases: testsApi.TestCase[] = [
      {
        id: '1',
        project_id: 'proj-1',
        tc_id: 'TC-001',
        name: 'test_calculate_sum',
        file_path: 'tests/test_math.py',
        function_name: 'test_calculate_sum',
        linked_req_ids: ['REQ-001'],
        source: 'user_uploaded',
        status: 'passed',
        created_at: '2026-11-21T00:00:00',
        updated_at: '2026-11-21T00:00:00',
      },
    ];

    vi.mocked(testsApi.listTests).mockResolvedValueOnce({
      test_cases: mockCases,
      total: 1,
    });

    const handleSelect = vi.fn();
    renderWithClient(<TestsPanel projectId="proj-1" onSelectTest={handleSelect} />);

    expect(await screen.findByText('TC-001')).toBeInTheDocument();
    expect(screen.getByText('test_calculate_sum')).toBeInTheDocument();
    expect(screen.getByText('REQ-001')).toBeInTheDocument();

    const item = screen.getByText('TC-001').closest('div[class*="cursor-pointer"]');
    if (item) {
      fireEvent.click(item);
      expect(handleSelect).toHaveBeenCalledWith('tests/test_math.py', 'test_calculate_sum');
    }
  });
});
