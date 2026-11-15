# 11. Project Structure and Monorepo Organization

## 1. Physical Directory Architecture

The YottaFlex project workspace is structured to strictly isolate the Three-Tier Architecture, data generation pipelines, testing harnesses, and deployment configuration:

```
C:\CandidateWorkspace
│
├── frontend/                              # PRESENTATION TIER
│   ├── public/                            # Static public web assets
│   │   ├── favicon.svg
│   │   └── assets/
│   ├── src/
│   │   ├── app/                           # Application entry & routing
│   │   │   └── App.tsx                    # React Router configuration & route tree
│   │   ├── components/
│   │   │   ├── common/                    # Core reusable UI state components
│   │   │   │   ├── ErrorBoundary.tsx      # Application-level error boundary
│   │   │   │   ├── LoadingState.tsx       # Reusable loading spinner & status
│   │   │   │   ├── EmptyState.tsx         # Reusable empty data placeholder
│   │   │   │   └── ErrorState.tsx         # Standardized RFC-7807 problem presenter
│   │   │   └── layout/                    # Reusable layout containers
│   │   │       ├── Navbar.tsx             # Top navigation with live API health pill
│   │   │       ├── Footer.tsx             # Enterprise footer with specs & invariants
│   │   │       └── PageContainer.tsx      # Responsive max-width wrapper with headers
│   │   ├── layouts/
│   │   │   └── AppLayout.tsx              # Root layout wrapping Navbar, Outlet, Footer
│   │   ├── pages/                         # Core page views (Phase 0 blueprint mapping)
│   │   │   ├── HomePage.tsx               # System overview & live diagnostic card
│   │   │   ├── AboutPage.tsx              # Ledger principles & tier earning table
│   │   │   ├── SignInPage.tsx             # Enterprise login view (Phase 2 prepared)
│   │   │   ├── SignUpPage.tsx             # Customer registration (Phase 2 prepared)
│   │   │   ├── ForgotPasswordPage.tsx     # Password reset request view
│   │   │   ├── DashboardPage.tsx          # Multi-role tabbed console foundation
│   │   │   ├── SettingsPage.tsx           # Profile & identity settings view
│   │   │   └── NotFoundPage.tsx           # Standardized 404 handler
│   │   ├── services/
│   │   │   └── apiClient.ts               # Centralized fetch wrapper & error interceptor
│   │   ├── styles/
│   │   │   └── index.css                  # Tailwind directives & CSS design tokens
│   │   └── main.tsx                       # React DOM root entry point
│   ├── package.json                       # Node dependencies (React 18, Vite 5, Router 6)
│   ├── tsconfig.json                      # Strict TypeScript compiler options with aliases
│   ├── tsconfig.node.json                 # Node compiler options for Vite config
│   ├── vite.config.ts                     # Vite build configuration (port 5173, alias @)
│   ├── tailwind.config.js                 # Custom enterprise loyalty design palette
│   ├── postcss.config.js                  # PostCSS plugins (Tailwind, Autoprefixer)
│   ├── vercel.json                        # Vercel SPA routing rewrite rules
│   └── .env.example                       # Client-side environment template
│
├── backend/                               # APPLICATION & BUSINESS LOGIC TIER
│   ├── app/
│   │   ├── api/                           # API Layer
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py          # GET /api/v1/health with truthful DB check
│   │   │       └── router.py              # Root API v1 router definition
│   │   ├── core/                          # Cross-cutting concerns
│   │   │   ├── config.py                  # Pydantic Settings (CORS, URLs, DB pool)
│   │   │   ├── logging.py                 # Structured logger configuration
│   │   │   ├── errors.py                  # Centralized RFC-7807 exception handlers
│   │   │   └── database.py                # Async SQLAlchemy engine & connection ping
│   │   ├── models/                        # Data Tier Models
│   │   │   └── base.py                    # DeclarativeBase base class
│   │   ├── schemas/                       # Pydantic Request/Response contracts
│   │   │   └── common.py                  # ProblemDetails, HealthResponse, StandardResponse
│   │   ├── repositories/                  # Data Access Abstraction Layer
│   │   │   └── base.py                    # Generic BaseRepository[ModelType]
│   │   ├── services/                      # Domain Business Logic Layer
│   │   │   └── base.py                    # Generic BaseService[ModelType]
│   │   └── main.py                        # FastAPI application instantiation & lifespan
│   ├── tests/                             # Automated Test Suite (pytest)
│   │   ├── conftest.py                    # Async HTTP test client fixture
│   │   ├── test_health.py                 # Health and root endpoint assertions
│   │   ├── test_errors.py                 # RFC-7807 error format validation
│   │   └── test_cors_integration.py       # CORS headers and frontend origin tests
│   ├── alembic/                           # Database Migrations
│   │   ├── versions/                      # Migration version scripts
│   │   └── env.py                         # Async Alembic execution environment
│   ├── alembic.ini                        # Alembic CLI configuration
│   └── requirements.txt                   # Locked backend Python dependencies
│
├── data/                                  # DATA GENERATION REPOSITORY (Phase 3)
│   ├── generated/                         # Operational synthetic CSV/JSON data
│   ├── ground_truth/                      # Isolated ground-truth anomaly manifests
│   └── manifests/                         # Checksum manifests (SHA-256)
│
├── scripts/                               # Maintenance & Generation Scripts
├── docs/                                  # Engineering Blueprints (01 to 15)
├── reports/                               # Empirical QA & Benchmark Reports
├── .env.example                           # Root environment variable template
├── .gitignore                             # Clean repository hygiene rules
├── pytest.ini                             # Pytest discovery and asyncio configuration
└── README.md                              # Project runbook and architectural overview
```

---

## 2. Structural Separation of Concerns

1. **Zero Frontend-to-Database Leakage**: The frontend directory contains zero database connection libraries, ORM references, or SQL strings. All data interactions are mediated by `apiClient.ts`.
2. **Zero Route-Level Business Logic**: API route handlers in `backend/app/api/v1/` delegate directly to domain services in `backend/app/services/`.
3. **Repository Pattern for Data Access**: `backend/app/repositories/` encapsulates database querying logic, ensuring that domain services remain decoupled from the persistence layer.
4. **Isolated Ground Truth**: The `data/ground_truth/` directory is isolated from the operational data generation path to prevent accidental leakage into anomaly detection models.
