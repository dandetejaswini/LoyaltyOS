import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <PageContainer>
      <div className="text-center py-16">
        <h1 className="text-6xl font-extrabold font-mono text-navy-900 mb-4">404</h1>
        <h2 className="text-xl font-bold text-navy-950 mb-2">Page Not Found</h2>
        <p className="text-sm text-platinum-600 max-w-sm mx-auto mb-6">
          The requested resource path does not exist in LoyaltyOS.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy-900 hover:bg-navy-800 text-white rounded-lg text-xs font-medium transition"
        >
          <ArrowLeft className="w-4 h-4 text-lavender-400" />
          Return to Overview
        </Link>
      </div>
    </PageContainer>
  );
};
