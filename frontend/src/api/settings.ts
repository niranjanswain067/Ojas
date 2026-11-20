import { apiGet, apiPut } from "./client";
import type { HealthResponse, Settings, SettingsUpdateResponse } from "./types";

/**
 * Fetch the current runtime settings from backend.
 */
export async function getSettings(): Promise<Settings> {
  return apiGet<Settings>("/settings");
}

/**
 * Update runtime settings.
 */
export async function updateSettings(
  updates: Partial<Settings>
): Promise<SettingsUpdateResponse> {
  return apiPut<SettingsUpdateResponse>("/settings", updates);
}

/**
 * Fetch backend health status.
 */
export async function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

