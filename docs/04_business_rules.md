# 04. Business Rules and Policy Specifications

## 1. Core Principles of the Loyalty Ledger

The YottaFlex loyalty platform operates under strict financial accounting and auditability principles:
1. **Append-Only Immutability**: The points ledger (`PointsTransaction`) is strictly append-only. Financial records are never updated or deleted. Corrections are executed exclusively through compensating credit or debit entries (`ADJUSTMENT_CREDIT`, `ADJUSTMENT_DEBIT`).
2. **Deterministic Ledger Balance Reconciliation**: The true points balance of any loyalty account is the mathematical sum of all historical credits minus all historical debits. Cached account balances are materialized views that must strictly equal the ledger sum.
3. **Traceability and Parent-Child Lineage**: Every derivative transaction (reversal, redemption allocation, expiration) must maintain an unbroken foreign-key link to its source entity (order, accrual transaction, points lot).
4. **Idempotency & Concurrency Safety**: All write operations enforce unique idempotency keys to guarantee that network retries produce zero duplicate ledger debits or credits. Concurrent redemptions are protected via pessimistic row locking.
5. **Auditable Decision Boundaries**: Rejected transactions (e.g., overdraft attempts) are captured in dedicated decision logs without corrupting the financial ledger.

---

## 2. Spend & Earning Rules

### Rule BR-01: Eligible Net Spend Calculation
- **Definition**: Points are awarded strictly on money spent on eligible goods and services, net of discounts.
- **Formula**:
  $$\text{EligibleNetSpend} = \sum_{i \in \text{OrderLines}} \max(0, (\text{unit\_price}_i \times \text{quantity}_i) - \text{discount}_i) \quad \text{for } \text{is\_eligible}_i = \text{TRUE}$$
- **Exclusions**:
  - Sales tax, VAT, and government duties are strictly excluded.
  - Shipping, courier, and delivery fees are strictly excluded.
  - Tips, gratuities, and service convenience charges are excluded.
  - Gift card purchases are excluded (points are earned when the gift card is redeemed for merchandise, not upon gift card acquisition).
- **Inclusions**:
  - Regular merchandise and service line items.
  - Partial coupon discounts applied proportionally or at the line-item level.

### Rule BR-02: Base & Tier-Specific Earning Rates
- **Base Earning Multiplier**: 1.0 points per \$1.00 USD of eligible net spend.
- **Tier-Specific Multipliers**:
  | Tier Level | Name | Minimum Qualifying Spend (Rolling 365 Days) | Earning Multiplier | Points per \$1.00 Net Spend |
  |---|---|---|---|---|
  | Level 1 | **Bronze** | \$0.00 – \$499.99 | 1.00x | 1.00 pts / \$1 |
  | Level 2 | **Silver** | \$500.00 – \$999.99 | 1.25x | 1.25 pts / \$1 |
  | Level 3 | **Gold** | \$1,000.00 – \$2,499.99 | 1.50x | 1.50 pts / \$1 |
  | Level 4 | **Platinum** | $\ge \$2,500.00$ | 2.00x | 2.00 pts / \$1 |

### Rule BR-03: Promotional Rule Multipliers
- Additional rule multipliers may apply based on active promotional campaigns (e.g., category multipliers, double points weekends, holiday events).
- Multiple active rules apply multiplicatively or additively based on the rule configuration:
  $$\text{EffectiveMultiplier} = \text{TierMultiplier} \times \prod_{r \in \text{ActiveMultipliers}} r.\text{multiplier}$$

### Rule BR-04: Points Rounding Policy
- **Policy**: Points earned are calculated using **Integer Floor Rounding** (`FLOOR`).
- **Formula**:
  $$\text{PointsEarned} = \left\lfloor \text{EligibleNetSpend} \times \text{EffectiveMultiplier} \right\rfloor$$
- **Example**:
  - Eligible Net Spend: \$49.80.
  - Customer Tier: Silver (1.25x).
  - Raw calculation: $49.80 \times 1.25 = 62.25$.
  - Points awarded: $\lfloor 62.25 \rfloor = 62$ points.
- **Rationale**: Eliminates fractional point liabilities on the ledger and prevents rounding manipulation.

---

## 3. Tier Qualification & Progression Rules

### Rule BR-05: Qualifying Spend vs Gross Spend
- **Gross Spend**: Total invoice amount paid by customer, including taxes, delivery fees, and tips.
- **Qualifying Spend**: Accumulated eligible net spend on completed orders within the rolling qualification window (365 days), minus returns.
  $$\text{QualifyingSpend}(t) = \sum_{o \in \text{CompletedOrders}(t - 365, t)} o.\text{eligible\_net\_spend} - \sum_{r \in \text{Returns}(t - 365, t)} r.\text{refunded\_eligible\_spend}$$
