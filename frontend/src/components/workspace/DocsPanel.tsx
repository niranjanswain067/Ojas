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
} from "lucide-react";
import {
  DocumentItem,
  listDocuments,
  uploadDocuments,
  deleteDocument,
  getDocument,
} from "../../api/documents";
import { UploadArea } from "./UploadArea";
import { StatusChip } from "../shared/StatusChip";

interface DocsPanelProps {
  projectId?: string;
}

export const DocsPanel: React.FC<DocsPanelProps> = ({
  projectId = "default-project",
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
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
    } catch (err: any) {
      setNotification({
        type: "error",
        message: `Failed to load documents: ${err.message || err}`,
      });
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

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
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.message || "Upload failed",
      });
    } finally {
      setUploading(false);
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
    } catch (err: any) {
      setNotification({
        type: "error",
        message: `Failed to delete document: ${err.message || err}`,
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
    } catch (err: any) {
      setNotification({
        type: "error",
        message: `Failed to load preview: ${err.message || err}`,
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

      {/* Documents List Card */}
      <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#D5DBE3] dark:border-[#2D3541]">
          <div className="flex items-center gap-2">
            <FolderOpen size={18} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
            <h3 className="font-semibold text-sm text-[#1B2430] dark:text-[#E6EAF0]">
              Requirement Documents ({documents.length})
            </h3>
          </div>
          <button
            type="button"
            onClick={fetchDocs}
            disabled={loading}
            className="p-1.5 rounded-md text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-white dark:hover:bg-gray-800 transition disabled:opacity-50"
            title="Refresh documents list"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-8 space-y-2">
            <FileText size={28} className="mx-auto text-gray-300 dark:text-gray-600" />
            <p className="text-xs text-[#5F6B7A] dark:text-[#98A3B3]">
              {loading ? "Loading documents…" : "No requirement documents uploaded yet."}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl hover:border-gray-400 transition"
              >
                {/* File info */}
                <div className="flex items-start gap-2.5 overflow-hidden">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-gray-800 flex items-center justify-center text-[#1F3A5F] dark:text-[#6FA0E0] shrink-0 mt-0.5">
                    <FileText size={16} />
                  </div>
                  <div className="overflow-hidden">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-xs text-[#1B2430] dark:text-[#E6EAF0] truncate">
                        {doc.filename}
                      </span>
                      <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 font-mono">
                        {doc.file_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-[#5F6B7A] dark:text-[#98A3B3] mt-0.5">
                      <span>{formatSize(doc.size_bytes)}</span>
                      <span>•</span>
                      <span>Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                      {doc.chunk_count > 0 && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-0.5 text-blue-600 dark:text-blue-400 font-medium">
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
                    onClick={() => handlePreview(doc)}
                    disabled={previewLoading}
                    className="p-1.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-gray-50 dark:hover:bg-gray-800 transition"
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

      {/* Text Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-[#D5DBE3] dark:border-[#2D3541] flex items-center justify-between bg-[#F5F7FA] dark:bg-[#14181F]">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
                <h4 className="text-xs font-semibold text-[#1B2430] dark:text-[#E6EAF0] truncate">
                  Parsed Text: {previewDoc.doc.filename}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setPreviewDoc(null)}
                className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-1 rounded"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 overflow-y-auto flex-1 font-mono text-xs text-[#1B2430] dark:text-[#E6EAF0] whitespace-pre-wrap leading-relaxed bg-white dark:bg-[#14181F]">
              {previewDoc.text}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-[#D5DBE3] dark:border-[#2D3541] bg-[#F5F7FA] dark:bg-[#14181F] flex justify-end">
              <button
                type="button"
                onClick={() => setPreviewDoc(null)}
                className="px-4 py-1.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] hover:bg-gray-100 dark:hover:bg-gray-800"
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

