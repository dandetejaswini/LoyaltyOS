import React from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import { BookOpen } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <PageContainer
      title="Architecture & Operational Principles"
      subtitle="Complete documentation of the LoyaltyOS double-entry loyalty ledger model."
    >
      <div className="bg-white border border-platinum-200 rounded-lg p-6 sm:p-8 mb-6 shadow-sm">
        <h2 className="text-lg font-bold text-navy-950 mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-lavender-600" />
          The Financial Ledger Accounting Invariant
        </h2>
        <p className="text-sm text-platinum-700 leading-relaxed mb-4">
          In <strong className="text-navy-950">LoyaltyOS</strong>, points are not mutable database counter columns. Every point awarded, redeemed, reversed, or expired is an immutable ledger entry in <code className="bg-platinum-100 px-1 py-0.5 rounded text-xs font-mono text-navy-900">points_transactions</code>.
        </p>
        <div className="bg-navy-950 border border-navy-800 rounded-lg p-4 font-mono text-xs text-platinum-200 mb-6 shadow-inner">
          <p className="font-semibold text-lavender-300 mb-1">Mathematical Balance Reconciliation Invariant:</p>
          <p className="text-platinum-300">CurrentBalance = SUM(Credits: ACCRUAL + ADJUSTMENT_CREDIT) - SUM(Debits: REDEMPTION + REVERSAL + EXPIRY + ADJUSTMENT_DEBIT)</p>
        </div>

        <h3 className="text-base font-semibold text-navy-950 mb-3">Core Tier Earning Multipliers</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border border-platinum-200 rounded-lg overflow-hidden">
            <thead className="bg-platinum-100 text-platinum-700 uppercase font-semibold">
              <tr>
                <th className="px-4 py-2.5 border-b">Tier Level</th>
                <th className="px-4 py-2.5 border-b">Qualifying Spend (Rolling 365d)</th>
                <th className="px-4 py-2.5 border-b">Earning Multiplier</th>
                <th className="px-4 py-2.5 border-b">Points per $1.00 Net Spend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-platinum-200">
              <tr>
                <td className="px-4 py-2.5 font-semibold text-loyalty-bronze">Bronze</td>
                <td className="px-4 py-2.5 text-platinum-700">$0.00 – $499.99</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.00x</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.00 pt / $1</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 font-semibold text-loyalty-silver">Silver</td>
                <td className="px-4 py-2.5 text-platinum-700">$500.00 – $999.99</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.25x</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.25 pts / $1</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 font-semibold text-loyalty-gold">Gold</td>
                <td className="px-4 py-2.5 text-platinum-700">$1,000.00 – $2,499.99</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.50x</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">1.50 pts / $1</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 font-semibold text-navy-900">Platinum</td>
                <td className="px-4 py-2.5 text-platinum-700">≥ $2,500.00</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">2.00x</td>
                <td className="px-4 py-2.5 font-mono text-navy-900">2.00 pts / $1</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
};
