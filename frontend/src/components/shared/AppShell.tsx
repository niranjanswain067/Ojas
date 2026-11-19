import React, { useEffect, useState } from "react";
import { FolderGit2, Code2, FileText, Settings as SettingsIcon, Terminal } from "lucide-react";
import { StatusChip } from "./StatusChip";
import { HealthResponse } from "../../api/types";
import { getHealth } from "../../api/settings";

interface AppShellProps {
  children: React.ReactNode;
  activeTab?: "projects" | "workspace" | "reports" | "settings";
  onTabChange?: (tab: "projects" | "workspace" | "reports" | "settings") => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeTab = "settings",
  onTabChange,
}) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => {});
  }, []);

  const navItems = [
    { id: "projects", label: "Projects", icon: FolderGit2 },
    { id: "workspace", label: "Workspace", icon: Code2 },
    { id: "reports", label: "Reports", icon: FileText },
    { id: "settings", label: "Settings", icon: SettingsIcon },
  ] as const;

  return (
    <div className="min-h-screen bg-[#FFFFFF] dark:bg-[#14181F] text-[#1B2430] dark:text-[#E6EAF0] flex flex-col transition-colors duration-200">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-[#D5DBE3] dark:border-[#2D3541] bg-[#F5F7FA] dark:bg-[#1C222B] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-6">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#1F3A5F] dark:bg-[#6FA0E0] text-white dark:text-[#14181F] flex items-center justify-center font-bold text-sm shadow-sm">
              O
            </div>
            <span className="font-bold text-base tracking-tight text-[#1B2430] dark:text-[#E6EAF0]">
              Ojas
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {navItems.map(({ id, label, icon: Icon }) => {
              const isActive = activeTab === id;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => onTabChange && onTabChange(id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-[#1F3A5F] text-white dark:bg-[#6FA0E0] dark:text-[#14181F] shadow-sm"
                      : "text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-gray-200/60 dark:hover:bg-gray-800"
                  }`}
                >
                  <Icon size={14} />
                  <span>{label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Status chip */}
        <div className="flex items-center gap-3">
          <StatusChip
            status={
              health
                ? health.model_loaded
                  ? "healthy"
                  : health.status
                : "loading"
            }
            label={
              health
                ? health.model_loaded
                  ? "Model: Ready"
                  : "Model: Not Loaded"
                : "Checking Model…"
            }
            size="sm"
          />
        </div>
      </header>

      {/* Main Page Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* Offline Footer Indicator */}
      <footer className="h-7 border-t border-[#D5DBE3] dark:border-[#2D3541] bg-[#F5F7FA] dark:bg-[#1C222B] px-4 flex items-center justify-between text-[11px] text-[#5F6B7A] dark:text-[#98A3B3]">
        <div className="flex items-center gap-1.5">
          <Terminal size={12} />
          <span>Local CPU Offline Environment</span>
        </div>
        <div>
          <span>Bound to 127.0.0.1</span>
        </div>
      </footer>
    </div>
  );
};