- **Invariant**: Tier progression is evaluated strictly on `QualifyingSpend`, **never** on Gross Spend. Using Gross Spend is a designated anomaly (`GROSS_SPEND_TIER_CALCULATION`).

### Rule BR-06: Tier Progression (Upgrades)
- Evaluated immediately upon order completion.
- If `QualifyingSpend` $\ge$ higher tier threshold:
  - Account `tier_id` is updated immediately.
  - New tier status takes effect immediately; subsequent orders earn at the new multiplier.
  - `TierTransition` record is logged with `transition_type='UPGRADE'`.

### Rule BR-07: Tier Retention and Downgrades
- Evaluated annually on the customer's membership qualification anniversary date.
- If `QualifyingSpend` within the preceding 365 days is below the current tier's threshold:
  - The customer is transitioned to the highest tier for which their qualifying spend qualifies.
  - `TierTransition` record is logged with `transition_type='DOWNGRADE'`.

---

## 4. Points Redemption & Lot Allocation Rules

### Rule BR-08: Redemption Validation
- Customer must have an active `LoyaltyAccount` in `ACTIVE` status.
- Requested redemption points must be an integer $> 0$.
- **Balance Invariant**:
  $$\text{RequestedPoints} \le \text{AvailableBalance}$$
  where $\text{AvailableBalance} = \sum_{\text{lots}} \text{remaining\_points} \quad \text{for } \text{status} \in (\text{'ACTIVE'}, \text{'PARTIALLY\_REDEEMED'}) \land \text{expires\_at} > \text{NOW()}$.
- If $\text{RequestedPoints} > \text{AvailableBalance}$, the request is rejected with error code `INSUFFICIENT_BALANCE` and logged to `RejectedOperation`.

### Rule BR-09: Points-Lot Allocation Policy (FIFO Policy)
- Points lots are consumed on a strict **First-In, First-Out (FIFO)** basis.
- Candidate lots are ordered deterministically:
  $$\text{ORDER BY expires\_at ASC, created\_at ASC}$$
- **Allocation Algorithm**:
  ```python
  remaining_to_deduct = requested_points
  for lot in active_unexpired_lots:
      if remaining_to_deduct == 0:
          break
      deduction = min(lot.remaining_points, remaining_to_deduct)
      lot.remaining_points -= deduction
      if lot.remaining_points == 0:
          lot.status = "EXHAUSTED"
      else:
          lot.status = "PARTIALLY_REDEEMED"
      
      # Record allocation link
      create_lot_allocation(redemption_id, lot.id, deduction)
      remaining_to_deduct -= deduction
  ```
- **Rationale**: Prioritizing lots nearest to expiration protects customer value and minimizes accidental point loss.

### Rule BR-10: Partial Redemption Support
- Points may be redeemed for distinct catalog rewards or applied as a flexible discount against an order at a fixed valuation (e.g., 100 points = \$1.00 USD).
- A customer may execute multiple redemptions across different transactions, each generating a unique voucher and ledger debit.

---

## 5. Order Returns & Points Reversal Rules

### Rule BR-11: Full Order Return Reversal
- When an entire order is returned or cancelled, 100% of the points awarded for that order must be reversed.
- The reversal transaction must populate `related_transaction_id` pointing directly to the original accrual `PointsTransaction`.

### Rule BR-12: Partial Order Return Proportional Reversal
- When a customer returns a subset of items from an order, points are reversed strictly proportional to the returned line item's net spend:
  $$\text{ReversalPoints} = \text{ROUND}\left( \frac{\text{ReturnedLineEligibleNetSpend}}{\text{OriginalOrderEligibleNetSpend}} \times \text{OriginalAccrualPoints} \right)$$
- Example:
  - Original Order: Item A (\$60.00), Item B (\$40.00). Total Net = \$100.00. Points Earned = 100 points.
  - Return: Item B (\$40.00).
  - Points Reversed: $\text{ROUND}((40.00 / 100.00) \times 100) = 40$ points.

### Rule BR-13: Reversal Ceiling & Parent Linkage
- **Ceiling Constraint**: Cumulative points reversed for any order across all return events must never exceed the original accrual points:
  $$\sum_{r \in \text{Reversals}(\text{order})} r.\text{points} \le \text{OriginalAccrual}.\text{points}$$
- Attempting to reverse more points than originally granted is rejected with error code `REVERSAL_EXCEEDS_ACCRUAL`.
- Every reversal must populate `related_transaction_id`.

