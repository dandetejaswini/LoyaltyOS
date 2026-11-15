# LoyaltyOS

Intelligent customer loyalty and ledger management platform designed for secure points accounting, automated anomaly detection, and transparent financial operations.

- **Live Production Application**: [https://loyaltyos-omega.vercel.app/](https://loyaltyos-omega.vercel.app/)
- **GitHub Repository**: [https://github.com/dandetejaswini/LoyaltyOS](https://github.com/dandetejaswini/LoyaltyOS)

---

### Platform Highlights

- **Double-Entry Loyalty Ledger**: Maintains an auditable record of points credits, debits, redemptions, and reversals.
- **FIFO Points Accounting**: Tracks individual points lots and consumes them in first-in, first-out order with a 365-day expiry period.
- **Automated Ledger Reconciliation**: Identifies discrepancies between customer account balances and transaction records.
- **LLIRE Anomaly Detection**: Detects balance mismatches, over-redemptions, unreversed returns, duplicate expiry deductions, and incorrect tier assignments.
- **Dual-Key Approval Governance**: Requires independent approval before executing sensitive corrective actions.
- **Role-Based Workspaces**: Provides dedicated dashboards for customers, operators, analysts, and operations managers.

---

### Platform Roles

- **Customer**: Views loyalty balance, tier progression, available rewards, expiry details, and redemption history.
- **Store / Warehouse Operator**: Manages customer records, processes orders and returns, and initiates ledger reconciliation.
- **Merchandising / E-commerce Analyst**: Monitors ledger health, runs anomaly scans, and investigates transaction inconsistencies.
- **Operations Manager**: Reviews incidents, proposes corrective actions, and approves remediation requests through dual-key governance.

---

### LLIRE Intelligence & Governance

- **Five Anomaly Detectors**: Identifies balance mismatches, over-redemptions, unreversed returns, double expiry, and incorrect tier assignments.
- **Explainable Findings**: Provides structured evidence and explanations to support anomaly investigation.
- **Controlled Remediation**: Supports adjustment credits, adjustment debits, account freezes, reversals, and finding dismissal.
- **Independent Approval**: Prevents users from approving their own proposed corrective actions.
- **Audit Traceability**: Preserves original ledger entries and records corrections through compensating transactions.

---

### Loyalty Accounting & Business Rules

- **Tier-Based Accrual**: Calculates points using eligible merchandise spend and customer tier multipliers.
- **Eligible Spend**: Excludes sales tax and shipping charges before calculating reward points.
- **Proportional Return Reversals**: Reverses points based on returned merchandise value.
- **Negative Balance Handling**: Accounts for returns involving previously redeemed points.
- **Idempotent Expiry Processing**: Prevents duplicate deductions when expiry batches are executed repeatedly.
- **Balance Integrity**: Reconciles account balances against ledger transactions and active points lots.

---

### Quick Start & Local Development

**Clone Repository**

```bash
git clone https://github.com/dandetejaswini/LoyaltyOS.git
cd LoyaltyOS
```

**Install Dependencies**

```bash
cd frontend
npm install
```

**Configure Environment**

- Copy `.env.example` to `.env`.
- Configure the Supabase project URL and publishable key.

**Run Application**

```bash
npm run dev
```

- `npm run dev` — Starts the local development server at `http://localhost:5173`.
- `npm run build` — Generates the production frontend build.
- `pytest backend/tests -v` — Executes automated Python tests.
- `python tools/seed_generator.py --scale TEST --seed 42` — Generates deterministic synthetic data.
- `python tools/benchmark_evaluator.py` — Runs offline LLIRE benchmark evaluation.

---

### Technical Stack

| Component | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend Platform | Supabase |
| Database | PostgreSQL 15+ |
| Authentication | Supabase Auth |
| Database Security | Row Level Security (RLS) |
| Business Logic | PostgreSQL Functions and RPC |
| Server-Side Processing | Supabase Edge Functions |
| Deployment | Vercel |
| Developer Utilities | Python, Pytest |

---

### Testing & Evaluation

- **Automated Tests**: 85 / 85 passing.
- **LLIRE Benchmark**: 100% precision, recall, and F1-score on the reported labelled benchmark.
- **Frontend Compilation**: TypeScript checks and Vite production build passed.
- **Dual-Key Governance**: Independent approval validation verified.
- **Database Structure**: 21 domain tables and five immutability triggers reported verified.

---

### Technical Documentation Directory (`docs/`)

- [AI Usage](docs/AI_USAGE.md) — Documents AI-assisted development, prompts, implementation support, and developer verification.
- [Architecture](docs/ARCHITECTURE.md) — Explains the overall system architecture, technology stack, components, and design decisions.
- [Data Dictionary](docs/DATA_DICTIONARY.md) — Describes the 21 domain tables, their fields, data types, constraints, and relationships.
- [Deployment Guide](docs/DEPLOYMENT.md) — Covers Supabase configuration, database migrations, environment variables, and Vercel deployment.
- [Limitations & Roadmap](docs/LIMITATIONS_AND_ROADMAP.md) — Outlines current system limitations, known gaps, and planned improvements.
- [Testing & Evaluation](docs/TESTING_AND_EVALUATION.md) — Describes automated test coverage, LLIRE benchmark methodology, and evaluation results.

---

**LoyaltyOS — Intelligent Loyalty Management. Complete Ledger Transparency.**
