/**
 * CodeEditor component for Ojas.
 * Embeds Monaco Editor locally with offline workers, custom Ojas dark theme,
 * Ctrl+S hotkey binding, and status bar.
 */

import React, { useEffect } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { Save, Code2 } from 'lucide-react';
import type { OpenFile } from '../../store/uiStore';
import '../../monaco/loader';

interface CodeEditorProps {
  activeFile: OpenFile | null;
  onChangeContent: (content: string) => void;
  onSaveFile: () => void;
  isSaving?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  activeFile,
  onChangeContent,
  onSaveFile,
  isSaving = false,
}) => {
  // Global Ctrl+S listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (activeFile) {
          onSaveFile();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeFile, onSaveFile]);

  const handleEditorMount: OnMount = (editor, monaco) => {
    // Add Monaco-level Command for Save (Ctrl+S)
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      onSaveFile();
    });
  };

  if (!activeFile) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-neutral-900/40 text-neutral-400 p-8 select-none">
        <Code2 className="w-12 h-12 text-neutral-600 mb-3" />
        <h3 className="text-sm font-medium text-neutral-300">No file open</h3>
        <p className="text-xs text-neutral-400 mt-1 text-center max-w-sm">
          Select a file from the explorer on the left or create a new one to begin editing.
        </p>
        <div className="mt-4 flex items-center gap-4 text-[11px] text-neutral-400">
          <span><kbd className="px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-300">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 bg-neutral-800 rounded border border-neutral-700 text-neutral-300">S</kbd> to save</span>
        </div>
      </div>
    );
  }

  const lineCount = activeFile.content.split('\n').length;
  const byteSize = new Blob([activeFile.content]).size;

  return (
    <div className="flex flex-col h-full bg-neutral-900 overflow-hidden">
      {/* Editor Main Canvas */}
      <div className="flex-1 overflow-hidden relative">
        <Editor
          height="100%"
          path={activeFile.path}
          defaultLanguage={activeFile.language || 'plaintext'}
          language={activeFile.language || 'plaintext'}
          value={activeFile.content}
          theme="ojas-dark"
          onChange={(value) => onChangeContent(value ?? '')}
          onMount={handleEditorMount}
          options={{
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'off',
            tabSize: 4,
            renderWhitespace: 'selection',
            smoothScrolling: true,
          }}
        />
      </div>

      {/* Editor Status Bar */}
      <div className="flex items-center justify-between px-3 py-1 bg-neutral-950 border-t border-neutral-800 text-[11px] text-neutral-400 select-none">
        <div className="flex items-center gap-4">
          <span className="truncate max-w-[300px] text-neutral-300">
            {activeFile.path}
          </span>
          <span>{lineCount} lines</span>
          <span>{byteSize} B</span>
        </div>

        <div className="flex items-center gap-3">
          {activeFile.isDirty ? (
            <span className="text-amber-400 flex items-center gap-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Unsaved
            </span>
          ) : (
            <span className="text-emerald-400 flex items-center gap-1">
              <Save className="w-3 h-3" />
              Saved
            </span>
          )}

          <span className="uppercase text-neutral-400 font-mono text-[10px] px-1 bg-neutral-800 rounded">
            {activeFile.language}
          </span>

          <button
            type="button"
            onClick={onSaveFile}
            disabled={!activeFile.isDirty || isSaving}
            className="px-2 py-0.5 text-[11px] text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:hover:bg-sky-600 rounded transition-colors"
          >
            {isSaving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
