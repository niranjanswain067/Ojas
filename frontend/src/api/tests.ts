/**
 * Typed API client for Test Cases and Test Execution Results.
 */

import { apiGet, apiPost } from './client';

export interface TestCase {
  id: string;
  project_id: string;
  tc_id: string;
  name: string;
  file_path: string;
  function_name?: string | null;
  linked_req_ids: string[];
  source: string;
  status: 'not_run' | 'passed' | 'failed' | 'error';
  created_at: string;
  updated_at: string;
}

export interface TestCaseListResponse {
  test_cases: TestCase[];
  total: number;
}

export interface TestResult {
  id: string;
  run_id: string;
  test_case_id: string;
  tc_id: string;
  iteration: number;
  result: 'passed' | 'failed' | 'error' | 'skipped';
  duration_ms?: number | null;
  stdout?: string;
  stderr?: string;
  error_message?: string | null;
  created_at: string;
}

export interface TestResultsListResponse {
  results: TestResult[];
  total: number;
}

export interface TestUploadResponse {
  message: string;
  file_path: string;
  test_cases: TestCase[];
  total_extracted: number;
}

/**
 * Upload a pytest file (.py) to the project workspace and extract test cases.
 */
export async function uploadTests(projectId: string, file: File): Promise<TestUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return apiPost<TestUploadResponse>(`/projects/${encodeURIComponent(projectId)}/tests`, formData);
}

/**
 * List all registered test cases for a project.
 */
export async function listTests(projectId: string): Promise<TestCaseListResponse> {
  return apiGet<TestCaseListResponse>(`/projects/${encodeURIComponent(projectId)}/tests`);
}

/**
 * Get recent test execution results for a project.
 */
export async function getTestResults(projectId: string): Promise<TestResultsListResponse> {
  return apiGet<TestResultsListResponse>(`/projects/${encodeURIComponent(projectId)}/tests/results`);
}

/**
 * Get test execution results for a specific run.
 */
export async function getRunTestResults(runId: string): Promise<TestResultsListResponse> {
  return apiGet<TestResultsListResponse>(`/runs/${encodeURIComponent(runId)}/test-results`);
}
