# 14. Deployment Architecture and Hosting Strategy

## 1. Hosting Overview & Constraint Compliance

The deployment architecture is designed to strictly adhere to the hackathon constraint:
> **"Use only free-tier or open-source technologies throughout the project. Do not assume Vercel supports a persistent FastAPI server."**

```mermaid
flowchart LR
    subgraph Users ["Client Browsers"]
        Browser["End Users / Operators"]
    end

    subgraph Vercel ["Vercel Edge Network (Free Tier)"]
        SPA["Vite Static SPA (React/TS)<br>Automatic HTTPS, Global CDN<br>SPA Rewrites via vercel.json"]
    end

    subgraph BackendPaaS ["Free-Tier Backend Container / PaaS"]
        FastAPI["Uvicorn ASGI + FastAPI<br>Host options: Render / Railway / Fly.io<br>Free Web Service Tier"]
    end

    subgraph SupabaseCloud ["Supabase Cloud (Free Tier)"]
        PG["Managed PostgreSQL 15+<br>PgBouncer Connection Pooler<br>Row-Level Security (RLS)"]
    end

    Browser -->|HTTPS CDN| SPA
    Browser -->|REST API / Bearer Token| FastAPI
    FastAPI -->|Async Connection Pool (port 6543)| PG
```

---

## 2. Presentation Tier Deployment (Vercel)

- **Target**: Vercel Free Hobby Tier.
- **Build Settings**:
  - Framework Preset: `Vite`
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Node.js Version: `20.x` or `22.x`
- **SPA Routing Rewrites**:
  Vercel serves single-page applications using the `frontend/vercel.json` configuration:
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
  This ensures deep links (e.g., `/dashboard`, `/about`, `/sign-in`) resolve correctly on page refresh without throwing 404 errors.
- **Environment Variables**:
  - `VITE_API_BASE_URL`: URL of the deployed FastAPI backend.
  - `VITE_SUPABASE_URL`: Public Supabase API URL.
  - `VITE_SUPABASE_ANON_KEY`: Public Supabase client anon key.
  - `VITE_FIREBASE_...`: Public Firebase client web configuration.

---

## 3. Application Tier Deployment (Free-Tier Backend PaaS)

Since Vercel is optimized for static frontends and serverless edge functions rather than long-running, connection-pooled FastAPI applications with background tasks, the Application Tier is architected for independent deployment on free-tier container PaaS providers:

1. **Option A: Render.com (Recommended Free Web Service)**
   - Environment: Python 3.12+ / Docker
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/api/v1/health`
   - Free-tier features: 512MB RAM, automatic HTTPS, custom domains.

2. **Option B: Railway.app (Free / Trial Starter Tier)**
   - Environment: Docker or Nixpacks
   - Auto-detects `backend/requirements.txt` and `Procfile`.

3. **Option C: Fly.io (Free Allowance)**
   - Multi-region deployment via minimal `fly.toml` Docker container.

---

## 4. Data Tier Hosting (Supabase PostgreSQL Free Tier)

- **Managed PostgreSQL**: Hosted on Supabase AWS Free Tier.
- **Connection Mode**: Session Pooler or Transaction Pooler via port `6543` / `5432` with `asyncpg`.
- **Row-Level Security**: Policies deployed via SQL migrations in Phase 2.
