/**
 * CoverageTable component for Ojas.
 * Interactive requirement traceability matrix linking REQs -> Code -> Tests -> Bugs.
 */

import React, { useState } from 'react';
import { Search, CheckCircle2, XCircle, AlertCircle, HelpCircle, Code, Bug } from 'lucide-react';
import type { TraceabilityCoverageItem } from '../../api/reports';

interface CoverageTableProps {
  items: TraceabilityCoverageItem[];
  onSelectReq?: (reqId: string) => void;
}

export const CoverageTable: React.FC<CoverageTableProps> = ({ items, onSelectReq }) => {
  const [filter, setFilter] = useState<'all' | 'passing' | 'failing' | 'uncovered'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredItems = items.filter((item) => {
    if (filter !== 'all' && item.status !== filter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = item.req_id.toLowerCase().includes(q);
      const matchHeading = item.heading.toLowerCase().includes(q);
      const matchDesc = item.description?.toLowerCase().includes(q);
      const matchSymbols = item.code_symbols.some((s) => s.symbol_name.toLowerCase().includes(q) || s.file_path.toLowerCase().includes(q));
      return matchId || matchHeading || matchDesc || matchSymbols;
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/70 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="w-3 h-3" />
            <span>Passing</span>
          </span>
        );
      case 'failing':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-950/70 text-rose-400 border border-rose-800/60">
            <XCircle className="w-3 h-3" />
            <span>Failing</span>
          </span>
        );
      case 'partial':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-950/70 text-amber-400 border border-amber-800/60">
            <AlertCircle className="w-3 h-3" />
            <span>Partial</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-neutral-800 text-neutral-400 border border-neutral-700">
            <HelpCircle className="w-3 h-3" />
            <span>Uncovered</span>
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden select-none">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-neutral-900/90 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              filter === 'all'
                ? 'bg-neutral-800 text-white font-medium border border-neutral-700'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            All ({items.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('passing')}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              filter === 'passing'
                ? 'bg-emerald-950/80 text-emerald-300 font-medium border border-emerald-800/70'
                : 'text-neutral-400 hover:text-emerald-400'
            }`}
          >
            Passing ({items.filter((i) => i.status === 'passing').length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('failing')}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              filter === 'failing'
                ? 'bg-rose-950/80 text-rose-300 font-medium border border-rose-800/70'
                : 'text-neutral-400 hover:text-rose-400'
            }`}
          >
            Failing ({items.filter((i) => i.status === 'failing').length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('uncovered')}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              filter === 'uncovered'
                ? 'bg-neutral-800 text-neutral-200 font-medium border border-neutral-700'
                : 'text-neutral-400 hover:text-neutral-300'
            }`}
          >
            Uncovered ({items.filter((i) => i.status === 'uncovered').length})
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            type="text"
            placeholder="Filter requirements or symbols..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1 bg-neutral-950 border border-neutral-800 rounded text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-neutral-950/60 border-b border-neutral-800 text-neutral-400 font-medium">
            <tr>
              <th className="py-2.5 px-3 w-28">REQ-ID</th>
              <th className="py-2.5 px-3 min-w-[220px]">Requirement Heading</th>
              <th className="py-2.5 px-3 min-w-[180px]">Code Symbols</th>
              <th className="py-2.5 px-3 min-w-[200px]">Linked Test Cases</th>
              <th className="py-2.5 px-3 w-28">Bugs</th>
              <th className="py-2.5 px-3 w-28 text-right">Coverage Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/60">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-neutral-500">
                  No matching requirements found.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr
                  key={item.req_id}
                  onClick={() => onSelectReq?.(item.req_id)}
                  className="hover:bg-neutral-800/40 transition-colors group cursor-pointer"
                >
                  {/* REQ-ID */}
                  <td className="py-2.5 px-3 font-mono font-semibold text-sky-400 whitespace-nowrap">
                    {item.req_id}
                  </td>

                  {/* Heading & description */}
                  <td className="py-2.5 px-3">
                    <div className="font-medium text-neutral-200">{item.heading}</div>
                    {item.description && (
                      <div className="text-[11px] text-neutral-400 line-clamp-1 mt-0.5">
                        {item.description}
                      </div>
                    )}
                  </td>

                  {/* Code Symbols */}
                  <td className="py-2.5 px-3">
                    {item.code_symbols.length === 0 ? (
                      <span className="text-neutral-500 italic text-[11px]">No symbols linked</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {item.code_symbols.map((sym, idx) => (
                          <span
                            key={idx}
                            title={`${sym.file_path}:${sym.start_line}-${sym.end_line}`}
                            className="inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 bg-neutral-950 text-neutral-300 rounded border border-neutral-800"
                          >
                            <Code className="w-2.5 h-2.5 text-neutral-500" />
                            <span>{sym.symbol_name}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </td>

                  {/* Linked Tests */}
                  <td className="py-2.5 px-3">
                    {item.test_cases.length === 0 ? (
                      <span className="text-neutral-500 italic text-[11px]">No tests written</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {item.test_cases.map((tc) => {
                          const isPass = tc.status === 'passed';
                          const isFail = tc.status === 'failed' || tc.status === 'error';
                          return (
                            <span
                              key={tc.id || tc.tc_id}
                              title={`${tc.name} (${tc.status})`}
                              className={`inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 rounded border ${
                                isPass
                                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50'
                                  : isFail
                                  ? 'bg-rose-950/60 text-rose-300 border-rose-800/50'
                                  : 'bg-neutral-800 text-neutral-300 border-neutral-700'
                              }`}
                            >
                              {isPass ? (
                                <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                              ) : isFail ? (
                                <XCircle className="w-2.5 h-2.5 text-rose-400" />
                              ) : null}
                              <span>{tc.tc_id}</span>
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </td>

                  {/* Open Bugs */}
                  <td className="py-2.5 px-3">
                    {item.bugs.length === 0 ? (
                      <span className="text-emerald-500/80 text-[11px]">None</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {item.bugs.map((b) => (
                          <span
                            key={b.bug_id}
                            title={`${b.bug_id}: ${b.title || b.severity}`}
                            className="inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 bg-rose-950/60 text-rose-300 border border-rose-800/50 rounded"
                          >
                            <Bug className="w-2.5 h-2.5 text-rose-400" />
                            <span>{b.bug_id}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </td>

                  {/* Status Badge */}
                  <td className="py-2.5 px-3 text-right">
                    {getStatusBadge(item.status)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
