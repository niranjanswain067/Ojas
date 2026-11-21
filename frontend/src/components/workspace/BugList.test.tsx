import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BugList } from './BugList';
import * as bugsApi from '../../api/bugs';
import { useRunStore } from '../../store/runStore';

vi.mock('../../api/bugs', () => ({
  listBugs: vi.fn(),
  updateBugStatus: vi.fn(),
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

describe('BugList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useRunStore.getState().reset();
  });

  it('renders empty message when no bug reports exist', async () => {
    vi.mocked(bugsApi.listBugs).mockResolvedValueOnce({
      bugs: [],
      total: 0,
    });

    renderWithClient(<BugList projectId="proj-1" />);

    expect(await screen.findByText(/No bugs recorded/i)).toBeInTheDocument();
  });

  it('renders bug cards with severity, REQ/TC links, and probable cause', async () => {
    const mockBugs: bugsApi.BugReport[] = [
      {
        id: 'b-1',
        project_id: 'proj-1',
        run_id: 'run-1',
        bug_id: 'B-001',
        req_id: 'REQ-001',
        tc_id: 'TC-001',
        file_path: 'app/calc.py',
        function_name: 'add',
        severity: 'high',
        expected_result: '5',
        actual_result: '4',
        probable_cause: 'Off by one in loop',
        iteration: 1,
        status: 'open',
        created_at: '2026-11-21T00:00:00',
        updated_at: '2026-11-21T00:00:00',
      },
    ];

    vi.mocked(bugsApi.listBugs).mockResolvedValueOnce({
      bugs: mockBugs,
      total: 1,
    });

    const handleSelectBug = vi.fn();
    renderWithClient(<BugList projectId="proj-1" onSelectBug={handleSelectBug} />);

    expect(await screen.findByText('B-001')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('REQ-001')).toBeInTheDocument();
    expect(screen.getByText('TC-001')).toBeInTheDocument();
    expect(screen.getByText('Off by one in loop')).toBeInTheDocument();
    expect(screen.getByText(/5/)).toBeInTheDocument();
    expect(screen.getByText(/4/)).toBeInTheDocument();

    const openLink = screen.getByText('app/calc.py:add');
    fireEvent.click(openLink);
    expect(handleSelectBug).toHaveBeenCalledWith('app/calc.py', 'add');
  });
});
