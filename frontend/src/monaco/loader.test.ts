import { describe, it, expect } from 'vitest';
import { initMonaco } from './loader';

describe('Monaco Loader Offline Setup', () => {
  it('initializes monaco with local offline configuration', () => {
    const monacoInstance = initMonaco();
    expect(monacoInstance).toBeDefined();
    expect(window.MonacoEnvironment).toBeDefined();
    expect(typeof window.MonacoEnvironment?.getWorker).toBe('function');
  });

  it('provides workers for supported editor languages', () => {
    initMonaco();
    const getWorker = window.MonacoEnvironment!.getWorker;

    // Verify worker instantiation works for all requested labels
    const jsonWorkerInstance = getWorker(null, 'json');
    expect(jsonWorkerInstance).toBeDefined();

    const editorWorkerInstance = getWorker(null, 'python');
    expect(editorWorkerInstance).toBeDefined();

    const tsWorkerInstance = getWorker(null, 'typescript');
    expect(tsWorkerInstance).toBeDefined();
  });
});

