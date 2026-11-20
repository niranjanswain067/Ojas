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

export interface RequirementChunk {
  id: string;
  document_id: string;
  project_id: string;
  req_id: string;
  chunk_type: string;
  heading: string;
  content: string;
  token_count?: number | null;
  chunk_index: number;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface RequirementListResponse {
  requirements: RequirementChunk[];
  total: number;
}

export interface IndexTriggerResponse {
  status: "queued" | "completed" | "already_indexed" | "error" | string;
  message: string;
  task_id?: string | null;
  chunks_indexed?: number | null;
  documents_processed?: number | null;
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

/**
 * List indexed requirements for a project with optional search.
 */
export async function listRequirements(
  projectId: string,
  search?: string,
  documentId?: string
): Promise<RequirementListResponse> {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append("search", search.trim());
  if (documentId) params.append("document_id", documentId);

  const query = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/requirements${query}`);
  if (!res.ok) {
    throw new Error(`Failed to list requirements: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch a single requirement by REQ-ID or chunk ID.
 */
export async function getRequirement(
  projectId: string,
  reqId: string
): Promise<RequirementChunk> {
  const res = await fetch(
    `/api/projects/${encodeURIComponent(projectId)}/requirements/${encodeURIComponent(reqId)}`
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch requirement: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Trigger indexing of documents for a project.
 */
export async function triggerIndex(
  projectId: string,
  documentId?: string,
  force: boolean = false
): Promise<IndexTriggerResponse> {
  let url = `/api/projects/${encodeURIComponent(projectId)}/index?force=${force}&background=false`;
  if (documentId) {
    url = `/api/projects/${encodeURIComponent(projectId)}/documents/${encodeURIComponent(documentId)}/index?force=${force}`;
  }

  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    let errorMsg = `Indexing failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorMsg = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}
