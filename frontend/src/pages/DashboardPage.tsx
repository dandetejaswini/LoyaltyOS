import React, { useState } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { Wallet, ShieldAlert, BarChart3, Store } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [activeRole, setActiveRole] = useState<'customer' | 'operator' | 'analyst' | 'ops_manager'>('customer');

  const roleTabs = [
    { id: 'customer', label: 'Customer Portal', icon: <Wallet className="w-4 h-4" /> },
    { id: 'operator', label: 'Store Operator Desk', icon: <Store className="w-4 h-4" /> },
    { id: 'analyst', label: 'Analyst Hub', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'ops_manager', label: 'Ops Manager Console', icon: <ShieldAlert className="w-4 h-4" /> },
  ];

  return (
    <PageContainer
      title="Operations & Loyalty Dashboard"
      subtitle="Role-tailored interfaces for ledger oversight, redemptions, returns, and reconciliation."
    >
      {/* Role Navigation Tabs */}
      <div className="flex border-b border-slate-200 mb-6 space-x-1 overflow-x-auto">
        {roleTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveRole(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
              activeRole === tab.id
                ? 'border-brand-700 text-brand-800 bg-brand-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Role Content Placeholder Cards */}
      <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm">
        {activeRole === 'customer' && (
          <div>
            <h3 className="text-base font-semibold text-slate-900 mb-2">Customer Account View Foundation</h3>
            <p className="text-xs text-slate-600 mb-6">
              Displays real-time points balance, tier progress bar, 365-day points expiring countdown, and catalog reward redemption modals.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded border border-slate-200">
                <span className="text-[11px] text-slate-500 block mb-1">Available Points</span>
                <span className="text-2xl font-bold font-mono text-slate-900">0 PTS</span>
              </div>
              <div className="p-4 bg-slate-50 rounded border border-slate-200">
                <span className="text-[11px] text-slate-500 block mb-1">Current Tier</span>
                <span className="text-2xl font-bold text-amber-800">Bronze</span>
              </div>
              <div className="p-4 bg-slate-50 rounded border border-slate-200">
                <span className="text-[11px] text-slate-500 block mb-1">Expiring within 30 Days</span>
                <span className="text-2xl font-bold font-mono text-slate-500">0 PTS</span>
              </div>
            </div>
          </div>
        )}

        {activeRole === 'operator' && (
          <div>
            <h3 className="text-base font-semibold text-slate-900 mb-2">Store Operator Desk Foundation</h3>
            <p className="text-xs text-slate-600 mb-4">
              Allows cashiers and fulfillment associates to process full/partial order returns with automatic proportional points reversal linked to the parent accrual transaction.
            </p>
            <div className="p-4 bg-brand-50 border border-brand-200 rounded text-xs text-brand-900">
              Operator return scanning tools and voucher inspection will be populated in Phase 6.
            </div>
          </div>
        )}

        {activeRole === 'analyst' && (
          <div>
            <h3 className="text-base font-semibold text-slate-900 mb-2">Analyst Hub Foundation</h3>
            <p className="text-xs text-slate-600 mb-4">
              Monitors active loyalty program financial liability (unredeemed active points) and points breakage velocity over rolling 365-day cycles.
            </p>
            <div className="p-4 bg-brand-50 border border-brand-200 rounded text-xs text-brand-900">
              Liability charts and promotional rule configuration engines will be populated in Phase 6.
            </div>
          </div>
        )}

        {activeRole === 'ops_manager' && (
          <div>
            <h3 className="text-base font-semibold text-slate-900 mb-2">Operations Manager Console Foundation</h3>
            <p className="text-xs text-slate-600 mb-4">
              Central hub for the Loyalty Ledger Intelligence & Reconciliation Engine (LLIRE). Displays detected anomalies, blast radius diagnostics, and dual-key corrective action approval queues.
            </p>
            <div className="p-4 bg-brand-50 border border-brand-200 rounded text-xs text-brand-900">
              Anomaly review queues and dual-key compensation approval modals will be populated in Phase 6.
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
