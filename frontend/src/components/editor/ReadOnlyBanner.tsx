/**
 * ReadOnlyBanner component for Ojas.
 * Displayed when the AI model is actively generating or editing a file.
 */

import React from 'react';
import { Lock, Loader2 } from 'lucide-react';

interface ReadOnlyBannerProps {
  filename?: string;
  isGenerating?: boolean;
}

export const ReadOnlyBanner: React.FC<ReadOnlyBannerProps> = ({
  filename = 'file',
  isGenerating = true,
}) => {
  return (
    <div className="flex items-center justify-between px-3 py-1.5 bg-amber-950/80 border-b border-amber-800/80 text-amber-300 text-xs select-none">
      <div className="flex items-center gap-2">
        {isGenerating ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
        ) : (
          <Lock className="w-3.5 h-3.5 text-amber-400" />
        )}
        <span className="font-medium">
          {isGenerating
            ? `AI model is writing ${filename}... File is temporarily read-only.`
            : `${filename} is currently in read-only mode.`}
        </span>
      </div>
      <span className="text-[10px] uppercase font-mono tracking-wider bg-amber-900/60 px-1.5 py-0.5 rounded border border-amber-700/60 text-amber-200">
        Read Only
      </span>
    </div>
  );
};
