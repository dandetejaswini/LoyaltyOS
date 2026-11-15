import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  ArrowRight,
  Sparkles,
  RefreshCw,
  Coins,
  Gift,
  Clock,
  FileCheck,
  Scale,
  Users,
  ShieldCheck,
  Cpu,
  History,
  Eye,
  RotateCcw,
  UserCheck,
  ChevronRight
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const capabilities = [
    { num: '01', title: 'Loyalty Account Management', desc: 'Enterprise accounts with customer IDs, status controls, and rolling spend tracking.', icon: <Users className="w-4 h-4 text-lavender-600" /> },
    { num: '02', title: 'Points Accrual (BR-03)', desc: 'Net merchandise spend calculation excluding tax and shipping with tier floor-rounding.', icon: <Coins className="w-4 h-4 text-lavender-600" /> },
    { num: '03', title: 'Reward Redemption', desc: 'Atomic voucher redemption under pessimistic row locks preventing double-spending.', icon: <Gift className="w-4 h-4 text-lavender-600" /> },
    { num: '04', title: 'FIFO Points Allocation', desc: 'Points lots consumed in strict First-In, First-Out order for liability accounting.', icon: <Clock className="w-4 h-4 text-lavender-600" /> },
    { num: '05', title: 'Points Expiration', desc: 'Explicit 365-day lifecycles per lot executed via idempotent batch cron routines.', icon: <RefreshCw className="w-4 h-4 text-lavender-600" /> },
    { num: '06', title: 'Returns and Reversals', desc: 'Proportional point clawbacks on merchandise returns with safe negative balance support.', icon: <RotateCcw className="w-4 h-4 text-lavender-600" /> },
    { num: '07', title: 'Ledger Reconciliation', desc: 'Continuous mathematical parity checks: Stored balance == Journal sum == Active lots.', icon: <Scale className="w-4 h-4 text-lavender-600" /> },
    { num: '08', title: 'LLIRE Anomaly Detection', desc: 'Automated forensic scanner monitoring for balance, redemption, and expiry anomalies.', icon: <Cpu className="w-4 h-4 text-lavender-600" /> },
    { num: '09', title: 'Explainable Investigation', desc: '7-part structured forensic reports detailing invariant violations and root causes.', icon: <Eye className="w-4 h-4 text-lavender-600" /> },
    { num: '10', title: 'Corrective Actions', desc: 'Compensating ledger transactions posted with mandatory justification codes.', icon: <FileCheck className="w-4 h-4 text-lavender-600" /> },
    { num: '11', title: 'Dual-Key Approval', desc: 'Two-person authorization (proposer != approver) preventing unauthorized balance edits.', icon: <UserCheck className="w-4 h-4 text-lavender-600" /> },
    { num: '12', title: 'Audit History', desc: 'Immutable, trigger-protected PostgreSQL audit journals with zero in-place updates.', icon: <History className="w-4 h-4 text-lavender-600" /> },
  ];

  const workflowSteps = [
    { title: 'Customer Activity', desc: 'Purchases, returns, or checkouts occur at store POS or online cart.' },
    { title: 'Points Calculation', desc: 'Eligible net spend & tier multiplier compute floor-rounded points.' },
    { title: 'Loyalty Ledger', desc: 'Append-only double-entry journal transaction posted with row locking.' },
    { title: 'LLIRE Monitoring', desc: 'Anomaly engine continuously validates accounting invariants.' },
    { title: 'Investigation', desc: 'Incident flagged with 7-part explainability and auditable evidence.' },
    { title: 'Approved Correction', desc: 'Proposer submits action; independent second manager approves.' },
    { title: 'Audit', desc: 'Compensating transaction balances ledger with zero historical mutation.' },
  ];

  const detectors = [
    { name: 'Balance Mismatches', code: 'DET-BALANCE-MISMATCH', sev: 'CRITICAL', desc: 'Flags discrepancy between cached balance and algebraic journal sum.' },
    { name: 'Over-Redemption', code: 'DET-OVER-REDEMPTION', sev: 'HIGH', desc: 'Catches negative balance dips caused by race conditions or glitch exploits.' },
    { name: 'Unreversed Returns', code: 'DET-UNREVERSED-RETURN', sev: 'HIGH', desc: 'Detects refunded orders where points clawback failed to post.' },
    { name: 'Duplicate Expiry', code: 'DET-DOUBLE-EXPIRY', sev: 'CRITICAL', desc: 'Discovers lots deducted multiple times across batch expiration cron jobs.' },
    { name: 'Incorrect Tier Calculations', code: 'DET-INCORRECT-TIER', sev: 'MEDIUM', desc: 'Identifies tier assignments out of sync with 365-day qualifying spend.' },
  ];

  const roles = [
    { role: 'Customer', name: 'Alice Walker', focus: 'Member Experience', desc: 'View current balance, tier multiplier, 365-day lot expiry countdowns, catalog rewards, and instant voucher redemption.' },
    { role: 'Operator', name: 'Marcus Brody', focus: 'POS Fulfillment', desc: 'Lookup customer accounts, process real-time order point accruals with floor-rounding previews, and execute proportional return reversals.' },
    { role: 'Analyst', name: 'Sarah Chen', focus: 'Forensic Risk & LLIRE', desc: 'Scan ledger records for anomalies, inspect 7-part forensic evidence drawers, and evaluate ground-truth precision/recall benchmark metrics.' },
    { role: 'Operations Manager', name: 'Eleanor & David', focus: 'Dual-Key Governance', desc: 'Review investigation cases, propose structured compensating actions, and enforce two-person dual-key authorization before ledger execution.' },
  ];

  return (
    <PageContainer>
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden rounded-2xl bg-navy-950 text-white p-8 sm:p-14 mb-14 border border-navy-800 shadow-xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5 text-lavender-400" />
            <span>Intelligent Loyalty &amp; Ledger Platform</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight text-white mb-6">
            Intelligent Loyalty Management. Complete Ledger Transparency.
          </h1>

          <p className="text-base sm:text-lg text-platinum-300 mb-8 leading-relaxed max-w-2xl">
            Manage loyalty accounts, track points, process rewards, and identify ledger inconsistencies through an explainable intelligence engine.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Link
              to="/workspace"
              className="btn-accent px-6 py-3 text-xs uppercase tracking-wider font-bold shadow-md hover:shadow-lg"
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/features"
              className="btn-outline px-6 py-3 text-xs bg-navy-900 text-platinum-200 border-navy-700 hover:bg-navy-800"
            >
              Explore Features
            </Link>
          </div>
        </div>

        {/* Live System Invariant Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-12 pt-8 border-t border-navy-800/80 text-xs font-mono">
          <div>
            <span className="text-2xl sm:text-3xl font-bold text-emerald-400 block font-mono">0.00%</span>
            <span className="text-[11px] text-platinum-400 uppercase font-sans">Balance Drift Allowed</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold text-lavender-300 block font-mono">365 Days</span>
            <span className="text-[11px] text-platinum-400 uppercase font-sans">Strict FIFO Lot Lifecycle</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold text-amber-300 block font-mono">&lt; 0.5s</span>
            <span className="text-[11px] text-platinum-400 uppercase font-sans">LLIRE Anomaly Scan</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold text-white block font-mono">100%</span>
            <span className="text-[11px] text-platinum-400 uppercase font-sans">Two-Person Dual-Key</span>
          </div>
        </div>
      </section>

      {/* 2. PRODUCT SHOWCASE */}
      <section className="mb-16">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-navy-950">Architectural Product Showcase</h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            A unified system connecting consumer rewards, store cashier terminals, forensic risk auditing, and dual-key governance.
          </p>
        </div>

        {/* Interactive Application Preview Window */}
        <div className="card-surface p-0 overflow-hidden shadow-lg border border-platinum-300">
          {/* Mock Browser Header */}
          <div className="bg-navy-950 px-4 py-3 border-b border-navy-800 flex items-center justify-between text-xs text-platinum-400">
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></span>
              </div>
              <span className="font-mono text-[11px] text-platinum-300 ml-2">app.loyaltyos.internal / workspace</span>
            </div>
            <span className="badge-demo">Product Architecture Preview</span>
          </div>

          {/* Showcase Content Grid */}
          <div className="p-6 bg-platinum-50/70 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Snapshot: Customer Balance */}
              <div className="bg-white p-4 rounded-xl border border-platinum-200 shadow-sm">
                <div className="flex justify-between items-center mb-1 text-xs">
                  <span className="text-platinum-500 font-semibold uppercase text-[10px]">Points Balance</span>
                  <span className="badge-accent">GOLD TIER (1.50x)</span>
                </div>
                <div className="text-2xl font-bold font-mono text-navy-950">1,450 PTS</div>
                <span className="text-[11px] text-platinum-500 font-mono">Value: $14.50 USD &bull; 0 Drift</span>
              </div>

              {/* Snapshot: Ledger Activity */}
              <div className="bg-white p-4 rounded-xl border border-platinum-200 shadow-sm">
                <div className="flex justify-between items-center mb-1 text-xs">
                  <span className="text-platinum-500 font-semibold uppercase text-[10px]">Recent Ledger Entry</span>
                  <span className="badge-success">IMMUTABLE</span>
                </div>
                <div className="text-xs font-mono font-bold text-navy-900">TX-ACC-9801: +1,000 PTS</div>
                <span className="text-[11px] text-platinum-500">Order #ORD-9801 &bull; Merchandise Net $666.67</span>
              </div>

              {/* Snapshot: LLIRE Intelligence */}
              <div className="bg-white p-4 rounded-xl border border-platinum-200 shadow-sm">
                <div className="flex justify-between items-center mb-1 text-xs">
                  <span className="text-platinum-500 font-semibold uppercase text-[10px]">LLIRE Intelligence</span>
                  <span className="badge-warning">MONITORING</span>
                </div>
                <div className="text-xs font-mono font-bold text-rose-700">DET-BALANCE-MISMATCH</div>
                <span className="text-[11px] text-platinum-500">7-Part Forensic Report Ready &bull; Dual-Key</span>
              </div>
            </div>

            {/* Workflow preview bar */}
            <div className="bg-white p-4 rounded-xl border border-platinum-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span className="text-platinum-700">
                  <strong>Dual-Key Governance Flow:</strong> Proposer structures compensating action &rarr; Second Manager reviews &rarr; Executed with zero historical mutation.
                </span>
              </div>
              <Link to="/workspace" className="text-lavender-700 font-semibold hover:text-lavender-900 flex items-center gap-1 shrink-0">
                Open Workspace <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 3. FEATURES SECTION (12 Core Capabilities) */}
      <section className="mb-16">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-navy-950">Twelve Core Enterprise Capabilities</h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Every feature is backed by strict business rules, automated tests, and database-level protections.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {capabilities.map((cap) => (
            <div key={cap.num} className="card-surface hover:border-lavender-300 transition">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-platinum-100 rounded-lg">{cap.icon}</div>
                <span className="font-mono text-xs font-bold text-platinum-400">{cap.num}</span>
              </div>
              <h3 className="text-sm font-bold text-navy-950 mb-1">{cap.title}</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">{cap.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 4. HOW IT WORKS */}
      <section className="mb-16 card-surface bg-navy-950 text-white border-navy-800">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-white">How LoyaltyOS Works</h2>
          <p className="text-xs sm:text-sm text-platinum-400 mt-2">
            An auditable seven-stage lifecycle from in-store transaction to mathematical balance reconciliation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 text-center">
          {workflowSteps.map((step, idx) => (
            <div key={idx} className="p-3 bg-navy-900/90 border border-navy-800 rounded-xl relative flex flex-col justify-between">
              <div>
                <span className="w-5 h-5 rounded-full bg-lavender-900 border border-lavender-600 text-lavender-300 text-[10px] font-bold flex items-center justify-center mx-auto mb-2 font-mono">
                  {idx + 1}
                </span>
                <h4 className="text-xs font-bold text-white mb-1">{step.title}</h4>
              </div>
              <p className="text-[11px] text-platinum-400 leading-relaxed mt-2">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. USER ROLES SECTION */}
      <section className="mb-16">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-navy-950">Four Role-Based Operational Perspectives</h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Tailored interfaces with server-enforced permissions and strict separation of concerns.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {roles.map((r, i) => (
            <div key={i} className="card-surface flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="badge-neutral font-mono text-[10px]">{r.role}</span>
                  <span className="text-[10px] font-semibold text-platinum-500">{r.focus}</span>
                </div>
                <h3 className="text-sm font-bold text-navy-950 mb-1">{r.name}</h3>
                <p className="text-xs text-platinum-600 leading-relaxed mb-4">{r.desc}</p>
              </div>
              <Link to="/workspace" className="text-xs text-lavender-700 font-semibold hover:text-lavender-900 flex items-center gap-1 pt-2 border-t border-platinum-100">
                Launch Role Portal <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* 6. INTELLIGENCE SECTION (LLIRE) */}
      <section className="mb-16">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-navy-950">LLIRE — Loyalty Ledger Intelligence &amp; Reconciliation Engine</h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Five explainable anomaly detectors continuously scan ledger transactions to prevent fraud and unexplainable drift.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {detectors.map((d, i) => (
            <div key={i} className="card-surface">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-navy-950">{d.code}</span>
                <span className={d.sev === 'CRITICAL' ? 'badge-danger' : d.sev === 'HIGH' ? 'badge-warning' : 'badge-neutral'}>
                  {d.sev}
                </span>
              </div>
              <h3 className="text-sm font-bold text-navy-900 mb-1">{d.name}</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">{d.desc}</p>
            </div>
          ))}

          <div className="card-surface bg-lavender-50/60 border-lavender-200 md:col-span-1">
            <span className="badge-accent mb-2">HUMAN-IN-THE-LOOP</span>
            <h3 className="text-sm font-bold text-navy-950 mb-1">Explainable Governance</h3>
            <p className="text-xs text-platinum-700 leading-relaxed">
              LLIRE never modifies account balances autonomously. It surfaces forensic evidence for review by authorized Operations Managers under two-person approval.
            </p>
          </div>
        </div>
      </section>

      {/* 7. SECURITY & TRANSPARENCY SECTION */}
      <section className="mb-16 card-surface">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-emerald-50 text-emerald-700 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-navy-950">Security, Auditability &amp; Architectural Transparency</h2>
            <p className="text-xs text-platinum-500">Core software design principles implemented across application code and database triggers.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-platinum-50 rounded-xl border border-platinum-200">
            <h4 className="font-bold text-navy-950 mb-1">Transaction Traceability</h4>
            <p className="text-platinum-600 leading-relaxed">
              Every balance update is mapped to an immutable transaction record with explicit reason codes, idempotency keys, and order references.
            </p>
          </div>

          <div className="p-4 bg-platinum-50 rounded-xl border border-platinum-200">
            <h4 className="font-bold text-navy-950 mb-1">Database Trigger Immutability</h4>
            <p className="text-platinum-600 leading-relaxed">
              PostgreSQL triggers block UPDATE or DELETE operations against points transactions, enforcing append-only immutability at the engine level.
            </p>
          </div>

          <div className="p-4 bg-platinum-50 rounded-xl border border-platinum-200">
            <h4 className="font-bold text-navy-950 mb-1">Server-Authoritative RBAC</h4>
            <p className="text-platinum-600 leading-relaxed">
              FastAPI dependencies enforce role scopes (CUSTOMER, OPERATOR, ANALYST, OPERATIONS_MANAGER). Persona switching cannot escalate privileges.
            </p>
          </div>
        </div>
      </section>

      {/* 8. FINAL CTA */}
      <section className="card-surface-dark text-center p-10 relative overflow-hidden">
        <div className="max-w-2xl mx-auto py-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">
            Ready to explore LoyaltyOS?
          </h2>
          <p className="text-xs sm:text-sm text-platinum-300 mb-6 leading-relaxed">
            Open the live operational workspace to inspect double-entry transactions, test customer redemptions, trigger LLIRE anomaly detection, and review dual-key approval flows.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3.5">
            <Link to="/workspace" className="btn-accent px-6 py-3 font-bold uppercase tracking-wider">
              Launch Operational Workspace
            </Link>
            <Link to="/about" className="btn-outline text-white border-navy-700 bg-navy-900 hover:bg-navy-800 px-6 py-3">
              Read Architecture Principles
            </Link>
          </div>
        </div>
      </section>
    </PageContainer>
  );
};
