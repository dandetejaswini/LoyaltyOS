# LoyaltyOS — Supabase & Firebase Integration Setup Guide (Phase 2)

**Product Name**: LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Target Environments**: Supabase PostgreSQL + Supabase Auth (Email/Password & JWKS) & Firebase Auth (Google OAuth)
**Document Reference**: `docs/16_phase2_supabase_firebase_setup.md`  
**Status**: Implemented & Verified in Test Suite | Pending Manual Live Dashboard Execution

---

## 1. Responsibility Matrix & Status Classification

| Component / Task | Category | Description | Status |
|---|---|---|---|
| **SQLAlchemy 2.0 Relational Models** | **Implemented in Code** | 21 core tables across Identity, Master, Ledger, Audit & Operations mapped in `backend/app/models/` | Verified (42 tests pass) |
| **Alembic Version Migration** | **Implemented in Code** | `001_initial_schema` defined in `backend/alembic/versions/001_initial_loyaltyos_schema.py` | Verified (100% DDL parity) |
| **Standalone SQL DDL Script** | **Implemented in Code** | Complete DDL with 5 immutability triggers & 9 RLS policies in `scripts/001_initial_schema.sql` | Ready to run in SQL Editor |
| **5 PostgreSQL Immutability Triggers**| **Implemented in Code** | Append-only triggers on transactions, audit events, lot allocations, expiry items, and lot guard | Verified in DDL & Alembic |
| **Row Level Security (RLS)** | **Implemented in Code** | Table-by-table RLS enabled with `auth.uid()` customer data isolation policies | Defined in DDL & Alembic |
| **Supabase JWT Verification** | **Implemented in Code** | Cryptographic verification for both HS256 (secret) and RS256/ES256 (JWKS). Never unverified. | Verified in Unit Tests |
| **Firebase Token Verification** | **Implemented in Code** | RS256 signature, audience, issuer, expiry verification against Google's public certs. | Verified with Mocked RS256 |
| **Account Linking Security** | **Implemented in Code** | Prohibits automatic merge on matching email. Requires authenticated ownership. Preserves roles. | Verified in Unit Tests |
| **Role-Based Access Control (RBAC)**| **Implemented in Code** | `CUSTOMER`, `OPERATOR`, `ANALYST`, `OPERATIONS_MANAGER` resolved from DB, enforced via `require_role` | Verified (HTTP 403 ProblemDetails) |
| **Frontend Auth Context & Client** | **Implemented in Code** | Unified `AuthContext`, `@supabase/supabase-js`, and `firebase/auth` clients | Built and bundled cleanly |
| **Frontend Sign In & Sign Up Pages**| **Implemented in Code** | Form inputs, error banners, loading indicators, Google OAuth buttons | Built and bundled cleanly |
| **Supabase Project Credentials** | **Manual Local** | Add project password & JWT secret to `.env` | Pending User Dashboard Retrieval |
| **Supabase SQL Schema Execution** | **Manual Dashboard**| Paste `scripts/001_initial_schema.sql` into Supabase SQL Editor and click **Run** | Pending Dashboard Action |
| **Firebase Google Provider Enablement**| **Manual Dashboard**| Enable Google Sign-In in Firebase Console > Authentication > Sign-in method | Pending Dashboard Action |
| **Firebase Web API Key Retrieval** | **Manual Local** | Copy Web API Key from Firebase Project Settings to `frontend/.env` | Pending Dashboard Action |

---

## 2. Infrastructure Identifiers (Supplied)

- **Supabase Project URL**: `https://ahxjaplreytmauwpedgh.supabase.co`
- **Supabase Anon / Publishable Key**: `sb_publishable_ELzvKrq9lf9MRnfc73vvhA_qjvW-Ou2`
- **Firebase Project ID**: `loyaltyos-2a2a0`
- **Firebase Project Number**: `179762121658`
- **Firebase Public Project Name**: `project-179762121658`
- **Firebase Auth Domain**: `loyaltyos-2a2a0.firebaseapp.com`

---

## 3. Database Security, RLS & Connection Privileges

### 3.1 Backend Database Connection Privilege Architecture
In Supabase PostgreSQL, the backend API connects via `DATABASE_URL` (typically the `postgres` superuser role or session pooler user). In PostgreSQL:
- **Table owners and superusers bypass RLS by default** (`BYPASSRLS` attribute).
- Therefore, **RLS does NOT enforce security on queries issued by the backend connection**.
- Instead, **Application-Tier RBAC** (`backend/app/api/deps.py`) and parameterized query filtering strictly enforce customer data isolation, preventing horizontal privilege escalation at the API layer.
- **Row Level Security (RLS)** acts as a crucial defense-in-depth boundary for **direct client connections** (e.g., frontend querying PostgREST directly using the Supabase publishable anon key).

### 3.2 Table-by-Table RLS Policy Specifications

