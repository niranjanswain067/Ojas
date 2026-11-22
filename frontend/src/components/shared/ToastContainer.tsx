/**
 * ToastContainer component for Ojas.
 * Renders floating toast notifications.
 */

import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';
import type { ToastItem } from '../../store/toastStore';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  const getIcon = (type: ToastItem['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-sky-400 shrink-0" />;
    }
  };

  const getBorderColor = (type: ToastItem['type']) => {
    switch (type) {
      case 'success':
        return 'border-emerald-800/80 bg-neutral-900 text-emerald-300';
      case 'error':
        return 'border-rose-800/80 bg-neutral-900 text-rose-300';
      case 'warning':
        return 'border-amber-800/80 bg-neutral-900 text-amber-300';
      default:
        return 'border-sky-800/80 bg-neutral-900 text-sky-300';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none select-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-2.5 p-3 rounded-lg border shadow-lg text-xs pointer-events-auto transition-all ${getBorderColor(
            toast.type
          )}`}
        >
          {getIcon(toast.type)}
          <div className="flex-1 text-neutral-200">{toast.message}</div>
          <button
            type="button"
            onClick={() => removeToast(toast.id)}
            className="text-neutral-500 hover:text-white p-0.5 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
