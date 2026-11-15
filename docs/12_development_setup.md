# 12. Local Development and Verification Guide

## 1. Prerequisites Verification

The local development environment has been validated with the following exact runtimes:
- **Operating System**: Windows 11 / Windows Server (PowerShell 5.1 / 7+)
- **Python Version**: `Python 3.14.6`
- **Node.js Version**: `v22.11.0`
- **npm Version**: `10.9.0`
- **Git Version**: `2.48.1.windows.1`

---

## 2. Windows PowerShell Setup Commands

### Step 1: Python Virtual Environment Installation
```powershell
Set-Location "C:\CandidateWorkspace"

# Create virtual environment
python -m venv venv

# Install backend dependencies
.\venv\Scripts\pip.exe install -r backend\requirements.txt
```

### Step 2: Frontend Dependency Installation
```powershell
Set-Location "C:\CandidateWorkspace\frontend"

# Install node dependencies
npm install

Set-Location "C:\CandidateWorkspace"
```

---

## 3. Launching Development Servers

### Launch Backend API Server
```powershell
# From C:\CandidateWorkspace
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The server will start at `http://localhost:8000`. You can inspect:
- Root Landing: `http://localhost:8000/`
- Truthful Health Diagnostic: `http://localhost:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://localhost:8000/api/v1/docs`

### Launch Frontend Development Server
```powershell
# In a new PowerShell terminal
Set-Location "C:\CandidateWorkspace\frontend"
npm run dev
```
The Vite development server will start at `http://localhost:5173`.

---

## 4. Running Verification Test Suites

### Backend Unit & Integration Tests (pytest)
```powershell
Set-Location "C:\CandidateWorkspace"
.\venv\Scripts\pytest.exe -v
```
All 5 test assertions verify:
1. `GET /api/v1/health` returns status code 200 with truthful database connectivity (`not_configured`).
2. `GET /` returns API metadata and documentation URLs.
3. Unmatched routes return RFC-7807 compliant `ProblemDetails` JSON.
4. CORS preflight OPTIONS requests return valid `Access-Control-Allow-Origin: http://localhost:5173`.
5. Standard GET requests from frontend origin return `Access-Control-Expose-Headers` including `Idempotency-Key`.

### Frontend TypeScript Compilation & Production Build
```powershell
Set-Location "C:\CandidateWorkspace\frontend"

# Verify type safety (0 errors)
npx tsc --noEmit

# Execute production build
npm run build
```
Build output is generated into `frontend/dist/`.
