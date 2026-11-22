/**
 * ReportSummary component for Ojas.
 * Displays executive summary KPIs: tests count, pass rate, iterations, duration, open bugs.
 */

import React from 'react';
import { CheckCircle2, XCircle, Clock, RotateCw, Layers } from 'lucide-react';
import type { ReportSummaryStats } from '../../api/reports';

interface ReportSummaryProps {
  summary?: ReportSummaryStats | null;
  totalRequirements?: number;
  passingRequirements?: number;
}

export const ReportSummary: React.FC<ReportSummaryProps> = ({
  summary,
  totalRequirements = 0,
  passingRequirements = 0,
}) => {
  const totalTests = summary?.total_tests ?? 0;
  const passedTests = summary?.passed ?? 0;
  const failedTests = summary?.failed ?? 0;
  const iterations = summary?.iterations ?? 0;
  const totalSeconds = summary?.total_time_s ?? 0;

  const testPassRate = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : '0.0';
  const reqPassRate = totalRequirements > 0 ? ((passingRequirements / totalRequirements) * 100).toFixed(1) : '0.0';

  const formatDuration = (secs: number) => {
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins}m ${rem}s`;
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* Test Pass Rate */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Test Pass Rate</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2">
          <span className="text-xl font-bold text-white">{testPassRate}%</span>
          <p className="text-[10px] text-neutral-400 mt-0.5">
            {passedTests} of {totalTests} passed
          </p>
        </div>
      </div>

      {/* Requirement Coverage */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Req. Passed</span>
          <Layers className="w-4 h-4 text-sky-400" />
        </div>
        <div className="mt-2">
          <span className="text-xl font-bold text-white">{reqPassRate}%</span>
          <p className="text-[10px] text-neutral-400 mt-0.5">
            {passingRequirements} of {totalRequirements} passing
          </p>
        </div>
      </div>

      {/* Total Test Cases */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Test Cases</span>
          <CheckCircle2 className="w-4 h-4 text-neutral-400" />
        </div>
        <div className="mt-2">
          <span className="text-xl font-bold text-white">{totalTests}</span>
          <p className="text-[10px] text-neutral-400 mt-0.5">
            {passedTests} passed, {failedTests} failed
          </p>
        </div>
      </div>

      {/* Failing Tests */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Failing Tests</span>
          <XCircle className={`w-4 h-4 ${failedTests > 0 ? 'text-rose-400' : 'text-neutral-500'}`} />
        </div>
        <div className="mt-2">
          <span className={`text-xl font-bold ${failedTests > 0 ? 'text-rose-400' : 'text-white'}`}>
            {failedTests}
          </span>
          <p className="text-[10px] text-neutral-400 mt-0.5">
            {failedTests === 0 ? 'All passing' : 'Needs resolution'}
          </p>
        </div>
      </div>

      {/* Fix Iterations */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Fix Iterations</span>
          <RotateCw className="w-4 h-4 text-amber-400" />
        </div>
        <div className="mt-2">
          <span className="text-xl font-bold text-white">{iterations}</span>
          <p className="text-[10px] text-neutral-400 mt-0.5">Loop cycles executed</p>
        </div>
      </div>

      {/* Execution Time */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 flex flex-col justify-between">
        <div className="flex items-center justify-between text-neutral-400">
          <span className="text-[11px] font-medium">Execution Time</span>
          <Clock className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="mt-2">
          <span className="text-xl font-bold text-white">{formatDuration(totalSeconds)}</span>
          <p className="text-[10px] text-neutral-400 mt-0.5">Total run elapsed</p>
        </div>
      </div>
    </div>
  );
};
