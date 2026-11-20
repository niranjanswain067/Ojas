import React, { useEffect, useState, useCallback } from "react";
import {
  FileText,
  Trash2,
  Eye,
  RefreshCw,
  FolderOpen,
  CheckCircle2,
  AlertTriangle,
  X,
  Layers,
  Sparkles,
  FileCheck2,
} from "lucide-react";
import type { DocumentItem, RequirementChunk } from "../../api/documents";
import {
  listDocuments,
  uploadDocuments,
  deleteDocument,
  getDocument,
  triggerIndex,
  listRequirements,
} from "../../api/documents";
import { UploadArea } from "./UploadArea";
import { RequirementList } from "./RequirementList";
import { StatusChip } from "../shared/StatusChip";

interface DocsPanelProps {
  projectId?: string;
}

export const DocsPanel: React.FC<DocsPanelProps> = ({
  projectId = "default-project",
}) => {
  const [activeTab, setActiveTab] = useState<"documents" | "requirements">("documents");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [requirements, setRequirements] = useState<RequirementChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [reqsLoading, setReqsLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<{
    doc: DocumentItem;
    text: string;
  } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error";
    message: string;
  } | null>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listDocuments(projectId);
      setDocuments(res.documents);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setNotification({
        type: "error",
        message: `Failed to load documents: ${msg}`,
      });
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const fetchReqs = useCallback(async (searchQuery?: string) => {
    setReqsLoading(true);
    try {
      const res = await listRequirements(projectId, searchQuery);
      setRequirements(res.requirements);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setNotification({
        type: "error",
        message: `Failed to load requirements: ${msg}`,
      });
    } finally {
      setReqsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchDocs();
    fetchReqs();
  }, [fetchDocs, fetchReqs]);

  const handleUpload = async (files: File[]) => {
    setUploading(true);
    setNotification(null);
    try {
      const res = await uploadDocuments(projectId, files);
      let msg = `Successfully uploaded ${res.total_uploaded} document(s).`;
      if (res.skipped_duplicates > 0) {
        msg += ` (${res.skipped_duplicates} duplicate file(s) skipped).`;
        setNotification({
          type: "warning",
          message: msg,
        });
      } else {
        setNotification({
          type: "success",
          message: msg,
        });
      }
      await fetchDocs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setNotification({
        type: "error",
        message: msg,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleIndexAll = async (force: boolean = false) => {
    setIndexing(true);
    setNotification(null);
    try {
      const res = await triggerIndex(projectId, undefined, force);
      setNotification({
        type: res.status === "error" ? "error" : "success",
        message: res.message,
      });
      await Promise.all([fetchDocs(), fetchReqs()]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Indexing failed";
      setNotification({
        type: "error",
        message: msg,
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleIndexSingle = async (docId: string, filename: string) => {
    setIndexing(true);
    setNotification(null);
    try {
      const res = await triggerIndex(projectId, docId, true);
      setNotification({
        type: "success",
        message: `Indexed "${filename}": ${res.message}`,
      });
      await Promise.all([fetchDocs(), fetchReqs()]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Document indexing failed";
      setNotification({
        type: "error",
        message: msg,
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }
    try {
      await deleteDocument(projectId, docId);
      setNotification({
        type: "success",
        message: `Deleted "${filename}".`,
      });
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (previewDoc?.doc.id === docId) {
        setPreviewDoc(null);
      }
      await fetchReqs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete document";
      setNotification({
        type: "error",
        message: msg,
      });
    }
  };

  const handlePreview = async (doc: DocumentItem) => {
    setPreviewLoading(true);
    try {
      const res = await getDocument(projectId, doc.id);
      setPreviewDoc({
        doc,
        text: res.raw_text || "No text could be extracted.",
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load preview";
      setNotification({
        type: "error",
        message: msg,
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const formatSize = (bytes?: number | null): string => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <UploadArea onUpload={handleUpload} uploading={uploading} />

      {/* Notification */}
      {notification && (
        <div
          className={`flex items-center justify-between p-3 rounded-xl text-xs border ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
              : notification.type === "warning"
              ? "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800"
              : "bg-red-50 text-red-800 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800"
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === "success" && <CheckCircle2 size={15} />}
            {notification.type === "warning" && <AlertTriangle size={15} />}
            <span>{notification.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="text-gray-400 hover:text-gray-600 text-sm font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* Tabs and Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "documents"
                ? "bg-primary text-white shadow-sm"
                : "text-muted hover:text-text hover:bg-border/30"
            }`}
          >
            <FolderOpen size={14} />
            <span>Documents ({documents.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("requirements")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "requirements"
                ? "bg-primary text-white shadow-sm"
                : "text-muted hover:text-text hover:bg-border/30"
            }`}
          >
            <FileCheck2 size={14} />
            <span>Requirements ({requirements.length || totalChunks})</span>
          </button>
        </div>

        {/* Indexing trigger button */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleIndexAll(false)}
            disabled={indexing || documents.length === 0}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-40"
            title="Index all uploaded documents into vector and FTS search"
          >
            {indexing ? (
              <>
                <RefreshCw size={13} className="animate-spin" />
                <span>Indexing…</span>
              </>
            ) : (
              <>
                <Sparkles size={13} />
                <span>Index Documents</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleIndexAll(true)}
            disabled={indexing || documents.length === 0}
            className="p-1.5 border border-border text-muted hover:text-text rounded-lg hover:bg-border/30 transition disabled:opacity-40 text-xs"
            title="Force re-index all documents from scratch"
          >
            <RefreshCw size={13} className={indexing ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Tab 1: Documents View */}
      {activeTab === "documents" && (
        <div className="bg-surface dark:bg-[#1C222B] border border-border rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <FolderOpen size={18} className="text-primary" />
              <h3 className="font-semibold text-sm text-text">
                Uploaded Requirement Documents
              </h3>
            </div>
            <button
              type="button"
              onClick={fetchDocs}
              disabled={loading}
              className="p-1.5 rounded-md text-muted hover:text-text hover:bg-border/30 transition disabled:opacity-50"
              title="Refresh documents list"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <FileText size={28} className="mx-auto text-muted/50" />
              <p className="text-xs text-muted">
                {loading ? "Loading documents…" : "No requirement documents uploaded yet."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-bg dark:bg-[#14181F] border border-border rounded-xl hover:border-muted transition"
                >
                  {/* File info */}
                  <div className="flex items-start gap-2.5 overflow-hidden">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0 mt-0.5">
                      <FileText size={16} />
                    </div>
                    <div className="overflow-hidden">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-xs text-text truncate">
                          {doc.filename}
                        </span>
                        <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-border/40 text-muted font-mono">
                          {doc.file_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-muted mt-0.5">
                        <span>{formatSize(doc.size_bytes)}</span>
                        <span>•</span>
                        <span>Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                        {doc.chunk_count > 0 && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-0.5 text-primary font-medium">
                              <Layers size={10} />
                              {doc.chunk_count} chunks
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <StatusChip
                      status={doc.status}
                      label={
                        doc.status === "indexed"
                          ? "Indexed"
                          : doc.status === "indexing"
                          ? "Indexing…"
                          : "Uploaded"
                      }
                      size="sm"
                    />

                    <button
                      type="button"
                      onClick={() => handleIndexSingle(doc.id, doc.filename)}
                      disabled={indexing}
                      className="p-1.5 rounded-lg border border-border text-muted hover:text-text hover:bg-border/30 transition text-xs"
                      title="Index this document"
                    >
                      <Sparkles size={13} />
                    </button>

                    <button
                      type="button"
                      onClick={() => handlePreview(doc)}
                      disabled={previewLoading}
                      className="p-1.5 rounded-lg border border-border text-muted hover:text-text hover:bg-border/30 transition"
                      title="Preview extracted plain text"
                    >
                      <Eye size={13} />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="p-1.5 rounded-lg border border-red-200 dark:border-red-900/50 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition"
                      title="Delete document"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Requirements View */}
      {activeTab === "requirements" && (
        <RequirementList
          requirements={requirements}
          loading={reqsLoading}
          onRefresh={() => fetchReqs()}
          onSearchChange={(term) => fetchReqs(term)}
        />
      )}

      {/* Text Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface dark:bg-[#1C222B] border border-border rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-border flex items-center justify-between bg-bg dark:bg-[#14181F]">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-primary" />
                <h4 className="text-xs font-semibold text-text truncate">
                  Parsed Text: {previewDoc.doc.filename}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setPreviewDoc(null)}
                className="text-muted hover:text-text p-1 rounded"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 overflow-y-auto flex-1 font-mono text-xs text-text whitespace-pre-wrap leading-relaxed bg-bg dark:bg-[#14181F]">
              {previewDoc.text}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-border bg-surface dark:bg-[#1C222B] flex justify-end">
              <button
                type="button"
                onClick={() => setPreviewDoc(null)}
                className="px-4 py-1.5 rounded-lg border border-border text-xs font-medium text-text hover:bg-border/30"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
