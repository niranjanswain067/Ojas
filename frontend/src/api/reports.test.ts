import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  listReports,
  getReport,
  getReportMarkdown,
  generateReport,
  getTraceability,
} from './reports';
import { apiGet, apiPost } from './client';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

describe('reports API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('listReports calls GET /projects/:id/reports', async () => {
    const mockReports = {
      reports: [
        {
          name: 'consolidated_test_report',
          title: 'Consolidated Test Report',
          type: 'markdown',
          generated_at: '2026-11-22T10:00:00Z',
        },
      ],
    };
    (apiGet as any).mockResolvedValueOnce(mockReports);

    const res = await listReports('p1');
    expect(apiGet).toHaveBeenCalledWith('/projects/p1/reports');
    expect(res.reports).toHaveLength(1);
    expect(res.reports[0].name).toBe('consolidated_test_report');
  });

  it('getReport requests JSON formatted report', async () => {
    const mockDetail = {
      report_name: 'test_report',
      title: 'Test Report',
      content: '# Tests',
      summary: { total_tests: 10, passed: 9, failed: 1, iterations: 1, total_time_s: 30 },
      coverage: [],
    };
    (apiGet as any).mockResolvedValueOnce(mockDetail);

    const res = await getReport('p1', 'test_report');
    expect(apiGet).toHaveBeenCalledWith('/projects/p1/reports/test_report', {
      format: 'json',
    });
    expect(res.report_name).toBe('test_report');
    expect(res.summary?.total_tests).toBe(10);
  });

  it('getReportMarkdown requests raw text/markdown', async () => {
    (apiGet as any).mockResolvedValueOnce('# Markdown Content');

    const res = await getReportMarkdown('p1', 'consolidated_test_report');
    expect(apiGet).toHaveBeenCalledWith('/projects/p1/reports/consolidated_test_report', {
      format: 'markdown',
    });
    expect(res).toBe('# Markdown Content');
  });

  it('generateReport calls POST /projects/:id/reports/generate', async () => {
    const mockRes = {
      report_name: 'consolidated_test_report',
      title: 'Consolidated Test Report',
      content: '# Fresh Report',
    };
    (apiPost as any).mockResolvedValueOnce(mockRes);

    const res = await generateReport('p1');
    expect(apiPost).toHaveBeenCalledWith('/projects/p1/reports/generate');
    expect(res.content).toBe('# Fresh Report');
  });

  it('getTraceability calls GET /projects/:id/traceability', async () => {
    const mockTrace = {
      project_id: 'p1',
      total_requirements: 5,
      covered_by_code: 4,
      covered_by_tests: 3,
      passing_requirements: 3,
      coverage: [],
    };
    (apiGet as any).mockResolvedValueOnce(mockTrace);

    const res = await getTraceability('p1');
    expect(apiGet).toHaveBeenCalledWith('/projects/p1/traceability');
    expect(res.total_requirements).toBe(5);
  });
});
