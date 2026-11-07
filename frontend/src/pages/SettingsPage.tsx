import React from 'react';
import { Sliders } from 'lucide-react';
import { EmptyState } from '../components/shared/EmptyState';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Settings</h1>
          <p className="text-xs text-muted mt-1">
            Configure local LLM inference, embedding parameters, and runtime options.
          </p>
        </div>
      </div>

      <EmptyState
        icon={Sliders}
        title="Settings configuration"
        description="Local runtime configurations (context length, thread count, temperature, timeout) will be manageable in Phase 11."
      />
    </div>
  );
};

