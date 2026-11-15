/**
 * LoyaltyOS — Core Loyalty & Ledger Types (Phase 4 Contracts)
 */

export interface LoyaltyAccount {
  account_id: string;
  customer_id: string;
  tier_id: string;
  current_balance: number;
  lifetime_accrued: number;
  lifetime_redeemed: number;
  qualifying_spend: string | number;
  status: 'ACTIVE' | 'FROZEN' | 'CLOSED';
  created_at: string;
  updated_at: string;
  tier_name?: string;
}

export interface Tier {
  tier_id: string;
  name: string;
  rank: number;
  min_spend: string | number;
  earning_multiplier: string | number;
}

export interface PointsTransaction {
  transaction_id: string;
  account_id: string;
  order_id?: string | null;
  related_transaction_id?: string | null;
  rule_id?: string | null;
  entry_type: 'ACCRUAL' | 'REDEMPTION' | 'REVERSAL' | 'EXPIRY' | 'ADJUSTMENT_CREDIT' | 'ADJUSTMENT_DEBIT' | string;
  direction: 'CREDIT' | 'DEBIT';
  points: number;
  running_balance: number;
  balance_after?: number;
  reference_type?: string | null;
  reference_id?: string | null;
  idempotency_key: string;
  notes?: string | null;
  created_at: string;
}
export interface TransactionHistoryPage {
  items: PointsTransaction[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PointsLot {
  lot_id: string;
  transaction_id: string;
  account_id: string;
  initial_points: number;
  remaining_points: number;
  status: 'ACTIVE' | 'PARTIALLY_REDEEMED' | 'EXHAUSTED' | 'EXPIRED' | 'REVERSED';
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface Reward {
  reward_id: string;
  name: string;
  reward_type: string;
  points_required: number;
  monetary_value: string | number;
  stock_quantity?: number | null;
  is_active: boolean;
}

export interface Redemption {
  redemption_id: string;
  account_id: string;
  reward_id: string;
  transaction_id: string;
  points_redeemed: number;
  voucher_code: string;
  status: string;
  created_at: string;
}
export interface ReconciliationReport {
  account_id: string;
  customer_id: string;
  stored_balance: number;
  ledger_derived_balance: number;
  discrepancy_amount: number;
  is_reconciled: boolean;
  status: 'RECONCILED' | 'DISCREPANCY_DETECTED';
  breakdown: Record<string, number>;
  evaluation_time: string;
  reconciled_at?: string;
  sum_ledger_credits?: number;
  sum_ledger_debits?: number;
}

export interface OrderLine {
  order_line_id?: string;
  line_number: number;
  sku: string;
  product_name: string;
  category: string;
  quantity: number;
  unit_price: number | string;
  item_discount: number | string;
  net_amount: number | string;
  is_eligible: boolean;
}

export interface Order {
  order_id: string;
  customer_id: string;
  order_date: string;
  gross_amount: number | string;
  tax_amount: number | string;
  shipping_amount: number | string;
  discount_amount: number | string;
  eligible_net_spend: number | string;
  status: string;
  accrual_status: string;
  lines: OrderLine[];
}

export interface OrderReturn {
  return_id: string;
  order_id: string;
  return_type: 'FULL' | 'PARTIAL';
  total_refund_amount: number | string;
  refund_amount?: number | string;
  points_reversed: number;
  status: string;
  created_at: string;
}
