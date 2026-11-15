import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <PageContainer>
      <div className="text-center py-20 bg-white border border-pastel-border rounded-2xl max-w-xl mx-auto shadow-xs p-8 my-8">
        <span className="px-3 py-1 rounded-full bg-pastel-rose text-pastel-roseDark text-xs font-mono font-bold border border-pastel-border inline-block mb-3">
          Error 404
        </span>
        <h1 className="text-6xl font-extrabold font-mono text-pastel-dark mb-3">404</h1>
        <h2 className="text-xl font-bold text-pastel-dark mb-2">Page Not Found</h2>
        <p className="text-xs text-pastel-muted max-w-sm mx-auto mb-6 leading-relaxed">
          The requested resource path does not exist in the LoyaltyOS operational workspace or public routing directory.
        </p>
        <Link
          to="/"
          className="btn-primary inline-flex items-center gap-2 shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Overview
        </Link>
      </div>
    </PageContainer>
  );
};
