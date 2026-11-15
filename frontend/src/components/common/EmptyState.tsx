import React, { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-white border border-dashed border-pastel-border rounded-2xl min-h-[220px]">
      <div className="w-12 h-12 rounded-xl bg-pastel-ivory flex items-center justify-center text-pastel-muted border border-pastel-border mb-3">
        {icon || <Inbox className="w-6 h-6 text-pastel-muted" />}
      </div>
      <h3 className="text-base font-bold text-pastel-dark mb-1">{title}</h3>
      <p className="text-xs text-pastel-muted max-w-sm mb-4 leading-relaxed">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};
