import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { Shield } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <PageContainer
      title="Profile & Identity Settings"
      subtitle="Manage unified identity linkages, security preferences, and environment configurations."
    >
      <div className="bg-white border border-platinum-200 rounded-xl p-6 mb-6 shadow-sm">
        <h3 className="text-sm font-bold text-navy-950 mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-lavender-600" />
          LoyaltyOS Unified Identity Security
        </h3>
        <p className="text-xs text-platinum-600 mb-4">
          The LoyaltyOS identity model maps internal application user IDs to Supabase Auth and Firebase Auth without sharing secrets.
        </p>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3.5 bg-platinum-50 border border-platinum-200 rounded-lg">
            <div>
              <span className="text-xs font-semibold text-navy-950 block">Email / Password Identity Provider</span>
              <span className="text-[11px] text-platinum-500">Supabase Auth (Prepared for Phase 2 Integration)</span>
            </div>
            <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-100 text-amber-800 rounded">
              Pending Phase 2
            </span>
          </div>

          <div className="flex items-center justify-between p-3.5 bg-platinum-50 border border-platinum-200 rounded-lg">
            <div>
              <span className="text-xs font-semibold text-navy-950 block">Google OAuth Provider</span>
              <span className="text-[11px] text-platinum-500">Firebase Auth Minimal Scopes (Prepared for Phase 2 Integration)</span>
            </div>
            <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-100 text-amber-800 rounded">
              Pending Phase 2
            </span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
