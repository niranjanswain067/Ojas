/**
 * DisconnectedBanner component for Ojas.
 * Displays a full-width alert when the FastAPI backend is unreachable.
 */

import React, { useEffect, useState } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { apiGet } from '../../api/client';

export const DisconnectedBanner: React.FC = () => {
  const [isDisconnected, setIsDisconnected] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const checkConnection = async () => {
    try {
      await apiGet('/health');
      setIsDisconnected(false);
    } catch {
      setIsDisconnected(true);
    }
  };

  useEffect(() => {
    // Probe every 10 seconds
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await apiGet('/health');
      setIsDisconnected(false);
    } catch {
      setIsDisconnected(true);
    } finally {
      setIsRetrying(false);
    }
  };

  if (!isDisconnected) return null;

  return (
    <div className="bg-rose-950 border-b border-rose-800 text-rose-200 px-4 py-2 text-xs flex items-center justify-between z-50">
      <div className="flex items-center gap-2">
        <WifiOff className="w-4 h-4 text-rose-400" />
        <span className="font-semibold">Backend Unreachable:</span>
        <span>Cannot connect to local Ojas server at http://127.0.0.1:8000.</span>
      </div>

      <button
        type="button"
        onClick={handleRetry}
        disabled={isRetrying}
        className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-900 hover:bg-rose-800 text-white rounded text-[11px] font-medium transition-colors"
      >
        <RefreshCw className={`w-3 h-3 ${isRetrying ? 'animate-spin' : ''}`} />
        <span>Retry Connection</span>
      </button>
    </div>
  );
};
