# LoyaltyOS — Limitations & Roadmap

**Repository:** https://github.com/dandetejaswini/LoyaltyOS

---

## 1. Current System Boundaries

- **Database Credentials**: In local development, `DATABASE_URL` is kept empty in `.env` to prevent accidental credential commits. Production uses the Supabase transaction pooler on port 6543.
- **Frontend Persona Switcher**: The role switcher on the dashboard lets you test all four roles (Customer, Operator, Analyst, Operations Manager) without logging into four separate OAuth accounts. In production, roles are strictly loaded from the database via signed JWT tokens.
- **Synchronous Expiration**: The expiration endpoint (`POST /api/v1/expiry/execute`) runs synchronously. For large catalogs with over 100,000 active lots, an asynchronous background worker is recommended.
- **Single Loyalty Currency**: The ledger currently tracks a single points currency.
- **UTC Time Standard**: All expiration dates and tier evaluations rely on UTC database timestamps.

---

## 2. Engineering Roadmap

### Near-Term Enhancements
- **Asynchronous Task Queue**: Offload daily points expiration and rolling spend calculations to background workers (e.g. Celery or BullMQ).
- **Outbound Webhooks**: Send signed webhooks when key events occur (`order.accrued`, `redemption.completed`, `anomaly.detected`).
- **Export Reports**: Add one-click CSV and PDF exports for financial liability and audit trails.

### Long-Term Enhancements
- **Multi-Brand Alliances**: Support multi-tenant loyalty programs with shared points redemption across partner brands.
- **Cloud Key Management (KMS)**: Sign voucher redemption codes using cloud KMS for hardware-level tampering prevention.
- **Custom Rule Builder**: Web interface for marketing teams to design custom promotion multipliers and bonus point rules.
