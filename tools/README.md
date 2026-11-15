# LoyaltyOS — Offline Development & Evaluation Tools

> **Architecture Notice:**
> LoyaltyOS in production uses **100% Supabase** (PostgreSQL 15+, Supabase Auth, Row Level Security, PostgreSQL Stored Functions/RPC, and Edge Functions) deployed to **Vercel**. There is **no production Python backend or FastAPI runtime server**.
>
> The scripts in this directory are **offline developer utilities** retained exclusively for synthetic dataset generation, mathematical invariant testing, and offline LLIRE anomaly detection benchmark evaluation.

---

## Available Developer Tools

### 1. Synthetic Data Generator (`tools/seed_generator.py`)
Generates mathematically valid loyalty datasets (customers, accounts, orders, ledger transactions, FIFO lots, redemptions, returns, and expiry batches) with optional controlled anomaly injection for testing.

```bash
# Generate test scale dataset (100 customers, 500 orders)
python tools/seed_generator.py --scale TEST --seed 42

# Generate medium scale dataset (1,000 customers, 5,000 orders)
python tools/seed_generator.py --scale MEDIUM --seed 42

# Generate full scale dataset (10,000 customers, 50,000 orders)
python tools/seed_generator.py --scale FULL --seed 42
```

Outputs generated fixtures and ground-truth manifests to `data/generated/`, `data/ground_truth/`, and `data/manifests/`.

---

### 2. Offline LLIRE Benchmark Evaluator (`tools/benchmark_evaluator.py`)
Executes the 5 LLIRE fraud and ledger anomaly detection algorithms against the ground-truth benchmark dataset to evaluate detection accuracy without needing a running database:

```bash
python tools/benchmark_evaluator.py
```

#### Ground-Truth Target Metrics:
- `BALANCE_MISMATCH`: Precision 100.0%, Recall 100.0%, F1 100.0%
- `OVER_REDEMPTION`: Precision 100.0%, Recall 100.0%, F1 100.0%
- `UNREVERSED_RETURN`: Precision 100.0%, Recall 100.0%, F1 100.0%
- `DOUBLE_EXPIRY`: Precision 100.0%, Recall 100.0%, F1 100.0%
- `INCORRECT_TIER`: Precision 100.0%, Recall 100.0%, F1 100.0%
- **Overall Aggregate**: **Precision 100.0%, Recall 100.0%, F1 100.0%**

---

### 3. Offline Mathematical Invariant Unit Tests (`pytest backend/tests`)
Runs offline unit tests verifying financial ledger invariants, FIFO lot allocation ordering, accrual floor-rounding, and anomaly injection integrity:

```bash
pytest backend/tests -v
```
