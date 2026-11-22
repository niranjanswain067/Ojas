/**
 * RequirementBadge component for Ojas.
 * Small badge indicating linked requirement ID (REQ-xxx) on functions or files.
 */

import React from 'react';
import { Tag } from 'lucide-react';

interface RequirementBadgeProps {
  reqId: string;
  title?: string;
  onClick?: () => void;
}

export const RequirementBadge: React.FC<RequirementBadgeProps> = ({
  reqId,
  title,
  onClick,
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title || `Linked to requirement ${reqId}`}
      className="inline-flex items-center gap-1 font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded bg-sky-950/70 text-sky-400 border border-sky-800/60 hover:bg-sky-900/80 transition-colors cursor-pointer select-none"
    >
      <Tag className="w-2.5 h-2.5" />
      <span>{reqId}</span>
    </button>
  );
};
