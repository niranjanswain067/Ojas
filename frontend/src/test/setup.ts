import '@testing-library/jest-dom';
import { vi, beforeEach } from 'vitest';

export function setupMatchMedia() {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
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
}

setupMatchMedia();

beforeEach(() => {
  setupMatchMedia();
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

// Synchronize AbortController and AbortSignal across JSDOM and Node global
if (typeof globalThis.AbortController !== 'undefined') {
  window.AbortController = globalThis.AbortController;
}
if (typeof globalThis.AbortSignal !== 'undefined') {
  window.AbortSignal = globalThis.AbortSignal;
}
if (typeof globalThis.Request !== 'undefined') {
  window.Request = globalThis.Request;
  window.Response = globalThis.Response;
  window.Headers = globalThis.Headers;
}
