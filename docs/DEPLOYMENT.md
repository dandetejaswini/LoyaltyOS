# LoyaltyOS — Deployment Guide

**Product Name:** LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Target Environments:** Vercel (Frontend SPA) + Container / PaaS (FastAPI Backend) + Supabase (PostgreSQL 15+) + Firebase (Google OAuth)

---

## 1. Prerequisites

- **Node.js**: `v18.0.0` or higher (`npm v9+`)
- **Python**: `3.11` to `3.14` (with virtual environment support)
- **Supabase Account**: Managed PostgreSQL instance with transaction pooler enabled
- **Firebase Project**: Google Authentication provider enabled
- **Vercel Account**: For frontend static hosting and global edge CDN

---

## 2. Local Development Setup

### 2.1 Backend Setup (FastAPI)

1. Navigate to repository root:
   ```powershell
   cd C:\CandidateWorkspace
   ```
2. Activate Python virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install backend dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```
4. Configure local environment:
   ```powershell
   cp .env.example .env
   # Edit .env with your local or staging database credentials
   ```
5. Launch FastAPI development server:
   ```powershell
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
6. Verify backend health:
   ```powershell
   curl http://127.0.0.1:8000/api/v1/health
   ```

### 2.2 Frontend Setup (React + Vite)

1. Navigate to frontend directory:
   ```powershell
   cd frontend
   ```
2. Install frontend dependencies:
   ```powershell
   npm install
   ```
3. Configure frontend environment:
   ```powershell
   cp .env.example .env
   ```
4. Start Vite development server:
   ```powershell
   npm run dev
   ```
5. Open `http://localhost:5173` in your browser.

---

## 3. Database Setup (Supabase PostgreSQL)

### 3.1 Connection Architecture
Supabase offers two connection modes:
- **Direct Connection** (`port 5432`): Requires direct IPv6 access or enterprise firewall permissions.
- **Transaction Pooler** (`port 6543` / `5432`): Recommended for serverless and asynchronous applications.
  - Pooler Host: `aws-0-[REGION].pooler.supabase.com`
  - Port: `6543` (Transaction Mode)
  - Driver: `postgresql+asyncpg`

Format:
```
postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

### 3.2 Schema & Trigger Execution
1. Open your Supabase Dashboard > **SQL Editor**.
2. Run `scripts/001_initial_schema.sql` to create all 21 tables, constraints, foreign keys, and indexes.
3. Run `scripts/002_security_hardening_patch.sql` to install the 5 immutability triggers, 9 RLS customer isolation policies, and Alembic version stamp (`001_initial_schema`).

---

## 4. Deploying Frontend and Backend on Vercel (Unified Fullstack)

LoyaltyOS is fully configured for a **unified fullstack deployment on Vercel**. In this model, Vercel hosts both the React/Vite SPA and the FastAPI backend (as a Python Serverless Function) under a single project and domain.

### 4.1 Architecture & Benefits

```
Browser Request
      │
      ├──> /api/v1/*  ──> [vercel.json] ──> api/index.py (FastAPI Serverless) ──> Supabase Pooler (Port 6543)
      │
      └──> /*         ──> [vercel.json] ──> frontend/dist/index.html (React SPA)
```

- **Zero CORS Configuration**: Both frontend and backend share the identical origin (`https://<project>.vercel.app`).
- **Single Deployment Pipeline**: A single git push triggers builds for both frontend assets and backend serverless endpoints.
- **Unified Environment Settings**: Manage both public client variables and serverless secrets in a single Vercel dashboard.

### 4.2 Vercel Project Settings (Root Directory)

When importing `dandetejaswini/LoyaltyOS` into Vercel:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Other` (or leave default) | Governed by root `vercel.json` |
| **Root Directory** | `./` (Repository Root) | Do **NOT** set to `frontend` so backend can be built |
| **Build Command** | `npm --prefix frontend install && npm --prefix frontend run build` | Defined in `vercel.json` |
| **Output Directory** | `frontend/dist` | Defined in `vercel.json` |
| **Python Version** | `3.11` / `3.12` | Handled automatically by Vercel Python runtime |

### 4.3 Environment Variables in Vercel Dashboard

Configure the following in **Vercel Project Settings > Environment Variables**:

#### Frontend Variables (Client-Safe, exposed in browser)
| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `/api/v1` | **Relative URL** (hits same domain on Vercel, no CORS!) |
| `VITE_SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase API endpoint |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` | Supabase publishable anonymous key |
| `VITE_FIREBASE_API_KEY` | `AIzaSyC...` | Google Firebase Web API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `loyaltyos-2a2a0.firebaseapp.com` | Firebase authentication domain |
| `VITE_FIREBASE_PROJECT_ID` | `loyaltyos-2a2a0` | Firebase project identifier |

#### Backend Variables (Server-Side Secrets, inaccessible to browser)
| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.ahxjaplreytmauwpedgh:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres` | Supabase pooler on port 6543 |
| `DB_POOL_SIZE` | `1` | Recommended connection pool for serverless instances |
| `DB_MAX_OVERFLOW` | `2` | Overflow connections |
| `SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase project URL |
| `SUPABASE_JWT_SECRET` | `[ROTATED_JWT_SECRET]` | Min 32 chars for local HS256 verification |
| `SUPABASE_JWT_ALGORITHM` | `HS256` | Token algorithm |
| `ENVIRONMENT` | `production` | Runtime mode |
| `LOG_LEVEL` | `INFO` | Logger verbosity |

---

## 5. Alternative: Separate Deployments (Frontend on Vercel + Backend on PaaS/Docker)

If you prefer to deploy frontend and backend as two completely separate services:

### 5.1 Frontend-Only on Vercel
- **Root Directory**: `frontend`
- **Framework Preset**: `Vite`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **`VITE_API_BASE_URL`**: Set to the absolute URL of the external backend (e.g., `https://api.yourdomain.com/api/v1`).
- Uses `frontend/vercel.json` for SPA fallback rewrites.

### 5.2 Backend on Container PaaS (Railway, Render, Fly.io, AWS ECS)

#### Dockerfile Specification
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY scripts/ scripts/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Backend Environment Configuration
Set the following environment variables in your backend PaaS dashboard:
- `DATABASE_URL`: Your Supabase pooler connection string.
- `SUPABASE_URL`: `https://ahxjaplreytmauwpedgh.supabase.co`
- `SUPABASE_JWT_SECRET`: Rotated, private JWT secret (minimum 32 characters).
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (backend only).
- `FIREBASE_PROJECT_ID`: `loyaltyos-2a2a0`
- `ALLOWED_ORIGINS`: Comma-separated list of your production frontend origins (e.g. `https://loyaltyos.vercel.app`).

---

## 6. Pre-Flight Verification Checklist

- [ ] All 21 tables verified in Supabase PostgreSQL catalog.
- [ ] 5 immutability triggers verified active on ledger tables.
- [ ] 9 RLS policies active on customer-facing tables.
- [ ] Backend health probe returns `{"status": "healthy"}`.
- [ ] Backend CORS configuration allows Vercel production domain (`ALLOW_ORIGIN_REGEX = r"^https:\/\/.*\.vercel\.app$"`).
- [ ] Frontend build succeeds with zero errors: `npm run build`.
- [ ] All public environment variables configured in Vercel project settings.
