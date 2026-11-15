# 13. Environment Configuration and Secret Isolation

## 1. Overview & Secret Isolation Principles

The YottaFlex system adheres to strict defense-in-depth configuration standards:
1. **Zero Secret Leakage in Client Bundles**: Any environment variable prefixed with `VITE_` is statically injected into the client JavaScript bundle. Therefore, `VITE_` variables must contain **only public non-sensitive identifiers** (e.g. Supabase project URL, public anon key, Firebase web client ID).
2. **Server-Side Exclusivity**: High-privilege credentials—such as `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, and `FIREBASE_SERVICE_ACCOUNT`—must only be accessed by the backend server.
3. **No Committed Secrets**: `.env` files containing actual passwords, tokens, or private keys are excluded from git via `.gitignore`.
4. **No Invented Credentials**: Placeholder configuration strings in `.env.example` clearly indicate pending Phase 2 Supabase and Firebase provisioning.

---

## 2. Environment Variables Matrix

| Variable Name | Tier | Sensitivity | Purpose | Required in Phase 1? |
|---|:---:|:---:|---|:---:|
| `APP_NAME` | Backend | Public | Name of application | Yes (default: `"YottaFlex Loyalty Ledger"`) |
| `APP_VERSION` | Backend | Public | Current release version | Yes (default: `"1.0.0"`) |
| `APP_ENV` | Backend | Public | Environment (`development`, `staging`, `production`) | Yes (default: `"development"`) |
| `DEBUG` | Backend | Low | Enable debug logs & reload | Yes (default: `false`) |
| `LOG_LEVEL` | Backend | Low | Log output level (`INFO`, `DEBUG`, `WARN`) | Yes (default: `"INFO"`) |
| `HOST` | Backend | Low | Server bind host | Yes (default: `"0.0.0.0"`) |
| `PORT` | Backend | Low | Server bind port | Yes (default: `8000`) |
| `ALLOWED_ORIGINS` | Backend | Low | CORS whitelist | Yes (includes `http://localhost:5173`) |
| `DATABASE_URL` | Backend | **High (Secret)** | Supabase async PostgreSQL connection string | Prepared (Phase 2 configuration) |
| `DB_POOL_SIZE` | Backend | Medium | SQLAlchemy connection pool size | Yes (default: `5`) |
| `SUPABASE_URL` | Both | Public | Supabase project API endpoint | Prepared (Phase 2 configuration) |
| `SUPABASE_ANON_KEY` | Both | Public | Public anon key for client-side API | Prepared (Phase 2 configuration) |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | **High (Secret)** | Server-side admin key (bypasses RLS) | Prepared (Phase 2 configuration) |
| `SUPABASE_JWT_SECRET` | Backend | **High (Secret)** | HMAC / RSA key to verify user JWTs | Prepared (Phase 2 configuration) |
| `FIREBASE_PROJECT_ID` | Both | Public | Firebase project identifier | Prepared (Phase 2 configuration) |
| `FIREBASE_SERVICE_ACCOUNT_PATH`| Backend | **High (Secret)** | Server-side service account JSON path | Prepared (Phase 2 configuration) |
| `VITE_API_BASE_URL` | Frontend | Public | Base URL for FastAPI backend | Yes (default: `http://localhost:8000/api/v1`) |

---

## 3. JWT Verification Strategy (Supabase & Firebase)

In accordance with Phase 0 requirements:
- **Supabase Token Verification**: Supabase projects typically issue HS256 or RS256 JWTs. The backend verifies the token using the project's JWT secret or public keys via `pyjwt[crypto]`. Claims verified include `sub` (Supabase UID), `email`, and expiration (`exp`).
- **Firebase ID Token Verification**: Google OAuth tokens issued by Firebase Auth are verified server-side against Google's public x509 certs. Claims verified include `uid` (Firebase UID), `email`, and `email_verified`.
- **Identity Resolution**: Verified UIDs map to an internal application `customer_id` via the `user_identity_mappings` table.
