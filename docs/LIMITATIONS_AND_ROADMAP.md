# LoyaltyOS — Limitations & Engineering Roadmap

**Product Name:** LoyaltyOS — Intelligent Loyalty & Ledger Management Platform  
**Repository:** https://github.com/dandetejaswini/LoyaltyOS

---

## 1. Current System Limitations

In accordance with transparent engineering principles, the current limitations of the platform are documented below:

### 1.1 Local Runtime Database Configuration
- In the local workspace environment, `DATABASE_URL` is unconfigured (`""`) in `.env` to protect against credential leaks.
- Direct PostgreSQL port `5432` on the Supabase project host is filtered/closed by network boundaries. Live remote connections require using the Supabase transaction pooler on port `6543`.
- Live remote database insertion of the full 20,000 customer dataset has not been executed from this local machine.

### 1.2 Frontend Persona Switcher Simulation
- The Phase 7 persona switcher in [DashboardPage.tsx](file:///C:/CandidateWorkspace/frontend/src/pages/DashboardPage.tsx) (Alice, Marcus, Sarah, Eleanor, David) operates as an interactive client-side simulation.
- It enables instant demonstration and evaluation of role-tailored dashboards and two-person approval invariants without requiring evaluators to authenticate through 5 external OAuth accounts.
- In a production environment without simulated credentials, the FastAPI backend strictly rejects mock tokens and requires cryptographically signed JWTs from Google Firebase or Supabase.

### 1.3 Expiration Processing Concurrency
- Points expiration batches currently execute synchronously via `POST /api/v1/expiry/execute`.
- For enterprise programs exceeding 100,000 active lots, expiration scanning should be offloaded to an asynchronous distributed task worker (e.g. Celery with Redis or AWS SQS) to prevent HTTP request timeouts.

---

## 2. Architectural Assumptions & Boundaries

- **Single Currency per Program**: The current ledger implementation assumes all points operate on a unified integer currency unit.
- **Tenant Scope**: Built as a dedicated single-tenant loyalty platform. Multi-brand loyalty alliances require adding an explicit `tenant_id` foreign key across all 21 tables.
- **Clock Drift**: Expiration and rolling 365-day qualifying spend calculations rely on UTC database timestamps. Client-provided timestamps are strictly ignored.

---

## 3. Engineering Roadmap

### Phase 8 — Production Deployment & Final Submission
- [ ] Connect FastAPI backend to the verified Supabase transaction pooler on port 6543.
- [ ] Ingest seed dataset into live Supabase instance using `--load-db` flag.
- [ ] Deploy frontend to Vercel and verify edge CDN routing.
- [ ] Deploy backend container to a managed PaaS (Railway / Render / AWS ECS).
- [ ] Execute live smoke tests verifying end-to-end customer and manager flows on live URLs.

### Post-Hackathon Enhancements
- [ ] **Distributed Task Queue**: Implement Celery/Redis workers for daily points expiration and rolling spend recalculation.
- [ ] **Webhook Gateway**: Emit cryptographically signed webhooks on ledger events (`order.accrued`, `redemption.completed`, `anomaly.detected`).
- [ ] **Multi-Tenant Federation**: Support partitioned loyalty programs for retail conglomerates with distinct tier structures and cross-brand redemption conversion ratios.
- [ ] **Hardware Security Module (HSM) Key Signing**: Integrate AWS KMS or HashiCorp Vault for signing voucher redemption codes and sensitive audit exports.
