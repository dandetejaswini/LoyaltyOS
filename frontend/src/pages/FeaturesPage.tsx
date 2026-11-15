import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  Sparkles,
  Wallet,
  Database,
  Cpu,
  ShieldCheck,
  Users,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Coins,
  Gift,
  Clock,
  Layers,
  FileCheck,
  Scale,
  Lock,
  Eye
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const FeaturesPage: React.FC = () => {
  return (
    <PageContainer
      title="Platform Capabilities & Feature Matrix"
      subtitle="Complete architectural catalog of LoyaltyOS capabilities across customer accounts, financial ledgers, LLIRE intelligence, and dual-key governance."
    >
      {/* Hero Showcase */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-950 via-navy-900 to-navy-950 text-white p-8 sm:p-12 mb-12 border border-navy-800 shadow-xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-lavender-400" />
            <span>Enterprise Feature Directory</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight mb-4 text-white">
            Engineered for Mathematical Certainty & Auditability
          </h1>
          <p className="text-sm sm:text-base text-platinum-300 leading-relaxed max-w-2xl mb-6">
            LoyaltyOS treats customer loyalty points as material balance-sheet liabilities, backed by immutable double-entry ledger bookkeeping, automated forensic anomaly detection, and two-person dual-key remediation.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/workspace"
              className="px-5 py-2.5 bg-lavender-600 hover:bg-lavender-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition shadow-sm flex items-center gap-2"
            >
              Open Live Workspace
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              to="/about"
              className="px-5 py-2.5 bg-navy-800 hover:bg-navy-700 text-platinum-200 border border-navy-700 rounded-lg text-xs font-medium transition"
            >
              Architecture & Invariants
            </Link>
          </div>
        </div>
      </div>

      <div className="space-y-12">
        {/* 1. LOYALTY MANAGEMENT */}
        <section id="loyalty-management" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-lavender-100 text-lavender-700 rounded-lg">
              <Wallet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-navy-950">1. Loyalty Program Management</h2>
              <p className="text-xs text-platinum-500">Core member accounts, tier multiplier progression, and FIFO points lifecycles.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Users className="w-4 h-4 text-lavender-600" />
                Customer Accounts
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Unique loyalty accounts linked to authenticated customer profiles with status flags (ACTIVE, FROZEN, CLOSED) and lifetime statistics.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Scale className="w-4 h-4 text-lavender-600" />
                Dynamic Loyalty Tiers
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Four progressive tiers (Bronze 1.0x, Silver 1.25x, Gold 1.5x, Platinum 2.0x) automatically evaluated on rolling 365-day qualifying spend.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Coins className="w-4 h-4 text-lavender-600" />
                Points Accrual (BR-03)
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Floor-rounding calculations on net eligible spend: <code className="bg-platinum-100 px-1 py-0.5 rounded font-mono text-[10px]">floor(net_spend &times; multiplier)</code>, excluding tax, shipping, and item discounts.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Clock className="w-4 h-4 text-lavender-600" />
                FIFO 365-Day Expiry
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Every earned lot carries an explicit 365-day expiration timestamp. Redemptions consume lots in strict First-In, First-Out order.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Gift className="w-4 h-4 text-lavender-600" />
                Rewards Catalog
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Configurable reward items with point requirements, monetary values, stock quantities, and instant voucher issuance.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Lock className="w-4 h-4 text-lavender-600" />
                Atomic Redemptions (BR-11)
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Pessimistic row-level locking (<code className="font-mono text-[10px] bg-platinum-100 px-1 rounded">FOR UPDATE</code>) ensures zero race conditions or double-spending during concurrent checkouts.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <RefreshCw className="w-4 h-4 text-lavender-600" />
                Idempotent Expiry Batches
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Batch expiration cron routines transition lots safely without double-deduction risks across repeated or interrupted runs.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <FileCheck className="w-4 h-4 text-lavender-600" />
                Voucher Management
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Generates unique digital voucher codes with status tracking and clipboard copy integration for streamlined POS redemption.
              </p>
            </div>
          </div>
        </section>

        {/* 2. LEDGER MANAGEMENT */}
        <section id="ledger-management" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-navy-950">2. Financial Ledger Management</h2>
              <p className="text-xs text-platinum-500">Double-entry accounting, append-only journals, and mathematical balance parity.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Layers className="w-4 h-4 text-emerald-600" />
                Append-Only Journal (BR-02)
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                All point movements post to <code className="bg-platinum-100 px-1 rounded font-mono text-[10px]">points_transactions</code>. Database triggers block UPDATE or DELETE queries.
              </p>
              <span className="badge-success">Trigger-Enforced Immutability</span>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <Scale className="w-4 h-4 text-emerald-600" />
                Proportional Returns (BR-06)
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                Order returns calculate the exact ratio of refunded merchandise and reverse points proportionally. Balances may safely transition negative.
              </p>
              <span className="badge-neutral">Negative Balance Support</span>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-navy-950 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Reconciliation Engine (BR-01)
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                Continuously asserts: <code className="bg-platinum-100 px-1 rounded font-mono text-[10px]">Stored == &Sigma;Credits - &Sigma;Debits == &Sigma;ActiveLots</code> with zero drift tolerance.
              </p>
              <span className="badge-accent">0.00% Drift Guaranteed</span>
            </div>
          </div>
        </section>

        {/* 3. LLIRE INTELLIGENCE */}
        <section id="llire-intelligence" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-lg">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-navy-950">3. LLIRE Forensic Intelligence</h2>
              <p className="text-xs text-platinum-500">Explainable audit and anomaly scanner with five specialized detectors.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">DET-BALANCE-MISMATCH</span>
                <span className="badge-danger">CRITICAL</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Flags discrepancy between the cached <code className="font-mono text-[10px]">current_balance</code> and the algebraic sum of immutable ledger entries.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">DET-OVER-REDEMPTION</span>
                <span className="badge-warning">HIGH</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Detects instances where redemptions exceeded available balance outside of an authorized merchandise return context.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">DET-UNREVERSED-RETURN</span>
                <span className="badge-warning">HIGH</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Identifies returned merchandise orders where the corresponding point reversal transaction failed to post to the ledger.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">DET-DOUBLE-EXPIRY</span>
                <span className="badge-danger">CRITICAL</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Discovers points lots deducted multiple times across batch expiration cron executions, preventing unjustified customer balance losses.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">DET-INCORRECT-TIER</span>
                <span className="badge-neutral">MEDIUM</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Identifies accounts whose active tier does not match their rolling 365-day qualifying spend window.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-sans text-xs font-bold text-navy-950 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-lavender-600" />
                  7-Part Explainability (BR-08)
                </span>
                <span className="badge-accent">Auditable</span>
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Every detected incident outputs summary, invariant violated, drift amount, affected records, hypothesis, dollar exposure, and recommendation.
              </p>
            </div>
          </div>
        </section>

        {/* 4. CORRECTIVE ACTIONS */}
        <section id="corrective-actions" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-purple-100 text-purple-700 rounded-lg">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-navy-950">4. Corrective Actions & Dual-Key Governance</h2>
              <p className="text-xs text-platinum-500">Two-person human-in-the-loop authorization prevents unilateral adjustments.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card-surface">
              <span className="text-[10px] font-mono font-bold text-purple-600 block mb-1">STAGE 1</span>
              <h3 className="text-sm font-bold text-navy-950 mb-1">Formal Case Opening</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Operations Manager reviews forensic evidence, logs timestamped investigator findings, and initiates the remediation workspace.
              </p>
            </div>

            <div className="card-surface">
              <span className="text-[10px] font-mono font-bold text-purple-600 block mb-1">STAGE 2</span>
              <h3 className="text-sm font-bold text-navy-950 mb-1">Action Proposal</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Proposer structures a compensating transaction (ADJUSTMENT_CREDIT, ADJUSTMENT_DEBIT, ACCOUNT_FREEZE) with mandatory audit notes.
              </p>
            </div>

            <div className="card-surface">
              <span className="text-[10px] font-mono font-bold text-purple-600 block mb-1">STAGE 3</span>
              <h3 className="text-sm font-bold text-navy-950 mb-1">Dual-Key Approval (BR-09)</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                An independent second manager must review. The system strictly rejects self-approval (<code className="font-mono text-[10px]">proposer &ne; approver</code>).
              </p>
            </div>

            <div className="card-surface">
              <span className="text-[10px] font-mono font-bold text-purple-600 block mb-1">STAGE 4</span>
              <h3 className="text-sm font-bold text-navy-950 mb-1">Compensating Journal</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">
                Upon approval, an immutable compensating transaction executes, balancing the ledger without altering historical records.
              </p>
            </div>
          </div>
        </section>

        {/* 5. ROLE-BASED ACCESS */}
        <section id="role-based-access" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-navy-100 text-navy-900 rounded-lg">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-navy-950">5. Role-Based Operational Portals</h2>
              <p className="text-xs text-platinum-500">Dedicated operational interfaces tailored for each enterprise stakeholder.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 font-bold text-sm text-navy-950">
                <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                Customer Portal
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                View personal points balance, tier multiplier progress, 365-day expiry countdowns, catalog rewards, and instant voucher redemption.
              </p>
              <span className="badge-neutral font-mono text-[10px]">CUSTOMER Role</span>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 font-bold text-sm text-navy-950">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                Store Operator Desk
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                Lookup accounts, calculate net spend accruals with tier multipliers, execute proportional returns, and provision new customer accounts.
              </p>
              <span className="badge-neutral font-mono text-[10px]">OPERATOR Role</span>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 font-bold text-sm text-navy-950">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                Risk & Fraud Analyst Hub
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                Run LLIRE ledger scans, inspect 7-part forensic evidence drawers, review true positive benchmark metrics, and triage findings.
              </p>
              <span className="badge-neutral font-mono text-[10px]">ANALYST Role</span>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 font-bold text-sm text-navy-950">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                Operations Manager
              </div>
              <p className="text-xs text-platinum-600 leading-relaxed mb-3">
                Manage case investigations, structure corrective actions, review dual-key approval queues, and verify post-remediation reconciliation.
              </p>
              <span className="badge-neutral font-mono text-[10px]">OPERATIONS_MANAGER</span>
            </div>
          </div>
        </section>
      </div>

      {/* Bottom CTA */}
      <div className="mt-14 card-surface-dark text-center relative overflow-hidden">
        <div className="max-w-2xl mx-auto py-4">
          <h2 className="text-xl sm:text-2xl font-bold mb-2 text-white">Explore All Capabilities Live</h2>
          <p className="text-xs text-platinum-300 mb-6 leading-relaxed">
            Switch between user roles in the operational workspace to test order accruals, reward redemptions, LLIRE anomaly detection, and dual-key authorization.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link to="/workspace" className="btn-accent">
              Launch Workspace
            </Link>
            <Link to="/contact" className="btn-outline text-white border-navy-700 bg-navy-900 hover:bg-navy-800">
              Contact Solutions Team
            </Link>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
