/**
 * Document API client.
 */

export interface DocumentItem {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_hash: string;
  file_path: string;
  status: "uploaded" | "indexing" | "indexed" | "failed" | string;
  chunk_count: number;
  uploaded_at: string;
  indexed_at: string | null;
  size_bytes?: number | null;
  text_preview?: string | null;
}

export interface DocumentUploadItem {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  uploaded_at: string;
  is_duplicate: boolean;
  message?: string;
}

export interface DocumentUploadResponse {
  documents: DocumentUploadItem[];
  total_uploaded: number;
  skipped_duplicates: number;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total: number;
}

export interface DocumentDetailResponse {
  document: DocumentItem;
  raw_text?: string | null;
}

/**
 * Upload one or more files to a project.
 */
export async function uploadDocuments(
  projectId: string,
  files: File[]
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let errorMsg = `Upload failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  return res.json();
}

/**
 * List all documents uploaded to a project.
 */
export async function listDocuments(projectId: string): Promise<DocumentListResponse> {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/documents`);
  if (!res.ok) {
    throw new Error(`Failed to list documents: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch detail and parsed text for a document.
 */
export async function getDocument(
  projectId: string,
  documentId: string
): Promise<DocumentDetailResponse> {
  const res = await fetch(
    `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}`
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch document: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Delete a document from disk and database.
 */
export async function deleteDocument(projectId: string, documentId: string): Promise<void> {
  const res = await fetch(
    `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
    }
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`Failed to delete document: ${res.statusText}`);
  }
}
