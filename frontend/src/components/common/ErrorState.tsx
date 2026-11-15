import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ProblemDetails } from '@/services/apiClient';

interface ErrorStateProps {
  title?: string;
  problem?: ProblemDetails;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  problem,
  message,
  onRetry,
}) => {
  const displayMessage =
    problem?.detail || message || 'An error occurred while communicating with the server.';

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-rose-50/50 border border-rose-200 rounded-lg min-h-[220px]">
      <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-600 max-w-md mb-4">{displayMessage}</p>
      {problem?.status && (
        <span className="inline-block px-2.5 py-0.5 rounded text-xs font-mono bg-rose-100 text-rose-800 mb-4">
          HTTP {problem.status} {problem.title && `— ${problem.title}`}
        </span>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded shadow-sm transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
};
