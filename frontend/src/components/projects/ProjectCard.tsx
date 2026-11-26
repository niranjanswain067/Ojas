import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  Bug,
  Calendar,
  CheckCircle2,
  Download,
  FileCode,
  FileText,
  Loader2,
  Play,
  Trash2,
} from 'lucide-react';
import { downloadProjectZip } from '../../api/projects';
import type { Project } from '../../api/types';

export interface ProjectCardProps {
  project: Project;
  onDelete: (project: Project) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  const navigate = useNavigate();
  const [isDownloading, setIsDownloading] = useState(false);

  const handleOpen = () => {
    navigate(`/workspace/${project.id}`);
  };

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      await downloadProjectZip(project.id, project.name);
    } catch (err) {
      console.error('Failed to download project:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'done':
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-status-success/15 text-status-success border border-status-success/30">
            <CheckCircle2 className="w-2.5 h-2.5" /> Done
          </span>
        );
      case 'running':
      case 'developing':
      case 'indexing':
      case 'testing':
      case 'fixing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-status-info/15 text-status-info border border-status-info/30 animate-pulse">
            <Play className="w-2.5 h-2.5" /> {status}
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-status-error/15 text-status-error border border-status-error/30">
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-muted/15 text-muted border border-border">
            Idle
          </span>
        );
    }
  };

  const formattedDate = new Date(project.updated_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="flex flex-col justify-between bg-panel border border-border rounded-lg p-5 hover:border-primary/50 transition-all hover:shadow-md group">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3
              onClick={handleOpen}
              className="text-sm font-semibold text-text truncate group-hover:text-primary transition-colors cursor-pointer"
              title={project.name}
            >
              {project.name}
            </h3>
            <p className="text-xs text-muted mt-1 line-clamp-2 leading-relaxed">
              {project.description || 'No description provided.'}
            </p>
          </div>
          <div className="shrink-0">{getStatusBadge(project.status)}</div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-2 mt-4 pt-3.5 border-t border-border/60">
          <div className="flex flex-col items-center p-1.5 rounded bg-bg/50">
            <span className="text-muted flex items-center gap-1 text-[10px]">
              <FileText className="w-3 h-3" /> Docs
            </span>
            <span className="text-xs font-semibold text-text mt-0.5">
              {project.document_count || 0}
            </span>
          </div>

          <div className="flex flex-col items-center p-1.5 rounded bg-bg/50">
            <span className="text-muted flex items-center gap-1 text-[10px]">
              <BookOpen className="w-3 h-3" /> Reqs
            </span>
            <span className="text-xs font-semibold text-text mt-0.5">
              {project.requirement_count || 0}
            </span>
          </div>

          <div className="flex flex-col items-center p-1.5 rounded bg-bg/50">
            <span className="text-muted flex items-center gap-1 text-[10px]">
              <FileCode className="w-3 h-3" /> Tests
            </span>
            <span className="text-xs font-semibold text-text mt-0.5">
              {project.test_case_count || project.test_count || 0}
            </span>
          </div>

          <div className="flex flex-col items-center p-1.5 rounded bg-bg/50">
            <span className="text-muted flex items-center gap-1 text-[10px]">
              <Bug className="w-3 h-3" /> Bugs
            </span>
            <span className="text-xs font-semibold text-text mt-0.5">
              {project.bug_count || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between mt-5 pt-3 border-t border-border/60 text-xs text-muted">
        <div className="flex items-center gap-1 text-[11px]">
          <Calendar className="w-3 h-3" />
          <span>{formattedDate}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleDownload}
            disabled={isDownloading}
            className="p-1.5 rounded text-muted hover:text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
            title="Download project ZIP"
            aria-label={`Download ${project.name}`}
          >
            {isDownloading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
          </button>

          <button
            type="button"
            onClick={() => onDelete(project)}
            className="p-1.5 rounded text-muted hover:text-status-error hover:bg-status-error/10 transition-colors"
            title="Delete project"
            aria-label={`Delete ${project.name}`}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={handleOpen}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-medium text-xs bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors"
          >
            <span>Open</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
