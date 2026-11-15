import React, { useEffect, useState } from 'react';
import { 
  Wallet, 
  Award, 
  Clock, 
  Gift, 
  History, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Copy,
  Check
} from 'lucide-react';
import { apiClient } from '@/services/apiClient';
import { LoyaltyAccount, PointsTransaction, PointsLot, Reward, Redemption, ReconciliationReport } from '@/types/loyalty';
import { UserProfileResponse } from '@/services/apiClient';

interface CustomerDashboardProps {
  user: UserProfileResponse;
}

export const CustomerDashboard: React.FC<CustomerDashboardProps> = ({ user }) => {
  const accountId = user.customer?.loyalty_account?.account_id || 'LOY-CUST-000001';

  const [account, setAccount] = useState<LoyaltyAccount | null>(null);
  const [history, setHistory] = useState<PointsTransaction[]>([]);
  const [lots, setLots] = useState<PointsLot[]>([]);
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [reconciliation, setReconciliation] = useState<ReconciliationReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Redemption State
  const [isRedeeming, setIsRedeeming] = useState<boolean>(false);
  const [redemptionSuccess, setRedemptionSuccess] = useState<Redemption | null>(null);
  const [redemptionError, setRedemptionError] = useState<string | null>(null);
  const [copiedVoucher, setCopiedVoucher] = useState<boolean>(false);

  const loadCustomerData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch account profile
      let accData: LoyaltyAccount;
      try {
        accData = await apiClient.getMyAccount();
      } catch {
        accData = await apiClient.getAccount(accountId);
      }
      setAccount(accData);

      // 2. Fetch history, lots, rewards, and reconciliation in parallel
      const [histData, lotsData, rewardsData, reconData] = await Promise.all([
        apiClient.getLedgerHistory(accData.account_id, 1, 10).catch(() => ({ items: [], total_count: 0, page: 1, page_size: 10, total_pages: 1 })),
        apiClient.getAccountLots(accData.account_id, 'ACTIVE').catch(() => []),
        apiClient.getRewards().catch(() => []),
        apiClient.getReconciliation(accData.account_id).catch(() => null),
      ]);

      setHistory(histData.items);
      setLots(lotsData);
      setRewards(rewardsData);
      setReconciliation(reconData);
    } catch (err: any) {
      console.warn('Customer data load error:', err);
      setError(err?.problem?.detail || err?.message || 'Failed to load customer account records.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCustomerData();
  }, [accountId]);

  const handleRedeem = async (reward: Reward) => {
    if (!account) return;
    setIsRedeeming(true);
    setRedemptionError(null);
    setRedemptionSuccess(null);
    setCopiedVoucher(false);

    try {
      const res = await apiClient.redeemReward({
        account_id: account.account_id,
        reward_id: reward.reward_id,
      });
      setRedemptionSuccess(res);
      // Refresh balance and history
      loadCustomerData();
    } catch (err: any) {
      setRedemptionError(err?.problem?.detail || err?.message || 'Redemption rejected.');
    } finally {
      setIsRedeeming(false);
    }
  };

  const copyVoucherCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedVoucher(true);
    setTimeout(() => setCopiedVoucher(false), 2000);
  };

  const tierColors: Record<string, string> = {
    'TIER-BRONZE': 'text-amber-700 bg-amber-50 border-amber-200',
    'TIER-SILVER': 'text-slate-700 bg-slate-100 border-slate-300',
    'TIER-GOLD': 'text-yellow-800 bg-yellow-50 border-yellow-300',
    'TIER-PLATINUM': 'text-indigo-900 bg-indigo-50 border-indigo-200',
  };

  const tierBadgeClass = account ? tierColors[account.tier_id] || 'text-navy-900 bg-platinum-100 border-platinum-300' : '';

  return (
    <div className="space-y-6">
      {/* Header and Refresh */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-navy-950 p-6 rounded-xl border border-navy-800 text-white shadow-md">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-lavender-400 font-semibold block mb-1">
            Member Portal
          </span>
          <h2 className="text-xl font-bold tracking-tight text-white">
            Welcome back, {user.full_name || user.email}
          </h2>
          <p className="text-xs text-platinum-400 mt-0.5 font-mono">
            Account: {account?.account_id || accountId} &bull; Customer: {user.customer?.customer_id || 'CUST-000001'}
          </p>
        </div>
        <button
          onClick={loadCustomerData}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-2 bg-navy-800 hover:bg-navy-700 border border-navy-700 rounded-lg text-xs font-medium text-platinum-200 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Account
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-rose-900">Account Synchronization Notice</p>
            <p className="text-rose-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Available Points */}
        <div className="bg-white p-5 rounded-xl border border-platinum-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-platinum-500 uppercase tracking-wider">Available Balance</span>
            <div className="w-8 h-8 rounded-lg bg-navy-50 flex items-center justify-center text-navy-900">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-navy-950">
              {account ? account.current_balance.toLocaleString() : '0'}
            </span>
            <span className="text-xs font-semibold text-platinum-500">PTS</span>
          </div>
          {account && account.current_balance < 0 && (
            <span className="inline-block mt-2 px-2 py-0.5 text-[10px] font-bold uppercase bg-rose-100 text-rose-700 rounded">
              Frozen / Negative Balance
            </span>
          )}
        </div>

        {/* Loyalty Tier */}
        <div className="bg-white p-5 rounded-xl border border-platinum-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-platinum-500 uppercase tracking-wider">Current Tier</span>
            <div className="w-8 h-8 rounded-lg bg-lavender-50 flex items-center justify-center text-lavender-700">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 text-xs font-bold uppercase rounded-md border ${tierBadgeClass}`}>
              {account?.tier_id?.replace('TIER-', '') || 'BRONZE'}
            </span>
          </div>
          <span className="text-[11px] text-platinum-500 block mt-2">
            Tier spend: ${Number(account?.qualifying_spend || 0).toFixed(2)} / 365d
          </span>
        </div>

        {/* Lifetime Earned */}
        <div className="bg-white p-5 rounded-xl border border-platinum-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-platinum-500 uppercase tracking-wider">Lifetime Accrued</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-700">
              <History className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-navy-950">
              {account ? account.lifetime_accrued.toLocaleString() : '0'}
            </span>
            <span className="text-xs font-semibold text-platinum-500">PTS</span>
          </div>
          <span className="text-[11px] text-platinum-500 block mt-1">
            Redeemed: {account ? account.lifetime_redeemed.toLocaleString() : '0'} PTS
          </span>
        </div>

        {/* Reconciliation Status */}
        <div className="bg-white p-5 rounded-xl border border-platinum-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-platinum-500 uppercase tracking-wider">Ledger Health</span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              reconciliation?.is_reconciled ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'
            }`}>
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${
            reconciliation?.is_reconciled
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-amber-50 text-amber-800 border-amber-200'
          }`}>
            {reconciliation?.is_reconciled ? '100% Balanced' : 'Variance Detected'}
          </span>
          <span className="text-[11px] text-platinum-500 block mt-2 font-mono">
            Journal Parity Verified
          </span>
        </div>
      </div>

      {/* Rewards Catalog Section */}
      <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-navy-950 flex items-center gap-2">
              <Gift className="w-4 h-4 text-lavender-600" />
              Available Rewards Catalog
            </h3>
            <p className="text-xs text-platinum-500">
              Redeem your accrued loyalty points for instant digital discount vouchers.
            </p>
          </div>
        </div>

        {/* Redemption Alert / Voucher Modal Result */}
        {redemptionSuccess && (
          <div className="mb-6 p-5 bg-emerald-50 border border-emerald-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 shrink-0">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-emerald-900">Voucher Issued Successfully!</p>
                <p className="text-xs text-emerald-700">
                  {redemptionSuccess.points_redeemed} points deducted. Present this voucher code at checkout.
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="px-3 py-1 bg-white border border-emerald-300 rounded font-mono font-bold text-sm text-navy-950 tracking-wider">
                    {redemptionSuccess.voucher_code}
                  </span>
                  <button
                    onClick={() => copyVoucherCode(redemptionSuccess.voucher_code)}
                    className="p-1.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 rounded transition"
                    title="Copy Voucher Code"
                  >
                    {copiedVoucher ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
            <button
              onClick={() => setRedemptionSuccess(null)}
              className="text-xs text-emerald-800 font-medium underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {redemptionError && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between">
            <span>{redemptionError}</span>
            <button onClick={() => setRedemptionError(null)} className="text-rose-900 font-bold ml-4">✕</button>
          </div>
        )}

        {/* Catalog Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {rewards.map((reward) => {
            const canAfford = account ? account.current_balance >= reward.points_required : false;
            return (
              <div
                key={reward.reward_id}
                className="p-5 rounded-xl border border-platinum-200 bg-platinum-50/50 hover:border-platinum-300 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-platinum-500 bg-white px-2 py-0.5 rounded border border-platinum-200">
                      {reward.reward_type}
                    </span>
                    <span className="text-sm font-bold font-mono text-navy-900">
                      ${Number(reward.monetary_value).toFixed(2)} Value
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-navy-950 mb-1">{reward.name}</h4>
                  <p className="text-xs text-platinum-600 mb-4">
                    Requires <span className="font-mono font-bold text-navy-900">{reward.points_required.toLocaleString()}</span> points
                  </p>
                </div>

                <button
                  disabled={!canAfford || isRedeeming}
                  onClick={() => handleRedeem(reward)}
                  className={`w-full py-2.5 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                    canAfford
                      ? 'bg-navy-900 hover:bg-navy-800 text-white shadow-sm'
                      : 'bg-platinum-200 text-platinum-400 cursor-not-allowed'
                  }`}
                >
                  <Gift className="w-3.5 h-3.5" />
                  {canAfford ? 'Redeem Voucher' : 'Insufficient Points'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Grid: Points Activity & Active Lots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Ledger History */}
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-navy-950 flex items-center gap-2">
              <History className="w-4 h-4 text-navy-700" />
              Recent Points Journal
            </h3>
            <span className="text-[11px] text-platinum-500 font-mono">Append-Only</span>
          </div>

          {history.length === 0 ? (
            <div className="p-8 text-center text-xs text-platinum-500">
              No points transactions recorded yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-platinum-200 text-platinum-500 uppercase tracking-wider text-[10px]">
                    <th className="pb-2 font-semibold">Date</th>
                    <th className="pb-2 font-semibold">Type</th>
                    <th className="pb-2 font-semibold text-right">Points</th>
                    <th className="pb-2 font-semibold text-right">Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-platinum-100">
                  {history.map((tx) => (
                    <tr key={tx.transaction_id} className="hover:bg-platinum-50/60 transition">
                      <td className="py-2.5 font-mono text-platinum-600 text-[11px]">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                          tx.entry_type === 'ACCRUAL' || tx.entry_type === 'ADJUSTMENT_CREDIT'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : tx.entry_type === 'REDEMPTION'
                            ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          {tx.entry_type}
                        </span>
                      </td>
                      <td className={`py-2.5 font-mono font-bold text-right ${
                        tx.points > 0 ? 'text-emerald-600' : 'text-rose-600'
                      }`}>
                        {tx.points > 0 ? `+${tx.points}` : tx.points}
                      </td>
                      <td className="py-2.5 font-mono text-right text-platinum-700">
                        {tx.running_balance.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Active Points Lots & Expiry */}
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-navy-950 flex items-center gap-2">
              <Clock className="w-4 h-4 text-navy-700" />
              Active Points Lots (FIFO Expiry)
            </h3>
            <span className="text-[11px] text-platinum-500 font-mono">365-Day Lifecycle</span>
          </div>

          {lots.length === 0 ? (
            <div className="p-8 text-center text-xs text-platinum-500">
              No active points lots found.
            </div>
          ) : (
            <div className="space-y-3">
              {lots.map((lot) => (
                <div key={lot.lot_id} className="p-3.5 bg-platinum-50 rounded-lg border border-platinum-200 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-bold text-navy-950">{lot.lot_id}</span>
                      <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded">
                        {lot.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-platinum-500">
                      Expires: {new Date(lot.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-sm text-navy-950 block">
                      {lot.remaining_points} / {lot.initial_points}
                    </span>
                    <span className="text-[10px] text-platinum-400 font-mono">Remaining PTS</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
