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
    <div className="flex flex-col items-center justify-center p-8 text-center bg-pastel-rose/40 border border-pastel-border rounded-2xl min-h-[220px]">
      <div className="w-12 h-12 rounded-xl bg-pastel-rose flex items-center justify-center text-pastel-roseDark border border-pastel-border mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-pastel-dark mb-1">{title}</h3>
      <p className="text-xs text-pastel-muted max-w-md mb-4 leading-relaxed">{displayMessage}</p>
      {problem?.status && (
        <span className="inline-block px-2.5 py-0.5 rounded-md text-xs font-mono bg-white text-pastel-roseDark border border-pastel-border mb-4 font-semibold">
          HTTP {problem.status} {problem.title && `— ${problem.title}`}
        </span>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-pastel-border hover:bg-pastel-ivory text-pastel-dark text-xs font-bold rounded-xl shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-pastel-muted" />
          Retry Request
        </button>
      )}
    </div>
  );
};
