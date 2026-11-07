import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

// Mock Monaco Editor component to avoid heavy canvas rendering in jsdom
vi.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, theme }: { value: string; theme: string }) => (
    <div data-testid="mock-monaco-editor" data-theme={theme}>
      <pre>{value}</pre>
    </div>
  ),
  loader: {
    config: vi.fn(),
  },
}));

describe('App Scaffold Component', () => {
  it('renders heading and scaffold info', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        status: 'healthy',
        model_loaded: true,
        model_name: 'qwen2.5-coder-3b-instruct-q4_k_m.gguf',
        load_time_seconds: 1.2,
        version: '0.1.0',
        paths: {
          workspace: 'workspace/',
          models: 'models/',
          data: 'data/',
          logs: 'logs/',
          reports: 'reports/',
        },
        last_error: null,
      }),
    } as Response);

    render(<App />);

    expect(screen.getByText('Ojas Platform')).toBeInTheDocument();
    expect(screen.getByText('Phase 6: Frontend Scaffold')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/healthy/i)).toBeInTheDocument();
    });

    expect(screen.getByTestId('mock-monaco-editor')).toBeInTheDocument();
  });
});

