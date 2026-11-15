import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  Database,
  RefreshCw,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Scale,
  Sparkles,
  Cpu
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const pillars = [
    {
      icon: <Database className="w-5 h-5 text-lavender-600" />,
      title: 'Append-Only Financial Journal',
      desc: 'Points are treated like currency, not mutable database counters. Every credit and debit posts to an immutable journal protected by PostgreSQL engine triggers.',
      badge: 'BR-01 & BR-02'
    },
    {
      icon: <RefreshCw className="w-5 h-5 text-emerald-600" />,
      title: 'FIFO Lot Lifecycle & 365-Day Expiry',
      desc: 'Every earned point lot carries an exact 365-day expiration. Redemptions consume lots in strict FIFO order; batch expiration runs idempotently.',
      badge: 'BR-03 & BR-04'
    },
    {
      icon: <Scale className="w-5 h-5 text-indigo-600" />,
      title: 'Proportional Return Reversals',
      desc: 'Order returns reverse earned points strictly proportional to eligible net merchandise spend. Safely handles negative balances without data loss.',
      badge: 'BR-06'
    },
    {
      icon: <Cpu className="w-5 h-5 text-purple-600" />,
      title: 'LLIRE Forensic Fraud Intelligence',
      desc: 'Continuous anomaly scanner with 5 explainable detectors. Generates 7-part forensic reports and feeds two-person dual-key remediation queues.',
      badge: 'BR-07, BR-08, BR-09'
    }
  ];

  const enterpriseDomains = [
    {
      title: 'Omnichannel Retail & Department Stores',
      desc: 'Unify in-store POS checkout and online carts with instant floor-rounded points accrual and return reversals.',
      image: 'https://images.unsplash.com/photo-1556742049-0a67c5574f73?auto=format&fit=crop&w=800&q=80',
      tag: 'Point-of-Sale Real-Time'
    },
    {
      title: 'Fintech, Digital Wallets & Neo-Banks',
      desc: 'High-concurrency ledger operations with pessimistic row locking, eliminating race conditions and double-spending.',
      image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80',
      tag: 'Strict Invariant Guarantee'
    },
    {
      title: 'Hospitality & Airline Loyalty Programs',
      desc: 'Tier qualification tracking with rolling 365-day spend windows and automated tier multiplier progression.',
      image: 'https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=800&q=80',
      tag: 'Tier Multipliers (1.0x - 2.0x)'
    }
  ];

  return (
    <PageContainer>
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-950 via-navy-900 to-navy-950 text-white p-8 sm:p-14 mb-10 border border-navy-800 shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/2 opacity-10 pointer-events-none hidden lg:block">
          <img
            src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
            alt="Infrastructure Architecture"
            className="w-full h-full object-cover"
          />
        </div>

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5 text-lavender-400" />
            <span>Enterprise Loyalty Infrastructure &bull; Double-Entry Ledger</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight text-white mb-6">
            The Auditable Loyalty Engine for Modern Enterprise Commerce
          </h1>

          <p className="text-base sm:text-lg text-platinum-300 mb-8 leading-relaxed max-w-2xl">
            Eliminate point balance drift, enforce strict 365-day FIFO lot expiry, and detect accounting anomalies with automated forensic explainability and two-person dual-key remediation.
          </p>

          <div className="flex flex-wrap items-center gap-3.5">
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 px-6 py-3 bg-lavender-600 hover:bg-lavender-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition shadow-md hover:shadow-lg"
            >
              Open Interactive Workspace
              <ArrowRight className="w-4 h-4 text-white" />
            </Link>

            <Link
              to="/about"
              className="inline-flex items-center gap-2 px-5 py-3 bg-navy-800 hover:bg-navy-700 text-platinum-100 border border-navy-700 rounded-lg text-xs font-medium transition"
            >
              Architecture & Invariants
            </Link>

            <Link
              to="/contact"
              className="inline-flex items-center gap-2 px-5 py-3 bg-transparent hover:bg-navy-800 text-platinum-300 border border-navy-700 rounded-lg text-xs font-medium transition"
            >
              Contact Team
            </Link>
          </div>
        </div>

        {/* Live Guaranteed Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-12 pt-8 border-t border-navy-800/80">
          <div>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-emerald-400 block">0.00%</span>
            <span className="text-[11px] text-platinum-400 uppercase tracking-wider">Balance Drift Allowed</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-lavender-300 block">365 Days</span>
            <span className="text-[11px] text-platinum-400 uppercase tracking-wider">FIFO Lot Expiration</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-amber-300 block">&lt; 0.5s</span>
            <span className="text-[11px] text-platinum-400 uppercase tracking-wider">LLIRE Anomaly Scan</span>
          </div>
          <div>
            <span className="text-2xl sm:text-3xl font-bold font-mono text-white block">100%</span>
            <span className="text-[11px] text-platinum-400 uppercase tracking-wider">Dual-Key Governance</span>
          </div>
        </div>
      </div>

      {/* Comparison: Legacy Counter vs LoyaltyOS Immutable Ledger */}
      <div className="mb-12">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-navy-950">
            Why Traditional Loyalty Counters Fail
          </h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Most loyalty systems store points as a single mutable integer column. Under high-concurrency, returns, and expirations, balances silently diverge from reality.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Legacy Counter Problems */}
          <div className="bg-rose-50/50 border border-rose-200 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-rose-100 text-rose-700 rounded-lg">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-navy-950">Legacy Mutable Counters</h3>
                <span className="text-[11px] text-rose-700 font-mono">Unjournaled integer updates</span>
              </div>
            </div>
            <ul className="space-y-2.5 text-xs text-platinum-700">
              <li className="flex items-start gap-2">
                <span className="text-rose-500 font-bold shrink-0">&times;</span>
                <span><strong>Silent Balance Drift:</strong> Points can change with zero audit trail or journal entry explaining who or what changed them.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-500 font-bold shrink-0">&times;</span>
                <span><strong>Double-Spending & Race Conditions:</strong> Concurrent checkout sessions can redeem the same points twice without row locking.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-500 font-bold shrink-0">&times;</span>
                <span><strong>Distorted Order Returns:</strong> Returns do not reverse points proportionally, leaving retailers vulnerable to policy exploitation.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-500 font-bold shrink-0">&times;</span>
                <span><strong>Unchecked Administrative Edits:</strong> A single rogue operator can alter customer balances without dual-person authorization.</span>
              </li>
            </ul>
          </div>

          {/* LoyaltyOS Solution */}
          <div className="bg-emerald-50/40 border border-emerald-200 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-navy-950">LoyaltyOS Financial Ledger</h3>
                <span className="text-[11px] text-emerald-700 font-mono">Double-entry immutable architecture</span>
              </div>
            </div>
            <ul className="space-y-2.5 text-xs text-platinum-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Append-Only Ledger Journal:</strong> Balances equal the exact mathematical sum of immutable transactions and active FIFO lots.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Pessimistic Concurrency Locking:</strong> Prevents race conditions during simultaneous redemption requests.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Proportional Reversals & Negative Balances:</strong> Accurately recoups points on returned merchandise, even if spent.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Two-Person Dual-Key Governance:</strong> Remediation requires a proposer and an independent approver (proposer &ne; approver).</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="mb-12">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-navy-950">
            Four Pillars of Financial Rigor
          </h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Engineered with strict business rules implemented at both the application and database trigger levels.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pillars.map((pillar, i) => (
            <div
              key={i}
              className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm hover:border-lavender-300 transition group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-2.5 bg-platinum-100 rounded-lg group-hover:bg-lavender-50 transition">
                  {pillar.icon}
                </div>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-platinum-100 text-platinum-700">
                  {pillar.badge}
                </span>
              </div>
              <h3 className="text-base font-bold text-navy-950 mb-2">{pillar.title}</h3>
              <p className="text-xs text-platinum-600 leading-relaxed">{pillar.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Enterprise Application Domains with Images */}
      <div className="mb-12">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-navy-950">
            Designed for Mission-Critical Enterprise Retail
          </h2>
          <p className="text-xs sm:text-sm text-platinum-600 mt-2">
            Trusted where customer loyalty points carry material balance-sheet liabilities.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {enterpriseDomains.map((domain, i) => (
            <div
              key={i}
              className="bg-white border border-platinum-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition flex flex-col"
            >
              <div className="h-44 overflow-hidden relative">
                <img
                  src={domain.image}
                  alt={domain.title}
                  className="w-full h-full object-cover transition duration-300 hover:scale-105"
                />
                <span className="absolute top-3 left-3 bg-navy-950/80 backdrop-blur-xs text-white text-[10px] font-mono px-2 py-0.5 rounded">
                  {domain.tag}
                </span>
              </div>
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-bold text-navy-950 mb-1.5">{domain.title}</h3>
                  <p className="text-xs text-platinum-600 leading-relaxed">{domain.desc}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Workspace Call-to-Action */}
      <div className="rounded-2xl bg-navy-950 text-white p-8 sm:p-12 text-center border border-navy-800 shadow-xl relative overflow-hidden">
        <div className="max-w-2xl mx-auto relative z-10">
          <h2 className="text-2xl sm:text-3xl font-extrabold mb-3">
            Experience the Workspace Live
          </h2>
          <p className="text-xs sm:text-sm text-platinum-300 mb-8 leading-relaxed">
            Test all four platform roles: redeem rewards as a Customer, process orders as a Store Operator, detect anomalies as a Fraud Analyst, and execute dual-key remediation as an Operations Manager.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/workspace"
              className="px-6 py-3 bg-lavender-600 hover:bg-lavender-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition shadow-md"
            >
              Launch Interactive Workspace
            </Link>
            <Link
              to="/contact"
              className="px-6 py-3 bg-navy-800 hover:bg-navy-700 text-platinum-200 border border-navy-700 rounded-lg text-xs font-medium transition"
            >
              Contact Support
            </Link>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
