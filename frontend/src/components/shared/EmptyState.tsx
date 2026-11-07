import React from 'react';
import { type LucideIcon, Inbox } from 'lucide-react';

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-8 rounded-xl border border-dashed border-border bg-surface/50 ${className}`}
    >
      <div className="p-3 rounded-full bg-border/40 text-muted mb-4">
        <Icon className="w-8 h-8" />
      </div>

      <h3 className="text-base font-semibold text-text mb-1">{title}</h3>

      {description && (
        <p className="text-xs text-muted max-w-sm mb-6 leading-relaxed">
          {description}
        </p>
      )}

      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-primary text-white hover:opacity-90 active:scale-95 transition-all shadow-sm"
        >
          {action.icon && <action.icon className="w-3.5 h-3.5" />}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
};

