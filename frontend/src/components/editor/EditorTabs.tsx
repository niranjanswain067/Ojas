/**
 * EditorTabs component for Ojas multi-file workspace editing.
 * Displays tabs for all open files, active tab indicator, unsaved dirty dot,
 * and individual tab close buttons.
 */

import React from 'react';
import { X, FileCode, FileText, FileJson, File } from 'lucide-react';
import type { OpenFile } from '../../store/uiStore';

interface EditorTabsProps {
  files: OpenFile[];
  activeFilePath: string | null;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string) => void;
}

function getTabIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py':
      return <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    case 'ts':
    case 'tsx':
    case 'js':
    case 'jsx':
      return <FileCode className="w-3.5 h-3.5 text-sky-400 shrink-0" />;
    case 'json':
      return <FileJson className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    case 'md':
    case 'txt':
      return <FileText className="w-3.5 h-3.5 text-neutral-400 shrink-0" />;
    default:
      return <File className="w-3.5 h-3.5 text-neutral-400 shrink-0" />;
  }
}

export const EditorTabs: React.FC<EditorTabsProps> = ({
  files,
  activeFilePath,
  onSelectTab,
  onCloseTab,
}) => {
  if (files.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center overflow-x-auto bg-neutral-950/80 border-b border-neutral-800 scrollbar-thin scrollbar-thumb-neutral-800 select-none">
      {files.map((file) => {
        const isActive = file.path === activeFilePath;
        return (
          <div
            key={file.path}
            role="tab"
            aria-selected={isActive}
            tabIndex={0}
            onClick={() => onSelectTab(file.path)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectTab(file.path);
              }
            }}
            className={`group relative flex items-center gap-2 px-3 py-2 text-xs border-r border-neutral-800 cursor-pointer transition-colors shrink-0 max-w-[220px] ${
              isActive
                ? 'bg-neutral-900 text-white font-medium border-t-2 border-t-sky-500'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40'
            }`}
          >
            {getTabIcon(file.name)}
            <span className="truncate">{file.name}</span>

            {/* AI Generated pill */}
            {file.isGenerated && (
              <span className="px-1 text-[8px] font-semibold text-emerald-400 bg-emerald-950/60 rounded border border-emerald-800/60">
                AI
              </span>
            )}

            {/* Unsaved dirty dot or Close button */}
            <div className="flex items-center ml-1">
              {file.isDirty ? (
                <span
                  title="Unsaved changes"
                  className="w-2 h-2 rounded-full bg-amber-400 group-hover:hidden"
                />
              ) : null}

              <button
                type="button"
                title={`Close ${file.name}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onCloseTab(file.path);
                }}
                className={`p-0.5 rounded text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors ${
                  file.isDirty ? 'hidden group-hover:block' : 'opacity-0 group-hover:opacity-100'
                }`}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
