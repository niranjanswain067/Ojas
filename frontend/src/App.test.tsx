import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Providers } from './app/providers';
import { AppShell } from './components/shared/AppShell';
import { ProjectsPage } from './pages/ProjectsPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

function TestApp({ initialEntry = '/' }: { initialEntry?: string }) {
  return (
    <Providers>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Navigate to="/projects" replace />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="workspace" element={<WorkspacePage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/projects" replace />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </Providers>
  );
}

describe('App Navigation and Shell', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders top navigation and defaults to Projects page', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
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

    render(<TestApp initialEntry="/" />);

    // Verify branding and logo
    expect(screen.getByText('Ojas')).toBeInTheDocument();
    expect(screen.getByText('Autonomous Dev')).toBeInTheDocument();

    // Verify nav links
    expect(screen.getByRole('link', { name: /projects/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /workspace/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /reports/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();

    // Default route redirects to /projects
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Projects' })).toBeInTheDocument();
    });

    // Verify model health chip
    await waitFor(() => {
      expect(screen.getByText('Ready')).toBeInTheDocument();
      expect(screen.getByText('qwen2.5-coder-3b-instruct-q4_k_m')).toBeInTheDocument();
    });
  });

  it('navigates between routes on link click', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        status: 'healthy',
        model_loaded: false,
        model_name: '',
        load_time_seconds: 0,
        version: '0.1.0',
        paths: { workspace: '', models: '', data: '', logs: '', reports: '' },
        last_error: null,
      }),
    } as Response);

    render(<TestApp initialEntry="/projects" />);

    // Initial page is Projects
    expect(await screen.findByRole('heading', { level: 1, name: 'Projects' })).toBeInTheDocument();

    // Navigate to Workspace
    fireEvent.click(screen.getByRole('link', { name: /workspace/i }));
    expect(await screen.findByRole('heading', { level: 1, name: 'Workspace' })).toBeInTheDocument();

    // Navigate to Reports
    fireEvent.click(screen.getByRole('link', { name: /reports/i }));
    expect(await screen.findByRole('heading', { level: 1, name: 'Reports' })).toBeInTheDocument();

    // Navigate to Settings
    fireEvent.click(screen.getByRole('link', { name: /settings/i }));
    expect(await screen.findByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
  });
});
