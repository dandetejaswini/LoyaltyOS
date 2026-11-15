# LoyaltyOS — Deployment Guide

**Target Deployment:** Vercel Fullstack (React Frontend + FastAPI Serverless API)
**Database:** Supabase PostgreSQL 15+ (Transaction Pooler Port 6543)
**Authentication:** Supabase Auth & Google Firebase

---

## 1. Prerequisites

- **Node.js**: v18.0.0 or higher
- **Python**: 3.11 to 3.14
- **Supabase Account**: Managed PostgreSQL instance with transaction pooler enabled
- **Vercel Account**: For deploying the frontend and serverless API under one domain

---

## 2. Supabase Database Setup

### 2.1 Connection Configuration
- **Host**: `aws-0-ap-south-1.pooler.supabase.com`
- **Port**: `6543` (Transaction Pooler Mode)
- **Protocol**: `postgresql+asyncpg`
- **Connection String**:
  ```
  postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
  ```

### 2.2 Execute SQL Scripts
1. Open your Supabase project > **SQL Editor**.
2. Run `scripts/001_initial_schema.sql` to create all 21 tables, foreign keys, and indexes.
3. Run `scripts/002_security_hardening_patch.sql` to install the 5 immutability triggers and 9 Row-Level Security policies.

---

## 3. Vercel Fullstack Deployment (Frontend + Backend)

LoyaltyOS deploys both the React web application and the Python FastAPI API together in a single Vercel project.

### 3.1 Project Settings in Vercel
1. In the Vercel dashboard, click **Add New...** > **Project** and select `dandetejaswini/LoyaltyOS`.
2. Configure the following build settings:
   - **Framework Preset**: `Other` (or leave default)
   - **Root Directory**: `./` (Keep as repository root)
   - **Build Command**: `npm --prefix frontend install && npm --prefix frontend run build` (Handled by `vercel.json`)
   - **Output Directory**: `frontend/dist` (Handled by `vercel.json`)

### 3.2 Environment Variables in Vercel Dashboard

Add these variables in **Project Settings > Environment Variables**:

#### Frontend Variables (Client-Safe)
| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `/api/v1` | Relative path to API on same domain (No CORS!) |
| `VITE_SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase API endpoint |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` | Supabase publishable anonymous key |
| `VITE_FIREBASE_API_KEY` | `AIzaSyC...` | Google Firebase Web API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `loyaltyos-2a2a0.firebaseapp.com` | Firebase authentication domain |
| `VITE_FIREBASE_PROJECT_ID` | `loyaltyos-2a2a0` | Firebase project identifier |

#### Backend Variables (Server-Side Secrets)
| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.ahxjaplreytmauwpedgh:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres` | Supabase connection string on port 6543 |
| `DB_POOL_SIZE` | `1` | Connection pool size for serverless functions |
| `DB_MAX_OVERFLOW` | `2` | Overflow database connections |
| `SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase URL for JWT validation |
| `SUPABASE_JWT_SECRET` | `[ROTATED_JWT_SECRET]` | Secret for verifying auth tokens (min 32 chars) |
| `ENVIRONMENT` | `production` | Runtime mode |
| `LOG_LEVEL` | `INFO` | Logger verbosity |

### 3.3 Deploy
Click **Deploy**. Vercel will bundle the frontend assets into `frontend/dist` and deploy `api/index.py` as a serverless function handling all `/api/*` traffic.

---

## 4. Verification After Deployment

After deployment completes, check these endpoints on your live Vercel URL:

- **Frontend App**: `https://<your-project>.vercel.app/`
- **API Status**: `https://<your-project>.vercel.app/api`
- **Health Check**: `https://<your-project>.vercel.app/api/v1/health`
- **Interactive API Docs**: `https://<your-project>.vercel.app/api/v1/docs`

---

## 5. Local Development Commands

### Backend Local Run
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start local FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Local Run
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.
