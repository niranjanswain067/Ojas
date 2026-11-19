import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Loader2 } from "lucide-react";

export type StatusChipVariant = "healthy" | "degraded" | "error" | "loading" | "idle";

interface StatusChipProps {
  status: StatusChipVariant | string;
  label?: string;
  size?: "sm" | "md";
}

export const StatusChip: React.FC<StatusChipProps> = ({
  status,
  label,
  size = "md",
}) => {
  let displayLabel = label;
  let bgClass = "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-300 dark:border-gray-700";
  let IconComponent = AlertTriangle;

  const normalized = status.toLowerCase();

  if (normalized === "healthy" || normalized === "ready" || normalized === "passed" || normalized === "done") {
    displayLabel = displayLabel || "Ready";
    bgClass = "bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800";
    IconComponent = CheckCircle2;
  } else if (normalized === "degraded" || normalized === "warning" || normalized === "not loaded") {
    displayLabel = displayLabel || "Model Degraded";
    bgClass = "bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800";
    IconComponent = AlertTriangle;
  } else if (normalized === "error" || normalized === "failed") {
    displayLabel = displayLabel || "Error";
    bgClass = "bg-red-50 text-red-700 border-red-300 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800";
    IconComponent = XCircle;
  } else if (normalized === "loading" || normalized === "reloading") {
    displayLabel = displayLabel || "Loading…";
    bgClass = "bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800";
    IconComponent = Loader2;
  }

  const paddingClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs sm:text-sm";
  const iconSize = size === "sm" ? 13 : 15;

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${bgClass} ${paddingClass}`}
      role="status"
    >
      <IconComponent
        size={iconSize}
        className={normalized === "loading" || normalized === "reloading" ? "animate-spin" : ""}
      />
      <span>{displayLabel}</span>
    </span>
  );
};

