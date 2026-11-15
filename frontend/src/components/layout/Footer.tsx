import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-navy-950 border-t border-navy-800 text-platinum-400 py-12 mt-auto text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand info */}
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 text-white font-bold text-base mb-3 group">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-lavender-500 to-navy-900 border border-lavender-400/30 flex items-center justify-center text-xs text-white font-bold">
                LO
              </div>
              Loyalty<span className="text-lavender-400">OS</span>
            </Link>
            <p className="text-platinum-400 max-w-sm leading-relaxed text-xs mb-4">
              Enterprise customer loyalty platform built with financial double-entry bookkeeping. Guarantees 100% auditable points accrual, FIFO lot redemption, explainable anomaly detection, and dual-key remediation.
            </p>
            <div className="flex items-center gap-2 text-platinum-300 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>All Ledger Integrity Invariants Guaranteed</span>
            </div>
          </div>

          {/* Quick Navigation */}
          <div>
            <h4 className="text-platinum-200 font-semibold text-xs tracking-wider uppercase mb-3.5">Platform</h4>
            <ul className="space-y-2.5">
              <li>
                <Link to="/" className="hover:text-lavender-300 transition">
                  Platform Overview
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-lavender-300 transition">
                  About & Architecture
                </Link>
              </li>
              <li>
                <Link to="/features" className="hover:text-lavender-300 transition">
                  Features & Capabilities
                </Link>
              </li>
              <li>
                <Link to="/workspace" className="hover:text-lavender-300 transition font-medium text-lavender-400 flex items-center gap-1">
                  Enterprise Workspace <ArrowRight className="w-3 h-3" />
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-lavender-300 transition">
                  Contact & Support
                </Link>
              </li>
            </ul>
          </div>

          {/* Core Guarantees */}
          <div>
            <h4 className="text-platinum-200 font-semibold text-xs tracking-wider uppercase mb-3.5">Core Guarantees</h4>
            <ul className="space-y-2.5 font-mono text-[11px] text-platinum-400">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-lavender-400 shrink-0" />
                <span>Immutable Journal</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-lavender-400 shrink-0" />
                <span>365-Day FIFO Expiry</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-lavender-400 shrink-0" />
                <span>LLIRE Forensic Engine</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-lavender-400 shrink-0" />
                <span>Dual-Key Remediation</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-navy-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-platinum-500">
          <p>© {new Date().getFullYear()} LoyaltyOS. Intelligent Loyalty & Ledger Management Platform. All rights reserved.</p>
          <div className="flex items-center gap-4 text-[11px]">
            <Link to="/about" className="hover:text-platinum-400 transition">Architecture</Link>
            <span>•</span>
            <Link to="/contact" className="hover:text-platinum-400 transition">Contact Us</Link>
            <span>•</span>
            <span className="text-lavender-400 font-medium">Enterprise Edition</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
