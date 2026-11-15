# LoyaltyOS

### Intelligent Loyalty & Ledger Management Platform

LoyaltyOS is an intelligent customer loyalty management platform designed to help businesses manage reward points, track transactions, process redemptions, and maintain accurate loyalty records.

The platform combines secure ledger management, FIFO-based points accounting, automated anomaly detection, and approval workflows to make loyalty operations more transparent, reliable, and easy to audit.

## Live Application

| Resource | Link |
|---|---|
| Live Website | [LoyaltyOS](https://loyaltyos-omega.vercel.app/) |
| GitHub Repository | [LoyaltyOS Repository](https://github.com/dandetejaswini/LoyaltyOS) |
| Database Platform | [Supabase](https://supabase.com) |
| Hosting Platform | [Vercel](https://vercel.com) |

## Key Features

- **Points Management:** Manage customer points earned through purchases, redemptions, and returns.
- **FIFO Points Accounting:** Track individual points lots and consume points in first-in, first-out order.
- **Points Expiry:** Automatically manage points with a 365-day expiry period.
- **Transaction Ledger:** Maintain an auditable history of all points transactions.
- **Returns and Reversals:** Handle partial and full returns with proportional points reversals.
- **LLIRE:** Detect ledger mismatches, over-redemptions, incorrect expiry, and other anomalies.
- **Dual-Key Approval:** Require approval from a second authorized person before executing sensitive corrective actions.
- **Ledger Reconciliation:** Compare account balances with transaction records to identify inconsistencies.
- **Role-Based Dashboards:** Provide separate workspaces for Customers, Operators, Analysts, and Operations Managers.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Routing | React Router |
| Backend Platform | Supabase |
| Database | PostgreSQL 15+ |
| Authentication | Supabase Auth |
| Database Security | Row Level Security (RLS) |
| Business Logic | PostgreSQL Functions and RPC |
| Server-Side Processing | Supabase Edge Functions |
| Hosting | Vercel |
| Developer Utilities | Python |
| Automated Testing | Pytest |

## System Architecture

    React 18 + TypeScript + Vite
                |
                v
          Vercel Hosting
                |
                v
        Supabase JavaScript Client
                |
                v
          Supabase Platform
                |
          PostgreSQL Database
                |
       +--------+---------+
       |        |         |
       v        v         v
    Supabase  Database  PostgreSQL
      Auth     RLS       Functions
       |        |         |
       +--------+---------+
                |
                v
        Ledger and LLIRE
         Business Logic

Supabase is the only production backend platform. Python is retained for offline synthetic data generation, mathematical validation, and benchmark evaluation.

## LLIRE - Anomaly Detection

The Loyalty Ledger Intelligence & Reconciliation Engine (LLIRE) identifies inconsistencies in loyalty transactions through five specialized detectors.

| Detector | Description |
|---|---|
| DET-BALANCE-MISMATCH | Detects differences between account balances and ledger records. |
| DET-OVER-REDEMPTION | Identifies redemption activity exceeding available points. |
| DET-UNREVERSED-RETURN | Detects returns with missing or incomplete points reversals. |
| DET-DOUBLE-EXPIRY | Identifies duplicate points expiry deductions. |
| DET-INCORRECT-TIER | Detects incorrect customer loyalty tier assignments. |

Findings support investigation and corrective-action workflows. Sensitive corrections require independent approval before execution.

## Platform Roles

| Role | Responsibilities |
|---|---|
| CUSTOMER | View points balance, tier progression, rewards, expiry, and redemption history. |
| OPERATOR | Manage customer records, process orders, handle returns, and initiate reconciliation. |
| ANALYST | Monitor ledger health, run anomaly detection, and investigate findings. |
| OPERATIONS_MANAGER | Review incidents, propose corrective actions, and approve remediation requests. |


## Local Setup

### 1. Clone the Repository

    git clone https://github.com/dandetejaswini/LoyaltyOS.git

### 2. Navigate to the Frontend

    cd LoyaltyOS/frontend

### 3. Install Dependencies

    npm install

### 4. Configure Environment Variables

    cp .env.example .env

Add your Supabase project URL and publishable key to the `.env` file.

### 5. Start the Development Server

    npm run dev

The application will be available at:

    http://localhost:5173

## Database Setup

LoyaltyOS uses Supabase PostgreSQL for data storage, security, and business operations.

To connect the project and apply database migrations:

    supabase link --project-ref ahxjaplreytmauwpedgh

    supabase db push

Database migrations are maintained in:

    supabase/migrations/

They define the database schema, security policies, business functions, anomaly detection, and corrective-action workflows.

## Testing and Evaluation

| Test Suite | Result |
|---|---|
| Automated Tests | 85/85 Passing |
| LLIRE Benchmark | 100% F1 Score |
| Frontend TypeScript Check | Passed |
| Vite Production Build | Passed |
| Dual-Key Approval Validation | Passed |

Detailed test coverage and evaluation results are available in the testing documentation.

## Project Documentation

The `docs/` directory contains detailed information about the system's design, implementation, deployment, and testing.

| Document | Purpose |
|---|---|
| `ARCHITECTURE.md` | Explains the overall system architecture, components, and database design. |
| `DATA_DICTIONARY.md` | Describes the database tables, columns, and relationships. |
| `DEPLOYMENT.md` | Provides instructions for deploying and configuring the application using Vercel and Supabase. |
| `TESTING_AND_EVALUATION.md` | Explains automated tests, test coverage, and LLIRE benchmark results. |
| `LIMITATIONS_AND_ROADMAP.md` | Lists current limitations, known gaps, and planned improvements. |
| `tools/README.md` | Explains Python developer utilities, synthetic data generation, and benchmark execution. |

## Engineering Principles

- Maintain accurate and auditable transaction records.
- Enforce important business rules at the database level.
- Detect and explain ledger inconsistencies.
- Require independent approval for sensitive corrections.
- Protect customer data through authentication and database security.
- Preserve transaction history through compensating entries rather than modifying original records.

---

**LoyaltyOS - Intelligent Loyalty Management. Complete Ledger Transparency.**
