/**
 * Main WorkspacePage component for Ojas.
 * Hosts the 4-panel resizable layout:
 *   1. Left Sidebar (Docs, Code, Tests) with recursive FileTree
 *   2. Center Top: EditorTabs + Monaco CodeEditor
 *   3. Center Bottom: BottomPanel (Logs, Tests, Bugs, Model)
 *   4. Right: RunPanel (Prompt, Plan, Develop, Test, Fix loop)
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Code2, ArrowRight, Download, Loader2 } from 'lucide-react';

import { getProject, downloadProjectZip } from '../api/projects';
import { getFileTree, getFileContent, saveFile, deleteFile } from '../api/files';
import type { FileNode } from '../api/types';
import { useUIStore } from '../store/uiStore';
import { useRunStore } from '../store/runStore';

import { Sidebar } from '../components/workspace/Sidebar';
import { EditorTabs } from '../components/editor/EditorTabs';
import { CodeEditor } from '../components/editor/CodeEditor';
import { DiffEditorView } from '../components/editor/DiffEditorView';
import { RunPanel } from '../components/workspace/RunPanel';
import { BottomPanel } from '../components/workspace/BottomPanel';
import { EmptyState } from '../components/shared/EmptyState';

export const WorkspacePage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // Run store state
  const { diffData, setDiffData } = useRunStore();

  const handleDownloadProject = async () => {
    if (!projectId || isDownloading) return;
    setIsDownloading(true);
    try {
      await downloadProjectZip(projectId, project?.name);
    } catch (err) {
      console.error('Failed to download project:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  // UI state from Zustand
  const {
    openFiles,
    activeFilePath,
    sidebarTab,
    bottomPanelTab,
    isBottomPanelOpen,
    openFile,
    closeFile,
    setActiveFile,
    updateFileContent,
    markFileSaved,
    setSidebarTab,
    setBottomPanelTab,
    toggleBottomPanel,
  } = useUIStore();

  // Fetch project details
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: Boolean(projectId),
  });

  // Fetch workspace file tree
  const {
    data: fileTreeData,
    isLoading: isLoadingFiles,
    refetch: refetchFiles,
  } = useQuery({
    queryKey: ['files', projectId],
    queryFn: () => getFileTree(projectId!),
    enabled: Boolean(projectId),
  });

  if (!projectId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold tracking-tight text-white mb-6">Workspace</h1>
        <EmptyState
          icon={Code2}
          title="No project selected"
          description="Open a project from the Projects dashboard to launch its workspace editor."
          action={{
            label: 'Go to Projects',
            icon: ArrowRight,
            onClick: () => navigate('/projects'),
          }}
        />
      </div>
    );
  }

  const activeFile = openFiles.find((f) => f.path === activeFilePath) ?? null;

  // Handle clicking a file in FileTree
  const handleSelectFile = async (node: FileNode) => {
    if (node.type === 'directory') return;

    const alreadyOpen = openFiles.find((f) => f.path === node.path);
    if (alreadyOpen) {
      setActiveFile(node.path);
      return;
    }

    try {
      const fileData = await getFileContent(projectId, node.path);
      openFile({
        path: node.path,
        name: node.name,
        language: fileData.language,
        content: fileData.content,
        isGenerated: fileData.is_generated,
      });
    } catch {
      // In case of error reading file
    }
  };

  // Handle selecting a test or bug to view in editor
  const handleSelectTestOrBug = async (filePath: string, _functionName?: string | null) => {
    const alreadyOpen = openFiles.find((f) => f.path === filePath);
    if (alreadyOpen) {
      setActiveFile(filePath);
      return;
    }

    try {
      const fileData = await getFileContent(projectId, filePath);
      openFile({
        path: filePath,
        name: filePath.split('/').pop() || filePath,
        language: fileData.language,
        content: fileData.content,
        isGenerated: fileData.is_generated,
      });
    } catch {
      // Handled gracefully
    }
  };

  // Handle creating a new file
  const handleCreateFile = async (filePath: string) => {
    try {
      await saveFile(projectId, filePath, '');
      await queryClient.invalidateQueries({ queryKey: ['files', projectId] });
      const filename = filePath.split('/').pop() || filePath;
      openFile({
        path: filePath,
        name: filename,
        language: 'plaintext',
        content: '',
      });
    } catch {
      // File creation error handled gracefully
    }
  };

  // Handle deleting a file
  const handleDeleteFile = async (filePath: string) => {
    try {
      await deleteFile(projectId, filePath);
      closeFile(filePath);
      await queryClient.invalidateQueries({ queryKey: ['files', projectId] });
    } catch {
      // File deletion error handled gracefully
    }
  };

  // Handle saving the currently active file
  const handleSaveActiveFile = async () => {
    if (!activeFile || isSaving) return;

    setIsSaving(true);
    try {
      await saveFile(projectId, activeFile.path, activeFile.content);
      markFileSaved(activeFile.path);
      await queryClient.invalidateQueries({ queryKey: ['files', projectId] });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-neutral-950 overflow-hidden">
      {/* Workspace Top Mini-Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-neutral-900 border-b border-neutral-800 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">
            {project?.name || 'Workspace'}
          </span>
          {project?.description && (
            <span className="text-neutral-400 truncate max-w-md hidden sm:inline">
              — {project.description}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleDownloadProject}
            disabled={isDownloading}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white rounded transition-colors disabled:opacity-50"
            title="Download project code as ZIP folder"
            aria-label="Download project"
          >
            {isDownloading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 text-sky-400" />
            )}
            <span>Download Project</span>
          </button>
        </div>
      </div>

      {/* 4-Panel Resizable Workspace Layout */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" autoSaveId={`ojas-ws-h-${projectId}`}>
          {/* Left Panel: Sidebar (Tabs: Docs, Code, Tests) */}
          <Panel defaultSize={20} minSize={15} maxSize={35}>
            <Sidebar
              projectId={projectId}
              currentTab={sidebarTab}
              onTabChange={setSidebarTab}
              fileTree={fileTreeData?.tree ?? []}
              activeFilePath={activeFilePath}
              isLoadingFiles={isLoadingFiles}
              onSelectFile={handleSelectFile}
              onSelectTest={handleSelectTestOrBug}
              onCreateFile={handleCreateFile}
              onDeleteFile={handleDeleteFile}
              onRefreshFiles={() => refetchFiles()}
            />
          </Panel>

          <PanelResizeHandle className="w-1 bg-neutral-800 hover:bg-sky-500/80 active:bg-sky-500 transition-colors cursor-col-resize select-none" />

          {/* Center Panel: Editor + Bottom Panel */}
          <Panel defaultSize={55} minSize={30}>
            <PanelGroup direction="vertical" autoSaveId={`ojas-ws-v-${projectId}`}>
              {/* Top Center: Tabs + Monaco Editor */}
              <Panel defaultSize={isBottomPanelOpen ? 70 : 100} minSize={30}>
                <div className="flex flex-col h-full bg-neutral-900">
                  <EditorTabs
                    files={openFiles}
                    activeFilePath={activeFilePath}
                    onSelectTab={setActiveFile}
                    onCloseTab={closeFile}
                  />
                  <div className="flex-1 overflow-hidden">
                    {diffData ? (
                      <DiffEditorView
                        original={diffData.original}
                        modified={diffData.modified}
                        filePath={diffData.filePath}
                        onAccept={async () => {
                          try {
                            await saveFile(projectId, diffData.filePath, diffData.modified);
                            updateFileContent(diffData.filePath, diffData.modified);
                            markFileSaved(diffData.filePath);
                            await queryClient.invalidateQueries({ queryKey: ['files', projectId] });
                          } finally {
                            setDiffData(null);
                          }
                        }}
                        onReject={() => setDiffData(null)}
                        onClose={() => setDiffData(null)}
                      />
                    ) : (
                      <CodeEditor
                        activeFile={activeFile}
                        onChangeContent={(content) =>
                          activeFile && updateFileContent(activeFile.path, content)
                        }
                        onSaveFile={handleSaveActiveFile}
                        isSaving={isSaving}
                      />
                    )}
                  </div>
                </div>
              </Panel>

              <PanelResizeHandle className="h-1 bg-neutral-800 hover:bg-sky-500/80 active:bg-sky-500 transition-colors cursor-row-resize select-none" />

              {/* Bottom Center: Logs, Test Results, Bugs, Model Output */}
              <Panel
                defaultSize={30}
                minSize={8}
                collapsible
                collapsedSize={0}
              >
                <BottomPanel
                  projectId={projectId}
                  currentTab={bottomPanelTab}
                  onTabChange={setBottomPanelTab}
                  isOpen={isBottomPanelOpen}
                  onToggleOpen={toggleBottomPanel}
                  onSelectBug={handleSelectTestOrBug}
                />
              </Panel>
            </PanelGroup>
          </Panel>

          <PanelResizeHandle className="w-1 bg-neutral-800 hover:bg-sky-500/80 active:bg-sky-500 transition-colors cursor-col-resize select-none" />

          {/* Right Panel: Agent Execution Run Panel */}
          <Panel defaultSize={25} minSize={18} maxSize={35}>
            <RunPanel projectId={projectId} />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
};
