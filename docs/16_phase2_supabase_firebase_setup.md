# LoyaltyOS — Supabase & Firebase Integration Setup Guide (Phase 2)

**Product Name**: LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Target Environments**: Supabase PostgreSQL + Supabase Auth (Email/Password) & Firebase Auth (Google OAuth)  
**Document Reference**: `docs/16_phase2_supabase_firebase_setup.md`  
**Status**: Architecture & Code Implemented | Ready for Dashboard Verification

---

## 1. Responsibility Matrix & Status Classification

| Component / Task | Category | Description | Status |
|---|---|---|---|
| **SQLAlchemy 2.0 Relational Models** | **Implemented** | 21 core tables across Identity, Master, Ledger, Audit & Operations mapped in `backend/app/models/` | Verified (23 tests pass) |
| **Alembic Version Migration** | **Implemented** | `001_initial_schema` defined in `backend/alembic/versions/001_initial_loyaltyos_schema.py` | Implemented |
| **Standalone SQL DDL Script** | **Implemented** | Complete DDL with triggers & RLS in `scripts/001_initial_schema.sql` | Ready to run in SQL Editor |
| **PostgreSQL Immutability Trigger** | **Implemented** | Trigger `tg_points_transactions_immutable` prevents UPDATE and DELETE on `points_transactions` | Defined in DDL & Alembic |
| **Row Level Security (RLS)** | **Implemented** | RLS enabled on customer/account tables with `auth.uid()` policies | Defined in DDL script |
| **Backend Token Validation** | **Implemented** | Auto-detects `SUPABASE_PASSWORD` vs `FIREBASE_GOOGLE`, validates claims & signatures | Verified with PyJWT |
| **Unified Identity Resolution** | **Implemented** | `AuthService.resolve_or_provision_user` links providers to `app_users` and auto-provisions accounts | Verified in Unit Tests |
| **Role-Based Access Control (RBAC)**| **Implemented** | `CUSTOMER`, `OPERATOR`, `ANALYST`, `OPERATIONS_MANAGER` resolved from DB, enforced via `require_role` | Verified (HTTP 403 ProblemDetails) |
| **Frontend Auth Context & Client** | **Implemented** | Unified `AuthContext`, `@supabase/supabase-js`, and `firebase/auth` clients | Built and bundled cleanly |
| **Frontend Sign In & Sign Up Pages**| **Implemented** | Form inputs, error banners, loading indicators, Google OAuth buttons | Built and bundled cleanly |
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

## 3. Step-by-Step Supabase Setup Instructions

### Step 3.1: Execute Schema Migration
You have two straightforward options:

#### Option A: Supabase Dashboard SQL Editor (Recommended & Fastest)
1. Open your browser and navigate to the Supabase Dashboard: `https://supabase.com/dashboard/project/ahxjaplreytmauwpedgh`.
2. In the left navigation menu, click on **SQL Editor**.
3. Click **New Query**.
4. Open `scripts/001_initial_schema.sql` in your workspace, copy the entire SQL script, and paste it into the editor.
5. Click **Run** (or press `Ctrl + Enter`).
6. Confirm the result message: `Success. No rows returned`.
7. Verify that all 21 tables appear in the **Table Editor**:
   - `app_users`, `user_identity_mappings`
   - `customers`, `tiers`, `loyalty_accounts`, `rules`, `orders`, `order_lines`, `order_returns`, `order_return_lines`
   - `points_transactions`, `points_lots`, `rewards`, `redemptions`, `points_lot_allocations`, `expiry_batches`, `expiry_batch_items`
   - `audit_events`, `rejected_operations`, `anomaly_incidents`, `corrective_actions`

#### Option B: Alembic Async CLI Migration
If your database password is configured in `.env` as `DATABASE_URL`:
```powershell
# Set your DATABASE_URL in .env
DATABASE_URL="postgresql+asyncpg://postgres.ahxjaplreytmauwpedgh:[YOUR_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

# Execute migration
venv\Scripts\alembic upgrade head
```

### Step 3.2: Enable Email/Password in Supabase Auth
1. In the Supabase Dashboard, click **Authentication** > **Providers**.
2. Select **Email**.
3. Ensure **Enable Email provider** is switched **ON**.
4. (Optional for development): If you do not want to wait for email confirmation links during hackathon testing, toggle **Confirm email** to **OFF** in Authentication > Providers > Email.
5. Click **Save**.

