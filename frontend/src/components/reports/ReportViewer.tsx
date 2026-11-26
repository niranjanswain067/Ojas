/**
 * ReportViewer component for Ojas.
 * Renders Markdown report contents with action controls for downloading and copying.
 */

import React, { useState } from 'react';
import { Download, Copy, Check, FileText } from 'lucide-react';

interface ReportViewerProps {
  title: string;
  reportName: string;
  content: string;
  projectId?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  title,
  reportName,
  content,
  projectId = 'project',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!content) return;
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${projectId}_${reportName}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-neutral-950/80 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-sky-400" />
          <span className="font-semibold text-xs text-white">{title}</span>
          <span className="font-mono text-[11px] text-neutral-400">({reportName}.md)</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-neutral-300 hover:text-white bg-neutral-800 hover:bg-neutral-700 rounded transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
          </button>

          <button
            type="button"
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-white bg-sky-600 hover:bg-sky-500 rounded transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .md</span>
          </button>
        </div>
      </div>

      {/* Rendered Document Body */}
      <div className="p-6 font-mono text-xs text-neutral-300 leading-relaxed overflow-x-auto whitespace-pre-wrap select-text bg-neutral-950/40">
        {content ? (
          content
        ) : (
          <div className="text-center py-12 text-neutral-500 font-sans">
            No report content available.
          </div>
        )}
      </div>
    </div>
  );
};
