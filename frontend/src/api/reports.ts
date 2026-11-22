/**
 * Reports and Traceability API client for Ojas.
 */

import { apiGet, apiPost } from './client';

export interface ReportSummaryItem {
  name: string;
  title: string;
  type: string;
  generated_at: string;
  run_id?: string | null;
  file_size?: number | null;
}

export interface ReportListResponse {
  reports: ReportSummaryItem[];
}

export interface ReportCoverageTest {
  tc_id: string;
  result: string;
}

export interface ReportCoverageItem {
  req_id: string;
  heading: string;
  tests: ReportCoverageTest[];
  bugs: string[];
  status?: string;
}

export interface ReportSummaryStats {
  total_tests: number;
  passed: number;
  failed: number;
  iterations: number;
  total_time_s: number;
}

export interface ReportDetailResponse {
  report_name: string;
  title: string;
  content: string;
  summary?: ReportSummaryStats | null;
  coverage?: ReportCoverageItem[] | null;
}

export interface TraceabilitySymbol {
  file_path: string;
  symbol_name: string;
  start_line: number;
  end_line: number;
}

export interface TraceabilityCoverageItem {
  req_id: string;
  heading: string;
  description?: string;
  code_symbols: TraceabilitySymbol[];
  test_cases: Array<{ id: string; tc_id: string; name: string; status: string }>;
  results: Array<{ tc_id: string; result: string }>;
  bugs: Array<{ bug_id: string; tc_id?: string; title: string; severity: string; status: string }>;
  status: 'passing' | 'failing' | 'partial' | 'uncovered';
}

export interface TraceabilityResponse {
  project_id: string;
  coverage: TraceabilityCoverageItem[];
  total_requirements: number;
  covered_by_code: number;
  covered_by_tests: number;
  passing_requirements: number;
}

/**
 * List all available reports for a project.
 */
export async function listReports(projectId: string): Promise<ReportListResponse> {
  return apiGet<ReportListResponse>(`/projects/${encodeURIComponent(projectId)}/reports`);
}

/**
 * Get structured report data (JSON).
 */
export async function getReport(
  projectId: string,
  reportName: string
): Promise<ReportDetailResponse> {
  return apiGet<ReportDetailResponse>(
    `/projects/${encodeURIComponent(projectId)}/reports/${encodeURIComponent(reportName)}`,
    { format: 'json' }
  );
}

/**
 * Download or read report as raw Markdown text.
 */
export async function getReportMarkdown(
  projectId: string,
  reportName: string
): Promise<string> {
  return apiGet<string>(
    `/projects/${encodeURIComponent(projectId)}/reports/${encodeURIComponent(reportName)}`,
    { format: 'markdown' }
  );
}

/**
 * Trigger regeneration of consolidated report.
 */
export async function generateReport(projectId: string): Promise<ReportDetailResponse> {
  return apiPost<ReportDetailResponse>(
    `/projects/${encodeURIComponent(projectId)}/reports/generate`
  );
}

/**
 * Get requirement traceability matrix and coverage stats.
 */
export async function getTraceability(projectId: string): Promise<TraceabilityResponse> {
  return apiGet<TraceabilityResponse>(
    `/projects/${encodeURIComponent(projectId)}/traceability`
  );
}
