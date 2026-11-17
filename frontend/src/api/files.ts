/**
 * Workspace Files API client functions for Ojas.
 */

import { apiDelete, apiGet, apiPut } from './client';
import type {
  FileContentResponse,
  FileSaveResponse,
  FileTreeResponse,
} from './types';

/**
 * Fetch the recursive file tree for a project workspace.
 */
export async function getFileTree(projectId: string): Promise<FileTreeResponse> {
  return apiGet<FileTreeResponse>(`/projects/${projectId}/files`);
}

/**
 * Read the content and metadata of a file.
 */
export async function getFileContent(
  projectId: string,
  filePath: string
): Promise<FileContentResponse> {
  const cleanPath = filePath.replace(/^\/+/, '');
  return apiGet<FileContentResponse>(`/projects/${projectId}/files/${cleanPath}`);
}

/**
 * Save or overwrite a file in the project workspace.
 */
export async function saveFile(
  projectId: string,
  filePath: string,
  content: string
): Promise<FileSaveResponse> {
  const cleanPath = filePath.replace(/^\/+/, '');
  return apiPut<FileSaveResponse>(`/projects/${projectId}/files/${cleanPath}`, {
    content,
  });
}

/**
 * Delete a file from the project workspace.
 */
export async function deleteFile(
  projectId: string,
  filePath: string
): Promise<void> {
  const cleanPath = filePath.replace(/^\/+/, '');
  return apiDelete<void>(`/projects/${projectId}/files/${cleanPath}`);
}
