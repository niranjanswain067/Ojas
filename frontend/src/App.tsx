import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { apiGet } from './api/client';
import type { HealthResponse } from './api/types';
import './monaco/loader'; // ensure offline Monaco setup is registered

const SAMPLE_PYTHON_CODE = `# Ojas: Autonomous Local AI Development Platform
# Generated sample code verification for Phase 6

def calculate_fibonacci(n: int) -> list[int]:
    """Return the first n Fibonacci numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


if __name__ == "__main__":
    print("Fibonacci(10):", calculate_fibonacci(10))
`;

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'ojas-dark' | 'ojas-light'>('ojas-dark');
  const [code, setCode] = useState<string>(SAMPLE_PYTHON_CODE);

  useEffect(() => {
    // Check dark mode on document element
    if (theme === 'ojas-dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    async function checkHealth() {
      try {
        setLoading(true);
        const data = await apiGet<HealthResponse>('/health');
        setHealth(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to reach backend');
      } finally {
        setLoading(false);
      }
    }

    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-bg text-text transition-colors duration-200">
      {/* Header */}
      <header className="border-b border-border bg-surface px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-lg shadow-sm">
            O
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Ojas Platform</h1>
            <p className="text-xs text-muted">Phase 6: Frontend Scaffold</p>
          </div>
        </div>

        {/* Controls and Status */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-muted font-medium">Backend:</span>
            {loading ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-500">
                Checking...
              </span>
            ) : health ? (
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  health.status === 'healthy'
                    ? 'bg-emerald-500/20 text-emerald-500'
                    : 'bg-amber-500/20 text-amber-500'
                }`}
              >
                ● {health.status} (v{health.version})
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/20 text-rose-500">
                Offline
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => setTheme((prev) => (prev === 'ojas-dark' ? 'ojas-light' : 'ojas-dark'))}
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-surface hover:bg-border/30 transition-colors"
          >
            {theme === 'ojas-dark' ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Verification Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Vite + React</span>
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-lg font-semibold">React 18 + TS</p>
            <p className="text-xs text-muted">Fast HMR and TypeScript bundling configured</p>
          </div>

          <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Backend Proxy</span>
              <span className={`h-2 w-2 rounded-full ${health ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            </div>
            <p className="text-lg font-semibold">{health ? 'Connected' : 'Target :8000'}</p>
            <p className="text-xs text-muted">
              {error ? error : health ? `Model: ${health.model_name || 'Qwen2.5-Coder'}` : 'Vite proxy routing to /api'}
            </p>
          </div>

          <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">Monaco Editor</span>
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
            </div>
            <p className="text-lg font-semibold">100% Offline</p>
            <p className="text-xs text-muted">Vite workers bundled, zero CDN dependencies</p>
          </div>
        </div>

        {/* Monaco Editor Section */}
        <div className="rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-bg/50">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-medium text-muted">workspace/sample.py</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary font-mono">Python</span>
            </div>
            <span className="text-xs text-muted">Monaco Editor Offline Test</span>
          </div>

          <div className="h-96">
            <Editor
              height="100%"
              defaultLanguage="python"
              theme={theme}
              value={code}
              onChange={(val) => setCode(val ?? '')}
              options={{
                automaticLayout: true,
                minimap: { enabled: false },
                wordWrap: 'off',
                scrollBeyondLastLine: false,
                fontSize: 14,
                fontFamily: 'Consolas, Menlo, Monaco, "Courier New", monospace',
              }}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
