# LoyaltyOS — Deployment Guide

**Target Deployment Architecture:** Pure Supabase + Vercel Edge Network  
**Frontend Platform:** Vercel (React 18, TypeScript, Vite SPA)  
**Backend & Database Platform:** Supabase (PostgreSQL 15+, Supabase Auth, Stored RPCs, RLS, Edge Functions)

---

## 1. System Architecture Overview

LoyaltyOS deploys cleanly without any intermediary Python server:

```
┌──────────────────────────────────────┐
│        Vercel Edge Network           │
│  React 18 + TypeScript + Vite SPA    │
└──────────────────┬───────────────────┘
                   │
                   │ HTTPS / Direct SDK (@supabase/supabase-js)
                   ▼
┌──────────────────────────────────────┐
│          Supabase Platform           │
│  ├── Supabase Auth (GoTrue)          │
│  ├── Supabase Edge Functions (Deno)  │
│  ├── PostgreSQL 15+ Database         │
│  │   ├── 21 Relational Tables        │
│  │   ├── 5 Immutability Triggers     │
│  │   ├── Row-Level Security Policies │
│  │   └── Stored Procedures / RPC     │
└──────────────────────────────────────┘
```

---

## 2. Supabase Database & Migrations Setup

All schema tables, immutability guards, and transactional procedures are version-controlled in `supabase/migrations/`.

### 2.1 Supabase Project Connection
- **Project Reference:** `ahxjaplreytmauwpedgh`
- **Project URL:** `https://ahxjaplreytmauwpedgh.supabase.co`
- **Region:** `aws-0-ap-south-1` (Mumbai)

### 2.2 Applying SQL Migrations
Apply the migrations in numerical order using either the Supabase CLI or the Supabase Web Dashboard SQL Editor:

```bash
# Option A: Using the Supabase CLI
supabase link --project-ref ahxjaplreytmauwpedgh
supabase db push
```

**Migration Sequence:**
1. `supabase/migrations/20261115000001_core_schema_and_immutability.sql`
   - Defines all 21 core tables with primary keys, foreign keys, and indexes.
   - Installs the 5 database engine immutability triggers (`points_transactions`, `audit_events`, `points_lot_allocations`, `expiry_batch_items`, `points_lots`).
   - Seeds the default loyalty tiers (`Bronze`, `Silver`, `Gold`, `Platinum`) and standard rewards catalog.
2. `supabase/migrations/20261115000002_rls_and_security.sql`
   - Implements `SECURITY DEFINER` role resolution helper functions.
   - Enables Row Level Security (RLS) across all 21 tables.
   - Sets strict customer isolation and cryptographic role-based access control.
3. `supabase/migrations/20261115000003_business_rpc_functions.sql`
   - Stored procedures: `fn_provision_customer`, `fn_get_my_profile`, `fn_accrue_order_points`, `fn_redeem_reward`, `fn_process_order_return`, `fn_reconcile_account`, `fn_evaluate_account_tier`, `fn_expire_points_lots`.
4. `supabase/migrations/20261115000004_llire_and_remediation_rpc.sql`
   - Stored procedures: `fn_run_llire_detection` (all 5 detectors), `fn_get_llire_summary`, `fn_evaluate_llire_benchmark`, `fn_investigate_incident`, `fn_propose_corrective_action`, `fn_review_corrective_action` (dual-key BR-09 check), `fn_health_check`.

### 2.3 Deploying Edge Functions
```bash
supabase functions deploy contact-inquiry --project-ref ahxjaplreytmauwpedgh
```

---

## 3. Vercel Frontend Deployment

### 3.1 Project Configuration
1. In the Vercel Dashboard, import the repository: `dandetejaswini/LoyaltyOS`.
2. Configure build settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `./` (Handled by `vercel.json`)
   - **Build Command**: `npm --prefix frontend install && npm --prefix frontend run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: Leave blank (handled in build command)

### 3.2 Environment Variables in Vercel
Configure these client-safe environment variables in **Project Settings > Environment Variables**:

| Variable Name | Value / Format | Description |
| :--- | :--- | :--- |
| `VITE_SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase project API URL |
| `VITE_SUPABASE_ANON_KEY` | `sb_publishable_...` (or public anon key) | Supabase public client key |
| `VITE_FIREBASE_API_KEY` | `AIzaSyC...` | Google Firebase Web API Key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `loyaltyos-2a2a0.firebaseapp.com` | Firebase authentication domain |
| `VITE_FIREBASE_PROJECT_ID` | `loyaltyos-2a2a0` | Firebase project identifier |

> **Security Note:** Never add `SUPABASE_SERVICE_ROLE_KEY` or database master passwords to Vercel environment variables or client-side code.

### 3.3 Deploy
Click **Deploy**. Vercel will bundle the Vite React application and distribute it across global edge CDN nodes.

---

## 4. Post-Deployment Verification

Verify all operational workflows directly in the production environment:

1. **Public Site Verification**:
   - Access `https://loyaltyos-omega.vercel.app/`
   - Confirm Home, Features, About, and Contact pages render with high-fidelity visuals.
   - Submit a test inquiry on the Contact page to verify Edge Function response.
2. **Interactive Persona Switcher**:
   - Navigate to `/workspace`.
   - Toggle between **Customer (Alice)**, **Operator (Marcus)**, **Analyst (Sarah)**, and **Ops Managers (Eleanor & David)**.
3. **Operational Workflows**:
   - In Store Operator desk, accrue points on a test order and verify floor-rounded point calculation.
   - In Analyst Hub, click **Run LLIRE Detection** to run the 5 anomaly detection procedures.
   - Click **Benchmark Evaluation** to confirm 100% precision, recall, and F1 score against ground truth.
   - In Ops Manager Console, verify that Eleanor proposing a corrective action cannot self-approve (`BR-09 Dual-Key Enforcement`), and that David can approve it.
