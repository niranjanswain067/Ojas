import React, { useState } from "react";
import {
  Search,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  FileCheck2,
  RefreshCw,
  Hash,
  Tag,
} from "lucide-react";
import type { RequirementChunk } from "../../api/documents";

interface RequirementListProps {
  requirements: RequirementChunk[];
  loading?: boolean;
  onRefresh?: () => void;
  onSearchChange?: (term: string) => void;
}

export const RequirementList: React.FC<RequirementListProps> = ({
  requirements,
  loading = false,
  onRefresh,
  onSearchChange,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedIds(new Set(filteredRequirements.map((r) => r.id)));
  };

  const collapseAll = () => {
    setExpandedIds(new Set());
  };

  const handleCopy = (reqId: string, text: string) => {
    navigator.clipboard.writeText(`${reqId}: ${text}`).catch(() => {});
    setCopiedId(reqId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchTerm(val);
    if (onSearchChange) {
      onSearchChange(val);
    }
  };

  // Local filtering if onSearchChange is not handling server-side FTS
  const filteredRequirements = requirements.filter((req) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      req.req_id.toLowerCase().includes(term) ||
      req.heading.toLowerCase().includes(term) ||
      req.content.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-4">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface dark:bg-[#1C222B] p-3 rounded-xl border border-border">
        <div className="relative flex-1">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder="Search requirements or REQ-IDs…"
            className="w-full pl-9 pr-3 py-1.5 bg-bg dark:bg-[#14181F] border border-border rounded-lg text-xs text-text placeholder:text-muted focus:ring-1 focus:ring-primary outline-none"
          />
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={expandAll}
            className="px-2.5 py-1 text-[11px] font-medium text-muted hover:text-text border border-border rounded-md hover:bg-border/20 transition"
          >
            Expand All
          </button>
          <button
            type="button"
            onClick={collapseAll}
            className="px-2.5 py-1 text-[11px] font-medium text-muted hover:text-text border border-border rounded-md hover:bg-border/20 transition"
          >
            Collapse All
          </button>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              title="Refresh requirements"
              className="p-1.5 text-muted hover:text-text border border-border rounded-md hover:bg-border/20 transition disabled:opacity-50"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            </button>
          )}
        </div>
      </div>

      {/* Requirements List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted">
          <RefreshCw size={18} className="animate-spin text-primary" />
          <span className="text-xs">Loading requirement chunks…</span>
        </div>
      ) : filteredRequirements.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-border rounded-xl bg-surface/50 p-6 space-y-2">
          <FileCheck2 size={32} className="mx-auto text-muted/60" />
          <h4 className="text-sm font-semibold text-text">No requirements found</h4>
          <p className="text-xs text-muted max-w-sm mx-auto">
            {searchTerm
              ? `No requirement chunks matched "${searchTerm}".`
              : "Upload requirement documents and trigger indexing to generate atomic REQ-IDs."}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filteredRequirements.map((req) => {
            const isExpanded = expandedIds.has(req.id);
            const isCopied = copiedId === req.req_id;

            return (
              <div
                key={req.id}
                className={`bg-surface dark:bg-[#1C222B] border rounded-xl transition-colors ${
                  isExpanded ? "border-primary/40 shadow-sm" : "border-border"
                }`}
              >
                {/* Collapsed Header */}
                <div
                  onClick={() => toggleExpand(req.id)}
                  className="flex items-center justify-between p-3 cursor-pointer select-none hover:bg-border/10 rounded-xl"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <button
                      type="button"
                      aria-label={isExpanded ? "Collapse requirement" : "Expand requirement"}
                      className="text-muted hover:text-text transition p-0.5"
                    >
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>

                    <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-primary/10 text-primary border border-primary/20 shrink-0">
                      {req.req_id}
                    </span>

                    <span className="text-xs font-semibold text-text truncate">
                      {req.heading || "Requirement Specification"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {req.token_count && (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[10px] text-muted font-mono bg-border/20 px-2 py-0.5 rounded">
                        <Tag size={10} />
                        {req.token_count} toks
                      </span>
                    )}

                    <span className="text-[10px] text-muted font-mono bg-border/20 px-1.5 py-0.5 rounded">
                      #{req.chunk_index}
                    </span>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(req.req_id, req.content);
                      }}
                      title="Copy REQ-ID and content"
                      className="p-1 text-muted hover:text-text rounded hover:bg-border/40 transition"
                    >
                      {isCopied ? (
                        <Check size={12} className="text-emerald-500" />
                      ) : (
                        <Copy size={12} />
                      )}
                    </button>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-3.5 pt-1 border-t border-border/60 space-y-2.5 text-xs text-text">
                    <div className="bg-bg dark:bg-[#14181F] p-3 rounded-lg border border-border font-mono text-[11px] leading-relaxed whitespace-pre-wrap selection:bg-primary/20">
                      {req.content}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted pt-1">
                      <div className="flex items-center gap-2">
                        <Hash size={11} />
                        <span className="font-mono text-[10px]">{req.id}</span>
                      </div>
                      {req.created_at && (
                        <span>Indexed at {new Date(req.created_at).toLocaleTimeString()}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
