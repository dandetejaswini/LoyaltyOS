import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  BookOpen,
  Scale,
  GitBranch,
  Cpu,
  Users,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  UserCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  return (
    <PageContainer
      title="About LoyaltyOS"
      subtitle="The architectural philosophy, financial principles, and engineering design behind the double-entry loyalty management platform."
    >
      {/* 1. PRODUCT INTRODUCTION & HERO */}
      <section className="card-surface-dark mb-10 p-8 sm:p-12 relative overflow-hidden">
        <div className="max-w-3xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-4">
            <BookOpen className="w-3.5 h-3.5 text-lavender-400" />
            <span>Product Overview &amp; Architecture Whitepaper</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-4">
            Financial Ledger Certainty for Enterprise Loyalty Programs
          </h1>
          <p className="text-sm sm:text-base text-platinum-300 leading-relaxed mb-6">
            LoyaltyOS was created to address a foundational flaw in modern retail loyalty software: treating customer reward points as mutable database counter columns rather than auditable financial currency.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link to="/features" className="btn-accent">
              Explore Product Features
            </Link>
            <Link to="/workspace" className="btn-outline text-white border-navy-700 bg-navy-900 hover:bg-navy-800">
              Open Operational Workspace
            </Link>
          </div>
        </div>
      </section>

      <div className="space-y-12">
        {/* 2. PROBLEM STATEMENT & WHY ACCURATE ACCOUNTING MATTERS */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-surface border-rose-200 bg-rose-50/30">
            <div className="flex items-center gap-2 mb-3 text-rose-800 font-bold text-sm">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              The Industry Problem: Mutable Counters
            </div>
            <p className="text-xs text-platinum-700 leading-relaxed mb-3">
              Traditional loyalty solutions store customer point balances as a single integer column (e.g. <code className="bg-rose-100 text-rose-900 px-1 py-0.5 rounded font-mono text-[11px]">points_balance = points_balance + N</code>).
            </p>
            <p className="text-xs text-platinum-700 leading-relaxed mb-3">
              Under high-concurrency checkout traffic, merchandise returns, and lot expiration cycles, this model experiences race conditions, silent balance drift, and unexplainable data loss with zero forensic audit trail.
            </p>
            <div className="p-3 bg-white rounded-lg border border-rose-200 text-rose-900 text-xs font-mono">
              Result: Unverified liabilities on retail corporate balance sheets.
            </div>
          </div>

          <div className="card-surface border-emerald-200 bg-emerald-50/30">
            <div className="flex items-center gap-2 mb-3 text-emerald-800 font-bold text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Why Accurate Loyalty Accounting Matters
            </div>
            <p className="text-xs text-platinum-700 leading-relaxed mb-3">
              Outstanding reward points represent deferred commercial liabilities and customer trust. Under standard financial accounting guidelines, points breakage and redemptions must be quantifiable and mathematically verifiable.
            </p>
            <p className="text-xs text-platinum-700 leading-relaxed mb-3">
              LoyaltyOS solves this by implementing an immutable, append-only double-entry journal where points can never be updated in-place or deleted, guaranteeing mathematical balance parity at all times.
            </p>
            <div className="p-3 bg-white rounded-lg border border-emerald-200 text-emerald-900 text-xs font-mono">
              Guarantee: 0.00% balance drift across journal entries and active FIFO lots.
            </div>
          </div>
        </section>

        {/* 3. PRODUCT VISION & MISSION */}
        <section className="card-surface">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <span className="badge-accent mb-2">PRODUCT VISION</span>
              <h3 className="text-lg font-bold text-navy-950 mb-2">Trust Through Cryptographic &amp; Financial Rigor</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                To establish double-entry ledger bookkeeping and explainable forensic anomaly detection as the universal gold standard for all enterprise retail, financial, and hospitality reward platforms.
              </p>
            </div>
            <div>
              <span className="badge-success mb-2">PRODUCT MISSION</span>
              <h3 className="text-lg font-bold text-navy-950 mb-2">Eliminate Inconsistency, Ensure Accountability</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                To provide retail operators, fraud analysts, and financial executives with complete transparency into points lifecycles, backed by human-in-the-loop dual-key authorization for every balance adjustment.
              </p>
            </div>
          </div>
        </section>

        {/* 4. THE CORE MATHEMATICAL INVARIANT */}
        <section className="card-surface">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-lavender-50 text-lavender-700 rounded-lg">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-navy-950">The Double-Entry Balance Invariant (BR-01)</h3>
              <p className="text-xs text-platinum-500">Continuous equality between three independent data structures</p>
            </div>
          </div>

          <p className="text-xs text-platinum-700 leading-relaxed mb-4">
            At any moment in time, an account's stored current balance must simultaneously equal the net sum of all historical journal entries and the sum of all unexpired active FIFO lots:
          </p>

          <div className="card-surface-dark p-4 font-mono text-xs sm:text-sm space-y-3">
            <div className="p-2.5 bg-navy-900 rounded-lg border border-navy-800 text-emerald-400 font-bold overflow-x-auto">
              Account.current_balance == &Sigma;(Credits: ACCRUAL + ADJUSTMENT_CREDIT) - &Sigma;(Debits: REDEMPTION + REVERSAL + EXPIRY + ADJUSTMENT_DEBIT)
            </div>
            <div className="p-2.5 bg-navy-900 rounded-lg border border-navy-800 text-lavender-300 font-bold overflow-x-auto">
              Account.current_balance == &Sigma;(PointsLot.remaining_points WHERE status = 'ACTIVE' AND expires_at &gt; NOW())
            </div>
          </div>
        </section>

        {/* 5. LLIRE EXPLANATION & HUMAN APPROVAL WORKFLOW */}
        <section className="card-surface">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-navy-950">LLIRE &amp; Dual-Key Governance</h3>
              <p className="text-xs text-platinum-500">Continuous anomaly monitoring paired with human-in-the-loop authorization</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-platinum-600 leading-relaxed">
            <div>
              <h4 className="font-bold text-navy-950 text-sm mb-2 flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-lavender-600" />
                Explainable Anomaly Intelligence
              </h4>
              <p className="mb-2">
                The Loyalty Ledger Intelligence &amp; Reconciliation Engine (LLIRE) executes five deterministic detectors to discover balance mismatches, over-redemptions, unreversed returns, duplicate expirations, and tier anomalies.
              </p>
              <p>
                Every detected incident produces a <strong>7-Part Forensic Report</strong> stating what happened, the exact invariant violated, numerical drift calculation, evidence records, dollar exposure, and recommendations.
              </p>
            </div>

            <div>
              <h4 className="font-bold text-navy-950 text-sm mb-2 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                Two-Person Dual-Key Remediation (BR-09)
              </h4>
              <p className="mb-2">
                To prevent unilateral administrative tampering, no single user can alter customer balances. A proposer creates a compensating transaction proposal with mandatory justification.
              </p>
              <p>
                An independent second Operations Manager must review the audit evidence and approve the action. Proposers are strictly blocked from self-approving their own proposals.
              </p>
            </div>
          </div>
        </section>

        {/* 6. FOUR USER ROLES */}
        <section className="card-surface">
          <h3 className="text-base font-bold text-navy-950 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-navy-700" />
            Four Role Perspectives
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3.5 bg-platinum-50 rounded-xl border border-platinum-200">
              <span className="font-bold text-navy-950 block mb-1">Customer Portal</span>
              <p className="text-platinum-600 leading-relaxed">
                Empowers members to view points balance, tier multipliers, 365-day expiry countdowns, catalog rewards, and instant voucher redemptions.
              </p>
            </div>

            <div className="p-3.5 bg-platinum-50 rounded-xl border border-platinum-200">
              <span className="font-bold text-navy-950 block mb-1">Store Operator Desk</span>
              <p className="text-platinum-600 leading-relaxed">
                Enables store cashiers to lookup customer accounts, process net spend accruals with floor-rounding, and execute proportional return clawbacks.
              </p>
            </div>

            <div className="p-3.5 bg-platinum-50 rounded-xl border border-platinum-200">
              <span className="font-bold text-navy-950 block mb-1">Analyst Hub (LLIRE)</span>
              <p className="text-platinum-600 leading-relaxed">
                Equips fraud &amp; risk analysts to trigger automated ledger anomaly scans, inspect 7-part forensic evidence drawers, and evaluate precision/recall benchmarks.
              </p>
            </div>

            <div className="p-3.5 bg-platinum-50 rounded-xl border border-platinum-200">
              <span className="font-bold text-navy-950 block mb-1">Operations Manager</span>
              <p className="text-platinum-600 leading-relaxed">
                Permits authorized directors to conduct formal investigations, structure corrective actions, and execute dual-key approvals without historical data edits.
              </p>
            </div>
          </div>
        </section>

        {/* 7. TECHNOLOGY ARCHITECTURE */}
        <section className="card-surface-dark p-6 sm:p-8">
          <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-lavender-400" />
            Full-Stack Technology Architecture
          </h3>
          <p className="text-xs text-platinum-400 mb-6">
            Engineered with modern, high-throughput components across the database, backend, and frontend tiers.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 bg-navy-900 rounded-xl border border-navy-800">
              <span className="text-lavender-400 font-bold block mb-1">Frontend Tier</span>
              <span className="text-platinum-300 block mb-2 font-sans text-xs">React 18 &bull; TypeScript &bull; Vite &bull; Tailwind CSS</span>
              <p className="text-[11px] text-platinum-400 font-sans leading-relaxed">
                Responsive single-page application with server-state handling, accessible component design system, and multi-persona operational consoles.
              </p>
            </div>

            <div className="p-4 bg-navy-900 rounded-xl border border-navy-800">
              <span className="text-emerald-400 font-bold block mb-1">Backend API Tier</span>
              <span className="text-platinum-300 block mb-2 font-sans text-xs">FastAPI &bull; Python 3.12 &bull; SQLAlchemy Async &bull; Pydantic v2</span>
              <p className="text-[11px] text-platinum-400 font-sans leading-relaxed">
                High-performance asynchronous REST endpoints, RFC 7807 ProblemDetails error responses, and dependency-injected RBAC authorization.
              </p>
            </div>

            <div className="p-4 bg-navy-900 rounded-xl border border-navy-800">
              <span className="text-amber-300 font-bold block mb-1">Persistence &amp; Triggers</span>
              <span className="text-platinum-300 block mb-2 font-sans text-xs">Supabase PostgreSQL &bull; Row-Level Triggers &bull; RLS</span>
              <p className="text-[11px] text-platinum-400 font-sans leading-relaxed">
                Engine-level immutability triggers (<code className="font-mono text-[10px]">trg_prevent_points_transactions_update_delete</code>) and multi-tenant Row-Level Security policies.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* Bottom CTA */}
      <div className="mt-12 text-center">
        <Link to="/workspace" className="btn-accent px-6 py-3 text-xs uppercase tracking-wider font-bold">
          Open LoyaltyOS Workspace
        </Link>
      </div>
    </PageContainer>
  );
};
