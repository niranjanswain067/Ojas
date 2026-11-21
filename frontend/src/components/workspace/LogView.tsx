/**
 * LogView component for live execution logs with auto-scroll and status indicators.
 */

import React, { useEffect, useRef } from 'react';
import type { LogEntry } from '../../store/runStore';

interface LogViewProps {
  logs: LogEntry[];
  autoScroll?: boolean;
}

export const LogView: React.FC<LogViewProps> = ({ logs, autoScroll = true }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-2.5 font-mono text-xs space-y-1 bg-neutral-950 text-neutral-300 select-text"
    >
      {logs.length === 0 ? (
        <div className="text-neutral-500 italic py-4 text-center">
          No logs recorded yet.
        </div>
      ) : (
        logs.map((log, idx) => {
          const levelColor =
            log.level === 'error'
              ? 'text-rose-400'
              : log.level === 'warn'
                ? 'text-amber-400'
                : 'text-neutral-300';

          return (
            <div key={idx} className="flex items-start gap-2 leading-relaxed hover:bg-neutral-900/60 px-1 py-0.5 rounded">
              <span className="text-neutral-500 select-none text-[11px] shrink-0">
                [{log.timestamp}]
              </span>
              <span className={`${levelColor} break-all whitespace-pre-wrap flex-1`}>
                {log.message}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
};
