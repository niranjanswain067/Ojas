import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  FolderPlus,
  Folders,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';
import { createProject, deleteProject, listProjects } from '../api/projects';
import type { Project } from '../api/types';
import { ProjectCard } from '../components/projects/ProjectCard';
import { NewProjectDialog } from '../components/projects/NewProjectDialog';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';

export const ProjectsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [isNewDialogOpen, setIsNewDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [dialogError, setDialogError] = useState<string | null>(null);

  // 1. Fetch Projects Query
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  // 2. Create Project Mutation
  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsNewDialogOpen(false);
      setDialogError(null);
    },
    onError: (err: any) => {
      setDialogError(err?.detail || err?.message || 'Failed to create project.');
    },
  });

  // 3. Delete Project Mutation
  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setProjectToDelete(null);
    },
  });

  const projects = data?.projects || [];
  const filteredProjects = projects.filter((p) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      (p.description && p.description.toLowerCase().includes(q))
    );
  });

  const handleCreateSubmit = (formData: { name: string; description: string }) => {
    createMutation.mutate(formData);
  };

  const handleConfirmDelete = () => {
    if (projectToDelete) {
      deleteMutation.mutate(projectToDelete.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-text">Projects</h1>
            {!isLoading && (
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-border text-muted">
                {projects.length}
              </span>
            )}
          </div>
          <p className="text-xs text-muted mt-1">
            Create, manage, and inspect your software development projects and workspaces.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isRefetching}
            className="p-2 rounded-md border border-border bg-panel text-muted hover:text-text hover:bg-hover transition-colors disabled:opacity-50"
            title="Refresh projects"
            aria-label="Refresh projects"
          >
            <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
          </button>

          <button
            type="button"
            onClick={() => {
              setDialogError(null);
              setIsNewDialogOpen(true);
            }}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary/90 transition-colors shadow-sm"
          >
            <FolderPlus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      {projects.length > 0 && (
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects by name or description..."
            className="w-full pl-9 pr-9 py-2 text-xs rounded-md border border-border bg-panel text-text placeholder:text-muted/60 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted hover:text-text p-0.5"
              aria-label="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-48 rounded-lg border border-border bg-panel/50 animate-pulse p-5 space-y-4"
            >
              <div className="flex justify-between items-start">
                <div className="h-5 w-1/2 bg-muted/20 rounded" />
                <div className="h-4 w-12 bg-muted/20 rounded-full" />
              </div>
              <div className="h-3 w-3/4 bg-muted/20 rounded" />
              <div className="h-12 w-full bg-muted/10 rounded mt-4" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && !isLoading && (
        <div className="p-6 rounded-lg border border-status-error/30 bg-status-error/10 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-status-error mx-auto" />
          <h3 className="text-sm font-semibold text-text">Failed to load projects</h3>
          <p className="text-xs text-muted max-w-sm mx-auto">
            {(error as any)?.detail || (error as Error)?.message || 'Could not connect to backend server.'}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className="px-3.5 py-1.5 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State: No projects created yet */}
      {!isLoading && !isError && projects.length === 0 && (
        <EmptyState
          icon={Folders}
          title="No projects found"
          description="Get started by creating your first software development project."
          action={{
            label: 'Create Project',
            icon: FolderPlus,
            onClick: () => {
              setDialogError(null);
              setIsNewDialogOpen(true);
            },
          }}
        />
      )}

      {/* Empty State: Search filter yielded no results */}
      {!isLoading && !isError && projects.length > 0 && filteredProjects.length === 0 && (
        <div className="p-10 border border-dashed border-border rounded-lg text-center space-y-3 bg-panel/30">
          <p className="text-sm font-medium text-text">No matching projects found</p>
          <p className="text-xs text-muted">
            No projects matched the search query &quot;{searchQuery}&quot;.
          </p>
          <button
            type="button"
            onClick={() => setSearchQuery('')}
            className="px-3 py-1.5 text-xs font-medium rounded-md border border-border bg-panel text-text hover:bg-hover transition-colors"
          >
            Clear Search Filter
          </button>
        </div>
      )}

      {/* Project Cards Grid */}
      {!isLoading && !isError && filteredProjects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={(p) => setProjectToDelete(p)}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <NewProjectDialog
        isOpen={isNewDialogOpen}
        isLoading={createMutation.isPending}
        error={dialogError}
        onClose={() => {
          setIsNewDialogOpen(false);
          setDialogError(null);
        }}
        onSubmit={handleCreateSubmit}
      />

      <ConfirmDialog
        isOpen={projectToDelete !== null}
        isLoading={deleteMutation.isPending}
        isDestructive={true}
        title="Delete Project"
        message={`Are you sure you want to delete "${projectToDelete?.name}"? This will permanently delete its workspace files, documents, tests, and reports. This action cannot be undone.`}
        confirmLabel="Delete Project"
        onConfirm={handleConfirmDelete}
        onCancel={() => setProjectToDelete(null)}
      />
    </div>
  );
};
