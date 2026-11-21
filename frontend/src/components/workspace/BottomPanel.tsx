/**
 * BottomPanel component for Ojas Workspace.
 * Hosts tabs for live execution Logs, Test results, Bug reports, and Model output.
 */

import React from 'react';
import { Terminal, CheckCircle2, AlertTriangle, Cpu, ChevronUp, ChevronDown } from 'lucide-react';
import type { BottomPanelTab } from '../../store/uiStore';
import { useRunStore } from '../../store/runStore';
import { LogView } from './LogView';

interface BottomPanelProps {
  currentTab: BottomPanelTab;
  onTabChange: (tab: BottomPanelTab) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  logs?: Array<{ timestamp: string; message: string; level?: 'info' | 'warn' | 'error' }>;
}

export const BottomPanel: React.FC<BottomPanelProps> = ({
  currentTab,
  onTabChange,
  isOpen,
  onToggleOpen,
  logs: propLogs,
}) => {
  const storeLogs = useRunStore((s) => s.logs);
  const logs = propLogs || storeLogs;
  return (
    <div className="flex flex-col h-full bg-neutral-950 border-t border-neutral-800 text-neutral-300 overflow-hidden select-none">
      {/* Panel Tab Header */}
      <div className="flex items-center justify-between px-2 bg-neutral-900 border-b border-neutral-800 h-9">
        <div className="flex items-center gap-1 h-full">
          <button
            type="button"
            onClick={() => onTabChange('logs')}
            className={`flex items-center gap-1.5 px-3 h-full text-xs font-medium border-b-2 transition-colors ${
              currentTab === 'logs'
                ? 'border-sky-500 text-white bg-neutral-800/60'
                : 'border-transparent text-neutral-400 hover:text-white'
            }`}
          >
            <Terminal className="w-3.5 h-3.5 text-sky-400" />
            <span>Logs</span>
          </button>

          <button
            type="button"
            onClick={() => onTabChange('tests')}
            className={`flex items-center gap-1.5 px-3 h-full text-xs font-medium border-b-2 transition-colors ${
              currentTab === 'tests'
                ? 'border-emerald-500 text-white bg-neutral-800/60'
                : 'border-transparent text-neutral-400 hover:text-white'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Test Results</span>
          </button>

          <button
            type="button"
            onClick={() => onTabChange('bugs')}
            className={`flex items-center gap-1.5 px-3 h-full text-xs font-medium border-b-2 transition-colors ${
              currentTab === 'bugs'
                ? 'border-rose-500 text-white bg-neutral-800/60'
                : 'border-transparent text-neutral-400 hover:text-white'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>Bug Reports</span>
          </button>

          <button
            type="button"
            onClick={() => onTabChange('model')}
            className={`flex items-center gap-1.5 px-3 h-full text-xs font-medium border-b-2 transition-colors ${
              currentTab === 'model'
                ? 'border-amber-500 text-white bg-neutral-800/60'
                : 'border-transparent text-neutral-400 hover:text-white'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            <span>Model Output</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onToggleOpen}
          title={isOpen ? 'Collapse Bottom Panel' : 'Expand Bottom Panel'}
          className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
        >
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {/* Panel Content (Visible when open) */}
      {isOpen && (
        <div className="flex-1 overflow-y-auto p-2.5 font-mono text-xs">
          {currentTab === 'logs' && <LogView logs={logs} />}

          {currentTab === 'tests' && (
            <div className="text-center py-6 text-neutral-400">
              <CheckCircle2 className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
              <p>No tests have been executed yet.</p>
              <p className="text-[11px] text-neutral-400 mt-0.5">
                Click "Test" in the right panel to execute pytest test suites.
              </p>
            </div>
          )}

          {currentTab === 'bugs' && (
            <div className="text-center py-6 text-neutral-400">
              <AlertTriangle className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
              <p>No bugs currently reported.</p>
            </div>
          )}

          {currentTab === 'model' && (
            <div className="text-center py-6 text-neutral-400">
              <Cpu className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
              <p>Raw model output will stream here during generation.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
