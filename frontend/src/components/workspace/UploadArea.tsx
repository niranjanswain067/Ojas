import React, { useRef, useState } from "react";
import { UploadCloud, FileText, X, AlertCircle, Check } from "lucide-react";

interface UploadAreaProps {
  onUpload: (files: File[]) => Promise<void>;
  uploading: boolean;
  disabled?: boolean;
}

const ALLOWED_EXTENSIONS = [".docx", ".pdf", ".txt", ".md"];

export const UploadArea: React.FC<UploadAreaProps> = ({
  onUpload,
  uploading,
  disabled = false,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndFilterFiles = (filesList: FileList | File[]): File[] => {
    setValidationError(null);
    const valid: File[] = [];
    const invalidNames: string[] = [];

    Array.from(filesList).forEach((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      if (ALLOWED_EXTENSIONS.includes(ext)) {
        valid.push(file);
      } else {
        invalidNames.push(file.name);
      }
    });

    if (invalidNames.length > 0) {
      setValidationError(
        `Unsupported file(s): ${invalidNames.join(", ")}. Only .docx, .pdf, .txt, and .md files are supported.`
      );
    }

    return valid;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled || uploading) return;

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (disabled || uploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const valid = validateAndFilterFiles(e.dataTransfer.files);
      if (valid.length > 0) {
        setSelectedFiles((prev) => [...prev, ...valid]);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const valid = validateAndFilterFiles(e.target.files);
      if (valid.length > 0) {
        setSelectedFiles((prev) => [...prev, ...valid]);
      }
      e.target.value = "";
    }
  };

  const removeSelectedFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0 || uploading) return;
    await onUpload(selectedFiles);
    setSelectedFiles([]);
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && !uploading && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-[#1F3A5F] bg-blue-50/50 dark:border-[#6FA0E0] dark:bg-blue-950/20 scale-[0.99]"
            : "border-[#D5DBE3] dark:border-[#2D3541] hover:border-[#1F3A5F] dark:hover:border-[#6FA0E0] bg-white dark:bg-[#14181F]"
        } ${disabled || uploading ? "opacity-60 cursor-not-allowed" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".docx,.pdf,.txt,.md"
          onChange={handleFileChange}
          disabled={disabled || uploading}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center gap-2 pointer-events-none">
          <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-gray-800 flex items-center justify-center text-[#1F3A5F] dark:text-[#6FA0E0]">
            <UploadCloud size={20} />
          </div>
          <div className="space-y-1">
            <p className="text-xs sm:text-sm font-medium text-[#1B2430] dark:text-[#E6EAF0]">
              <span className="text-[#1F3A5F] dark:text-[#6FA0E0] font-semibold underline">
                Click to browse
              </span>{" "}
              or drag & drop requirements files
            </p>
            <p className="text-[11px] text-[#5F6B7A] dark:text-[#98A3B3]">
              Supports PDF, DOCX, TXT, MD
            </p>
          </div>
        </div>
      </div>

      {/* Validation Alert */}
      {validationError && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-xs text-red-700 dark:text-red-300">
          <AlertCircle size={14} className="shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Selected Pending Files */}
      {selectedFiles.length > 0 && (
        <div className="p-3 bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1B2430] dark:text-[#E6EAF0]">
              Files ready for upload ({selectedFiles.length})
            </span>
            <button
              type="button"
              onClick={handleUploadSubmit}
              disabled={uploading}
              className="px-3 py-1.5 bg-[#1F3A5F] hover:bg-[#1F3A5F]/90 dark:bg-[#6FA0E0] dark:hover:bg-[#6FA0E0]/90 text-white dark:text-[#14181F] rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
            >
              {uploading ? (
                <>
                  <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" />
                  <span>Uploading…</span>
                </>
              ) : (
                <>
                  <Check size={13} />
                  <span>Upload Now</span>
                </>
              )}
            </button>
          </div>

          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {selectedFiles.map((f, idx) => (
              <div
                key={`${f.name}-${idx}`}
                className="flex items-center justify-between bg-white dark:bg-[#14181F] p-2 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] text-xs"
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <FileText size={14} className="text-gray-400 shrink-0" />
                  <span className="truncate font-mono text-[11px] text-[#1B2430] dark:text-[#E6EAF0]">
                    {f.name}
                  </span>
                  <span className="text-[10px] text-[#5F6B7A] dark:text-[#98A3B3]">
                    ({formatSize(f.size)})
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removeSelectedFile(idx)}
                  disabled={uploading}
                  className="text-gray-400 hover:text-red-500 p-0.5 rounded transition"
                  title="Remove file"
                >
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
