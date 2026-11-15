# LoyaltyOS — Seed Engine Operator Runbook

## 1. Overview

The LoyaltyOS Seed Engine generates deterministic synthetic data, injects controlled forensic anomalies, computes cryptographic manifests, and optionally loads records into PostgreSQL.

Entry points:
- Top-level script: `scripts/seed_data.py`
- Backend CLI module: `python -m backend.app.seed.cli`

---

## 2. Quickstart Commands

### Generate and Validate at TEST Scale (Default)
Generates 100 customers, 500 orders, validates invariants, and exports datasets:
```powershell
venv\Scripts\python scripts/seed_data.py --scale TEST --export-dir data
```

### Generate at MEDIUM Scale (Benchmarking)
Generates 1,000 customers, 5,000 orders (~6,000 transactions) in ~2 seconds:
```powershell
venv\Scripts\python scripts/seed_data.py --scale MEDIUM --export-dir data
```

### Generate at FULL Scale (Production Simulation)
Generates 20,000 customers, 100,000 orders (~300,000 transactions):
```powershell
venv\Scripts\python scripts/seed_data.py --scale FULL --export-dir data
```

### Specify Custom Seed
Override the default seed `20261022`:
```powershell
venv\Scripts\python scripts/seed_data.py --seed 12345678 --scale TEST
```

### Database Ingestion (Safe Flag)
Attempts loading into the configured PostgreSQL instance. If `DATABASE_URL` is unconfigured, safely outputs `PENDING` status without failing:
```powershell
venv\Scripts\python scripts/seed_data.py --scale TEST --load-db
```

To seed against a production database, the safety guard requires explicit confirmation:
```powershell
venv\Scripts\python scripts/seed_data.py --scale TEST --load-db --confirm-production-seed
```

---

## 3. Directory Layout and Output Artifacts

```
data/
├── generated/                     # Baseline 100% Valid Dataset
│   ├── customers.json
│   ├── loyalty_accounts.json
│   ├── orders.json
│   ├── order_lines.json
│   ├── points_transactions.json
│   ├── points_lots.json
│   ├── redemptions.json
│   ├── points_lot_allocations.json
│   ├── order_returns.json
│   ├── order_return_lines.json
│   ├── expiry_batches.json
│   └── expiry_batch_items.json
├── ground_truth/                  # Anomalous Ground Truth Dataset
│   ├── customers_anomalous.json
│   ├── loyalty_accounts_anomalous.json
│   ├── orders_anomalous.json
│   ├── order_lines_anomalous.json
│   ├── points_transactions_anomalous.json
│   ├── points_lots_anomalous.json
│   ├── redemptions_anomalous.json
│   ├── points_lot_allocations_anomalous.json
│   ├── order_returns_anomalous.json
│   ├── order_return_lines_anomalous.json
│   ├── expiry_batches_anomalous.json
│   └── expiry_batch_items_anomalous.json
└── manifests/
    └── ground_truth_manifest.json # Complete metadata, counts, checksums & labels
```

---

## 4. Invariant Verification Checklist

The generator executes `DatasetValidator.validate_baseline` on every run, asserting:
- [x] Primary key uniqueness across all 12 entities
- [x] Foreign key referential integrity
- [x] BR-01: Double-entry ledger reconciliation (`account.current_balance == sum(transactions)`)
- [x] Running balance mathematical continuity
- [x] BR-02: Floor rounding on points accrual
- [x] BR-06: FIFO lot depletion rules ($0 \le \text{remaining} \le \text{initial}$)
- [x] BR-01 / BR-05: Net merchandise spend calculation excluding tax and shipping
- [x] BR-10: Points reversal on returns supporting negative account balance
- [x] BR-11: 365-day expiration lot status transitions