### Rule BR-14: Negative Balance Policy
- If an order return reverses points that have already been redeemed by the customer, the account's `current_balance` is decremented below zero ($< 0$).
- When `current_balance < 0`:
  - Account status remains `ACTIVE`.
  - All redemption attempts are blocked until new accruals bring the balance back $\ge 0$.
  - Tier progression qualifying spend is decremented by the returned net spend.

---

## 6. Points Expiration Rules

### Rule BR-15: Expiration Validity Period
- Standard points lots expire exactly **365 days** after the date of accrual at 23:59:59 UTC:
  $$\text{expires\_at} = \text{accrual\_timestamp} + \text{INTERVAL '365 days'}$$

### Rule BR-16: Batch & Idempotent Expiration
- Points expiration runs via scheduled batch (`ExpiryBatch`).
- Candidates for expiration are filtered strictly by:
  ```sql
  WHERE expires_at <= :cutoff_timestamp 
    AND remaining_points > 0 
    AND status IN ('ACTIVE', 'PARTIALLY_REDEEMED')
  ```
- **Idempotency Guarantee**:
  - Once a lot has been processed for expiration, its `remaining_points` is set to `0` and its `status` is set to `EXPIRED`.
  - Re-running the batch job immediately on the same date will match zero candidate rows, resulting in zero additional ledger debits.
  - Expiring an already expired lot is a designated anomaly (`DOUBLE_EXPIRATION`).

---

## 7. Concurrency, Idempotency & Failure Rules

### Rule BR-17: Pessimistic Concurrency Control
- All points balance modifications (redemptions, accruals, reversals) must acquire an exclusive row-level lock on the target `LoyaltyAccount`:
  ```sql
  SELECT * FROM loyalty_accounts WHERE account_id = :id FOR UPDATE;
  ```
- Prevents race conditions and double-spending across concurrent requests.

### Rule BR-18: Idempotency Key Enforcement
- All mutation endpoints (`POST /accruals`, `POST /redemptions`, `POST /returns/reverse`, `POST /expiry/batch`) require an `Idempotency-Key` HTTP header.
- Pattern: `IDEMP-<operation>-<entity_id>-<hash>`.
- If an idempotency key is re-submitted:
  - If previous execution completed: return cached HTTP response and body with `X-Cache-Lookup: HIT`.
  - If previous execution is still processing: return `409 Conflict` (Concurrent Request in Progress).
  - If previous execution failed: allow retry.

### Rule BR-19: Audit Logging for Rejected Transactions
- Rejected or failed transactions (e.g., overdraft redemptions, invalid promo codes, over-reversals) must:
  1. **Never** create rows in `PointsTransaction`.
  2. Be recorded in `RejectedOperation` with timestamp, actor, error code, and payload.
  3. Emit an `OPERATION_REJECTED` audit event.

---

## 8. Business Rules Summary Matrix

| Rule ID | Rule Domain | Primary Entity | Critical Invariant | Anomaly if Violated |
|---|---|---|---|---|
| **BR-01** | Net Spend | `OrderLine` | Excludes tax, shipping, and gift cards. | Spend Inflation |
| **BR-02** | Earning Rate | `Tier` | Bronze: 1.0x, Silver: 1.25x, Gold: 1.5x, Platinum: 2.0x. | Multiplier Miscalculation |
| **BR-04** | Rounding | `PointsTransaction` | Integer Floor Rounding: $\lfloor spend \times rate \rfloor$. | Fractional Liability |
| **BR-05** | Qualifying Spend | `LoyaltyAccount` | Tiers calculated strictly on net spend, not gross. | `GROSS_SPEND_TIER_CALCULATION` |
| **BR-08** | Redemption | `LoyaltyAccount` | Requested points $\le$ available balance. | `OVER_REDEMPTION` |
| **BR-09** | Lot Allocation | `PointsLot` | Strict FIFO by `expires_at ASC, created_at ASC`. | Unfair Breakage |
| **BR-11** | Return Reversal | `PointsTransaction` | Returns must reverse earned points with parent link. | `RETURN_WITHOUT_REVERSAL` |
| **BR-13** | Reversal Ceiling | `PointsTransaction` | Cumulative reversals $\le$ original accrual points. | Negative Accrual Drift |
| **BR-16** | Expiration | `PointsLot` | Idempotent batch; lots expire exactly once. | `DOUBLE_EXPIRATION` |
| **BR-17** | Concurrency | `LoyaltyAccount` | Row locks (`FOR UPDATE`) prevent double spending. | Race Condition / Overdraft |
| **BR-18** | Idempotency | `IdempotencyRecord` | Re-sent requests return cached result. | Duplicate Transaction |
