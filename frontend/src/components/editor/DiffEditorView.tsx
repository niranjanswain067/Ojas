/**
 * DiffEditorView component for Ojas.
 * Embeds Monaco DiffEditor to inspect, review, and accept or reject code modifications
 * generated during development or fix loops.
 */

import React from 'react';
import { DiffEditor } from '@monaco-editor/react';
import { Check, X, GitCompare } from 'lucide-react';
import '../../monaco/loader';

interface DiffEditorViewProps {
  original: string;
  modified: string;
  filePath?: string;
  language?: string;
  onAccept?: () => void;
  onReject?: () => void;
  onClose?: () => void;
}

export const DiffEditorView: React.FC<DiffEditorViewProps> = ({
  original,
  modified,
  filePath = 'code.py',
  language = 'python',
  onAccept,
  onReject,
  onClose,
}) => {
  return (
    <div className="flex flex-col h-full bg-neutral-950 border border-neutral-800 rounded-lg overflow-hidden select-none">
      {/* Diff Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-neutral-900 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-sky-400" />
          <span className="font-mono text-xs font-semibold text-white">{filePath}</span>
          <span className="text-[10px] text-neutral-400 font-sans uppercase px-1.5 py-0.5 rounded bg-neutral-800">
            {language}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onAccept && (
            <button
              type="button"
              onClick={onAccept}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Accept Fix</span>
            </button>
          )}

          {onReject && (
            <button
              type="button"
              onClick={onReject}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-neutral-300 hover:text-white rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reject</span>
            </button>
          )}

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Close diff view"
              className="p-1 text-neutral-400 hover:text-white rounded hover:bg-neutral-800 transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Monaco Diff Editor */}
      <div className="flex-1 min-h-[300px]">
        <DiffEditor
          original={original}
          modified={modified}
          language={language}
          theme="vs-dark"
          options={{
            readOnly: true,
            renderSideBySide: true,
            minimap: { enabled: false },
            fontSize: 12,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
};
