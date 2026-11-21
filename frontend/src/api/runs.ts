/**
 * API client functions for execution runs, development plans, and history.
 */

import { apiGet, apiPost } from './client';

export interface RunResponse {
  run_id: string;
  status: string;
  message: string;
  run_type?: string;
}

export interface RunStep {
  id: string;
  run_id: string;
  step_index: number;
  stage: string;
  status: string;
  message: string;
  duration_ms?: number;
  created_at: string;
}

export interface RunDetail {
  id: string;
  project_id: string;
  run_type: string;
  status: string;
  prompt: string;
  plan_text?: string;
  iteration_count: number;
  iteration_limit: number;
  stop_reason?: string;
  error_message?: string;
  tokens_generated: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  steps: RunStep[];
}

export interface RunListResponse {
  runs: RunDetail[];
  total: number;
}

export interface PlanResponse {
  project_id: string;
  plan_text: string;
  status: string;
  run_id?: string;
  updated_at?: string;
}

export interface PlanApproveResponse {
  run_id: string;
  status: string;
  message: string;
}

/**
 * Start a new run (plan, develop, test, fix_loop).
 */
export async function startRun(
  projectId: string,
  runType: 'plan' | 'develop' | 'test' | 'fix_loop',
  prompt: string,
  planText?: string
): Promise<RunResponse> {
  return apiPost<RunResponse>(`/projects/${encodeURIComponent(projectId)}/runs`, {
    run_type: runType,
    prompt,
    plan_text: planText,
  });
}

/**
 * Fetch run history for a project.
 */
export async function listRuns(projectId: string, limit: number = 50): Promise<RunListResponse> {
  return apiGet<RunListResponse>(`/projects/${encodeURIComponent(projectId)}/runs?limit=${limit}`);
}

/**
 * Fetch detailed status of a specific run.
 */
export async function getRunDetail(runId: string): Promise<RunDetail> {
  return apiGet<RunDetail>(`/runs/${encodeURIComponent(runId)}`);
}

/**
 * Get the current development plan for a project.
 */
export async function getPlan(projectId: string): Promise<PlanResponse> {
  return apiGet<PlanResponse>(`/projects/${encodeURIComponent(projectId)}/plan`);
}

/**
 * Approve a development plan and trigger background code generation.
 */
export async function approvePlan(
  projectId: string,
  planText: string,
  proceed: boolean = true
): Promise<PlanApproveResponse> {
  return apiPost<PlanApproveResponse>(`/projects/${encodeURIComponent(projectId)}/plan/approve`, {
    plan_text: planText,
    proceed,
  });
}
