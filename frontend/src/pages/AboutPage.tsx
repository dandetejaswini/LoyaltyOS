import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  BookOpen,
  Lock,
  Scale,
  ArrowRight,
  GitBranch
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  const businessRules = [
    {
      group: 'Ledger Invariants & Immutability',
      rules: [
        { code: 'BR-01', title: 'Double-Entry Accounting Invariant', desc: 'Current balance must mathematically equal the sum of all transaction credits minus debits, and equal remaining active lots with zero drift.' },
        { code: 'BR-02', title: 'Immutable Append-Only Journal', desc: 'Points transactions cannot be updated or deleted in-place. PostgreSQL engine triggers reject UPDATE/DELETE statements on points_transactions.' },
        { code: 'BR-10', title: 'Auditable Reason Codes & Notes', desc: 'Manual corrections require mandatory justification notes and auditable reason codes before posting to the ledger.' }
      ]
    },
    {
      group: 'Accrual, Tiers & Expiry',
      rules: [
        { code: 'BR-03', title: 'Floor Rounding on Eligible Spend', desc: 'Points accrue only on net eligible merchandise spend (gross minus tax, shipping, and discounts) multiplied by tier multiplier, rounded down.' },
        { code: 'BR-04', title: '365-Day FIFO Lot Lifecycle', desc: 'Every accrual provisions a points lot with exact 365-day expiry. Expired lots are marked EXPIRED and cannot be redeemed.' },
        { code: 'BR-05', title: 'Spend-Based Tier Progression', desc: 'Tier status is evaluated on rolling 365-day qualifying spend: Bronze (<$500), Silver ($500-$999), Gold ($1k-$2.5k), Platinum (≥$2.5k).' }
      ]
    },
    {
      group: 'Redemptions & Returns',
      rules: [
        { code: 'BR-06', title: 'Proportional Return Reversals', desc: 'Returns calculate refunded eligible spend ratio and reverse points accordingly. If redeemed, balance may safely transition negative.' },
        { code: 'BR-11', title: 'Concurrency-Safe Pessimistic Locking', desc: 'Redemptions execute within a database transaction holding a row-level lock on the loyalty account to prevent race conditions.' }
      ]
    },
    {
      group: 'Forensic Intelligence & Dual-Key',
      rules: [
        { code: 'BR-07', title: 'LLIRE Continuous Anomaly Detection', desc: 'Automated engine runs 5 deterministic detectors: Balance Mismatch, Over-Redemption, Unreversed Return, Double Expiry, and Incorrect Tier.' },
        { code: 'BR-08', title: '7-Part Forensic Explainability', desc: 'Every detected anomaly includes summary, rule violated, mathematical drift, affected records, hypothesis, dollar impact, and recommendation.' },
        { code: 'BR-09', title: 'Two-Person Dual-Key Remediation', desc: 'Corrective actions require proposer_id != approver_id. A proposer can never approve their own compensating transaction.' }
      ]
    }
  ];

  return (
    <PageContainer
      title="Architecture & Operational Principles"
      subtitle="Complete documentation of the LoyaltyOS double-entry loyalty ledger model and mathematical invariants."
    >
      {/* Hero Showcase with Image */}
      <div className="relative overflow-hidden rounded-2xl bg-navy-950 text-white p-8 sm:p-12 mb-10 border border-navy-800 shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-2/5 opacity-15 pointer-events-none hidden md:block">
          <img
            src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=80"
            alt="Ledger Analytics"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-4">
            <BookOpen className="w-3.5 h-3.5 text-lavender-400" />
            Financial Engineering Whitepaper
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
            Why Loyalty Points Must Be Governed as Financial Currency
          </h1>
          <p className="text-sm sm:text-base text-platinum-300 leading-relaxed">
            In enterprise retail, outstanding customer loyalty points represent a material liability on the corporate balance sheet. LoyaltyOS replaces mutable counters with a verifiable double-entry ledger.
          </p>
        </div>
      </div>

      {/* The Mathematical Invariant Formula */}
      <div className="bg-white border border-platinum-200 rounded-xl p-6 sm:p-8 mb-10 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 bg-lavender-50 text-lavender-700 rounded-lg">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-navy-950">The Core Mathematical Invariant (BR-01)</h2>
            <p className="text-xs text-platinum-500">Continuous automated verification across three independent data structures</p>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-platinum-700 leading-relaxed mb-6">
          At any point in time, a customer's stored balance must satisfy two simultaneous equalities. If any difference &ne; 0 exists, the LLIRE engine immediately flags a <code className="bg-platinum-100 text-navy-900 px-1.5 py-0.5 rounded font-mono text-xs">BALANCE_MISMATCH</code> incident:
        </p>

        <div className="bg-navy-950 border border-navy-800 rounded-xl p-6 text-white font-mono text-xs sm:text-sm space-y-3 shadow-inner">
          <div className="text-lavender-300 font-semibold text-xs tracking-wider uppercase">
            Double-Entry Ledger Equality:
          </div>
          <div className="p-3 bg-navy-900 rounded-lg border border-navy-800 text-emerald-400 font-bold overflow-x-auto">
            Account.current_balance == &Sigma;(Credits: ACCRUAL + ADJUSTMENT_CREDIT) - &Sigma;(Debits: REDEMPTION + REVERSAL + EXPIRY + ADJUSTMENT_DEBIT)
          </div>
          <div className="text-lavender-300 font-semibold text-xs tracking-wider uppercase pt-2">
            FIFO Lot Depletion Equality:
          </div>
          <div className="p-3 bg-navy-900 rounded-lg border border-navy-800 text-lavender-300 font-bold overflow-x-auto">
            Account.current_balance == &Sigma;(PointsLot.remaining_points WHERE status = 'ACTIVE' AND expires_at &gt; NOW())
          </div>
        </div>
      </div>

      {/* Visual Architectural Data Flow */}
      <div className="mb-10">
        <h2 className="text-lg font-bold text-navy-950 mb-4 flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-lavender-600" />
          End-to-End Architectural Lifecycle
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-platinum-200 rounded-xl p-5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-lavender-600 uppercase block mb-1">Step 1</span>
            <h3 className="text-sm font-bold text-navy-950 mb-2">POS / Checkout Event</h3>
            <p className="text-xs text-platinum-600 leading-relaxed">
              Order created with eligible merchandise lines. Tax, shipping, and manufacturer discounts are excluded from accrual base.
            </p>
          </div>

          <div className="bg-white border border-platinum-200 rounded-xl p-5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-lavender-600 uppercase block mb-1">Step 2</span>
            <h3 className="text-sm font-bold text-navy-950 mb-2">Pessimistic Row Lock</h3>
            <p className="text-xs text-platinum-600 leading-relaxed">
              FastAPI opens a PostgreSQL transaction acquiring a <code className="font-mono text-[11px] bg-platinum-100 px-1 rounded">SELECT FOR UPDATE</code> lock on the account to prevent race conditions.
            </p>
          </div>

          <div className="bg-white border border-platinum-200 rounded-xl p-5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-lavender-600 uppercase block mb-1">Step 3</span>
            <h3 className="text-sm font-bold text-navy-950 mb-2">Append-Only Journal</h3>
            <p className="text-xs text-platinum-600 leading-relaxed">
              New transaction posted to <code className="font-mono text-[11px] bg-platinum-100 px-1 rounded">points_transactions</code>. Database triggers block UPDATE or DELETE operations.
            </p>
          </div>

          <div className="bg-white border border-platinum-200 rounded-xl p-5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-lavender-600 uppercase block mb-1">Step 4</span>
            <h3 className="text-sm font-bold text-navy-950 mb-2">LLIRE & Dual-Key</h3>
            <p className="text-xs text-platinum-600 leading-relaxed">
              Automated anomaly detectors scan ledger entries. Any discrepancy generates forensic evidence for two-person review.
            </p>
          </div>
        </div>
      </div>

      {/* Tier Multipliers Table */}
      <div className="bg-white border border-platinum-200 rounded-xl p-6 sm:p-8 mb-10 shadow-sm">
        <h2 className="text-lg font-bold text-navy-950 mb-2">Member Tier Structure & Multipliers</h2>
        <p className="text-xs text-platinum-600 mb-6">
          Calculated on rolling 365-day qualifying spend. Points earn on floor-rounded net spend multiplied by tier factor.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border border-platinum-200 rounded-lg overflow-hidden">
            <thead className="bg-platinum-100 text-platinum-700 uppercase font-semibold text-[11px]">
              <tr>
                <th className="px-4 py-3 border-b">Tier Level</th>
                <th className="px-4 py-3 border-b">Qualifying Spend (365d)</th>
                <th className="px-4 py-3 border-b">Earning Multiplier</th>
                <th className="px-4 py-3 border-b">Points per $1.00 Net Spend</th>
                <th className="px-4 py-3 border-b">Floor Example ($125.75)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-platinum-200">
              <tr>
                <td className="px-4 py-3 font-semibold text-amber-800">Bronze</td>
                <td className="px-4 py-3 text-platinum-700">$0.00 – $499.99</td>
                <td className="px-4 py-3 font-mono font-bold text-navy-950">1.00x</td>
                <td className="px-4 py-3 font-mono text-platinum-600">1 pt / $1</td>
                <td className="px-4 py-3 font-mono text-navy-900">125 pts</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-semibold text-slate-700">Silver</td>
                <td className="px-4 py-3 text-platinum-700">$500.00 – $999.99</td>
                <td className="px-4 py-3 font-mono font-bold text-navy-950">1.25x</td>
                <td className="px-4 py-3 font-mono text-platinum-600">1.25 pts / $1</td>
                <td className="px-4 py-3 font-mono text-navy-900">157 pts</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-semibold text-yellow-700">Gold</td>
                <td className="px-4 py-3 text-platinum-700">$1,000.00 – $2,499.99</td>
                <td className="px-4 py-3 font-mono font-bold text-navy-950">1.50x</td>
                <td className="px-4 py-3 font-mono text-platinum-600">1.50 pts / $1</td>
                <td className="px-4 py-3 font-mono text-navy-900">188 pts</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-semibold text-indigo-700">Platinum</td>
                <td className="px-4 py-3 text-platinum-700">&ge; $2,500.00</td>
                <td className="px-4 py-3 font-mono font-bold text-navy-950">2.00x</td>
                <td className="px-4 py-3 font-mono text-platinum-600">2 pts / $1</td>
                <td className="px-4 py-3 font-mono text-navy-900">251 pts</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* The 12 Business Rules Cards */}
      <div className="mb-10">
        <h2 className="text-lg font-bold text-navy-950 mb-2">
          Comprehensive Business Rules & Governance (BR-01 through BR-12)
        </h2>
        <p className="text-xs text-platinum-600 mb-6">
          Every rule is verified by automated pytest test suites and PostgreSQL security triggers.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {businessRules.map((group, idx) => (
            <div key={idx} className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-navy-950 pb-3 border-b border-platinum-200 mb-4">
                {group.group}
              </h3>
              <div className="space-y-4">
                {group.rules.map((rule) => (
                  <div key={rule.code} className="text-xs">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold px-1.5 py-0.5 rounded bg-lavender-50 text-lavender-800 border border-lavender-200 text-[11px]">
                        {rule.code}
                      </span>
                      <span className="font-semibold text-navy-950">{rule.title}</span>
                    </div>
                    <p className="text-platinum-600 leading-relaxed pl-1">{rule.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Database Security & Immutability Triggers */}
      <div className="bg-navy-950 text-white rounded-2xl p-6 sm:p-8 mb-10 border border-navy-800 shadow-xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-navy-800 rounded-lg text-emerald-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Database-Level Security & PostgreSQL Immutability Triggers
            </h2>
            <p className="text-xs text-platinum-400">
              Immutability is enforced inside PostgreSQL engine functions, not just in application code.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
          <div className="bg-navy-900 p-4 rounded-xl border border-navy-800">
            <span className="text-emerald-400 font-bold block mb-1">trg_prevent_points_transactions_update_delete</span>
            <span className="text-platinum-400 text-[11px] block">
              Raises EXCEPTION on UPDATE or DELETE against points_transactions.
            </span>
          </div>

          <div className="bg-navy-900 p-4 rounded-xl border border-navy-800">
            <span className="text-emerald-400 font-bold block mb-1">trg_prevent_points_lots_deletion</span>
            <span className="text-platinum-400 text-[11px] block">
              Raises EXCEPTION on DELETE against points_lots to protect lot history.
            </span>
          </div>

          <div className="bg-navy-900 p-4 rounded-xl border border-navy-800">
            <span className="text-emerald-400 font-bold block mb-1">Supabase Row-Level Security (RLS)</span>
            <span className="text-platinum-400 text-[11px] block">
              9 security policies isolate tenant customer records strictly to their auth.uid().
            </span>
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="text-center py-6">
        <Link
          to="/workspace"
          className="inline-flex items-center gap-2 px-6 py-3 bg-navy-900 hover:bg-navy-800 text-white rounded-lg text-xs font-semibold transition shadow-sm"
        >
          Open Operational Workspace
          <ArrowRight className="w-4 h-4 text-lavender-400" />
        </Link>
      </div>
    </PageContainer>
  );
};
