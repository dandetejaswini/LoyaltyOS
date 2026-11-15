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
    { num: '01', title: 'Loyalty Account Management', desc: 'Enterprise accounts with customer IDs, status controls, and rolling spend tracking.', icon: <Users className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-sage' },
    { num: '02', title: 'Points Accrual (BR-03)', desc: 'Net merchandise spend calculation excluding tax and shipping with tier floor-rounding.', icon: <Coins className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-blue' },
    { num: '03', title: 'Reward Redemption', desc: 'Atomic voucher redemption under pessimistic row locks preventing double-spending.', icon: <Gift className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-lavender' },
    { num: '04', title: 'FIFO Points Allocation', desc: 'Points lots consumed in strict First-In, First-Out order for retail liability accounting.', icon: <Clock className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-peach' },
    { num: '05', title: 'Points Expiration', desc: 'Explicit 365-day lifecycles per lot executed via idempotent batch cron routines.', icon: <RefreshCw className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-rose' },
    { num: '06', title: 'Returns and Reversals', desc: 'Proportional point clawbacks on merchandise returns with safe negative balance support.', icon: <RotateCcw className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-sage' },
    { num: '07', title: 'Ledger Reconciliation', desc: 'Continuous mathematical parity checks: Stored balance == Journal sum == Active lots.', icon: <Scale className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-blue' },
    { num: '08', title: 'LLIRE Anomaly Detection', desc: 'Automated forensic scanner monitoring for balance, redemption, and expiry anomalies.', icon: <Cpu className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-lavender' },
    { num: '09', title: 'Explainable Investigation', desc: '7-part structured forensic reports detailing invariant violations and root causes.', icon: <Eye className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-peach' },
    { num: '10', title: 'Corrective Actions', desc: 'Compensating ledger transactions posted with mandatory justification codes.', icon: <FileCheck className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-rose' },
    { num: '11', title: 'Dual-Key Approval', desc: 'Two-person authorization (proposer != approver) preventing unauthorized balance edits.', icon: <UserCheck className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-sage' },
    { num: '12', title: 'Audit History', desc: 'Immutable, trigger-protected PostgreSQL audit journals with zero in-place updates.', icon: <History className="w-4 h-4 text-pastel-dark" />, bg: 'bg-pastel-blue' },
  ];

  const detectors = [
    { name: 'Balance Mismatches', code: 'DET-BALANCE-MISMATCH', sev: 'CRITICAL', badgeClass: 'badge-danger', desc: 'Flags discrepancies between cached balance and algebraic journal sum.' },
    { name: 'Over-Redemption', code: 'DET-OVER-REDEMPTION', sev: 'HIGH', badgeClass: 'badge-warning', desc: 'Catches negative balance dips caused by race conditions or glitch exploits.' },
    { name: 'Unreversed Returns', code: 'DET-UNREVERSED-RETURN', sev: 'HIGH', badgeClass: 'badge-warning', desc: 'Detects refunded orders where points clawback failed to post to ledger.' },
    { name: 'Duplicate Expiry', code: 'DET-DOUBLE-EXPIRY', sev: 'CRITICAL', badgeClass: 'badge-danger', desc: 'Discovers lots deducted multiple times across batch expiration cron jobs.' },
    { name: 'Incorrect Tier Calculations', code: 'DET-INCORRECT-TIER', sev: 'MEDIUM', badgeClass: 'badge-info', desc: 'Identifies tier assignments out of sync with 365-day qualifying spend.' },
  ];

  const roles = [
    { role: 'Customer', name: 'Alice Walker', focus: 'Member Experience', desc: 'View current balance, tier multiplier, 365-day lot expiry countdowns, catalog rewards, and instant voucher redemption.', color: 'border-pastel-lavender bg-pastel-lavender/30' },
    { role: 'Store Operator', name: 'Marcus Brody', focus: 'POS Fulfillment', desc: 'Lookup customer accounts, process real-time order point accruals with floor-rounding previews, and execute proportional return reversals.', color: 'border-pastel-blue bg-pastel-blue/30' },
    { role: 'Fraud Analyst', name: 'Sarah Chen', focus: 'Forensic Risk & LLIRE', desc: 'Scan ledger records for anomalies, inspect 7-part forensic evidence drawers, and evaluate ground-truth precision/recall benchmark metrics.', color: 'border-pastel-peach bg-pastel-peach/30' },
    { role: 'Operations Manager', name: 'Eleanor & David', focus: 'Dual-Key Governance', desc: 'Review investigation cases, propose structured compensating actions, and enforce two-person dual-key authorization before ledger execution.', color: 'border-pastel-sage bg-pastel-sage/30' },
  ];

  return (
    <PageContainer>
      {/* 1. HERO SECTION (Bright, Elegant Pastel) */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-pastel-ivory via-pastel-blue/40 to-pastel-lavender/40 text-pastel-dark p-8 sm:p-12 lg:p-14 mb-14 border border-pastel-border shadow-xs">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Hero Content */}
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-pastel-border text-pastel-dark text-xs font-semibold mb-6 shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-pastel-lavenderDark" />
              <span>Intelligent Loyalty &amp; Ledger Platform</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight text-pastel-dark mb-6">
              Intelligent Loyalty Management. Complete Ledger Transparency.
            </h1>

            <p className="text-base sm:text-lg text-pastel-muted mb-8 leading-relaxed max-w-xl">
              Manage loyalty accounts, track points, process rewards, and identify ledger inconsistencies through an explainable intelligence engine. Built with double-entry accounting and two-person dual-key governance.
            </p>

            <div className="flex flex-wrap items-center gap-3.5">
              <Link
                to="/workspace"
                className="btn-primary px-6 py-3 text-sm font-semibold rounded-xl"
              >
                <span>Get Started in Workspace</span>
                <ArrowRight className="w-4 h-4 text-pastel-dark" />
              </Link>
              <Link
                to="/features"
                className="btn-outline px-5 py-3 text-sm font-medium rounded-xl"
              >
                <span>Explore Features</span>
              </Link>
            </div>
          </div>

          {/* Right Hero Visual Asset */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl overflow-hidden border border-pastel-border shadow-md bg-white p-2.5">
              <img
                src="/assets/hero_loyalty.jpg"
                alt="Modern retail customer loyalty and digital checkout experience"
                className="w-full h-72 sm:h-80 object-cover rounded-xl"
                loading="eager"
              />
              {/* Floating Pastel Badge Overlay */}
              <div className="absolute bottom-6 left-6 right-6 p-4 rounded-xl bg-white/95 backdrop-blur-md border border-pastel-border shadow-sm flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-pastel-muted">Accrual Verified</div>
                  <div className="text-sm font-extrabold text-pastel-dark">&#8970;Net Spend &times; 1.50&#8971; = +187 PTS</div>
                </div>
                <div className="w-9 h-9 rounded-full bg-pastel-sage flex items-center justify-center border border-pastel-border">
                  <ShieldCheck className="w-4 h-4 text-pastel-dark" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-10 pt-8 border-t border-pastel-border/80">
          <div className="bg-white/80 p-4 rounded-xl border border-pastel-border shadow-xs">
            <div className="text-xl sm:text-2xl font-extrabold text-pastel-dark">Append-Only</div>
            <div className="text-xs text-pastel-muted mt-0.5">Double-Entry Journal</div>
          </div>
          <div className="bg-white/80 p-4 rounded-xl border border-pastel-border shadow-xs">
            <div className="text-xl sm:text-2xl font-extrabold text-pastel-dark">365-Day</div>
            <div className="text-xs text-pastel-muted mt-0.5">FIFO Points Expiry</div>
          </div>
          <div className="bg-white/80 p-4 rounded-xl border border-pastel-border shadow-xs">
            <div className="text-xl sm:text-2xl font-extrabold text-pastel-dark">5 Detectors</div>
            <div className="text-xs text-pastel-muted mt-0.5">LLIRE Anomaly Scanner</div>
          </div>
          <div className="bg-white/80 p-4 rounded-xl border border-pastel-border shadow-xs">
            <div className="text-xl sm:text-2xl font-extrabold text-pastel-dark">Dual-Key</div>
            <div className="text-xs text-pastel-muted mt-0.5">BR-09 Two-Person Rule</div>
          </div>
        </div>
      </section>

      {/* 2. PLATFORM CAPABILITIES GRID */}
      <section className="mb-14">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs font-bold uppercase tracking-wider text-pastel-muted">Architecture &amp; Features</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-dark mt-1">Twelve Production Ledger Capabilities</h2>
          <p className="text-sm text-pastel-muted mt-2">
            Every point transaction is cryptographically secured, verified against mathematical invariants, and auditable for compliance.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {capabilities.map((c) => (
            <div
              key={c.num}
              className="card-surface hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3.5">
                  <div className={`w-8 h-8 rounded-lg ${c.bg} border border-pastel-border flex items-center justify-center shadow-xs`}>
                    {c.icon}
                  </div>
                  <span className="text-[11px] font-mono text-pastel-muted font-bold">{c.num}</span>
                </div>
                <h3 className="text-sm font-bold text-pastel-dark group-hover:text-pastel-dark transition mb-1.5">
                  {c.title}
                </h3>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  {c.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. LLIRE ANOMALY WORKFLOW DIAGRAM */}
      <section className="mb-14 card-surface p-8 sm:p-10 border border-pastel-border">
        <div className="max-w-2xl mb-8">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-pastel-lavender text-pastel-dark text-xs font-semibold mb-2.5 border border-pastel-border">
            <Cpu className="w-3.5 h-3.5" />
            <span>Explainable Intelligence</span>
          </div>
          <h2 className="text-2xl font-bold text-pastel-dark">How LLIRE Anomaly Remediation Works</h2>
          <p className="text-xs text-pastel-muted mt-1 leading-relaxed">
            The Loyalty Ledger Intelligence &amp; Reconciliation Engine automates anomaly detection, isolates root causes through 7-part forensic reports, and enforces dual-key approval before executing compensating ledger adjustments.
          </p>
        </div>

        {/* Local Localized SVG Workflow Diagram */}
        <div className="w-full overflow-x-auto rounded-xl border border-pastel-border bg-pastel-ivory p-4 mb-8">
          <img
            src="/assets/llire_workflow.svg"
            alt="LLIRE 4-stage workflow: Detection, Investigation, Dual-Key Review, and Reconciliation"
            className="w-full min-w-[700px] h-auto object-contain"
            loading="lazy"
          />
        </div>

        {/* 5 Detectors Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 pt-2">
          {detectors.map((d) => (
            <div key={d.code} className="p-3.5 rounded-xl bg-pastel-ivory border border-pastel-border">
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] ${d.badgeClass}`}>{d.sev}</span>
              </div>
              <div className="font-bold text-xs text-pastel-dark">{d.name}</div>
              <div className="text-[10px] font-mono text-pastel-muted mt-0.5">{d.code}</div>
              <div className="text-[11px] text-pastel-muted mt-2 leading-relaxed">{d.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. FOUR OPERATIONAL ROLE PORTALS */}
      <section className="mb-14">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs font-bold uppercase tracking-wider text-pastel-muted">Role-Based Access Control</span>
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-dark mt-1">Four Tailored Operational Experiences</h2>
          <p className="text-sm text-pastel-muted mt-2">
            Each role accesses dedicated tools, actions, and security scopes. Switch between personas anytime in the Workspace.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {roles.map((r) => (
            <div
              key={r.role}
              className={`rounded-xl border p-5 bg-white shadow-xs flex flex-col justify-between hover:shadow-md transition`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-pastel-muted">{r.role}</span>
                  <span className="w-2 h-2 rounded-full bg-pastel-sageDark"></span>
                </div>
                <h3 className="text-sm font-bold text-pastel-dark">{r.name}</h3>
                <div className="text-xs font-medium text-pastel-muted mb-3">{r.focus}</div>
                <p className="text-xs text-pastel-muted leading-relaxed">
                  {r.desc}
                </p>
              </div>

              <div className="mt-5 pt-3.5 border-t border-pastel-border">
                <Link
                  to="/workspace"
                  className="text-xs font-semibold text-pastel-dark hover:underline flex items-center justify-between"
                >
                  <span>Launch Workspace</span>
                  <ChevronRight className="w-3.5 h-3.5 text-pastel-dark" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. BOTTOM CTA */}
      <section className="rounded-2xl bg-gradient-to-r from-pastel-sage/50 via-pastel-lavender/50 to-pastel-blue/50 border border-pastel-border p-8 sm:p-12 text-center shadow-xs">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-pastel-dark mb-3">
            Ready to Explore the LoyaltyOS Platform?
          </h2>
          <p className="text-sm text-pastel-muted mb-6 leading-relaxed">
            Test all four role dashboards, execute transactions, run the LLIRE anomaly scanner, and evaluate dual-key approvals in real time.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/workspace"
              className="btn-primary px-6 py-3 text-sm font-semibold rounded-xl"
            >
              <span>Open Enterprise Workspace</span>
              <ArrowRight className="w-4 h-4 text-pastel-dark" />
            </Link>
            <Link
              to="/contact"
              className="btn-outline px-5 py-3 text-sm font-medium rounded-xl"
            >
              <span>Contact Engineering Team</span>
            </Link>
          </div>
        </div>
      </section>
    </PageContainer>
  );
};
