/**
 * TypeScript type definitions matching backend Pydantic models and API schemas.
 */

// ---------------------------------------------------------------------------
// Common & Health Schemas
// ---------------------------------------------------------------------------

export type HealthStatus = 'healthy' | 'degraded' | 'error';

export interface PathsInfo {
  workspace: string;
  models: string;
  data: string;
  logs: string;
  reports: string;
}

export interface HealthResponse {
  status: HealthStatus;
  model_loaded: boolean;
  model_name: string;
  load_time_seconds: number;
  version: string;
  paths: PathsInfo;
  last_error: string | null;
}

export interface ErrorResponse {
  status_code: number;
  detail: string;
  timestamp: string;
}

export interface SuccessResponse {
  status: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Settings Schemas
// ---------------------------------------------------------------------------

export interface Settings {
  model_path: string;
  n_ctx: number;
  n_threads: number;
  n_batch: number;
  n_gpu_layers: number;
  max_tokens: number;
  temperature: number;
  iteration_limit: number;
  test_timeout: number;
  host: string;
  port: number;
  log_level: string;
  theme: 'light' | 'dark' | 'system';
}

export type SettingsUpdate = Partial<Settings>;

// ---------------------------------------------------------------------------
// Project Schemas
// ---------------------------------------------------------------------------

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

// ---------------------------------------------------------------------------
// Workspace File Schemas
// ---------------------------------------------------------------------------

export interface WorkspaceFile {
  path: string;
  name: string;
  is_directory: boolean;
  size_bytes?: number;
  updated_at?: string;
  children?: WorkspaceFile[];
}

export interface WorkspaceFileContent {
  path: string;
  content: string;
  is_binary?: boolean;
}

// ---------------------------------------------------------------------------
// Document & Requirement Schemas
// ---------------------------------------------------------------------------

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  file_path: string;
  file_type: string;
  file_hash: string;
  indexed: boolean;
  created_at: string;
}

export interface Chunk {
  id: string;
  document_id: string;
  project_id: string;
  req_id?: string;
  title?: string;
  content: string;
  chunk_index: number;
  token_count: number;
}

// ---------------------------------------------------------------------------
// Run & Orchestrator Schemas
// ---------------------------------------------------------------------------

export type RunStage =
  | 'idle'
  | 'indexing'
  | 'planning'
  | 'generating'
  | 'static_check'
  | 'testing'
  | 'fixing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface Run {
  id: string;
  project_id: string;
  stage: RunStage;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  prompt: string;
  plan?: string;
  current_file?: string;
  current_iteration: number;
  iteration_limit: number;
  start_time?: string;
  end_time?: string;
  error_message?: string;
}

export interface RunCreate {
  prompt: string;
  action: 'plan' | 'develop' | 'test' | 'fix';
  iteration_limit?: number;
}

export interface RunStep {
  id: string;
  run_id: string;
  stage: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
}

export interface RunEvent {
  event: 'stage_change' | 'token' | 'file_write' | 'test_result' | 'bug' | 'log' | 'done' | 'error';
  data: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Testing & Bug Report Schemas
// ---------------------------------------------------------------------------

export interface TestCase {
  id: string;
  project_id: string;
  tc_id: string;
  title: string;
  file_path: string;
  function_name?: string;
  last_result?: 'pass' | 'fail' | 'not_run';
  duration_seconds?: number;
}

export interface TestResult {
  id: string;
  run_id: string;
  tc_id: string;
  name: string;
  result: 'pass' | 'fail' | 'error' | 'skipped';
  duration_seconds: number;
  output?: string;
}

export interface BugReport {
  id: string;
  project_id: string;
  run_id: string;
  bug_id: string;
  req_id?: string;
  tc_id?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  file_path: string;
  function_name?: string;
  expected_behavior: string;
  actual_behavior: string;
  probable_cause: string;
  status: 'open' | 'fixed' | 'ignored';
  created_at: string;
}

export interface TraceabilityLink {
  id: string;
  project_id: string;
  req_id: string;
  file_path?: string;
  function_name?: string;
  tc_id?: string;
  bug_id?: string;
}

