import React, { useState, useEffect } from 'react';
import {
  Store,
  Search,
  UserPlus,
  ShoppingBag,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Coins,
  Layers,
  FileText,
  ShieldCheck,
  ShieldAlert,
  Plus,
  Trash2
} from 'lucide-react';
import { apiClient, ApiError, UserProfileResponse } from '@/services/apiClient';
import {
  LoyaltyAccount,
  PointsTransaction,
  PointsLot,
  ReconciliationReport,
  OrderReturn
} from '@/types/loyalty';

interface OperatorDashboardProps {
  user: UserProfileResponse;
}

interface OrderLineInput {
  line_number: number;
  sku: string;
  product_name: string;
  category: string;
  quantity: number;
  unit_price: number;
  is_eligible: boolean;
}

export const OperatorDashboard: React.FC<OperatorDashboardProps> = ({ user: _user }) => {
  // --- Account State ---
  const [searchQuery, setSearchQuery] = useState<string>('LOY-CUST-000001');
  const [account, setAccount] = useState<LoyaltyAccount | null>(null);
  const [history, setHistory] = useState<PointsTransaction[]>([]);
  const [lots, setLots] = useState<PointsLot[]>([]);
  const [reconciliation, setReconciliation] = useState<ReconciliationReport | null>(null);
  const [isLoadingAccount, setIsLoadingAccount] = useState<boolean>(false);
  const [accountError, setAccountError] = useState<string | null>(null);

  // --- Active Sub-tab ---
  const [activeTab, setActiveTab] = useState<'accrual' | 'return' | 'ledger' | 'provision'>('accrual');

  // --- Accrual State ---
  const [grossAmount, setGrossAmount] = useState<number>(125.00);
  const [taxAmount, setTaxAmount] = useState<number>(10.00);
  const [shippingAmount, setShippingAmount] = useState<number>(5.00);
  const [discountAmount, setDiscountAmount] = useState<number>(0.00);
  const [orderLines, setOrderLines] = useState<OrderLineInput[]>([
    {
      line_number: 1,
      sku: 'SKU-APPAREL-001',
      product_name: 'Merino Wool Pullover',
      category: 'APPAREL',
      quantity: 1,
      unit_price: 110.00,
      is_eligible: true
    }
  ]);
  const [isAccruing, setIsAccruing] = useState<boolean>(false);
  const [accrualSuccess, setAccrualSuccess] = useState<{
    points_earned: number;
    transaction_id: string;
    account_balance_after: number;
  } | null>(null);
  const [accrualError, setAccrualError] = useState<string | null>(null);

  // --- Return State ---
  const [returnOrderId, setReturnOrderId] = useState<string>('');
  const [returnType, setReturnType] = useState<'FULL' | 'PARTIAL'>('FULL');
  const [refundAmount, setRefundAmount] = useState<number>(50.00);
  const [isProcessingReturn, setIsProcessingReturn] = useState<boolean>(false);
  const [returnSuccess, setReturnSuccess] = useState<OrderReturn | null>(null);
  const [returnError, setReturnError] = useState<string | null>(null);

  // --- Provision State ---
  const [provEmail, setProvEmail] = useState<string>('');
  const [provFirstName, setProvFirstName] = useState<string>('');
  const [provLastName, setProvLastName] = useState<string>('');
  const [provPhone, setProvPhone] = useState<string>('');
  const [isProvisioning, setIsProvisioning] = useState<boolean>(false);
  const [provisionSuccess, setProvisionSuccess] = useState<string | null>(null);
  const [provisionError, setProvisionError] = useState<string | null>(null);

  // Load initial account
  const loadAccount = async (targetId: string) => {
    if (!targetId.trim()) return;
    setIsLoadingAccount(true);
    setAccountError(null);
    try {
      const acc = await apiClient.getAccount(targetId.trim());
      setAccount(acc);

      // Fetch ledger history, lots, reconciliation
      const [histData, lotsData, reconData] = await Promise.all([
        apiClient.getLedgerHistory(acc.account_id, 1, 20).catch(() => ({ items: [], total_count: 0, page: 1, page_size: 20, total_pages: 1 })),
        apiClient.getAccountLots(acc.account_id).catch(() => []),
        apiClient.getReconciliation(acc.account_id).catch(() => null)
      ]);

      setHistory(histData.items);
      setLots(lotsData);
      setReconciliation(reconData);
    } catch (err) {
      if (err instanceof ApiError) {
        setAccountError(err.problem.detail || err.problem.title);
      } else {
        setAccountError(err instanceof Error ? err.message : 'Failed to retrieve account');
      }
      setAccount(null);
      setHistory([]);
      setLots([]);
      setReconciliation(null);
    } finally {
      setIsLoadingAccount(false);
    }
  };

  useEffect(() => {
    loadAccount(searchQuery);
  }, []);

  // Compute Net Eligible Spend for accrual preview
  const netEligibleSpend = Math.max(0, grossAmount - taxAmount - shippingAmount - discountAmount);
  // Default Tier Multiplier is 1.0 (Bronze), 1.2 (Silver), 1.5 (Gold), 2.0 (Platinum)
  const tierMultiplier = account?.tier_id?.toLowerCase().includes('plat') ? 2.0 :
                         account?.tier_id?.toLowerCase().includes('gold') ? 1.5 :
                         account?.tier_id?.toLowerCase().includes('silv') ? 1.2 : 1.0;
  const estimatedPoints = Math.floor(netEligibleSpend * tierMultiplier);

  // Handle Accrual
  const handleAccrue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!account) {
      setAccrualError('Please search and select a valid customer account first.');
      return;
    }
    setIsAccruing(true);
    setAccrualSuccess(null);
    setAccrualError(null);

    try {
      const idempotencyKey = `idemp-accrue-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const res = await apiClient.accrueOrder({
        customer_id: account.customer_id,
        gross_amount: Number(grossAmount),
        tax_amount: Number(taxAmount),
        shipping_amount: Number(shippingAmount),
        discount_amount: Number(discountAmount),
        lines: orderLines.map((line) => ({
          line_number: line.line_number,
          sku: line.sku,
          product_name: line.product_name,
          category: line.category,
          quantity: Number(line.quantity),
          unit_price: Number(line.unit_price),
          is_eligible: line.is_eligible
        })),
        idempotency_key: idempotencyKey
      });

      setAccrualSuccess({
        points_earned: res.points_earned,
        transaction_id: res.transaction_id,
        account_balance_after: res.account_balance_after
      });

      // Refresh account & ledger
      await loadAccount(account.account_id);
    } catch (err) {
      if (err instanceof ApiError) {
        setAccrualError(err.problem.detail || err.problem.title);
      } else {
        setAccrualError(err instanceof Error ? err.message : 'Order accrual failed');
      }
    } finally {
      setIsAccruing(false);
    }
  };

  // Handle Return
  const handleReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returnOrderId.trim()) {
      setReturnError('Please enter a valid Order ID (e.g. ORD-xxx).');
      return;
    }
    setIsProcessingReturn(true);
    setReturnSuccess(null);
    setReturnError(null);

    try {
      const idempotencyKey = `idemp-return-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const res = await apiClient.processReturn({
        order_id: returnOrderId.trim(),
        return_type: returnType,
        total_refund_amount: Number(refundAmount),
        idempotency_key: idempotencyKey
      });

      setReturnSuccess(res);

      // Refresh account if currently selected
      if (account) {
        await loadAccount(account.account_id);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setReturnError(err.problem.detail || err.problem.title);
      } else {
        setReturnError(err instanceof Error ? err.message : 'Return processing failed');
      }
    } finally {
      setIsProcessingReturn(false);
    }
  };

  // Handle Provisioning
  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProvisioning(true);
    setProvisionSuccess(null);
    setProvisionError(null);

    try {
      const res = await apiClient.provisionAccount({
        email: provEmail.trim(),
        first_name: provFirstName.trim(),
        last_name: provLastName.trim(),
        phone: provPhone.trim() || undefined
      });

      setProvisionSuccess(`Customer ${res.customer.first_name} ${res.customer.last_name} provisioned with Account ID: ${res.account.account_id}`);
      setSearchQuery(res.account.account_id);
      await loadAccount(res.account.account_id);
      setActiveTab('accrual');
    } catch (err) {
      if (err instanceof ApiError) {
        setProvisionError(err.problem.detail || err.problem.title);
      } else {
        setProvisionError(err instanceof Error ? err.message : 'Account provisioning failed');
      }
    } finally {
      setIsProvisioning(false);
    }
  };

  const addOrderLine = () => {
    setOrderLines([
      ...orderLines,
      {
        line_number: orderLines.length + 1,
        sku: `SKU-ITEM-00${orderLines.length + 1}`,
        product_name: 'Catalog Merchandise Item',
        category: 'GENERAL',
        quantity: 1,
        unit_price: 25.00,
        is_eligible: true
      }
    ]);
  };

  const removeOrderLine = (index: number) => {
    if (orderLines.length <= 1) return;
    const updated = orderLines.filter((_, idx) => idx !== index).map((l, idx) => ({ ...l, line_number: idx + 1 }));
    setOrderLines(updated);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Operator Identity */}
      <div className="bg-navy-950 text-white rounded-xl p-6 shadow-md border border-navy-800">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-navy-800/80 rounded-lg text-platinum-200 border border-navy-700">
              <Store className="w-6 h-6 text-lavender-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Store Operator Desk
                <span className="text-xs px-2 py-0.5 rounded-full bg-lavender-900/60 text-lavender-300 border border-lavender-700">
                  Cashier & Fulfillment Terminal
                </span>
              </h2>
              <p className="text-xs text-platinum-400 mt-1">
                Real-time POS order points accrual, partial/full return reversals, and customer account lookup.
              </p>
            </div>
          </div>

          {/* Account Search Bar */}
          <div className="flex items-center gap-2 w-full lg:w-auto">
            <div className="relative flex-1 lg:w-72">
              <Search className="w-4 h-4 text-platinum-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search Account ID (e.g. LOY-CUST-000001)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadAccount(searchQuery)}
                className="w-full pl-9 pr-3 py-2 text-xs bg-navy-900 border border-navy-700 rounded-lg text-white placeholder-platinum-500 focus:outline-none focus:border-lavender-500 transition"
              />
            </div>
            <button
              onClick={() => loadAccount(searchQuery)}
              disabled={isLoadingAccount}
              className="px-3 py-2 bg-lavender-600 hover:bg-lavender-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingAccount ? 'animate-spin' : ''}`} />
              Lookup
            </button>
          </div>
        </div>

        {/* Quick Sample Accounts Pill Selector */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-navy-800/80 text-xs text-platinum-400 flex-wrap">
          <span className="text-[11px] text-platinum-500 uppercase font-mono">Quick Load:</span>
          {['LOY-CUST-000001', 'LOY-CUST-000002', 'LOY-CUST-000003', 'LOY-CUST-000004'].map((sampleId) => (
            <button
              key={sampleId}
              onClick={() => {
                setSearchQuery(sampleId);
                loadAccount(sampleId);
              }}
              className="px-2 py-0.5 rounded bg-navy-900 hover:bg-navy-800 border border-navy-700 text-platinum-300 font-mono text-[11px] transition"
            >
              {sampleId}
            </button>
          ))}
        </div>
      </div>

      {/* Account Error Alert */}
      {accountError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-800 text-xs">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div className="flex-1">
            <span className="font-semibold block">Account Retrieval Error</span>
            <span>{accountError}</span>
          </div>
          <button
            onClick={() => setActiveTab('provision')}
            className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700 transition"
          >
            Provision Account
          </button>
        </div>
      )}

      {/* Active Customer Snapshot Card */}
      {account && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-platinum-200 pb-4 mb-4">
            <div>
              <span className="text-[11px] font-mono text-platinum-500 uppercase tracking-wider block">Active Customer Account</span>
              <h3 className="text-lg font-bold text-navy-950 font-mono">{account.account_id}</h3>
              <p className="text-xs text-platinum-600">Customer ID: <span className="font-mono">{account.customer_id}</span></p>
            </div>

            <div className="flex items-center gap-3">
              {reconciliation && (
                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                  reconciliation.is_reconciled
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}>
                  {reconciliation.is_reconciled ? <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> : <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />}
                  <span>{reconciliation.is_reconciled ? 'Ledger Balanced' : 'Ledger Discrepancy'}</span>
                </div>
              )}
              <span className="px-2.5 py-1 bg-lavender-100 text-lavender-900 border border-lavender-200 rounded-full text-xs font-semibold">
                Tier: {account.tier_id}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[11px] text-platinum-500 block mb-0.5">Current Balance</span>
              <span className="text-xl font-bold font-mono text-navy-950">{account.current_balance.toLocaleString()} PTS</span>
            </div>
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[11px] text-platinum-500 block mb-0.5">Lifetime Accrued</span>
              <span className="text-xl font-bold font-mono text-emerald-700">+{account.lifetime_accrued.toLocaleString()} PTS</span>
            </div>
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[11px] text-platinum-500 block mb-0.5">Lifetime Redeemed</span>
              <span className="text-xl font-bold font-mono text-platinum-600">-{account.lifetime_redeemed.toLocaleString()} PTS</span>
            </div>
            <div className="p-3 bg-platinum-50 rounded-lg border border-platinum-200">
              <span className="text-[11px] text-platinum-500 block mb-0.5">Qualifying Spend</span>
              <span className="text-xl font-bold font-mono text-navy-950">${Number(account.qualifying_spend || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Operator Workflow Navigation Tabs */}
      <div className="flex border-b border-platinum-200 space-x-1 overflow-x-auto">
        <button
          onClick={() => setActiveTab('accrual')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'accrual'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <ShoppingBag className="w-4 h-4" />
          Order Accrual POS
        </button>

        <button
          onClick={() => setActiveTab('return')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'return'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <RotateCcw className="w-4 h-4" />
          Process Return & Reversal
        </button>

        <button
          onClick={() => setActiveTab('ledger')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'ledger'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <Layers className="w-4 h-4" />
          Double-Entry Ledger Inspector
        </button>

        <button
          onClick={() => setActiveTab('provision')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
            activeTab === 'provision'
              ? 'border-lavender-600 text-navy-950 bg-lavender-50/60 font-semibold'
              : 'border-transparent text-platinum-500 hover:text-navy-950 hover:border-platinum-300'
          }`}
        >
          <UserPlus className="w-4 h-4" />
          Provision Customer
        </button>
      </div>

      {/* TAB 1: ORDER ACCRUAL POS */}
      {activeTab === 'accrual' && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-semibold text-navy-950">POS Order Points Accrual</h3>
            <p className="text-xs text-platinum-600 mt-1">
              Computes eligible merchandise spend, excludes taxes/shipping/discounts, and floor-rounds points earned per business rules.
            </p>
          </div>

          {accrualSuccess && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3 text-emerald-900 text-xs">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold block text-sm">Order Accrual Processed Successfully!</span>
                <p>Points Credited: <strong className="font-mono text-emerald-700">+{accrualSuccess.points_earned} PTS</strong></p>
                <p>New Account Balance: <strong className="font-mono">{accrualSuccess.account_balance_after} PTS</strong></p>
                <p className="font-mono text-[11px] text-emerald-800">Ledger Tx ID: {accrualSuccess.transaction_id}</p>
              </div>
            </div>
          )}

          {accrualError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-800 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
              <div>
                <span className="font-semibold block">Accrual Failed</span>
                <span>{accrualError}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleAccrue} className="space-y-6">
            {/* Financial Amounts Breakdown */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Gross Order Total ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={grossAmount}
                  onChange={(e) => setGrossAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Sales Tax ($ - Excluded)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={taxAmount}
                  onChange={(e) => setTaxAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Shipping Fee ($ - Excluded)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={shippingAmount}
                  onChange={(e) => setShippingAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Discount ($ - Excluded)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={discountAmount}
                  onChange={(e) => setDiscountAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                />
              </div>
            </div>

            {/* Live Calculation Preview Banner */}
            <div className="p-4 bg-lavender-50/70 border border-lavender-200 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-semibold text-navy-950 block">Floor-Rounding Accrual Preview</span>
                <p className="text-platinum-600 font-mono text-[11px]">
                  Net Eligible Spend: ${netEligibleSpend.toFixed(2)} &times; Tier Multiplier ({tierMultiplier}x) = {(netEligibleSpend * tierMultiplier).toFixed(2)}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[11px] text-platinum-500 block">Expected Credited Points</span>
                  <span className="text-xl font-bold font-mono text-lavender-900">+{estimatedPoints} PTS</span>
                </div>
                <div className="p-2 bg-lavender-600 text-white rounded-lg">
                  <Coins className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Line Items Table */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-semibold text-navy-950 uppercase tracking-wider">Order Line Items</h4>
                <button
                  type="button"
                  onClick={addOrderLine}
                  className="px-2.5 py-1 text-xs bg-platinum-100 hover:bg-platinum-200 text-navy-950 rounded-lg flex items-center gap-1 font-medium transition"
                >
                  <Plus className="w-3 h-3" /> Add Item Line
                </button>
              </div>

              <div className="border border-platinum-200 rounded-lg overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="px-3 py-2">Line #</th>
                      <th className="px-3 py-2">SKU</th>
                      <th className="px-3 py-2">Product Name</th>
                      <th className="px-3 py-2">Category</th>
                      <th className="px-3 py-2">Qty</th>
                      <th className="px-3 py-2">Unit Price ($)</th>
                      <th className="px-3 py-2">Eligible</th>
                      <th className="px-3 py-2 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-platinum-100">
                    {orderLines.map((line, idx) => (
                      <tr key={idx} className="hover:bg-platinum-50/50">
                        <td className="px-3 py-2 font-mono text-platinum-500">{line.line_number}</td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={line.sku}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].sku = e.target.value;
                              setOrderLines(updated);
                            }}
                            className="w-28 px-2 py-1 border border-platinum-200 rounded text-xs font-mono"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={line.product_name}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].product_name = e.target.value;
                              setOrderLines(updated);
                            }}
                            className="w-40 px-2 py-1 border border-platinum-200 rounded text-xs"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={line.category}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].category = e.target.value;
                              setOrderLines(updated);
                            }}
                            className="w-24 px-2 py-1 border border-platinum-200 rounded text-xs uppercase"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            min="1"
                            value={line.quantity}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].quantity = parseInt(e.target.value) || 1;
                              setOrderLines(updated);
                            }}
                            className="w-14 px-2 py-1 border border-platinum-200 rounded text-xs font-mono"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={line.unit_price}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].unit_price = parseFloat(e.target.value) || 0;
                              setOrderLines(updated);
                            }}
                            className="w-20 px-2 py-1 border border-platinum-200 rounded text-xs font-mono"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="checkbox"
                            checked={line.is_eligible}
                            onChange={(e) => {
                              const updated = [...orderLines];
                              updated[idx].is_eligible = e.target.checked;
                              setOrderLines(updated);
                            }}
                            className="rounded text-lavender-600 focus:ring-lavender-500"
                          />
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => removeOrderLine(idx)}
                            disabled={orderLines.length <= 1}
                            className="text-platinum-400 hover:text-rose-600 disabled:opacity-30 transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Submission Action */}
            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isAccruing || !account}
                className="px-5 py-2.5 bg-lavender-600 hover:bg-lavender-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition shadow-sm"
              >
                {isAccruing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Processing Accrual...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Process POS Accrual
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 2: PROCESS RETURN & REVERSAL */}
      {activeTab === 'return' && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-semibold text-navy-950">Process Order Return & Points Reversal</h3>
            <p className="text-xs text-platinum-600 mt-1">
              Initiates full or partial returns with proportional points reversal against the original order accrual.
            </p>
          </div>

          {returnSuccess && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3 text-emerald-900 text-xs">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold block text-sm">Return Processed Successfully!</span>
                <p>Return ID: <strong className="font-mono">{returnSuccess.return_id}</strong></p>
                <p>Refund Amount: <strong className="font-mono">${Number(returnSuccess.refund_amount || returnSuccess.total_refund_amount || 0).toFixed(2)}</strong></p>
                <p>Points Reversed: <strong className="font-mono text-rose-700">-{returnSuccess.points_reversed} PTS</strong></p>
                <p>Status: <strong className="font-mono">{returnSuccess.status}</strong></p>
              </div>
            </div>
          )}

          {returnError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-800 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
              <div>
                <span className="font-semibold block">Return Failed</span>
                <span>{returnError}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleReturn} className="space-y-4 max-w-xl">
            <div>
              <label className="block text-xs font-semibold text-navy-950 mb-1">Parent Order ID</label>
              <input
                type="text"
                required
                placeholder="e.g. ORD-20261115-001 or order UUID"
                value={returnOrderId}
                onChange={(e) => setReturnOrderId(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
              />
              <span className="text-[11px] text-platinum-500 block mt-1">
                Enter the order ID against which the customer is seeking a return.
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Return Type</label>
                <select
                  value={returnType}
                  onChange={(e) => setReturnType(e.target.value as 'FULL' | 'PARTIAL')}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-semibold"
                >
                  <option value="FULL">FULL Return (100% Refund)</option>
                  <option value="PARTIAL">PARTIAL Return</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Refund Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={refundAmount}
                  onChange={(e) => setRefundAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500 font-mono"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isProcessingReturn}
                className="px-5 py-2.5 bg-navy-950 hover:bg-navy-900 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition"
              >
                {isProcessingReturn ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Executing Return Reversal...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-4 h-4" />
                    Confirm & Execute Return Reversal
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 3: DOUBLE-ENTRY LEDGER INSPECTOR */}
      {activeTab === 'ledger' && (
        <div className="space-y-6">
          {/* Reconciliation Invariant Report */}
          {reconciliation && (
            <div className={`p-5 rounded-xl border ${
              reconciliation.is_reconciled
                ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950'
                : 'bg-rose-50/50 border-rose-200 text-rose-950'
            }`}>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                <div className="flex items-center gap-2">
                  {reconciliation.is_reconciled ? (
                    <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  ) : (
                    <ShieldAlert className="w-5 h-5 text-rose-600" />
                  )}
                  <h4 className="font-bold text-sm">
                    {reconciliation.is_reconciled
                      ? 'Reconciliation Invariant: ZERO Discrepancy Verified'
                      : 'Reconciliation Discrepancy Detected!'}
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-platinum-500">
                  Checked: {new Date(reconciliation.reconciled_at || reconciliation.evaluation_time || Date.now()).toLocaleString()}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="p-2.5 bg-white/80 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block font-mono">Current Balance</span>
                  <span className="font-bold font-mono">{reconciliation.stored_balance} PTS</span>
                </div>
                <div className="p-2.5 bg-white/80 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block font-mono">Derived Balance</span>
                  <span className="font-bold font-mono">{reconciliation.ledger_derived_balance} PTS</span>
                </div>
                <div className="p-2.5 bg-white/80 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block font-mono">Net Ledger Entries</span>
                  <span className="font-bold font-mono">
                    {(reconciliation.sum_ledger_credits ?? reconciliation.stored_balance) - (reconciliation.sum_ledger_debits ?? 0)} PTS
                  </span>
                </div>
                <div className="p-2.5 bg-white/80 rounded border border-platinum-200">
                  <span className="text-[10px] text-platinum-500 uppercase block font-mono">Discrepancy</span>
                  <span className={`font-bold font-mono ${reconciliation.discrepancy_amount === 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {reconciliation.discrepancy_amount} PTS
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Ledger Transactions Table */}
          <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-semibold text-navy-950 flex items-center gap-2">
                <FileText className="w-4 h-4 text-lavender-600" />
                Double-Entry Ledger Transactions
              </h3>
              <span className="text-xs text-platinum-500 font-mono">{history.length} records</span>
            </div>

            {history.length === 0 ? (
              <div className="p-8 text-center text-platinum-500 text-xs">
                No ledger transactions found for this account.
              </div>
            ) : (
              <div className="border border-platinum-200 rounded-lg overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="px-3 py-2.5">Date / Time</th>
                      <th className="px-3 py-2.5">Entry Type</th>
                      <th className="px-3 py-2.5">Points</th>
                      <th className="px-3 py-2.5">Balance After</th>
                      <th className="px-3 py-2.5">Reference Type</th>
                      <th className="px-3 py-2.5">Reference ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-platinum-100 font-mono">
                    {history.map((tx) => (
                      <tr key={tx.transaction_id} className="hover:bg-platinum-50/50">
                        <td className="px-3 py-2 text-platinum-600">
                          {new Date(tx.created_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 font-semibold">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            tx.entry_type === 'ACCRUAL' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' :
                            tx.entry_type === 'REDEMPTION' ? 'bg-lavender-50 text-lavender-800 border border-lavender-200' :
                            tx.entry_type === 'RETURN_REVERSAL' ? 'bg-rose-50 text-rose-800 border border-rose-200' :
                            tx.entry_type === 'EXPIRY' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
                            'bg-platinum-100 text-platinum-800'
                          }`}>
                            {tx.entry_type}
                          </span>
                        </td>
                        <td className="px-3 py-2 font-bold">
                          {tx.points > 0 ? (
                            <span className="text-emerald-700">+{tx.points}</span>
                          ) : (
                            <span className="text-rose-700">{tx.points}</span>
                          )}
                        </td>
                        <td className="px-3 py-2 font-semibold text-navy-950">
                          {tx.running_balance ?? tx.balance_after ?? 0} PTS
                        </td>
                        <td className="px-3 py-2 text-platinum-500 text-[11px]">
                          {tx.direction || tx.reference_type || 'LEDGER'}
                        </td>
                        <td className="px-3 py-2 text-platinum-400 text-[11px] truncate max-w-xs">
                          {tx.order_id || tx.related_transaction_id || tx.reference_id || tx.idempotency_key}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Points Lots Breakdown */}
          <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-semibold text-navy-950 flex items-center gap-2">
                <Coins className="w-4 h-4 text-emerald-600" />
                Active & Historic Points Lots (FIFO Tracking)
              </h3>
              <span className="text-xs text-platinum-500 font-mono">{lots.length} lots</span>
            </div>

            {lots.length === 0 ? (
              <div className="p-8 text-center text-platinum-500 text-xs">
                No points lots found for this account.
              </div>
            ) : (
              <div className="border border-platinum-200 rounded-lg overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-platinum-50 border-b border-platinum-200 text-platinum-600 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="px-3 py-2.5">Lot ID</th>
                      <th className="px-3 py-2.5">Status</th>
                      <th className="px-3 py-2.5">Initial PTS</th>
                      <th className="px-3 py-2.5">Remaining PTS</th>
                      <th className="px-3 py-2.5">Created At</th>
                      <th className="px-3 py-2.5">Expires At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-platinum-100 font-mono">
                    {lots.map((lot) => (
                      <tr key={lot.lot_id} className="hover:bg-platinum-50/50">
                        <td className="px-3 py-2 text-platinum-600 text-[11px]">{lot.lot_id}</td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            lot.status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' :
                            lot.status === 'EXHAUSTED' || (lot.status as string) === 'DEPLETED' ? 'bg-platinum-100 text-platinum-700' :
                            'bg-amber-50 text-amber-800 border border-amber-200'
                          }`}>
                            {lot.status}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-platinum-600">{lot.initial_points}</td>
                        <td className="px-3 py-2 font-bold text-navy-950">{lot.remaining_points}</td>
                        <td className="px-3 py-2 text-platinum-500 text-[11px]">{new Date(lot.created_at).toLocaleDateString()}</td>
                        <td className="px-3 py-2 text-platinum-500 text-[11px]">{new Date(lot.expires_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: PROVISION CUSTOMER */}
      {activeTab === 'provision' && (
        <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm space-y-6 max-w-xl">
          <div>
            <h3 className="text-base font-semibold text-navy-950">Provision New Customer & Loyalty Account</h3>
            <p className="text-xs text-platinum-600 mt-1">
              Creates a new customer profile, provisions a zero-balance Bronze loyalty account, and assigns a unique account ID.
            </p>
          </div>

          {provisionSuccess && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-900 text-xs">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <span className="font-semibold block">Provisioning Complete</span>
                <span>{provisionSuccess}</span>
              </div>
            </div>
          )}

          {provisionError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-800 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
              <div>
                <span className="font-semibold block">Provisioning Error</span>
                <span>{provisionError}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleProvision} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-navy-950 mb-1">Email Address</label>
              <input
                type="email"
                required
                placeholder="customer@example.com"
                value={provEmail}
                onChange={(e) => setProvEmail(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">First Name</label>
                <input
                  type="text"
                  required
                  placeholder="First name"
                  value={provFirstName}
                  onChange={(e) => setProvFirstName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-950 mb-1">Last Name</label>
                <input
                  type="text"
                  required
                  placeholder="Last name"
                  value={provLastName}
                  onChange={(e) => setProvLastName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-navy-950 mb-1">Phone Number (Optional)</label>
              <input
                type="tel"
                placeholder="+1 555 019 2834"
                value={provPhone}
                onChange={(e) => setProvPhone(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-500"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isProvisioning}
                className="px-5 py-2.5 bg-lavender-600 hover:bg-lavender-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition"
              >
                {isProvisioning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Provisioning Account...
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    Provision Customer & Loyalty Account
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
