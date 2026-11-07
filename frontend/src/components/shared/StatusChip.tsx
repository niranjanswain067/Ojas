import React from 'react';

export type StatusType =
  | 'healthy'
  | 'degraded'
  | 'error'
  | 'offline'
  | 'idle'
  | 'indexing'
  | 'planning'
  | 'developing'
  | 'generating'
  | 'testing'
  | 'fixing'
  | 'running'
  | 'done'
  | 'passed'
  | 'failed'
  | 'warning'
  | 'attention';

export interface StatusChipProps {
  status: StatusType;
  label?: string;
  tooltip?: string;
  className?: string;
  showDot?: boolean;
}

export const StatusChip: React.FC<StatusChipProps> = ({
  status,
  label,
  tooltip,
  className = '',
  showDot = true,
}) => {
  let colorClasses = 'bg-muted/10 text-muted border-border';
  let dotClasses = 'bg-muted';
  let isSpinning = false;
  let defaultLabel: string = status;

  switch (status) {
    case 'healthy':
    case 'done':
    case 'passed':
      colorClasses = 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      dotClasses = 'bg-emerald-500';
      defaultLabel = status === 'healthy' ? 'Ready' : status.toUpperCase();
      break;

    case 'degraded':
    case 'warning':
    case 'attention':
      colorClasses = 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30';
      dotClasses = 'bg-amber-500';
      defaultLabel = status === 'degraded' ? 'Degraded' : 'Warning';
      break;

    case 'error':
    case 'offline':
    case 'failed':
      colorClasses = 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30';
      dotClasses = 'bg-rose-500';
      defaultLabel = status === 'offline' ? 'Offline' : 'Failed';
      break;

    case 'indexing':
    case 'planning':
    case 'developing':
    case 'generating':
    case 'testing':
    case 'fixing':
    case 'running':
      colorClasses = 'bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30';
      dotClasses = 'bg-sky-500';
      isSpinning = true;
      defaultLabel = status.charAt(0).toUpperCase() + status.slice(1);
      break;

    case 'idle':
    default:
      colorClasses = 'bg-border/30 text-muted border-border';
      dotClasses = 'bg-muted';
      defaultLabel = 'Idle';
      break;
  }

  return (
    <span
      title={tooltip}
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors ${colorClasses} ${className}`}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          {isSpinning && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotClasses}`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotClasses}`} />
        </span>
      )}
      <span>{label ?? defaultLabel}</span>
    </span>
  );
};
