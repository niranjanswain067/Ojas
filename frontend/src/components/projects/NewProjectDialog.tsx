import React, { useState, useEffect } from 'react';
import { FolderPlus, X } from 'lucide-react';

export interface NewProjectDialogProps {
  isOpen: boolean;
  isLoading: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (data: { name: string; description: string }) => void;
}

export const NewProjectDialog: React.FC<NewProjectDialogProps> = ({
  isOpen,
  isLoading,
  error,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setName('');
      setDescription('');
      setValidationError(null);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setValidationError('Project name is required.');
      return;
    }
    setValidationError(null);
    onSubmit({ name: trimmedName, description: description.trim() });
  };

  const displayError = validationError || error;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="new-project-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div
        className="w-full max-w-lg bg-panel border border-border rounded-lg shadow-xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-primary/10 text-primary">
              <FolderPlus className="w-4 h-4" />
            </div>
            <h3 id="new-project-title" className="text-base font-semibold text-text">
              Create New Project
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-muted hover:text-text transition-colors p-1 rounded-md"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="p-5 space-y-4">
            {displayError && (
              <div className="p-3 text-xs rounded-md bg-status-error/15 border border-status-error/30 text-status-error">
                {displayError}
              </div>
            )}

            <div>
              <label
                htmlFor="project-name"
                className="block text-xs font-semibold text-text mb-1.5"
              >
                Project Name <span className="text-status-error">*</span>
              </label>
              <input
                id="project-name"
                type="text"
                autoFocus
                disabled={isLoading}
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (validationError) setValidationError(null);
                }}
                placeholder="e.g. Library System or Calculator"
                className="w-full px-3 py-2 text-xs rounded-md border border-border bg-bg text-text placeholder:text-muted/60 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary disabled:opacity-50"
              />
            </div>

            <div>
              <label
                htmlFor="project-description"
                className="block text-xs font-semibold text-text mb-1.5"
              >
                Description <span className="text-muted font-normal">(optional)</span>
              </label>
              <textarea
                id="project-description"
                rows={3}
                disabled={isLoading}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Briefly describe the purpose of this software project..."
                className="w-full px-3 py-2 text-xs rounded-md border border-border bg-bg text-text placeholder:text-muted/60 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary disabled:opacity-50 resize-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 px-5 py-3.5 bg-bg/50 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-3.5 py-1.5 text-xs font-medium rounded-md border border-border bg-panel text-text hover:bg-hover transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !name.trim()}
              className="px-3.5 py-1.5 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading && (
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              Create Project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
