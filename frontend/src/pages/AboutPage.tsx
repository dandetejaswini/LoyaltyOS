import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  BookOpen,
  Scale,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  UserCheck,
  Layers,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  return (
    <PageContainer
      title="About LoyaltyOS"
      subtitle="The architectural philosophy, financial principles, and engineering design behind the double-entry loyalty management platform."
    >
      {/* 1. PRODUCT INTRODUCTION & HERO (Bright Pastel with Image) */}
      <section className="rounded-2xl bg-gradient-to-br from-pastel-ivory via-pastel-lavender/30 to-pastel-blue/30 border border-pastel-border p-8 sm:p-12 mb-10 shadow-xs">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-pastel-border text-pastel-dark text-xs font-semibold mb-4 shadow-xs">
              <BookOpen className="w-3.5 h-3.5 text-pastel-lavenderDark" />
              <span>Product Overview &amp; Architecture Whitepaper</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-pastel-dark mb-4">
              Financial Ledger Certainty for Enterprise Loyalty Programs
            </h1>
            <p className="text-sm sm:text-base text-pastel-muted leading-relaxed mb-6">
              LoyaltyOS was created to address a foundational flaw in modern retail loyalty software: treating customer reward points as mutable database counter columns rather than auditable financial currency.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Link to="/features" className="btn-primary">
                <span>Explore Product Features</span>
                <ArrowRight className="w-4 h-4 text-pastel-dark" />
              </Link>
              <Link to="/workspace" className="btn-outline">
                <span>Open Operational Workspace</span>
              </Link>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="rounded-xl overflow-hidden border border-pastel-border shadow-sm bg-white p-2">
              <img
                src="/assets/about_trust.jpg"
                alt="Financial trust, transaction transparency, and collaborative loyalty management"
                className="w-full h-64 sm:h-72 object-cover rounded-lg"
                loading="lazy"
              />
              <div className="mt-2.5 px-2 py-1 flex items-center justify-between text-[11px] text-pastel-muted font-medium">
                <span>100% Cryptographic Audit Trail</span>
                <span className="text-pastel-sageDark font-semibold">&#10003; Zero Ledger Drift</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="space-y-10">
        {/* 2. PROBLEM STATEMENT & WHY ACCURATE ACCOUNTING MATTERS */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-surface bg-pastel-rose/30 border border-pastel-border">
            <div className="flex items-center gap-2 mb-3 text-pastel-roseDark font-bold text-sm">
              <AlertTriangle className="w-5 h-5 text-pastel-roseDark" />
              <span>The Industry Problem: Mutable Counters</span>
            </div>
            <p className="text-xs text-pastel-dark leading-relaxed mb-3">
              Traditional loyalty solutions store customer point balances as a single integer column (e.g. <code className="bg-white text-pastel-roseDark px-1.5 py-0.5 rounded font-mono text-[11px] border border-pastel-border">points_balance = points_balance + N</code>).
            </p>
            <p className="text-xs text-pastel-muted leading-relaxed mb-3">
              Under high-concurrency checkout traffic, merchandise returns, and lot expiration cycles, this model experiences race conditions, silent balance drift, and unexplainable data loss with zero forensic audit trail.
            </p>
            <div className="p-3 bg-white rounded-lg border border-pastel-border text-pastel-dark text-xs font-mono">
              Result: Unverified liabilities on retail corporate balance sheets.
            </div>
          </div>

          <div className="card-surface bg-pastel-sage/30 border border-pastel-border">
            <div className="flex items-center gap-2 mb-3 text-pastel-sageDark font-bold text-sm">
              <CheckCircle2 className="w-5 h-5 text-pastel-sageDark" />
              <span>Why Accurate Loyalty Accounting Matters</span>
            </div>
            <p className="text-xs text-pastel-dark leading-relaxed mb-3">
              Outstanding reward points represent deferred commercial liabilities and customer trust. Under standard financial accounting guidelines, points breakage and redemptions must be quantifiable and mathematically verifiable.
            </p>
            <p className="text-xs text-pastel-muted leading-relaxed mb-3">
              LoyaltyOS solves this by implementing an immutable, append-only double-entry journal where points can never be updated in-place or deleted, guaranteeing mathematical balance parity at all times.
            </p>
            <div className="p-3 bg-white rounded-lg border border-pastel-border text-pastel-dark text-xs font-mono">
              Guarantee: 0.00% balance drift across journal entries and active FIFO lots.
            </div>
          </div>
        </section>

        {/* 3. PRODUCT VISION & MISSION */}
        <section className="card-surface">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="p-5 rounded-xl bg-pastel-lavender/40 border border-pastel-border">
              <span className="badge-accent mb-2">PRODUCT VISION</span>
              <h3 className="text-base font-bold text-pastel-dark mb-2">Trust Through Cryptographic &amp; Financial Rigor</h3>
              <p className="text-xs text-pastel-muted leading-relaxed">
                To establish double-entry ledger bookkeeping and explainable forensic anomaly detection as the universal gold standard for all enterprise retail, financial, and hospitality reward platforms.
              </p>
            </div>
            <div className="p-5 rounded-xl bg-pastel-sage/40 border border-pastel-border">
              <span className="badge-success mb-2">PRODUCT MISSION</span>
              <h3 className="text-base font-bold text-pastel-dark mb-2">Eliminate Inconsistency, Ensure Accountability</h3>
              <p className="text-xs text-pastel-muted leading-relaxed">
                To provide retail operators, fraud analysts, and financial executives with complete transparency into points lifecycles, backed by human-in-the-loop dual-key authorization for every balance adjustment.
              </p>
            </div>
          </div>
        </section>

        {/* 4. THE CORE MATHEMATICAL INVARIANT */}
        <section className="card-surface">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-pastel-blue text-pastel-dark rounded-lg border border-pastel-border">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-pastel-dark">The Double-Entry Balance Invariant (BR-01)</h3>
              <p className="text-xs text-pastel-muted">Continuous equality between three independent data structures</p>
            </div>
          </div>

          <p className="text-xs text-pastel-muted leading-relaxed mb-4">
            At any moment in time, an account's stored current balance must simultaneously equal the net sum of all historical journal entries and the sum of all unexpired active FIFO lots:
          </p>

          <div className="p-4 bg-pastel-ivory rounded-xl border border-pastel-border font-mono text-xs sm:text-sm space-y-3">
            <div className="p-3 bg-white rounded-lg border border-pastel-border text-pastel-dark font-semibold overflow-x-auto shadow-xs">
              <span className="text-pastel-sageDark font-bold">&#9679; Invariant 1:</span> Account.current_balance == &Sigma;(Credits: ACCRUAL + ADJUSTMENT_CREDIT) - &Sigma;(Debits: REDEMPTION + REVERSAL + EXPIRY + ADJUSTMENT_DEBIT)
            </div>
            <div className="p-3 bg-white rounded-lg border border-pastel-border text-pastel-dark font-semibold overflow-x-auto shadow-xs">
              <span className="text-pastel-lavenderDark font-bold">&#9679; Invariant 2:</span> Account.current_balance == &Sigma;(PointsLot.remaining_points WHERE status = 'ACTIVE' AND expires_at &gt; NOW())
            </div>
          </div>
        </section>

        {/* 5. LLIRE EXPLANATION & HUMAN APPROVAL WORKFLOW */}
        <section className="card-surface">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-pastel-lavender text-pastel-dark rounded-lg border border-pastel-border">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-pastel-dark">LLIRE &amp; Dual-Key Governance</h3>
              <p className="text-xs text-pastel-muted">Continuous anomaly monitoring paired with human-in-the-loop authorization</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-pastel-muted leading-relaxed">
            <div>
              <h4 className="font-bold text-pastel-dark text-sm mb-2 flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-pastel-lavenderDark" />
                <span>Explainable Anomaly Intelligence</span>
              </h4>
              <p className="mb-2">
                The Loyalty Ledger Intelligence &amp; Reconciliation Engine (LLIRE) executes five deterministic detectors to discover balance mismatches, over-redemptions, unreversed returns, duplicate expirations, and tier anomalies.
              </p>
              <p>
                Every detected incident produces a <strong className="text-pastel-dark">7-Part Forensic Report</strong> stating what happened, the exact invariant violated, numerical drift calculation, evidence records, dollar exposure, and recommendations.
              </p>
            </div>

            <div>
              <h4 className="font-bold text-pastel-dark text-sm mb-2 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-pastel-sageDark" />
                <span>Two-Person Dual-Key Governance (BR-09)</span>
              </h4>
              <p className="mb-2">
                No single operator or developer can arbitrarily alter account balances. Under rule BR-09, when an Operations Manager proposes a corrective compensating action, it is placed in <code className="bg-pastel-ivory px-1 rounded border border-pastel-border text-pastel-dark font-mono text-[10px]">PENDING_APPROVAL</code>.
              </p>
              <p>
                A second, independent manager must review the forensic finding and approve it. Self-approval is strictly forbidden and blocked directly at the PostgreSQL stored procedure level.
              </p>
            </div>
          </div>
        </section>

        {/* 6. TECHNOLOGY STACK & ARCHITECTURE */}
        <section className="card-surface">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2 bg-pastel-peach text-pastel-dark rounded-lg border border-pastel-border">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-pastel-dark">100% Supabase Production Architecture</h3>
              <p className="text-xs text-pastel-muted">Modern cloud-native software engineering stack</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-pastel-ivory border border-pastel-border">
              <div className="font-bold text-pastel-dark mb-1">Frontend</div>
              <div className="text-pastel-muted">React 18 &bull; TypeScript &bull; Vite &bull; Tailwind CSS</div>
            </div>
            <div className="p-4 rounded-xl bg-pastel-ivory border border-pastel-border">
              <div className="font-bold text-pastel-dark mb-1">Database &amp; RPC</div>
              <div className="text-pastel-muted">Supabase PostgreSQL 15+ &bull; Stored Procedures &bull; 5 Triggers</div>
            </div>
            <div className="p-4 rounded-xl bg-pastel-ivory border border-pastel-border">
              <div className="font-bold text-pastel-dark mb-1">Security &amp; Auth</div>
              <div className="text-pastel-muted">Row-Level Security (RLS) &bull; Supabase Auth &bull; RBAC</div>
            </div>
            <div className="p-4 rounded-xl bg-pastel-ivory border border-pastel-border">
              <div className="font-bold text-pastel-dark mb-1">Deployment</div>
              <div className="text-pastel-muted">Vercel Global Edge Network &bull; Edge Functions (Deno)</div>
            </div>
          </div>
        </section>
      </div>
    </PageContainer>
  );
};
