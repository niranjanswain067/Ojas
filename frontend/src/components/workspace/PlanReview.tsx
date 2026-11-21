/**
 * PlanReview modal for inspecting, modifying, and approving
 * the development plan before code generation begins.
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle, X, Sparkles, Play } from 'lucide-react';

interface PlanReviewProps {
  isOpen: boolean;
  planText: string;
  onApprove: (editedPlan: string, proceed: boolean) => Promise<void>;
  onClose: () => void;
  isLoading?: boolean;
}

export const PlanReview: React.FC<PlanReviewProps> = ({
  isOpen,
  planText,
  onApprove,
  onClose,
  isLoading = false,
}) => {
  const [content, setContent] = useState(planText);

  useEffect(() => {
    setContent(planText);
  }, [planText]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="flex flex-col w-full max-w-3xl max-h-[85vh] bg-neutral-900 border border-neutral-700 rounded-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-neutral-950">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold text-white">Review Development Plan</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="p-1 text-neutral-400 hover:text-white rounded hover:bg-neutral-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Notice */}
        <div className="px-4 py-2 bg-sky-950/40 border-b border-sky-900/40 text-xs text-sky-300">
          The Development Agent generated the following modular file plan. You can edit the files,
          classes, functions, or dependencies below before approving.
        </div>

        {/* Editable Plan Area */}
        <div className="flex-1 p-4 overflow-y-auto">
          <label htmlFor="plan-editor" className="block text-xs font-medium text-neutral-300 mb-1.5">
            Plan Specification (JSON / Markdown)
          </label>
          <textarea
            id="plan-editor"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={16}
            disabled={isLoading}
            className="w-full p-3 font-mono text-xs bg-neutral-950 border border-neutral-800 rounded text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-sky-500 resize-none"
          />
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-800 bg-neutral-950">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-3 py-1.5 text-xs text-neutral-400 hover:text-white rounded hover:bg-neutral-800 transition-colors"
          >
            Cancel
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onApprove(content, false)}
              disabled={isLoading || !content.trim()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-neutral-200 bg-neutral-800 hover:bg-neutral-700 rounded transition-colors disabled:opacity-40"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Save Plan Only</span>
            </button>

            <button
              type="button"
              onClick={() => onApprove(content, true)}
              disabled={isLoading || !content.trim()}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-white bg-sky-600 hover:bg-sky-500 rounded transition-colors disabled:opacity-40 shadow-sm"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Approve & Generate Code</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
