/**
 * Recursive FileTree component for Ojas Workspace.
 * Fetches workspace hierarchy from API, handles folder expansion,
 * file selection, creation of new files, and deletion.
 */

import React, { useState } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  FileJson,
  File,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import type { FileNode } from '../../api/types';
import { ConfirmDialog } from '../shared/ConfirmDialog';

interface FileTreeProps {
  tree: FileNode[];
  activePath?: string | null;
  isLoading?: boolean;
  onSelectFile: (node: FileNode) => void;
  onCreateFile?: (path: string) => void;
  onDeleteFile?: (path: string) => void;
  onRefresh?: () => void;
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py':
      return <FileCode className="w-4 h-4 text-emerald-400 shrink-0" />;
    case 'ts':
    case 'tsx':
    case 'js':
    case 'jsx':
      return <FileCode className="w-4 h-4 text-sky-400 shrink-0" />;
    case 'json':
      return <FileJson className="w-4 h-4 text-amber-400 shrink-0" />;
    case 'md':
    case 'txt':
      return <FileText className="w-4 h-4 text-neutral-400 shrink-0" />;
    default:
      return <File className="w-4 h-4 text-neutral-400 shrink-0" />;
  }
}

interface TreeNodeProps {
  node: FileNode;
  level: number;
  activePath?: string | null;
  expandedFolders: Set<string>;
  toggleFolder: (path: string) => void;
  onSelectFile: (node: FileNode) => void;
  onRequestDelete: (path: string, e: React.MouseEvent) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level,
  activePath,
  expandedFolders,
  toggleFolder,
  onSelectFile,
  onRequestDelete,
}) => {
  const isDirectory = node.type === 'directory';
  const isExpanded = isDirectory && expandedFolders.has(node.path);
  const isActive = node.path === activePath;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDirectory) {
      toggleFolder(node.path);
    } else {
      onSelectFile(node);
    }
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleClick(e as unknown as React.MouseEvent);
          }
        }}
        style={{ paddingLeft: `${Math.max(8, level * 16)}px` }}
        className={`group flex items-center justify-between py-1 px-2 text-xs cursor-pointer select-none rounded transition-colors ${
          isActive
            ? 'bg-neutral-800 text-white font-medium'
            : 'text-neutral-300 hover:bg-neutral-800/60 hover:text-white'
        }`}
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isDirectory ? (
            <>
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-amber-300 shrink-0" />
              ) : (
                <Folder className="w-4 h-4 text-amber-400 shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5 h-3.5 shrink-0" />
              {getFileIcon(node.name)}
            </>
          )}
          <span className="truncate">{node.name}</span>
          {node.is_generated && (
            <span className="px-1 text-[9px] font-semibold tracking-wider text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 rounded">
              AI
            </span>
          )}
        </div>

        {!isDirectory && (
          <button
            type="button"
            title={`Delete ${node.name}`}
            onClick={(e) => onRequestDelete(node.path, e)}
            className="opacity-0 group-hover:opacity-100 p-0.5 text-neutral-400 hover:text-rose-400 transition-opacity rounded"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>

      {isDirectory && isExpanded && node.children && node.children.length > 0 && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              level={level + 1}
              activePath={activePath}
              expandedFolders={expandedFolders}
              toggleFolder={toggleFolder}
              onSelectFile={onSelectFile}
              onRequestDelete={onRequestDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileTree: React.FC<FileTreeProps> = ({
  tree,
  activePath,
  isLoading = false,
  onSelectFile,
  onCreateFile,
  onDeleteFile,
  onRefresh,
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    // Default expand all top-level directories
    const initial = new Set<string>();
    tree.forEach((node) => {
      if (node.type === 'directory') {
        initial.add(node.path);
      }
    });
    return initial;
  });

  const [isNewFileDialogOpen, setIsNewFileDialogOpen] = useState(false);
  const [newFilePath, setNewFilePath] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newFilePath.trim();
    if (trimmed && onCreateFile) {
      onCreateFile(trimmed);
      setNewFilePath('');
      setIsNewFileDialogOpen(false);
    }
  };

  const handleRequestDelete = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteTarget(path);
  };

  const handleConfirmDelete = () => {
    if (deleteTarget && onDeleteFile) {
      onDeleteFile(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-neutral-900/60 select-none">
      {/* File Tree Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-800 text-xs font-semibold text-neutral-400">
        <span className="uppercase tracking-wider">Explorer</span>
        <div className="flex items-center gap-1">
          {onCreateFile && (
            <button
              type="button"
              onClick={() => setIsNewFileDialogOpen(true)}
              title="New File"
              className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          )}
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              title="Refresh Tree"
              className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-1 py-2">
        {isLoading ? (
          <div className="p-3 space-y-2">
            <div className="h-4 bg-neutral-800 rounded animate-pulse w-3/4" />
            <div className="h-4 bg-neutral-800 rounded animate-pulse w-1/2 ml-4" />
            <div className="h-4 bg-neutral-800 rounded animate-pulse w-2/3 ml-4" />
          </div>
        ) : tree.length === 0 ? (
          <div className="p-4 text-center text-xs text-neutral-400">
            No files in workspace yet.
            {onCreateFile && (
              <button
                type="button"
                onClick={() => setIsNewFileDialogOpen(true)}
                className="mt-2 block mx-auto text-sky-400 hover:underline"
              >
                Create a file
              </button>
            )}
          </div>
        ) : (
          tree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              level={0}
              activePath={activePath}
              expandedFolders={expandedFolders}
              toggleFolder={toggleFolder}
              onSelectFile={onSelectFile}
              onRequestDelete={handleRequestDelete}
            />
          ))
        )}
      </div>

      {/* New File Modal */}
      {isNewFileDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-lg shadow-xl p-4">
            <h3 className="text-sm font-medium text-white mb-2">Create New File</h3>
            <form onSubmit={handleCreateSubmit} className="space-y-3">
              <div>
                <input
                  type="text"
                  autoFocus
                  placeholder="e.g. src/app.py"
                  value={newFilePath}
                  onChange={(e) => setNewFilePath(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-neutral-800 border border-neutral-700 rounded text-white focus:outline-none focus:border-sky-500"
                />
                <p className="mt-1 text-[11px] text-neutral-400">
                  Nested paths will create folders automatically.
                </p>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsNewFileDialogOpen(false)}
                  className="px-2.5 py-1 text-xs text-neutral-300 hover:bg-neutral-800 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newFilePath.trim()}
                  className="px-3 py-1 text-xs font-medium text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 rounded"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        title="Delete File"
        message={`Are you sure you want to permanently delete "${deleteTarget}"? This cannot be undone.`}
        confirmLabel="Delete"
        isDestructive
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
};
