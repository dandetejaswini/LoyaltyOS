import React, { useState, useEffect } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';
import {
  Wallet,
  Store,
  BarChart3,
  ShieldAlert,
  UserCheck,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { CustomerDashboard } from '@/components/dashboards/CustomerDashboard';
import { OperatorDashboard } from '@/components/dashboards/OperatorDashboard';
import { AnalystDashboard } from '@/components/dashboards/AnalystDashboard';
import { OpsManagerDashboard } from '@/components/dashboards/OpsManagerDashboard';
import { Role } from '@/types/auth';
import { UserProfileResponse } from '@/services/apiClient';

export const DashboardPage: React.FC = () => {
  const { user, role, simulatePersona, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'customer' | 'operator' | 'analyst' | 'ops_manager'>('analyst');
  const [opsMgrIndex, setOpsMgrIndex] = useState<1 | 2>(1);

  // Synchronize tab when role changes externally
  useEffect(() => {
    if (role === 'CUSTOMER') setActiveTab('customer');
    else if (role === 'OPERATOR') setActiveTab('operator');
    else if (role === 'ANALYST') setActiveTab('analyst');
    else if (role === 'OPERATIONS_MANAGER') setActiveTab('ops_manager');
  }, [role]);

  const perspectives = [
    {
      id: 'customer' as const,
      role: 'CUSTOMER' as Role,
      label: 'Customer Portal',
      persona: 'Alice Walker',
      roleDesc: 'Loyalty Member (Gold)',
      icon: <Wallet className="w-4 h-4 text-pastel-dark" />,
      activeColor: 'bg-pastel-lavender text-pastel-dark border-pastel-border font-bold'
    },
    {
      id: 'operator' as const,
      role: 'OPERATOR' as Role,
      label: 'Store Operator Desk',
      persona: 'Marcus Brody',
      roleDesc: 'Point-of-Sale Specialist',
      icon: <Store className="w-4 h-4 text-pastel-dark" />,
      activeColor: 'bg-pastel-blue text-pastel-dark border-pastel-border font-bold'
    },
    {
      id: 'analyst' as const,
      role: 'ANALYST' as Role,
      label: 'Risk & Fraud Analyst Hub',
      persona: 'Sarah Chen',
      roleDesc: 'Forensic Auditor (LLIRE)',
      icon: <BarChart3 className="w-4 h-4 text-pastel-dark" />,
      activeColor: 'bg-pastel-peach text-pastel-dark border-pastel-border font-bold'
    },
    {
      id: 'ops_manager' as const,
      role: 'OPERATIONS_MANAGER' as Role,
      label: 'Operations Manager Console',
      persona: opsMgrIndex === 1 ? 'Eleanor Vance (Proposer)' : 'David Ross (Approver)',
      roleDesc: 'Dual-Key Authority',
      icon: <ShieldAlert className="w-4 h-4 text-pastel-dark" />,
      activeColor: 'bg-pastel-sage text-pastel-dark border-pastel-border font-bold'
    }
  ];

  const handleSelectPerspective = (tabId: 'customer' | 'operator' | 'analyst' | 'ops_manager', roleTarget: Role) => {
    setActiveTab(tabId);
    if (tabId === 'ops_manager') {
      simulatePersona('OPERATIONS_MANAGER', opsMgrIndex);
    } else {
      simulatePersona(roleTarget);
    }
  };

  const handleToggleOpsMgr = (idx: 1 | 2) => {
    setOpsMgrIndex(idx);
    simulatePersona('OPERATIONS_MANAGER', idx);
  };

  // Provide fallback user profile for UI presentation if no real user is signed in
  const effectiveUser: UserProfileResponse = user ? {
    ...user,
    id: user.id || 'USR-AUTH-001',
    email: user.email || 'user@loyaltyos.internal',
    full_name: user.full_name || user.email?.split('@')[0] || 'Loyalty Member',
    role: (activeTab === 'customer' ? 'CUSTOMER' :
          activeTab === 'operator' ? 'OPERATOR' :
          activeTab === 'analyst' ? 'ANALYST' : 'OPERATIONS_MANAGER') as Role,
    is_active: true,
    created_at: user.created_at || new Date().toISOString(),
    customer: user.customer || {
      customer_id: 'CUST-' + (user.id || '001').substring(0, 8).toUpperCase(),
      email: user.email,
      first_name: (user.full_name || 'Member').split(' ')[0],
      last_name: (user.full_name || '').split(' ').slice(1).join(' ') || '',
      status: 'ACTIVE',
      loyalty_account: {
        account_id: 'LOY-' + (user.id || '001').substring(0, 8).toUpperCase(),
        tier_id: 'TIER-GOLD',
        current_balance: 1450,
        lifetime_accrued: 2200,
        lifetime_redeemed: 750,
        qualifying_spend: 1450.00,
        status: 'ACTIVE',
      }
    }
  } : {
    id: activeTab === 'customer' ? 'USR-CUST-001' :
        activeTab === 'operator' ? 'USR-OPR-001' :
        activeTab === 'analyst' ? 'USR-ANA-001' :
        opsMgrIndex === 1 ? 'USR-MGR-001' : 'USR-MGR-002',
    email: activeTab === 'customer' ? 'member@loyaltyos.internal' :
           activeTab === 'operator' ? 'operator@loyaltyos.internal' :
           activeTab === 'analyst' ? 'analyst@loyaltyos.internal' :
           opsMgrIndex === 1 ? 'eleanor@loyaltyos.internal' : 'david@loyaltyos.internal',
    full_name: activeTab === 'customer' ? 'Loyalty Member' :
               activeTab === 'operator' ? 'Store Operator' :
               activeTab === 'analyst' ? 'Risk Analyst' :
               opsMgrIndex === 1 ? 'Eleanor Vance' : 'David Ross',
    role: (activeTab === 'customer' ? 'CUSTOMER' :
          activeTab === 'operator' ? 'OPERATOR' :
          activeTab === 'analyst' ? 'ANALYST' : 'OPERATIONS_MANAGER') as Role,
    is_active: true,
    created_at: new Date().toISOString()
  };

  const currentPerspective = perspectives.find(p => p.id === activeTab);

  return (
    <PageContainer
      title="LoyaltyOS Operations & Intelligence Workspace"
      subtitle="Interactive multi-persona portal for double-entry ledger oversight, customer redemption, LLIRE fraud intelligence, and dual-key remediation."
    >
      {/* Unified Perspective Switcher Header */}
      <div className="bg-white border border-pastel-border rounded-2xl p-4 sm:p-5 mb-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-3.5 h-3.5 text-pastel-lavenderDark" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-pastel-muted font-mono">
                Workspace Persona Switcher:
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-pastel-sageDark"></span>
              <span className="text-pastel-dark font-medium">
                {user ? (
                  <span>
                    Authenticated Session: <strong className="text-pastel-dark font-bold">{user.full_name || user.email}</strong> &bull; Viewing <span className="text-pastel-muted">{currentPerspective?.label}</span>
                  </span>
                ) : (
                  <span>
                    Interactive Persona: <strong className="text-pastel-dark font-bold">{currentPerspective?.persona}</strong> &bull; <span className="text-pastel-muted">{currentPerspective?.roleDesc}</span>
                  </span>
                )}
              </span>
            </div>
          </div>

          {/* Perspective Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {perspectives.map((p) => {
              const isSelected = activeTab === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPerspective(p.id, p.role)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs transition border ${
                    isSelected
                      ? p.activeColor + ' shadow-xs'
                      : 'bg-white text-pastel-dark border-pastel-border hover:bg-pastel-ivory'
                  }`}
                >
                  {p.icon}
                  <span>{p.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dual-Key Segregation Switcher for Ops Manager */}
        {activeTab === 'ops_manager' && (
          <div className="mt-4 pt-3.5 border-t border-pastel-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-pastel-lavender/30 -mx-4 -mb-4 p-4 rounded-b-2xl">
            <div className="flex items-center gap-2 text-pastel-dark">
              <UserCheck className="w-4 h-4 text-pastel-lavenderDark" />
              <span><strong>BR-09 Dual-Key Segregation:</strong> Switch between Manager 1 (Proposer) and Manager 2 (Approver) to review and approve actions.</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => handleToggleOpsMgr(1)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                  opsMgrIndex === 1
                    ? 'bg-pastel-peach text-pastel-dark border-pastel-border shadow-xs'
                    : 'bg-white text-pastel-dark border-pastel-border hover:bg-pastel-ivory'
                }`}
              >
                Eleanor (Proposer)
              </button>
              <button
                onClick={() => handleToggleOpsMgr(2)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                  opsMgrIndex === 2
                    ? 'bg-pastel-sage text-pastel-dark border-pastel-border shadow-xs'
                    : 'bg-white text-pastel-dark border-pastel-border hover:bg-pastel-ivory'
                }`}
              >
                David (Approver)
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Role-Specific Dashboard View */}
      {isLoading ? (
        <div className="bg-white border border-pastel-border rounded-2xl p-12 text-center text-pastel-muted text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-pastel-lavenderDark" />
          <span>Synchronizing role session...</span>
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
