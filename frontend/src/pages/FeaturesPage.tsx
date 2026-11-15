import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  Sparkles,
  Wallet,
  Database,
  Cpu,
  ShieldCheck,
  Users,
  ArrowRight,
  RefreshCw,
  Clock,
  FileCheck,
  Scale
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const FeaturesPage: React.FC = () => {
  return (
    <PageContainer
      title="Platform Capabilities & Feature Matrix"
      subtitle="Complete architectural catalog of LoyaltyOS capabilities across customer accounts, financial ledgers, LLIRE intelligence, and dual-key governance."
    >
      {/* Hero Showcase (Bright Pastel) */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-pastel-ivory via-pastel-lavender/30 to-pastel-blue/30 text-pastel-dark p-8 sm:p-12 mb-12 border border-pastel-border shadow-xs">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-pastel-border text-pastel-dark text-xs font-semibold mb-4 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-pastel-lavenderDark" />
            <span>Enterprise Feature Directory</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight mb-4 text-pastel-dark">
            Engineered for Mathematical Certainty &amp; Auditability
          </h1>
          <p className="text-sm sm:text-base text-pastel-muted leading-relaxed max-w-2xl mb-6">
            LoyaltyOS treats customer loyalty points as material balance-sheet liabilities, backed by immutable double-entry ledger bookkeeping, automated forensic anomaly detection, and two-person dual-key remediation.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/workspace"
              className="btn-primary"
            >
              <span>Open Live Workspace</span>
              <ArrowRight className="w-3.5 h-3.5 text-pastel-dark" />
            </Link>
            <Link
              to="/about"
              className="btn-outline"
            >
              <span>Architecture &amp; Invariants</span>
            </Link>
          </div>
        </div>
      </div>

      <div className="space-y-14">
        {/* 1. LOYALTY POINTS & REWARDS MANAGEMENT */}
        <section id="loyalty-management" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-pastel-lavender text-pastel-dark rounded-lg border border-pastel-border">
              <Wallet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-pastel-dark">1. Loyalty Points &amp; Rewards Management</h2>
              <p className="text-xs text-pastel-muted">Core member accounts, tier multiplier progression, and FIFO points lifecycles.</p>
            </div>
          </div>

          {/* Visual Showcase for Points & Rewards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="rounded-xl overflow-hidden border border-pastel-border bg-white p-2.5 shadow-xs">
              <img
                src="/assets/feature_points.jpg"
                alt="Loyalty points accumulation, net spend calculations, and balance tracking"
                className="w-full h-48 object-cover rounded-lg"
                loading="lazy"
              />
              <div className="p-3">
                <div className="text-xs font-bold text-pastel-dark">Points Accrual &amp; Floor-Rounding (BR-03)</div>
                <div className="text-[11px] text-pastel-muted mt-1 leading-relaxed">
                  Points accrue exclusively on eligible merchandise spend: <code className="bg-pastel-ivory px-1 rounded text-pastel-dark font-mono text-[10px]">&#8970;net_spend &times; multiplier&#8971;</code>. Sales tax, shipping, and order discounts are safely excluded.
                </div>
              </div>
            </div>

            <div className="rounded-xl overflow-hidden border border-pastel-border bg-white p-2.5 shadow-xs">
              <img
                src="/assets/feature_rewards.jpg"
                alt="Rewards redemption catalog, atomic voucher issuance, and member perks"
                className="w-full h-48 object-cover rounded-lg"
                loading="lazy"
              />
              <div className="p-3">
                <div className="text-xs font-bold text-pastel-dark">Rewards Catalog &amp; Single-Use Vouchers</div>
                <div className="text-[11px] text-pastel-muted mt-1 leading-relaxed">
                  Atomic redemption under <code className="bg-pastel-ivory px-1 rounded text-pastel-dark font-mono text-[10px]">SELECT FOR UPDATE</code> locks prevents race conditions and issues unique single-use vouchers.
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                <Users className="w-4 h-4 text-pastel-sageDark" />
                Customer Accounts
              </div>
              <p className="text-xs text-pastel-muted leading-relaxed">
                Unique loyalty accounts linked to authenticated customer profiles with status flags (ACTIVE, FROZEN, CLOSED) and lifetime statistics.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                <Scale className="w-4 h-4 text-pastel-blueDark" />
                Dynamic Loyalty Tiers
              </div>
              <p className="text-xs text-pastel-muted leading-relaxed">
                Four progressive tiers (Bronze 1.0x, Silver 1.25x, Gold 1.5x, Platinum 2.0x) automatically evaluated on rolling 365-day qualifying spend.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                <Clock className="w-4 h-4 text-pastel-lavenderDark" />
                FIFO 365-Day Expiry
              </div>
              <p className="text-xs text-pastel-muted leading-relaxed">
                Every earned lot carries an explicit 365-day expiration timestamp. Redemptions consume lots in strict First-In, First-Out order.
              </p>
            </div>

            <div className="card-surface">
              <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                <RefreshCw className="w-4 h-4 text-pastel-roseDark" />
                Idempotent Expiry Batches
              </div>
              <p className="text-xs text-pastel-muted leading-relaxed">
                Batch expiration routines transition lots safely without double-deduction risks across repeated or interrupted runs.
              </p>
            </div>
          </div>
        </section>

        {/* 2. DIGITAL TRANSACTION LEDGER */}
        <section id="ledger-management" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-pastel-sage text-pastel-dark rounded-lg border border-pastel-border">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-pastel-dark">2. Double-Entry Financial Ledger</h2>
              <p className="text-xs text-pastel-muted">Immutable journals, FIFO lot allocation, and balance reconciliation.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center mb-6">
            <div className="lg:col-span-5">
              <div className="rounded-xl overflow-hidden border border-pastel-border bg-white p-2.5 shadow-xs">
                <img
                  src="/assets/feature_ledger.jpg"
                  alt="Digital transaction ledger, double-entry financial accounting, and balance sheet auditing"
                  className="w-full h-56 object-cover rounded-lg"
                  loading="lazy"
                />
                <div className="p-3">
                  <div className="text-xs font-bold text-pastel-dark">Append-Only Double-Entry Journal</div>
                  <div className="text-[11px] text-pastel-muted mt-0.5">PostgreSQL engine triggers block all UPDATE and DELETE mutations</div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="card-surface">
                <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                  <FileCheck className="w-4 h-4 text-pastel-sageDark" />
                  Append-Only Journal
                </div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Every credit, debit, return, and expiration posts to <code className="bg-pastel-ivory px-1 rounded text-pastel-dark font-mono text-[10px]">points_transactions</code> with cryptographic UUIDs and running balances.
                </p>
              </div>

              <div className="card-surface">
                <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                  <Scale className="w-4 h-4 text-pastel-blueDark" />
                  Three-Way Invariant Check
                </div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Reconciliation validates stored balances equal the algebraic journal sum and the sum of active FIFO lots with zero mathematical drift.
                </p>
              </div>

              <div className="card-surface">
                <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                  <RefreshCw className="w-4 h-4 text-pastel-peachDark" />
                  Proportional Return Reversals
                </div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Refunds claw back points proportionally. When points were already redeemed, balances safely go negative without crashing store operations.
                </p>
              </div>

              <div className="card-surface">
                <div className="flex items-center gap-2 mb-2 text-pastel-dark font-bold text-sm">
                  <ShieldCheck className="w-4 h-4 text-pastel-roseDark" />
                  5 Engine Triggers
                </div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  PostgreSQL engine triggers enforce immutability on transactions, audit events, lot allocations, batch items, and point lot ceilings.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 3. AI-POWERED ANOMALY DETECTION (LLIRE) */}
        <section id="llire-intelligence" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-pastel-blue text-pastel-dark rounded-lg border border-pastel-border">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-pastel-dark">3. AI-Powered Anomaly Detection (LLIRE)</h2>
              <p className="text-xs text-pastel-muted">Continuous ledger anomaly scanning, 7-part explainability, and ground-truth evaluation.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center mb-6">
            <div className="lg:col-span-5 order-last lg:order-first grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="card-surface">
                <div className="text-xs font-bold text-pastel-roseDark mb-1">DET-BALANCE-MISMATCH</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Detects drift between cached account balance and historical transaction ledger sum.
                </p>
              </div>
              <div className="card-surface">
                <div className="text-xs font-bold text-pastel-peachDark mb-1">DET-OVER-REDEMPTION</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Flags deficit accounts where lifetime redemptions exceed lifetime accruals without returns.
                </p>
              </div>
              <div className="card-surface">
                <div className="text-xs font-bold text-pastel-blueDark mb-1">DET-UNREVERSED-RETURN</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Discovers merchandise returns lacking corresponding points reversal debits in the journal.
                </p>
              </div>
              <div className="card-surface">
                <div className="text-xs font-bold text-pastel-lavenderDark mb-1">DET-DOUBLE-EXPIRY</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Catches points lots subjected to repeated expiration deductions across batch runs.
                </p>
              </div>
            </div>

            <div className="lg:col-span-7">
              <div className="rounded-xl overflow-hidden border border-pastel-border bg-white p-2.5 shadow-xs">
                <img
                  src="/assets/feature_ai.jpg"
                  alt="AI anomaly detection graph, algorithmic risk scoring, and intelligence monitoring"
                  className="w-full h-56 object-cover rounded-lg"
                  loading="lazy"
                />
                <div className="p-3 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-pastel-dark">LLIRE Benchmark Performance</div>
                    <div className="text-[11px] text-pastel-muted mt-0.5">Evaluated against rigorous ground-truth accounting anomaly benchmarks</div>
                  </div>
                  <div className="px-3 py-1 bg-pastel-sage rounded-full text-xs font-bold text-pastel-dark border border-pastel-border">
                    100% Precision &bull; 100% Recall
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 4. RECONCILIATION AND AUDIT WORKFLOWS */}
        <section id="dual-key-remediation" className="scroll-mt-24">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-pastel-peach text-pastel-dark rounded-lg border border-pastel-border">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-pastel-dark">4. Reconciliation &amp; Dual-Key Audit Workflows</h2>
              <p className="text-xs text-pastel-muted">Controlled remediation, two-person authorization, and immutable compensating transactions.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-6">
              <div className="rounded-xl overflow-hidden border border-pastel-border bg-white p-2.5 shadow-xs">
                <img
                  src="/assets/feature_reconciliation.jpg"
                  alt="Financial reconciliation, audit trails, and dual-key manager authorization"
                  className="w-full h-56 object-cover rounded-lg"
                  loading="lazy"
                />
                <div className="p-3">
                  <div className="text-xs font-bold text-pastel-dark">Rule BR-09: Four-Eyes Principle</div>
                  <div className="text-[11px] text-pastel-muted mt-0.5">Strictly enforced in PostgreSQL stored procedures: Proposer &#8800; Approver</div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-6 space-y-4">
              <div className="p-4 rounded-xl bg-white border border-pastel-border shadow-xs">
                <div className="text-xs font-bold text-pastel-dark mb-1">Human-in-the-Loop Investigation</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Analysts or operators assign open anomaly incidents, record investigatory findings, and attach audit notes before drafting action proposals.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white border border-pastel-border shadow-xs">
                <div className="text-xs font-bold text-pastel-dark mb-1">Structured Action Proposals</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Proposals define compensating credit/debit points, target accounts, and mandatory justification codes. Actions are placed in PENDING_APPROVAL.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white border border-pastel-border shadow-xs">
                <div className="text-xs font-bold text-pastel-dark mb-1">Compensating Journal Execution</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  Upon independent second-manager approval, the database posts an immutable compensating transaction, recalculates balances, and logs an audit event.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 5. COMPARISON TABLE */}
        <section className="card-surface">
          <div className="mb-6">
            <span className="text-xs font-bold uppercase tracking-wider text-pastel-muted">Architectural Comparison</span>
            <h3 className="text-lg font-bold text-pastel-dark mt-1">Traditional Counters vs. LoyaltyOS Financial Double-Entry</h3>
            <p className="text-xs text-pastel-muted mt-1">Why modern retail balance sheets require financial-grade loyalty accounting.</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-pastel-border text-pastel-muted uppercase text-[10px] tracking-wider bg-pastel-ivory">
                  <th className="py-3 px-4">Capability</th>
                  <th className="py-3 px-4">Traditional Loyalty Solutions</th>
                  <th className="py-3 px-4 text-pastel-dark font-bold">LoyaltyOS Platform</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-pastel-border">
                <tr>
                  <td className="py-3.5 px-4 font-bold text-pastel-dark">Points Storage</td>
                  <td className="py-3.5 px-4 text-pastel-muted">Single mutable integer counter column</td>
                  <td className="py-3.5 px-4 font-medium text-pastel-sageDark">&#10003; Append-only double-entry journal with triggers</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-bold text-pastel-dark">Points Expiration</td>
                  <td className="py-3.5 px-4 text-pastel-muted">Bulk counter reductions with silent rounding</td>
                  <td className="py-3.5 px-4 font-medium text-pastel-sageDark">&#10003; Strict 365-day FIFO lot expiration &amp; allocations</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-bold text-pastel-dark">Merchandise Returns</td>
                  <td className="py-3.5 px-4 text-pastel-muted">Fails or crashes if points are already redeemed</td>
                  <td className="py-3.5 px-4 font-medium text-pastel-sageDark">&#10003; Proportional clawback with safe negative balance support</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-bold text-pastel-dark">Balance Adjustments</td>
                  <td className="py-3.5 px-4 text-pastel-muted">Unchecked single-admin edits without audit trail</td>
                  <td className="py-3.5 px-4 font-medium text-pastel-sageDark">&#10003; Dual-key approval: Proposer &#8800; Approver enforced in RPC</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-bold text-pastel-dark">Anomaly Monitoring</td>
                  <td className="py-3.5 px-4 text-pastel-muted">Monthly batch scripts or customer complaints</td>
                  <td className="py-3.5 px-4 font-medium text-pastel-sageDark">&#10003; Continuous LLIRE engine with 7-part explainable reports</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </PageContainer>
  );
};
