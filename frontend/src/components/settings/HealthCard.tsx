import React, { useState } from "react";
import {
  Activity,
  Folder,
  RefreshCw,
  AlertCircle,
  Cpu,
  Clock,
  Layers,
} from "lucide-react";
import type { HealthResponse } from "../../api/types";
import { StatusChip } from "../shared/StatusChip";

interface HealthCardProps {
  health: HealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const HealthCard: React.FC<HealthCardProps> = ({
  health,
  loading,
  onRefresh,
}) => {
  const [showPaths, setShowPaths] = useState(false);

  return (
    <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#D5DBE3] dark:border-[#2D3541]">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
          <h3 className="font-semibold text-sm text-[#1B2430] dark:text-[#E6EAF0]">
            System Health & Model Status
          </h3>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 rounded-md text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-white dark:hover:bg-gray-800 transition disabled:opacity-50"
          title="Refresh health status"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {health ? (
        <div className="space-y-3">
          {/* Main Status Row */}
          <div className="flex items-center justify-between bg-white dark:bg-[#14181F] p-3 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541]">
            <span className="text-xs font-medium text-[#5F6B7A] dark:text-[#98A3B3]">
              Backend Status
            </span>
            <StatusChip
              status={health.status}
              label={
                health.model_loaded
                  ? "Model Ready"
                  : health.status === "degraded"
                  ? "Degraded (No Model)"
                  : "Error"
              }
            />
          </div>

          {/* Model Details */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-white dark:bg-[#14181F] p-2.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] flex items-center gap-2">
              <Cpu size={15} className="text-gray-400 shrink-0" />
              <div className="overflow-hidden">
                <span className="text-[10px] uppercase text-[#5F6B7A] dark:text-[#98A3B3] block">
                  Model Name
                </span>
                <span className="font-mono text-[#1B2430] dark:text-[#E6EAF0] truncate block">
                  {health.model_name || "None loaded"}
                </span>
              </div>
            </div>

            <div className="bg-white dark:bg-[#14181F] p-2.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] flex items-center gap-2">
              <Clock size={15} className="text-gray-400 shrink-0" />
              <div>
                <span className="text-[10px] uppercase text-[#5F6B7A] dark:text-[#98A3B3] block">
                  Load Time
                </span>
                <span className="font-mono text-[#1B2430] dark:text-[#E6EAF0]">
                  {health.load_time_seconds > 0
                    ? `${health.load_time_seconds.toFixed(2)}s`
                    : "—"}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-[#14181F] p-2.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-gray-400" />
              <span className="text-[#5F6B7A] dark:text-[#98A3B3]">Application Version</span>
            </div>
            <span className="font-mono font-medium text-[#1B2430] dark:text-[#E6EAF0]">
              v{health.version}
            </span>
          </div>

          {/* Last Error Banner if present */}
          {health.last_error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-medium text-red-700 dark:text-red-400">
                <AlertCircle size={14} />
                <span>Last Error</span>
              </div>
              <p className="font-mono text-[11px] text-red-600 dark:text-red-300 break-words">
                {health.last_error}
              </p>
            </div>
          )}

          {/* Collapsible Paths */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowPaths(!showPaths)}
              className="flex items-center gap-1 text-xs text-[#1F3A5F] dark:text-[#6FA0E0] hover:underline"
            >
              <Folder size={12} />
              <span>{showPaths ? "Hide Storage Paths" : "View Storage Paths"}</span>
            </button>

            {showPaths && (
              <div className="mt-2 p-2.5 bg-white dark:bg-[#14181F] rounded-lg border border-[#D5DBE3] dark:border-[#2D3541] text-[11px] space-y-1 font-mono text-[#5F6B7A] dark:text-[#98A3B3]">
                <div><strong className="text-[#1B2430] dark:text-[#E6EAF0]">Workspace:</strong> {health.paths.workspace}</div>
                <div><strong className="text-[#1B2430] dark:text-[#E6EAF0]">Models:</strong> {health.paths.models}</div>
                <div><strong className="text-[#1B2430] dark:text-[#E6EAF0]">Data:</strong> {health.paths.data}</div>
                <div><strong className="text-[#1B2430] dark:text-[#E6EAF0]">Logs:</strong> {health.paths.logs}</div>
                <div><strong className="text-[#1B2430] dark:text-[#E6EAF0]">Reports:</strong> {health.paths.reports}</div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-6 text-xs text-[#5F6B7A] dark:text-[#98A3B3]">
          {loading ? "Checking system health…" : "Unable to load health status."}
        </div>
      )}
    </div>
  );
};

