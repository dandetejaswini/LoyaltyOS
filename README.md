# LoyaltyOS

### Intelligent Loyalty & Ledger Management Platform

LoyaltyOS is a customer loyalty management platform that helps businesses manage reward points, track transactions, process redemptions, and detect ledger inconsistencies.

## Key Features

- **Points Management:** Earn, redeem, and track loyalty points.
- **FIFO Accounting:** Manage points lots with 365-day expiry.
- **Transaction Ledger:** Maintain an auditable transaction history.
- **LLIRE:** Detect ledger mismatches, over-redemptions, and other anomalies.
- **Dual-Key Approval:** Require independent approval for corrective actions.
- **Role-Based Dashboards:** Dedicated workspaces for Customers, Operators, Analysts, and Operations Managers.
- **Reconciliation:** Identify and investigate account balance discrepancies.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend | Supabase |
| Database | PostgreSQL 15+ |
| Authentication | Supabase Auth |
| Security | Row Level Security (RLS) |
| Business Logic | PostgreSQL Functions and RPC |
| Server-Side Processing | Supabase Edge Functions |
| Hosting | Vercel |
| Testing | Python, Pytest |

## Architecture

    React + TypeScript + Vite
              |
            Vercel
              |
           Supabase
              |
       PostgreSQL Database
          ├── Authentication
          ├── Row Level Security
          ├── Database Functions
          ├── Ledger Management
          └── LLIRE Detection

Supabase is the only production backend. Python is used for offline data generation, testing, and benchmark evaluation.

## Live Application

- **Website:** https://loyaltyos-omega.vercel.app/
- **GitHub Repository:** https://github.com/dandetejaswini/LoyaltyOS

## Local Setup

Clone the repository:

    git clone https://github.com/dandetejaswini/LoyaltyOS.git

Navigate to the frontend:

    cd LoyaltyOS/frontend

Install dependencies:

    npm install

Create the environment file:

    cp .env.example .env

Start the development server:

    npm run dev

Configure your Supabase project URL and publishable key in the `.env` file before running the application.

## Testing

| Test | Result |
|---|---|
| Automated Tests | 85/85 Passing |
| LLIRE Benchmark | 100% F1 Score |
| Frontend Build | Passed |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATA_DICTIONARY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Testing and Evaluation](docs/TESTING_AND_EVALUATION.md)
- [Limitations and Roadmap](docs/LIMITATIONS_AND_ROADMAP.md)

---

**LoyaltyOS - Intelligent Loyalty Management. Complete Ledger Transparency.**