| Table Name | RLS Status | Policy Name | Permitted Scope | SQL Condition |
|---|---|---|---|---|
| `app_users` | Enabled | `user_read_own_record` | SELECT (Self Only) | `auth.uid() = id` |
| `user_identity_mappings` | Enabled | `mapping_read_own_identities` | SELECT (Self Only) | `auth.uid() = user_id` |
| `customers` | Enabled | `customer_read_own_profile` | SELECT (Self Only) | `auth.uid() = user_id` |
| `loyalty_accounts` | Enabled | `customer_read_own_account` | SELECT (Self Only) | `customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid())` |
| `points_transactions` | Enabled | `customer_read_own_transactions`| SELECT (Self Only) | `account_id IN (SELECT la.account_id FROM loyalty_accounts la JOIN customers c ON c.customer_id = la.customer_id WHERE c.user_id = auth.uid())` |
| `points_lots` | Enabled | `customer_read_own_lots` | SELECT (Self Only) | `account_id IN (SELECT la.account_id FROM loyalty_accounts la JOIN customers c ON c.customer_id = la.customer_id WHERE c.user_id = auth.uid())` |
| `redemptions` | Enabled | `customer_read_own_redemptions` | SELECT (Self Only) | `account_id IN (SELECT la.account_id FROM loyalty_accounts la JOIN customers c ON c.customer_id = la.customer_id WHERE c.user_id = auth.uid())` |
| `orders` | Enabled | `customer_read_own_orders` | SELECT (Self Only) | `customer_id IN (SELECT customer_id FROM customers WHERE user_id = auth.uid())` |
| `order_lines` | Enabled | `customer_read_own_order_lines` | SELECT (Self Only) | `order_id IN (SELECT o.order_id FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.user_id = auth.uid())` |
| `audit_events` | Enabled | None (Internal Only) | No Direct Access | Direct client queries blocked; backend/service-role access only |

---

## 4. Ledger & Audit Immutability Triggers

The system strictly enforces financial accounting and audit immutability through 5 dedicated PostgreSQL triggers:

1. **`tg_points_transactions_immutable`** (on `points_transactions`):
   - Prohibits any `UPDATE` or `DELETE` on the points ledger journal.
2. **`tg_audit_events_immutable`** (on `audit_events`):
   - Prohibits any `UPDATE` or `DELETE` on historical security audit logs.
3. **`tg_points_lot_allocations_immutable`** (on `points_lot_allocations`):
   - Prohibits any `UPDATE` or `DELETE` on FIFO lot redemption allocations.
4. **`tg_expiry_batch_items_immutable`** (on `expiry_batch_items`):
   - Prohibits any `UPDATE` or `DELETE` on expiration batch audit records.
5. **`tg_points_lots_immutability_guard`** (on `points_lots`):
   - Strictly prohibits `DELETE` (lots must never be deleted).
   - Allows legitimate operational state updates: `remaining_points` decrementing, `status` transitioning (`ACTIVE` -> `PARTIALLY_REDEEMED` -> `EXHAUSTED` / `EXPIRED` / `REVERSED`), and `updated_at`.
   - Rejects any attempt to modify core immutable fields: `lot_id`, `transaction_id`, `account_id`, `initial_points`, or `created_at`.
   - Enforces `remaining_points <= initial_points`.

---

## 5. Account Linking & Anti-Takeover Security Policy

1. **No Automatic Account Merging**:
   - If an unlinked provider identity attempts sign-in with an email address that matches an existing `AppUser`, automatic account merging is **prohibited**.
   - The backend raises `409 Conflict` (`ConflictError`) directing the user to sign in with their primary credentials and perform authenticated linking.
2. **Explicit Authenticated Account Linking**:
   - Endpoint: `POST /api/v1/auth/link-identity`.
   - Requires verified primary authentication session (`get_current_user`).
   - Requires cryptographic signature and claims verification on the secondary provider token (`TokenPayload`).
   - Checks that the secondary provider UID is not already claimed by a different user.
3. **Role Preservation Invariant**:
   - **Existing roles CANNOT be elevated through account linking**.
   - Linking a secondary identity (even one with an email matching administrative lists) preserves the existing `AppUser.role` unchanged.

---

## 6. Token Verification Architecture

### Supabase JWT Verification
- **Supported Algorithms**: `HS256` (HMAC with `SUPABASE_JWT_SECRET`) and `RS256`/`ES256` (Asymmetric with Supabase JWKS from `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`).
- **Algorithm Whitelist**: Allowed: `HS256`, `RS256`, `ES256`. Tokens with `alg="none"` or unsupported algorithms are rejected immediately.
- **Claims Verified**: `sub` (subject), `email`, `aud` (`"authenticated"`), `exp` (expiration), `iss` (Supabase auth URL).
- **Strict Verification**: Unverified token decoding is prohibited. If the signing secret or JWKS public key is missing or invalid, an `UnauthorizedError` (HTTP 401) is returned.

### Firebase ID Token Verification
- **Algorithm**: `RS256`.
- **Public Key Resolution**: Fetches and caches Google's public certificates from `https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com`.
- **Claims Verified**:
  - `aud`: Must match `settings.FIREBASE_PROJECT_ID` (`loyaltyos-2a2a0`).
  - `iss`: Must match `https://securetoken.google.com/loyaltyos-2a2a0`.
  - `sub`: Must be present and non-empty.
  - `email`: Valid email address.
  - `exp`: Timestamp strictly in the future.
- **Service Failure**: If Google certificates cannot be fetched, verification strictly fails with HTTP 401.

---

## 7. Step-by-Step Manual Dashboard Instructions

### Step 7.1: Supabase Dashboard
1. Open `https://supabase.com/dashboard/project/ahxjaplreytmauwpedgh`.
2. Go to **SQL Editor** > **New Query**.
3. Copy and paste `scripts/001_initial_schema.sql`.
4. Click **Run** to execute all 21 table definitions, 5 immutability triggers, and 9 RLS policies.
5. In **Authentication** > **Providers** > **Email**, toggle **Enable Email provider** to **ON**.
6. In **Project Settings** > **API**, copy the **JWT Secret** and paste it into `.env` as `SUPABASE_JWT_SECRET`.

### Step 7.2: Firebase Dashboard
1. Open `https://console.firebase.google.com/project/loyaltyos-2a2a0/overview`.
2. Go to **Authentication** > **Sign-in method** > **Add new provider** > **Google**.
3. Toggle **Enable**, configure support email, and save.
4. Go to **Project Settings** > **General** > **Your apps**, copy the Web API Key into `frontend/.env` as `VITE_FIREBASE_API_KEY`.
