/**
 * ModelOutput component for Ojas Workspace BottomPanel.
 * Displays real-time streamed LLM output with auto-scroll and clear controls.
 */

import React, { useEffect, useRef, useState } from 'react';
import { Cpu, Trash2, ArrowDown, Copy, Check } from 'lucide-react';
import { useRunStore } from '../../store/runStore';

interface ModelOutputProps {
  output?: string;
  onClear?: () => void;
}

export const ModelOutput: React.FC<ModelOutputProps> = ({
  output: propOutput,
  onClear: propOnClear,
}) => {
  const storeOutput = useRunStore((s) => s.modelOutput);
  const storeClear = useRunStore((s) => s.clearModelOutput);
  const isRunning = useRunStore((s) => s.status === 'running');

  const output = propOutput !== undefined ? propOutput : storeOutput;
  const onClear = propOnClear || storeClear;

  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom as tokens stream in
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output, autoScroll]);

  const handleCopy = () => {
    if (!output) return;
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-neutral-950 font-mono text-xs select-text">
      {/* Action Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-neutral-900/80 border-b border-neutral-800 text-neutral-400">
        <div className="flex items-center gap-2">
          <Cpu className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-semibold text-neutral-200">Raw Model Stream</span>
          {isRunning && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
              Streaming
            </span>
          )}
          <span className="text-[10px] text-neutral-400">
            {output ? `${output.length} characters` : 'Empty'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setAutoScroll((prev) => !prev)}
            title={autoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll'}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] transition-colors ${
              autoScroll
                ? 'bg-sky-950/80 text-sky-400 border border-sky-800/60'
                : 'text-neutral-400 hover:text-white hover:bg-neutral-800'
            }`}
          >
            <ArrowDown className="w-3 h-3" />
            <span>Auto-scroll {autoScroll ? 'ON' : 'OFF'}</span>
          </button>

          <button
            type="button"
            onClick={handleCopy}
            disabled={!output}
            title="Copy model output"
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors disabled:opacity-40"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            type="button"
            onClick={onClear}
            disabled={!output}
            title="Clear output"
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-neutral-400 hover:text-rose-400 hover:bg-neutral-800 transition-colors disabled:opacity-40"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Stream Content */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 text-neutral-300 leading-relaxed whitespace-pre-wrap break-words"
      >
        {output ? (
          output
        ) : (
          <div className="flex flex-col items-center justify-center h-full py-12 text-neutral-400">
            <Cpu className="w-8 h-8 text-neutral-700 mb-2" />
            <p>No model output yet.</p>
            <p className="text-[11px] text-neutral-400 mt-1">
              Raw tokens will stream here live as the LLM generates plans or code.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