### Step 3.3: Retrieve Supabase JWT Secret for Backend Token Verification
1. In the Supabase Dashboard, click **Project Settings** (gear icon at the bottom left).
2. Click **API** under Configuration.
3. Scroll down to **JWT Settings**.
4. Copy the **JWT Secret**.
5. Paste it into your backend `.env` file:
   ```env
   SUPABASE_JWT_SECRET="[YOUR_COPIED_JWT_SECRET]"
   ```

---

## 4. Step-by-Step Firebase Google OAuth Setup Instructions

### Step 4.1: Enable Google Authentication Provider
1. Open the Firebase Console: `https://console.firebase.google.com/project/loyaltyos-2a2a0/overview`.
2. In the left navigation sidebar, click **Build** > **Authentication**.
3. Click on the **Sign-in method** tab.
4. Click **Add new provider** and select **Google**.
5. Toggle **Enable**.
6. Set the **Public-facing name for project** (e.g. `LoyaltyOS`).
7. Select your support email from the dropdown.
8. Click **Save**.

### Step 4.2: Add Authorized Domains in Firebase
1. Under **Authentication** > **Settings** > **Authorized domains**:
2. Confirm the following domains are listed:
   - `localhost`
   - `127.0.0.1`
   - `loyaltyos-2a2a0.firebaseapp.com`
   - `[YOUR_VERCEL_DOMAIN].vercel.app` (when deployed)

### Step 4.3: Retrieve Firebase Web Client Configuration
1. In Firebase Console, click the **Project Settings** gear icon (top left).
2. Under the **General** tab, scroll down to **Your apps**.
3. If no web app exists, click the `</>` (Web) icon to register a web app:
   - App nickname: `LoyaltyOS Web`
   - Leave Firebase Hosting unchecked (frontend is hosted on Vercel).
   - Click **Register app**.
4. Copy the values from the `firebaseConfig` snippet into `frontend/.env`:
   ```env
   VITE_FIREBASE_API_KEY="AIzaSy..."
   VITE_FIREBASE_AUTH_DOMAIN="loyaltyos-2a2a0.firebaseapp.com"
   VITE_FIREBASE_PROJECT_ID="loyaltyos-2a2a0"
   VITE_FIREBASE_STORAGE_BUCKET="loyaltyos-2a2a0.appspot.com"
   VITE_FIREBASE_MESSAGING_SENDER_ID="179762121658"
   VITE_FIREBASE_APP_ID="1:179762121658:web:..."
   ```

---

## 5. Unified Identity Flow Architecture

```
               [ User Interaction ]
                 /              \
                /                \
        [Email / Password]   [Google OAuth]
              /                    \
             v                      v
     Supabase Auth           Firebase Auth
     (Issues Supabase JWT)   (Issues Firebase ID Token)
             \                      /
              \                    /
               v                  v
         [ Authorization: Bearer <token> ]
                         |
                         v
              FastAPI Auth Middleware
           (decode_and_validate_token)
           - Detects provider by iss/claims
           - Validates signature & expiry
           - Extracts email & external UID
                         |
                         v
                    AuthService
           (resolve_or_provision_user)
           - Looks up user_identity_mappings
           - If new: creates AppUser + Mapping
           - Assigns RBAC role (default CUSTOMER)
           - If CUSTOMER: creates Customer & LoyaltyAccount
                         |
                         v
           [ Authenticated AppUser (Database) ]
```

---

## 6. Verification Checklist Before Starting Phase 3

- [x] All 21 SQLAlchemy models defined and tested in metadata.
- [x] Standalone SQL migration script created in `scripts/001_initial_schema.sql`.
- [x] Alembic migration created in `backend/alembic/versions/001_initial_loyaltyos_schema.py`.
- [x] Database immutability trigger created for ledger append-only compliance.
- [x] Dual-token parser implemented in `backend/app/core/security.py`.
- [x] RBAC authorization dependency implemented in `backend/app/api/deps.py`.
- [x] First-login provisioning implemented in `backend/app/services/auth_service.py`.
- [x] Auth endpoints `/api/v1/auth/me` and `/api/v1/auth/sync` registered.
- [x] Frontend `@supabase/supabase-js` and `firebase/auth` clients implemented.
- [x] Frontend `AuthContext`, `useAuth`, `SignInPage`, and `SignUpPage` wired.
- [x] Full test suite (23 backend unit tests) passing with 0 errors.
- [x] Frontend production build (`tsc && vite build`) passing with 0 errors.
