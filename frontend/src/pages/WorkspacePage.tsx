import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Code2, ArrowRight } from 'lucide-react';
import { EmptyState } from '../components/shared/EmptyState';

export const WorkspacePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Workspace</h1>
          <p className="text-xs text-muted mt-1">
            Browse files, view Monaco editor diffs, and inspect requirements and test suites.
          </p>
        </div>
      </div>

      <EmptyState
        icon={Code2}
        title="No active project selected"
        description="Select an existing project from the Projects tab to open the multi-pane editor and agent run panel."
        action={{
          label: 'Go to Projects',
          icon: ArrowRight,
          onClick: () => navigate('/projects'),
        }}
      />
    </div>
  );
};

