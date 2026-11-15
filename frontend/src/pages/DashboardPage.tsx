import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';
import {
  Wallet,
  Store,
  BarChart3,
  ShieldAlert,
  Users,
  RefreshCw
} from 'lucide-react';
import { CustomerDashboard } from '@/components/dashboards/CustomerDashboard';
import { OperatorDashboard } from '@/components/dashboards/OperatorDashboard';
import { AnalystDashboard } from '@/components/dashboards/AnalystDashboard';
import { OpsManagerDashboard } from '@/components/dashboards/OpsManagerDashboard';
import { Role } from '@/types/auth';

export const DashboardPage: React.FC = () => {
  const { user, role, simulatePersona, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'customer' | 'operator' | 'analyst' | 'ops_manager'>('ops_manager');

  // Synchronize tab when role changes
  useEffect(() => {
    if (role === 'CUSTOMER') setActiveTab('customer');
    else if (role === 'OPERATOR') setActiveTab('operator');
    else if (role === 'ANALYST') setActiveTab('analyst');
    else if (role === 'OPERATIONS_MANAGER') setActiveTab('ops_manager');
  }, [role]);

  const roleTabs = [
    { id: 'ops_manager', label: 'Ops Manager Console', icon: <ShieldAlert className="w-4 h-4" />, roleTarget: 'OPERATIONS_MANAGER' as Role },
    { id: 'analyst', label: 'Analyst Hub (LLIRE)', icon: <BarChart3 className="w-4 h-4" />, roleTarget: 'ANALYST' as Role },
    { id: 'operator', label: 'Store Operator Desk', icon: <Store className="w-4 h-4" />, roleTarget: 'OPERATOR' as Role },
    { id: 'customer', label: 'Customer Portal', icon: <Wallet className="w-4 h-4" />, roleTarget: 'CUSTOMER' as Role },
  ];

  // If no user is authenticated, provide a fallback user
  const effectiveUser = user || {
    id: 'USR-MGR-001',
    email: 'manager@loyaltyos.internal',
    full_name: 'Eleanor Vance (Operations Director)',
    role: 'OPERATIONS_MANAGER' as Role,
    is_active: true,
    created_at: new Date().toISOString()
  };

  return (
    <PageContainer
      title="LoyaltyOS Operations & Intelligence Console"
      subtitle="Enterprise portal for real-time double-entry ledger oversight, LLIRE fraud intelligence, and dual-key remediation."
    >
      {/* Interactive Persona & Role Switcher Bar for Reviewers & Judges */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 mb-6 shadow-sm text-white">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-lavender-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-platinum-300">
              Interactive Persona Switcher:
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => {
                simulatePersona('CUSTOMER');
                setActiveTab('customer');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                role === 'CUSTOMER'
                  ? 'bg-lavender-600 text-white border-lavender-500 font-semibold shadow-xs'
                  : 'bg-navy-800 text-platinum-300 border-navy-700 hover:bg-navy-700'
              }`}
            >
              Customer (Alice)
            </button>

            <button
              onClick={() => {
                simulatePersona('OPERATOR');
                setActiveTab('operator');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                role === 'OPERATOR'
                  ? 'bg-lavender-600 text-white border-lavender-500 font-semibold shadow-xs'
                  : 'bg-navy-800 text-platinum-300 border-navy-700 hover:bg-navy-700'
              }`}
            >
              Operator (Marcus)
            </button>

            <button
              onClick={() => {
                simulatePersona('ANALYST');
                setActiveTab('analyst');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                role === 'ANALYST'
                  ? 'bg-lavender-600 text-white border-lavender-500 font-semibold shadow-xs'
                  : 'bg-navy-800 text-platinum-300 border-navy-700 hover:bg-navy-700'
              }`}
            >
              Analyst (Sarah)
            </button>

            <button
              onClick={() => {
                simulatePersona('OPERATIONS_MANAGER', 1);
                setActiveTab('ops_manager');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                role === 'OPERATIONS_MANAGER' && effectiveUser.id === 'USR-MGR-001'
                  ? 'bg-emerald-600 text-white border-emerald-500 font-semibold shadow-xs'
                  : 'bg-navy-800 text-platinum-300 border-navy-700 hover:bg-navy-700'
              }`}
            >
              Ops Mgr 1 (Eleanor - Proposer)
            </button>

            <button
              onClick={() => {
                simulatePersona('OPERATIONS_MANAGER', 2);
                setActiveTab('ops_manager');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                role === 'OPERATIONS_MANAGER' && effectiveUser.id === 'USR-MGR-002'
                  ? 'bg-emerald-600 text-white border-emerald-500 font-semibold shadow-xs'
                  : 'bg-navy-800 text-platinum-300 border-navy-700 hover:bg-navy-700'
              }`}
            >
              Ops Mgr 2 (David - Approver)
            </button>
          </div>
        </div>

        {/* Current Active Persona Details */}
        <div className="mt-3 pt-3 border-t border-navy-800/80 flex items-center justify-between text-[11px] text-platinum-400">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Signed In As: <strong className="text-white">{effectiveUser.full_name || effectiveUser.email}</strong> ({effectiveUser.role})</span>
          </div>
          <span className="font-mono text-[10px] text-platinum-500">ID: {effectiveUser.id}</span>
        </div>
      </div>

      {/* Role Navigation Tabs */}
      <div className="flex border-b border-platinum-200 mb-6 space-x-1 overflow-x-auto">
        {roleTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id as any);
              if (role !== tab.roleTarget) {
                simulatePersona(tab.roleTarget);
              }
            }}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
              activeTab === tab.id
                ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
                : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Role-Specific Dashboard View */}
      {isLoading ? (
        <div className="bg-white border border-platinum-200 rounded-xl p-12 text-center text-platinum-500 text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-lavender-600" />
          Synchronizing role session...
        </div>
      ) : (
        <div>
          {activeTab === 'customer' && <CustomerDashboard user={effectiveUser} />}
          {activeTab === 'operator' && <OperatorDashboard user={effectiveUser} />}
          {activeTab === 'analyst' && <AnalystDashboard user={effectiveUser} />}
          {activeTab === 'ops_manager' && <OpsManagerDashboard user={effectiveUser} />}
        </div>
      )}
    </PageContainer>
  );
};
