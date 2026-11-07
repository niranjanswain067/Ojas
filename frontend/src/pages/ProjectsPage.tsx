import React from 'react';
import { FolderPlus, Folders } from 'lucide-react';
import { EmptyState } from '../components/shared/EmptyState';

export const ProjectsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Projects</h1>
          <p className="text-xs text-muted mt-1">
            Create, manage, and inspect your software development projects.
          </p>
        </div>
      </div>

      <EmptyState
        icon={Folders}
        title="No projects found"
        description="Get started by creating your first project or uploading software specification documents."
        action={{
          label: 'Create Project',
          icon: FolderPlus,
          onClick: () => {
            // Placeholder for Phase 8 Project CRUD
            alert('Project creation will be available in Phase 8.');
          },
        }}
      />
    </div>
  );
};

