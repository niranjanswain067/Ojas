import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from './uiStore';

describe('useUIStore', () => {
  beforeEach(() => {
    useUIStore.getState().closeAllFiles();
    useUIStore.getState().setSidebarTab('code');
    useUIStore.getState().setBottomPanelTab('logs');
    useUIStore.getState().setBottomPanelOpen(true);
  });

  it('initializes with empty files and active state', () => {
    const state = useUIStore.getState();
    expect(state.openFiles).toEqual([]);
    expect(state.activeFilePath).toBeNull();
    expect(state.sidebarTab).toBe('code');
    expect(state.bottomPanelTab).toBe('logs');
    expect(state.isBottomPanelOpen).toBe(true);
  });

  it('opens a file and sets it active', () => {
    useUIStore.getState().openFile({
      path: 'src/main.py',
      name: 'main.py',
      language: 'python',
      content: 'print("hello")',
      isGenerated: true,
    });

    const state = useUIStore.getState();
    expect(state.openFiles.length).toBe(1);
    expect(state.openFiles[0].path).toBe('src/main.py');
    expect(state.openFiles[0].isDirty).toBe(false);
    expect(state.openFiles[0].isGenerated).toBe(true);
    expect(state.activeFilePath).toBe('src/main.py');
  });

  it('does not duplicate files if already opened, only activates it', () => {
    const file = {
      path: 'src/main.py',
      name: 'main.py',
      language: 'python',
      content: 'print("hello")',
    };

    useUIStore.getState().openFile(file);
    useUIStore.getState().openFile({
      path: 'src/utils.py',
      name: 'utils.py',
      language: 'python',
      content: 'def util(): pass',
    });

    expect(useUIStore.getState().openFiles.length).toBe(2);
    expect(useUIStore.getState().activeFilePath).toBe('src/utils.py');

    // Re-open first file
    useUIStore.getState().openFile(file);
    expect(useUIStore.getState().openFiles.length).toBe(2);
    expect(useUIStore.getState().activeFilePath).toBe('src/main.py');
  });

  it('updates file content and marks dirty', () => {
    useUIStore.getState().openFile({
      path: 'app.py',
      name: 'app.py',
      language: 'python',
      content: 'initial',
    });

    useUIStore.getState().updateFileContent('app.py', 'modified content');
    const state = useUIStore.getState();
    expect(state.openFiles[0].content).toBe('modified content');
    expect(state.openFiles[0].isDirty).toBe(true);

    // Saving clears dirty flag
    useUIStore.getState().markFileSaved('app.py');
    expect(useUIStore.getState().openFiles[0].isDirty).toBe(false);
  });

  it('closes a file and updates activeFilePath', () => {
    useUIStore.getState().openFile({
      path: 'file1.py',
      name: 'file1.py',
      language: 'python',
      content: '',
    });
    useUIStore.getState().openFile({
      path: 'file2.py',
      name: 'file2.py',
      language: 'python',
      content: '',
    });

    expect(useUIStore.getState().activeFilePath).toBe('file2.py');

    // Close active file2 -> file1 becomes active
    useUIStore.getState().closeFile('file2.py');
    expect(useUIStore.getState().openFiles.length).toBe(1);
    expect(useUIStore.getState().activeFilePath).toBe('file1.py');

    // Close file1 -> active becomes null
    useUIStore.getState().closeFile('file1.py');
    expect(useUIStore.getState().openFiles.length).toBe(0);
    expect(useUIStore.getState().activeFilePath).toBeNull();
  });

  it('toggles tabs and bottom panel', () => {
    useUIStore.getState().setSidebarTab('docs');
    expect(useUIStore.getState().sidebarTab).toBe('docs');

    useUIStore.getState().setBottomPanelTab('tests');
    expect(useUIStore.getState().bottomPanelTab).toBe('tests');
    expect(useUIStore.getState().isBottomPanelOpen).toBe(true);

    useUIStore.getState().toggleBottomPanel();
    expect(useUIStore.getState().isBottomPanelOpen).toBe(false);
  });
});
