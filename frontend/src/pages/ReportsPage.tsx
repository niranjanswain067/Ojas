import React from 'react';
import { FileBarChart2 } from 'lucide-react';
import { EmptyState } from '../components/shared/EmptyState';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Reports</h1>
          <p className="text-xs text-muted mt-1">
            Requirement coverage matrices, bug summaries, and consolidated execution runs.
          </p>
        </div>
      </div>

      <EmptyState
        icon={FileBarChart2}
        title="No reports generated yet"
        description="Run development or test iterations in the workspace to automatically generate traceability reports and quality summaries."
      />
    </div>
  );
};

