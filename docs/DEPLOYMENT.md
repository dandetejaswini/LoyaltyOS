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

## 4. Vercel Frontend Deployment

### 4.1 Project Settings in Vercel Dashboard

When importing the GitHub repository `dandetejaswini/LoyaltyOS` into Vercel, configure the following project settings:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Vite` | Automatically detects Vite configuration. |
| **Root Directory** | `frontend` | **MANDATORY**: Points build context to the frontend subfolder. |
| **Build Command** | `npm run build` | Compiles TypeScript and runs `vite build`. |
| **Output Directory** | `dist` | Default Vite build output directory. |
| **Install Command** | `npm install` | Installs frontend dependencies cleanly. |
| **Node.js Version** | `18.x` or `20.x` | Standard modern Node LTS. |

### 4.2 Required Vercel Environment Variables

In Vercel **Project Settings > Environment Variables**, configure the public variables:

| Variable | Example Production Value | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `https://api.yourloyaltyos.com/api/v1` | URL of deployed FastAPI backend. |
| `VITE_SUPABASE_URL` | `https://ahxjaplreytmauwpedgh.supabase.co` | Supabase API URL. |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_ELzvKrq9lf9MRnfc73vvhA_qjvW-Ou2` | Supabase publishable anonymous key. |
| `VITE_FIREBASE_API_KEY` | `AIzaSyC9mwdIb25A4TTaOBfHjidCmWQfkGJMF90` | Google Firebase Web Client API key. |
| `VITE_FIREBASE_AUTH_DOMAIN` | `loyaltyos-2a2a0.firebaseapp.com` | Firebase authentication domain. |
| `VITE_FIREBASE_PROJECT_ID` | `loyaltyos-2a2a0` | Firebase Project ID. |
| `VITE_FIREBASE_STORAGE_BUCKET`| `loyaltyos-2a2a0.firebasestorage.app` | Firebase Storage Bucket. |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | `179762121658` | Firebase Sender ID. |
| `VITE_FIREBASE_APP_ID` | `1:179762121658:web:94a8d4fddc71e94b21ab83` | Firebase Web App ID. |

> [!CAUTION]
> **NEVER add backend secrets to Vercel environment variables.**  
> Do not add `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, or `SUPABASE_JWT_SECRET` to Vercel. These belong exclusively in the backend runtime.

### 4.3 Single-Page Application (SPA) Routing
The frontend includes `frontend/vercel.json` with rewrite rules:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/"
    }
  ]
}
```
This ensures direct browser navigation or page refreshes on `/dashboard`, `/sign-in`, or `/settings` resolve correctly to `index.html`.

---

## 5. Backend Production Deployment

FastAPI is designed as a long-running asynchronous ASGI service. Deploy it to a containerized PaaS such as **Railway**, **Render**, **Fly.io**, or **AWS ECS**.

### 5.1 Dockerfile Specification
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

### 5.2 Backend Environment Configuration
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
