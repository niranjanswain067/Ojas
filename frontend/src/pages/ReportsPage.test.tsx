import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportsPage } from './ReportsPage';
import * as projectsApi from '../api/projects';
import * as reportsApi from '../api/reports';
import * as runsApi from '../api/runs';

vi.mock('../api/projects');
vi.mock('../api/reports');
vi.mock('../api/runs');

describe('ReportsPage Component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    vi.spyOn(projectsApi, 'listProjects').mockResolvedValue({
      projects: [
        {
          id: 'p-1',
          name: 'Test Library',
          description: 'Sample library project',
          created_at: '2026-11-20T12:00:00Z',
          updated_at: '2026-11-20T12:00:00Z',
          status: 'idle',
          document_count: 1,
          requirement_count: 2,
          test_case_count: 1,
          test_count: 1,
          bug_count: 0,
          run_count: 1,
        },
      ],
      total: 1,
    });

    vi.spyOn(reportsApi, 'getTraceability').mockResolvedValue({
      project_id: 'p-1',
      total_requirements: 2,
      covered_by_code: 2,
      covered_by_tests: 1,
      passing_requirements: 1,
      coverage: [
        {
          req_id: 'REQ-01',
          heading: 'Add Book',
          code_symbols: [],
          test_cases: [],
          results: [],
          bugs: [],
          status: 'passing',
        },
      ],
    });

    vi.spyOn(reportsApi, 'listReports').mockResolvedValue({
      reports: [
        {
          name: 'consolidated_test_report',
          title: 'Consolidated Test Report',
          type: 'markdown',
          generated_at: '2026-11-22T10:00:00Z',
        },
      ],
    });

    vi.spyOn(reportsApi, 'getReport').mockResolvedValue({
      report_name: 'consolidated_test_report',
      title: 'Consolidated Test Report',
      content: '# Consolidated Quality Report\nAll passed.',
      summary: {
        total_tests: 5,
        passed: 5,
        failed: 0,
        iterations: 1,
        total_time_s: 15,
      },
      coverage: [],
    });

    vi.spyOn(runsApi, 'listRuns').mockResolvedValue({
      runs: [],
      total: 0,
    });
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  it('renders page header and project dropdown', async () => {
    renderWithProviders(<ReportsPage />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Reports' })).toBeInTheDocument();
    expect(await screen.findByDisplayValue('Test Library')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /regenerate report/i })).toBeInTheDocument();
  });

  it('renders summary KPIs and coverage table', async () => {
    renderWithProviders(<ReportsPage />);

    expect(await screen.findByText(/test pass rate/i)).toBeInTheDocument();
    expect(await screen.findByText('REQ-01')).toBeInTheDocument();
    expect(await screen.findByText('Add Book')).toBeInTheDocument();
  });
});
