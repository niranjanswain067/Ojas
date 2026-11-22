/**
 * ReportsPage component for Ojas.
 * Complete reports and traceability dashboard with project selector, summary cards,
 * interactive coverage matrix, Markdown report viewer, and execution run history.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileBarChart2,
  RefreshCw,
  Layers,
  FileText,
  Clock,
} from 'lucide-react';
import { listProjects } from '../api/projects';
import {
  listReports,
  getReport,
  generateReport,
  getTraceability,
} from '../api/reports';
import { listRuns } from '../api/runs';
import { ReportSummary } from '../components/reports/ReportSummary';
import { CoverageTable } from '../components/reports/CoverageTable';
import { ReportViewer } from '../components/reports/ReportViewer';
import { RunHistory } from '../components/reports/RunHistory';
import { EmptyState } from '../components/shared/EmptyState';
import { useToastStore } from '../store/toastStore';

type ActiveTab = 'coverage' | 'report' | 'history';

export const ReportsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToastStore();

  const [activeTab, setActiveTab] = useState<ActiveTab>('coverage');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedReportName, setSelectedReportName] = useState<string>('consolidated_test_report');

  // 1. Fetch all projects
  const { data: projectList, isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  const projects = projectList?.projects ?? [];

  // Default to first project if available
  const currentProjectId = selectedProjectId || (projects.length > 0 ? projects[0].id : '');

  // 2. Fetch Traceability & Coverage
  const {
    data: traceData,
  } = useQuery({
    queryKey: ['traceability', currentProjectId],
    queryFn: () => getTraceability(currentProjectId),
    enabled: Boolean(currentProjectId),
  });

  // 3. Fetch Reports list
  const { data: reportListData } = useQuery({
    queryKey: ['reports-list', currentProjectId],
    queryFn: () => listReports(currentProjectId),
    enabled: Boolean(currentProjectId),
  });

  // 4. Fetch Active Report content
  const { data: reportDetail } = useQuery({
    queryKey: ['report-detail', currentProjectId, selectedReportName],
    queryFn: () => getReport(currentProjectId, selectedReportName),
    enabled: Boolean(currentProjectId && selectedReportName),
  });

  // 5. Fetch Execution Runs history
  const { data: runsData } = useQuery({
    queryKey: ['runs', currentProjectId],
    queryFn: () => listRuns(currentProjectId),
    enabled: Boolean(currentProjectId),
  });

  // Mutation to regenerate report on demand
  const regenerateMutation = useMutation({
    mutationFn: () => generateReport(currentProjectId),
    onSuccess: () => {
      addToast('Consolidated report regenerated successfully.', 'success');
      queryClient.invalidateQueries({ queryKey: ['reports-list', currentProjectId] });
      queryClient.invalidateQueries({ queryKey: ['report-detail', currentProjectId] });
      queryClient.invalidateQueries({ queryKey: ['traceability', currentProjectId] });
    },
    onError: (err: any) => {
      addToast(`Failed to regenerate report: ${err?.message || err}`, 'error');
    },
  });

  if (isLoadingProjects) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-6 h-6 animate-spin text-neutral-500" />
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Reports</h1>
          <p className="text-xs text-neutral-400 mt-1">
            Requirement coverage matrices, bug summaries, and consolidated execution runs.
          </p>
        </div>
        <EmptyState
          icon={FileBarChart2}
          title="No projects found"
          description="Create a project and run development or tests to generate traceability and quality reports."
        />
      </div>
    );
  }

  const reports = reportListData?.reports ?? [];
  const coverageItems = traceData?.coverage ?? [];
  const runs = runsData?.runs ?? [];

  return (
    <div className="space-y-6 select-none">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Reports</h1>
          <p className="text-xs text-neutral-400 mt-1">
            End-to-end requirement traceability, test coverage verification, and quality metrics.
          </p>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="project-select" className="text-xs text-neutral-400 font-medium">
              Project:
            </label>
            <select
              id="project-select"
              value={currentProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-neutral-900 border border-neutral-800 text-neutral-200 text-xs rounded px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={() => regenerateMutation.mutate()}
            disabled={regenerateMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-medium rounded transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${regenerateMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Regenerate Report</span>
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <ReportSummary
        summary={reportDetail?.summary}
        totalRequirements={traceData?.total_requirements ?? coverageItems.length}
        passingRequirements={traceData?.passing_requirements}
      />

      {/* Dashboard Tabs Header */}
      <div className="flex items-center gap-2 border-b border-neutral-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('coverage')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            activeTab === 'coverage'
              ? 'bg-neutral-800 text-white font-semibold'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-sky-400" />
          <span>Requirement Coverage Matrix</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-neutral-900 text-neutral-400">
            {coverageItems.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('report')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            activeTab === 'report'
              ? 'bg-neutral-800 text-white font-semibold'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <FileText className="w-3.5 h-3.5 text-emerald-400" />
          <span>Markdown Reports</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-neutral-900 text-neutral-400">
            {reports.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
            activeTab === 'history'
              ? 'bg-neutral-800 text-white font-semibold'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span>Execution History</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-neutral-900 text-neutral-400">
            {runs.length}
          </span>
        </button>
      </div>

      {/* Tab 1: Coverage Matrix */}
      {activeTab === 'coverage' && (
        <CoverageTable items={coverageItems} />
      )}

      {/* Tab 2: Markdown Reports View */}
      {activeTab === 'report' && (
        <div className="space-y-4">
          {/* Sub-selector for reports */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {reports.length === 0 ? (
              <span className="text-xs text-neutral-500 italic">No reports generated yet.</span>
            ) : (
              reports.map((r) => (
                <button
                  key={r.name}
                  type="button"
                  onClick={() => setSelectedReportName(r.name)}
                  className={`px-3 py-1 text-xs rounded transition-colors whitespace-nowrap ${
                    selectedReportName === r.name
                      ? 'bg-sky-950/80 text-sky-300 font-medium border border-sky-800/80'
                      : 'bg-neutral-900 text-neutral-400 hover:text-white border border-neutral-800'
                  }`}
                >
                  {r.title}
                </button>
              ))
            )}
          </div>

          <ReportViewer
            title={reportDetail?.title || 'Report'}
            reportName={selectedReportName}
            content={reportDetail?.content || ''}
            projectId={currentProjectId}
          />
        </div>
      )}

      {/* Tab 3: Execution History */}
      {activeTab === 'history' && (
        <RunHistory runs={runs} />
      )}
    </div>
  );
};
