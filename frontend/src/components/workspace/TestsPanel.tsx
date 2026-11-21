/**
 * TestsPanel component for Ojas Workspace sidebar.
 * Displays uploaded test cases with TC-IDs, function names, status chips,
 * and an upload dropzone for pytest (.py) files.
 */

import React, { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FlaskConical, UploadCloud, CheckCircle2, XCircle, AlertCircle, Clock, RefreshCw } from 'lucide-react';

import { listTests, uploadTests, type TestCase } from '../../api/tests';

interface TestsPanelProps {
  projectId: string;
  onSelectTest?: (filePath: string, functionName?: string | null) => void;
}

export const TestsPanel: React.FC<TestsPanelProps> = ({ projectId, onSelectTest }) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const {
    data: testData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['tests', projectId],
    queryFn: () => listTests(projectId),
    enabled: Boolean(projectId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadTests(projectId, file),
    onSuccess: () => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['tests', projectId] });
      queryClient.invalidateQueries({ queryKey: ['files', projectId] });
    },
    onError: (err: any) => {
      setUploadError(err.detail || err.message || 'Failed to upload test file.');
    },
  });

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (!file.name.endsWith('.py')) {
      setUploadError('Only Python files (.py) can be uploaded as pytest test suites.');
      return;
    }
    uploadMutation.mutate(file);
  };

  const testCases = testData?.test_cases || [];

  const renderStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
      case 'failed':
        return <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-neutral-500 shrink-0" />;
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-800 bg-neutral-950/40">
        <div className="flex items-center gap-1.5 font-semibold text-neutral-300 uppercase tracking-wider text-[11px]">
          <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />
          <span>Test Cases ({testCases.length})</span>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          title="Refresh test cases"
          className="p-1 text-neutral-400 hover:text-white rounded hover:bg-neutral-800 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      {/* Upload Drop Area */}
      <div className="p-3 border-b border-neutral-800 bg-neutral-900/50">
        <input
          ref={fileInputRef}
          type="file"
          accept=".py"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-colors ${
            dragOver
              ? 'border-emerald-500 bg-emerald-950/20 text-emerald-300'
              : 'border-neutral-700 hover:border-neutral-500 text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <UploadCloud className="w-5 h-5 mx-auto mb-1 text-neutral-400" />
          <p className="font-medium text-[11px]">
            {uploadMutation.isPending ? 'Uploading...' : 'Drop pytest file or click to upload'}
          </p>
          <p className="text-[10px] text-neutral-500 mt-0.5">Supports test_*.py or *_test.py</p>
        </div>
        {uploadError && <p className="text-[11px] text-rose-400 mt-1.5">{uploadError}</p>}
      </div>

      {/* Test Case List */}
      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1.5">
        {isLoading ? (
          <div className="p-4 text-center text-neutral-500">Loading test cases...</div>
        ) : testCases.length === 0 ? (
          <div className="p-6 text-center text-neutral-500 select-none">
            <FlaskConical className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-neutral-400 text-xs">No test cases uploaded</p>
            <p className="text-[11px] text-neutral-500 mt-1">Upload a test file above to populate the test suite.</p>
          </div>
        ) : (
          testCases.map((tc: TestCase) => (
            <div
              key={tc.id}
              onClick={() => onSelectTest?.(tc.file_path, tc.function_name)}
              className="flex items-start gap-2 p-2 rounded bg-neutral-900/60 hover:bg-neutral-800 border border-neutral-800/80 cursor-pointer transition-colors group"
            >
              {renderStatusIcon(tc.status)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-neutral-800 text-emerald-400 font-semibold border border-neutral-700">
                    {tc.tc_id}
                  </span>
                  <span className="font-mono text-[11px] text-neutral-200 truncate group-hover:text-sky-300">
                    {tc.function_name || tc.name}
                  </span>
                </div>
                {tc.name && tc.name !== tc.function_name && (
                  <p className="text-[10px] text-neutral-400 truncate">{tc.name}</p>
                )}
                <div className="flex items-center gap-2 mt-1 text-[10px] text-neutral-500">
                  <span className="truncate">{tc.file_path}</span>
                  {tc.linked_req_ids && tc.linked_req_ids.length > 0 && (
                    <span className="text-amber-400 font-mono font-medium">
                      {tc.linked_req_ids.join(', ')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
