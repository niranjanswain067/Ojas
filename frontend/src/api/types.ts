export type ThemeMode = "light" | "dark" | "system";

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
  log_level: "debug" | "info" | "warning" | "error" | "critical" | string;
  theme: ThemeMode;
  editor_font_size: number;
}

export interface SettingsUpdateResponse {
  settings: Settings;
  model_reload_required: boolean;
  model_reload_status: "not_required" | "reloaded" | "reloading" | "error";
  message?: string;
}

export interface PathsInfo {
  workspace: string;
  models: string;
  data: string;
  logs: string;
  reports: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "error";
  model_loaded: boolean;
  model_name: string;
  load_time_seconds: number;
  version: string;
  paths: PathsInfo;
  last_error: string | null;
}

export interface ApiError {
  status_code: number;
  detail: string;
  timestamp?: string;
}

