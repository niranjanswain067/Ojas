/**
 * Project API client functions for Ojas.
 */

import { apiDelete, apiGet, apiPatch, apiPost } from './client';
import type {
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectUpdate,
} from './types';

/**
 * List all projects with aggregate statistics.
 */
export async function listProjects(): Promise<ProjectListResponse> {
  return apiGet<ProjectListResponse>('/projects');
}

/**
 * Get project details by UUID.
 */
export async function getProject(projectId: string): Promise<Project> {
  return apiGet<Project>(`/projects/${projectId}`);
}

/**
 * Create a new project.
 */
export async function createProject(data: ProjectCreate): Promise<Project> {
  return apiPost<Project>('/projects', data);
}

/**
 * Update project name and/or description.
 */
export async function updateProject(
  projectId: string,
  data: ProjectUpdate
): Promise<Project> {
  return apiPatch<Project>(`/projects/${projectId}`, data);
}

/**
 * Delete a project and clean up its workspace.
 */
export async function deleteProject(projectId: string): Promise<void> {
  return apiDelete<void>(`/projects/${projectId}`);
}

/**
 * Download the entire project workspace as a ZIP archive.
 */
export async function downloadProjectZip(
  projectId: string,
  projectName?: string
): Promise<void> {
  const response = await fetch(`/api/projects/${projectId}/download`, {
    method: 'GET',
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Failed to download project: ${response.statusText} (${errorText})`
    );
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;

  let filename = `${projectName || projectId}.zip`;
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
