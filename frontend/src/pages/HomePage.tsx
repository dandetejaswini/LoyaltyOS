import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Shield, Database, Lock, RefreshCw, ArrowRight } from 'lucide-react';
import { apiClient, HealthResponse } from '@/services/apiClient';

export const HomePage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getHealth()
      .then((res) => setHealth(res))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  }, []);

  const features = [
    {
      icon: <Shield className="w-6 h-6 text-brand-600" />,
      title: 'Append-Only Ledger Journal',
      desc: 'All point credits and debits are recorded as immutable financial journal entries. Zero in-place mutations or silent historical deletions.',
    },
    {
      icon: <RefreshCw className="w-6 h-6 text-brand-600" />,
      title: 'FIFO Lot Tracking & Idempotent Expiry',
      desc: 'Points lots are provisioned with 365-day expiry dates. Redemptions consume lots in strict FIFO order; batch expiration runs idempotently.',
    },
    {
      icon: <Lock className="w-6 h-6 text-brand-600" />,
      title: 'Concurrency-Safe Atomic Redemptions',
      desc: 'Pessimistic row locking on loyalty accounts prevents double-spending and race conditions under simultaneous traffic.',
    },
    {
      icon: <Database className="w-6 h-6 text-brand-600" />,
      title: 'Proportional Return Reversals',
      desc: 'Order returns reverse earned points strictly proportional to eligible net spend, maintaining foreign-key links to original accruals.',
    },
  ];

  return (
    <PageContainer>
      {/* Hero Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-8 sm:p-12 mb-8 shadow-sm">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold mb-4">
            <span className="w-2 h-2 rounded-full bg-brand-600"></span>
            Phase 1 Foundation Operational
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight mb-4">
            Financial-Grade Loyalty Ledger Platform
          </h1>
          <p className="text-base sm:text-lg text-slate-600 mb-8 leading-relaxed">
            Accrue, redeem, expire, and reverse customer loyalty points with complete auditability, mathematical reconciliation, and automated forensic anomaly detection.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-sm font-semibold transition shadow-sm"
            >
              Open Operations Dashboard
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/about"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-medium transition"
            >
              Architecture & Rules
            </Link>
          </div>
        </div>
      </div>

      {/* Live System Health Diagnostic Card */}
      <div className="bg-slate-900 text-white rounded-xl p-6 mb-8 border border-slate-800 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold tracking-wider uppercase text-brand-300">Live Backend Verification</h3>
            <p className="text-xs text-slate-400 mt-0.5">Real-time status reported by FastAPI Application Tier</p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
              {loading ? 'Checking...' : health?.status || 'Disconnected'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-xs font-mono">
          <div className="bg-slate-850 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px] mb-1">Application Version</span>
            <span className="text-white font-semibold">{health?.version || 'v1.0.0'}</span>
          </div>
          <div className="bg-slate-850 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px] mb-1">Environment</span>
            <span className="text-white font-semibold">{health?.environment || 'development'}</span>
          </div>
          <div className="bg-slate-850 p-3 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px] mb-1">Database State</span>
            <span className="text-amber-300 font-semibold">
              {health?.database.status || 'not_configured'} (Phase 2 Prep)
            </span>
          </div>
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((f, i) => (
          <div key={i} className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center mb-4">
              {f.icon}
            </div>
            <h3 className="text-base font-semibold text-slate-900 mb-2">{f.title}</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </PageContainer>
  );
};
