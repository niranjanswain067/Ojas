/**
 * Zustand UI Store for Ojas Workspace state.
 * Manages open editor tabs, active file, sidebar tab, and bottom panel state.
 */

import { create } from 'zustand';

export interface OpenFile {
  path: string;
  name: string;
  language: string;
  content: string;
  originalContent: string;
  isDirty: boolean;
  isGenerated?: boolean;
}

export type SidebarTab = 'docs' | 'code' | 'tests';
export type BottomPanelTab = 'logs' | 'tests' | 'bugs' | 'model';

export interface UIState {
  openFiles: OpenFile[];
  activeFilePath: string | null;
  sidebarTab: SidebarTab;
  bottomPanelTab: BottomPanelTab;
  isBottomPanelOpen: boolean;

  // Actions
  openFile: (file: {
    path: string;
    name: string;
    language: string;
    content: string;
    isGenerated?: boolean;
  }) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string) => void;
  updateFileContent: (path: string, content: string) => void;
  markFileSaved: (path: string, newContent?: string) => void;
  setSidebarTab: (tab: SidebarTab) => void;
  setBottomPanelTab: (tab: BottomPanelTab) => void;
  toggleBottomPanel: () => void;
  setBottomPanelOpen: (open: boolean) => void;
  closeAllFiles: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  openFiles: [],
  activeFilePath: null,
  sidebarTab: 'code',
  bottomPanelTab: 'logs',
  isBottomPanelOpen: true,

  openFile: (file) => {
    const { openFiles } = get();
    const existing = openFiles.find((f) => f.path === file.path);

    if (existing) {
      set({ activeFilePath: file.path });
      return;
    }

    const newOpenFile: OpenFile = {
      path: file.path,
      name: file.name,
      language: file.language,
      content: file.content,
      originalContent: file.content,
      isDirty: false,
      isGenerated: file.isGenerated ?? false,
    };

    set({
      openFiles: [...openFiles, newOpenFile],
      activeFilePath: file.path,
    });
  },

  closeFile: (path: string) => {
    const { openFiles, activeFilePath } = get();
    const remaining = openFiles.filter((f) => f.path !== path);

    let nextActive = activeFilePath;
    if (activeFilePath === path) {
      if (remaining.length > 0) {
        // Activate adjacent tab (previous if exists, else next)
        const closedIndex = openFiles.findIndex((f) => f.path === path);
        const newIndex = Math.max(0, closedIndex - 1);
        nextActive = remaining[newIndex]?.path ?? remaining[0].path;
      } else {
        nextActive = null;
      }
    }

    set({
      openFiles: remaining,
      activeFilePath: nextActive,
    });
  },

  setActiveFile: (path: string) => {
    set({ activeFilePath: path });
  },

  updateFileContent: (path: string, content: string) => {
    const { openFiles } = get();
    set({
      openFiles: openFiles.map((f) => {
        if (f.path === path) {
          return {
            ...f,
            content,
            isDirty: content !== f.originalContent,
          };
        }
        return f;
      }),
    });
  },

  markFileSaved: (path: string, newContent?: string) => {
    const { openFiles } = get();
    set({
      openFiles: openFiles.map((f) => {
        if (f.path === path) {
          const contentToSet = newContent !== undefined ? newContent : f.content;
          return {
            ...f,
            content: contentToSet,
            originalContent: contentToSet,
            isDirty: false,
          };
        }
        return f;
      }),
    });
  },

  setSidebarTab: (tab: SidebarTab) => {
    set({ sidebarTab: tab });
  },

  setBottomPanelTab: (tab: BottomPanelTab) => {
    set({ bottomPanelTab: tab, isBottomPanelOpen: true });
  },

  toggleBottomPanel: () => {
    set((state) => ({ isBottomPanelOpen: !state.isBottomPanelOpen }));
  },

  setBottomPanelOpen: (open: boolean) => {
    set({ isBottomPanelOpen: open });
  },

  closeAllFiles: () => {
    set({ openFiles: [], activeFilePath: null });
  },
}));
