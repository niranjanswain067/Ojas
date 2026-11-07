import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Polyfill window.matchMedia for JSDOM
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Polyfill Worker for JSDOM
class MockWorker {
  url: string;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  postMessage: (msg: unknown) => void = vi.fn();
  terminate: () => void = vi.fn();
  addEventListener: () => void = vi.fn();
  removeEventListener: () => void = vi.fn();
  dispatchEvent: () => boolean = vi.fn();

  constructor(url: string) {
    this.url = url;
  }
}

globalThis.Worker = MockWorker as unknown as typeof Worker;
