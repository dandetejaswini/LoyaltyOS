import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <PageContainer>
      <div className="text-center py-16">
        <h1 className="text-6xl font-bold font-mono text-brand-800 mb-4">404</h1>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">Page Not Found</h2>
        <p className="text-sm text-slate-600 max-w-sm mx-auto mb-6">
          The requested path does not exist in the YottaFlex loyalty portal.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white rounded text-xs font-medium transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Overview
        </Link>
      </div>
    </PageContainer>
  );
};
