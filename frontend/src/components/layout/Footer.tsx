import React from 'react';
import { Shield, BookOpen, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-navy-950 border-t border-navy-800 text-platinum-400 py-10 mt-auto text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand info */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 text-white font-semibold text-sm mb-2">
              <span className="w-5 h-5 rounded bg-lavender-600 flex items-center justify-center text-[10px] text-white font-bold">LO</span>
              LoyaltyOS — Intelligent Loyalty & Ledger Management Platform
            </div>
            <p className="text-platinum-400 max-w-sm leading-relaxed text-xs">
              Financial-grade, append-only loyalty points ledger supporting atomic accruals, FIFO lot-based redemptions, proportional return reversals, and idempotent batch expiration.
            </p>
          </div>

          {/* Quick specs */}
          <div>
            <h4 className="text-platinum-200 font-semibold text-xs tracking-wider uppercase mb-3">Core Invariants</h4>
            <ul className="space-y-2">
              <li className="flex items-center gap-1.5 text-platinum-400">
                <Shield className="w-3.5 h-3.5 text-lavender-400" />
                Append-only ledger journal
              </li>
              <li className="flex items-center gap-1.5 text-platinum-400">
                <Layers className="w-3.5 h-3.5 text-lavender-400" />
                FIFO lot allocation
              </li>
              <li className="flex items-center gap-1.5 text-platinum-400">
                <BookOpen className="w-3.5 h-3.5 text-lavender-400" />
                100% balance reconciliation
              </li>
            </ul>
          </div>

          {/* System metadata */}
          <div>
            <h4 className="text-platinum-200 font-semibold text-xs tracking-wider uppercase mb-3">Engineering Spec</h4>
            <div className="space-y-1 font-mono text-[11px] text-platinum-400">
              <p>Platform: LoyaltyOS Core</p>
              <p>Architecture: Three-Tier</p>
              <p>Frontend: React 18 / TS / Vite</p>
              <p>Application: FastAPI / Python 3.14</p>
              <p>Context: YottaFlex Hackathon</p>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-navy-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-platinum-500">
          <p>© 2026 LoyaltyOS. Built for YottaFlex AI Forward Deployed Engineer Hackathon.</p>
          <div className="flex items-center gap-4">
            <span className="text-lavender-400">Free-Tier & Open-Source Stack</span>
            <span>•</span>
            <span>Vercel-Ready SPA</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
