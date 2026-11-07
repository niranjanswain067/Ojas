import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Folders,
  Code2,
  FileBarChart2,
  Settings as SettingsIcon,
  Sun,
  Moon,
  Laptop,
} from 'lucide-react';
import { apiGet } from '../../api/client';
import type { HealthResponse } from '../../api/types';
import { useTheme } from '../../app/providers';
import { StatusChip } from './StatusChip';

const NAV_ITEMS = [
  { label: 'Projects', to: '/projects', icon: Folders },
  { label: 'Workspace', to: '/workspace', icon: Code2 },
  { label: 'Reports', to: '/reports', icon: FileBarChart2 },
  { label: 'Settings', to: '/settings', icon: SettingsIcon },
];

export const AppShell: React.FC = () => {
  const { theme, setTheme } = useTheme();

  // Poll backend health every 30 seconds
  const { data: health, isError } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthResponse>('/health'),
    refetchInterval: 30000,
    retry: 1,
  });

  const nextTheme = () => {
    if (theme === 'dark') setTheme('light');
    else if (theme === 'light') setTheme('system');
    else setTheme('dark');
  };

  const getThemeIcon = () => {
    if (theme === 'dark') return <Moon className="w-3.5 h-3.5" />;
    if (theme === 'light') return <Sun className="w-3.5 h-3.5" />;
    return <Laptop className="w-3.5 h-3.5" />;
  };

  const getModelChip = () => {
    if (isError) {
      return (
        <StatusChip
          status="offline"
          label="Backend Offline"
          tooltip="Cannot reach http://127.0.0.1:8000/api/health"
        />
      );
    }
    if (!health) {
      return (
        <StatusChip
          status="idle"
          label="Checking..."
          tooltip="Connecting to backend health service..."
        />
      );
    }

    const modelLabel = health.model_name
      ? health.model_name.replace('.gguf', '')
      : 'No Model Loaded';

    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted hidden sm:inline" title={health.model_name}>
          Model: <strong className="text-text font-medium">{modelLabel}</strong>
        </span>
        <StatusChip
          status={health.status}
          label={health.status === 'healthy' ? 'Ready' : health.status}
          tooltip={`v${health.version} - Status: ${health.status}`}
        />
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col font-sans selection:bg-primary/20">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-border bg-surface flex items-center justify-between px-4 sm:px-6 z-10 sticky top-0 shadow-sm">
        {/* Left: Branding & Navigation */}
        <div className="flex items-center gap-6">
          <NavLink
            to="/projects"
            className="flex items-center gap-2.5 focus:outline-none group"
          >
            <div className="h-7 w-7 rounded-lg bg-primary text-white flex items-center justify-center font-bold text-sm shadow-sm group-hover:opacity-90 transition-opacity">
              O
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight leading-none text-text">
                Ojas
              </span>
              <span className="text-[10px] text-muted leading-tight font-medium">
                Autonomous Dev
              </span>
            </div>
          </NavLink>

          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-primary/10 text-primary dark:text-primary font-semibold'
                      : 'text-muted hover:text-text hover:bg-border/30'
                  }`
                }
              >
                <item.icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right: Health Status & Theme Switcher */}
        <div className="flex items-center gap-3">
          {getModelChip()}

          <div className="h-4 w-px bg-border mx-1" />

          <button
            type="button"
            onClick={nextTheme}
            title={`Current theme: ${theme} (click to toggle)`}
            className="p-1.5 rounded-lg border border-border bg-surface hover:bg-border/40 text-muted hover:text-text transition-colors flex items-center gap-1 text-xs"
          >
            {getThemeIcon()}
            <span className="capitalize text-[11px] hidden md:inline">{theme}</span>
          </button>
        </div>
      </header>

      {/* Main Outlet */}
      <main className="flex-1 flex flex-col p-6 max-w-7xl w-full mx-auto">
        <Outlet />
      </main>
    </div>
  );
};

