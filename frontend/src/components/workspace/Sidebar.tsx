/**
 * Left Sidebar component for Ojas Workspace.
 * Features 3 tabs: Docs, Code, Tests.
 */

import React from 'react';
import { FileCode2, FileText, FlaskConical, UploadCloud } from 'lucide-react';
import type { FileNode } from '../../api/types';
import type { SidebarTab } from '../../store/uiStore';
import { FileTree } from './FileTree';
import { TestsPanel } from './TestsPanel';

interface SidebarProps {
  projectId?: string;
  currentTab: SidebarTab;
  onTabChange: (tab: SidebarTab) => void;
  fileTree: FileNode[];
  activeFilePath?: string | null;
  isLoadingFiles?: boolean;
  onSelectFile: (node: FileNode) => void;
  onSelectTest?: (filePath: string, functionName?: string | null) => void;
  onCreateFile?: (path: string) => void;
  onDeleteFile?: (path: string) => void;
  onRefreshFiles?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  projectId = 'default-project',
  currentTab,
  onTabChange,
  fileTree,
  activeFilePath,
  isLoadingFiles = false,
  onSelectFile,
  onSelectTest,
  onCreateFile,
  onDeleteFile,
  onRefreshFiles,
}) => {
  return (
    <aside className="flex flex-col h-full bg-neutral-900 border-r border-neutral-800 text-neutral-200 select-none overflow-hidden">
      {/* Sidebar Tabs */}
      <div className="flex border-b border-neutral-800 bg-neutral-950/60 p-1 gap-1">
        <button
          type="button"
          onClick={() => onTabChange('code')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium rounded transition-colors ${
            currentTab === 'code'
              ? 'bg-neutral-800 text-white shadow-sm'
              : 'text-neutral-400 hover:text-white hover:bg-neutral-800/40'
          }`}
        >
          <FileCode2 className="w-3.5 h-3.5 text-sky-400" />
          <span>Code</span>
        </button>

        <button
          type="button"
          onClick={() => onTabChange('docs')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium rounded transition-colors ${
            currentTab === 'docs'
              ? 'bg-neutral-800 text-white shadow-sm'
              : 'text-neutral-400 hover:text-white hover:bg-neutral-800/40'
          }`}
        >
          <FileText className="w-3.5 h-3.5 text-amber-400" />
          <span>Docs</span>
        </button>

        <button
          type="button"
          onClick={() => onTabChange('tests')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium rounded transition-colors ${
            currentTab === 'tests'
              ? 'bg-neutral-800 text-white shadow-sm'
              : 'text-neutral-400 hover:text-white hover:bg-neutral-800/40'
          }`}
        >
          <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />
          <span>Tests</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-hidden">
        {currentTab === 'code' && (
          <FileTree
            tree={fileTree}
            activePath={activeFilePath}
            isLoading={isLoadingFiles}
            onSelectFile={onSelectFile}
            onCreateFile={onCreateFile}
            onDeleteFile={onDeleteFile}
            onRefresh={onRefreshFiles}
          />
        )}

        {currentTab === 'docs' && (
          <div className="flex flex-col h-full p-4 overflow-y-auto">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">
              Requirement Documents
            </h4>
            <div className="border-2 border-dashed border-neutral-700 hover:border-amber-500/60 rounded-lg p-6 text-center transition-colors">
              <UploadCloud className="w-8 h-8 text-neutral-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-neutral-300">
                Drop requirement files here
              </p>
              <p className="text-[11px] text-neutral-400 mt-1">
                Supports PDF, DOCX, TXT
              </p>
            </div>
            <div className="mt-4 text-[11px] text-neutral-400">
              Uploaded requirement documents will be parsed and indexed for RAG retrieval during code generation.
            </div>
          </div>
        )}

        {currentTab === 'tests' && (
          <TestsPanel
            projectId={projectId}
            onSelectTest={onSelectTest}
          />
        )}
      </div>
    </aside>
  );
};
