import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { Shield } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <PageContainer
      title="Profile & Identity Settings"
      subtitle="Manage unified identity linkages, security preferences, and environment configurations."
    >
      <div className="bg-white border border-pastel-border rounded-2xl p-6 mb-6 shadow-xs">
        <h3 className="text-sm font-bold text-pastel-dark mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-pastel-lavenderDark" />
          LoyaltyOS Unified Identity Security
        </h3>
        <p className="text-xs text-pastel-muted mb-4 leading-relaxed">
          The LoyaltyOS identity model maps authenticated sessions to Supabase PostgreSQL Row Level Security (RLS) policies and PostgreSQL functions.
        </p>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3.5 bg-pastel-ivory border border-pastel-border rounded-xl">
            <div>
              <span className="text-xs font-semibold text-pastel-dark block">Email / Password Identity Provider</span>
              <span className="text-[11px] text-pastel-muted">Supabase Auth (PostgreSQL auth.users integration)</span>
            </div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-semibold bg-pastel-sage text-pastel-sageDark border border-pastel-border rounded-md">
              Active Provider
            </span>
          </div>

          <div className="flex items-center justify-between p-3.5 bg-pastel-ivory border border-pastel-border rounded-xl">
            <div>
              <span className="text-xs font-semibold text-pastel-dark block">Google OAuth Provider</span>
              <span className="text-[11px] text-pastel-muted">Supabase Auth Social Sign-In Minimal Scopes</span>
            </div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-semibold bg-pastel-blue text-pastel-blueDark border border-pastel-border rounded-md">
              Configured
            </span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
