import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-pastel-border text-pastel-muted py-12 mt-auto text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand info */}
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 text-pastel-dark font-bold text-base mb-3 group">
              <div className="w-7 h-7 rounded-lg bg-pastel-lavender border border-pastel-border flex items-center justify-center text-xs text-pastel-dark font-bold shadow-xs">
                LO
              </div>
              Loyalty<span className="text-pastel-lavenderDark">OS</span>
            </Link>
            <p className="text-pastel-muted max-w-sm leading-relaxed text-xs mb-4">
              Enterprise customer loyalty platform built with financial double-entry bookkeeping. Guarantees 100% auditable points accrual, FIFO lot redemption, explainable anomaly detection, and dual-key remediation.
            </p>
            <div className="flex items-center gap-2 text-pastel-dark text-xs">
              <span className="w-2 h-2 rounded-full bg-pastel-sageDark animate-pulse"></span>
              <span className="font-medium">All Ledger Integrity Invariants Guaranteed</span>
            </div>
          </div>

          {/* Quick Navigation */}
          <div>
            <h4 className="text-pastel-dark font-semibold text-xs tracking-wider uppercase mb-3.5">Platform</h4>
            <ul className="space-y-2.5">
              <li>
                <Link to="/" className="hover:text-pastel-dark transition">
                  Platform Overview
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-pastel-dark transition">
                  About &amp; Architecture
                </Link>
              </li>
              <li>
                <Link to="/features" className="hover:text-pastel-dark transition">
                  Features &amp; Capabilities
                </Link>
              </li>
              <li>
                <Link to="/workspace" className="hover:text-pastel-dark transition font-semibold text-pastel-dark flex items-center gap-1">
                  Enterprise Workspace <ArrowRight className="w-3 h-3 text-pastel-sageDark" />
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-pastel-dark transition">
                  Contact &amp; Support
                </Link>
              </li>
            </ul>
          </div>

          {/* Core Guarantees */}
          <div>
            <h4 className="text-pastel-dark font-semibold text-xs tracking-wider uppercase mb-3.5">Core Guarantees</h4>
            <ul className="space-y-2.5 font-mono text-[11px] text-pastel-muted">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-pastel-sageDark shrink-0" />
                <span className="text-pastel-dark">Immutable Journal</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-pastel-sageDark shrink-0" />
                <span className="text-pastel-dark">365-Day FIFO Expiry</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-pastel-sageDark shrink-0" />
                <span className="text-pastel-dark">LLIRE Forensic Engine</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-pastel-sageDark shrink-0" />
                <span className="text-pastel-dark">Dual-Key Remediation</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-pastel-border flex flex-col sm:flex-row items-center justify-between gap-4 text-pastel-muted">
          <p>&copy; {new Date().getFullYear()} LoyaltyOS. Intelligent Loyalty &amp; Ledger Management Platform. All rights reserved.</p>
          <div className="flex items-center gap-4 text-[11px]">
            <Link to="/about" className="hover:text-pastel-dark transition">Architecture</Link>
            <span>&bull;</span>
            <Link to="/contact" className="hover:text-pastel-dark transition">Contact Us</Link>
            <span>&bull;</span>
            <span className="text-pastel-dark font-medium">Enterprise Edition</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
