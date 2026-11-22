# OpportunityHunter AI — Deployment Readiness

## Environment Configuration

Copy `.env.example` to `.env` and set the following variables. All values are required unless noted otherwise.

### Required PostgreSQL Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URL for SQLAlchemy. Format: `postgresql+psycopg2://username:password@hostname:5432/database_name` | `postgresql+psycopg2://oh_user:oh_pass@localhost:5432/opportunity_hunter` |
| `DATABASE_POOL_SIZE` | SQLAlchemy connection pool size. Default: `5` | `5` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections beyond pool_size. Default: `10` | `10` |

### Authentication (Supabase JWT)

| Variable | Description | Example |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | `eyJhbGciOiJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (bypass RLS) | `eyJhbGciOiJ...` |
| `SUPABASE_JWT_SECRET` | **Critical**: JWT secret for verifying Supabase ID tokens (HS256). Must match the secret configured in your Supabase project. | `your-supabase-jwt-secret` |
| `SUPABASE_JWT_ISSUER` | JWT issuer URL. Defaults to `{SUPABASE_URL}/auth/v1` if omitted. | `https://your-project.supabase.co/auth/v1` |
| `SUPABASE_JWT_AUDIENCE` | JWT audience claim. Default: `authenticated` | `authenticated` |

### Firecrawl BYOK (Bring Your Own Key)

| Variable | Description | Example |
|---|---|---|
| `FIRECRAWL_BASE_URL` | Firecrawl API base URL. Default: `https://api.firecrawl.dev` | `https://api.firecrawl.dev` |
| `FIRECRAWL_TIMEOUT_SECONDS` | Request timeout in seconds. Default: `30` | `30` |
| `FIRECRAWL_VALIDATE_LIVE` | If `True`, validates API key against `/health` endpoint on save. Default: `False` | `False` |
| `FIRECRAWL_ENCRYPTION_KEY` | **Critical**: 32-byte (64 hex-character) key for per-user AES-256-GCM encryption of Firecrawl credentials. Must be set. | `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef` |

### Application Settings

| Variable | Description | Default | Example |
|---|---|---|---|
| `ENVIRONMENT` | Environment identifier. Set to `production` for prod. | `development` | `production` |
| `DEBUG` | Debug mode. Must be `false` in production. | `false` | `false` |
| `LOG_LEVEL` | Logging level. | `INFO` | `INFO` |
| `API_PREFIX` | API route prefix. | `/api/v1` | `/api/v1` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins. Must include your frontend production domain. | `http://localhost:3000,http://127.0.0.1:3000` | `https://app.example.com,https://example.com` |

### Discovery Limits

| Variable | Description | Default |
|---|---|---|
| `DISCOVERY_MAX_RESULTS` | Max opportunities per discovery job | `20` |
| `DISCOVERY_DEFAULT_RESULTS` | Default results per job | `20` |
| `DISCOVERY_MAX_CONCURRENT_JOBS` | Max active jobs per user | `2` |
| `DISCOVERY_DAILY_QUOTA` | Max jobs per user per day | `10` |
| `DISCOVERY_MAX_DOMAINS` | Max source domains per job | `8` |
| `DISCOVERY_MAX_RETRIES` | Max retry attempts for Firecrawl calls | `2` |

---

## Database Migration Process

### Migration Chain (0001 → 0004)

All migrations are linear and must be applied in order:

1. `0001_phase2_users` — Creates `user_profiles` and `user_api_credentials` tables
2. `0002_discovery_jobs` — Creates `discovery_jobs` table (depends on 0001)
3. `0003_opportunities` — Creates `opportunities` and `opportunity_sources` tables (depends on 0002)
4. `0004_application_tracker` — Creates `user_applications` table (depends on 0003)

### Apply Migrations to Fresh PostgreSQL Database

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Set DATABASE_URL and FIRECRAWL_ENCRYPTION_KEY in .env

# 3. Run migrations online (connects to DB with URL from .env)
cd backend
alembic upgrade head
```

### Verify Migrations Applied

```bash
alembic heads
# Should show: head -> 0004_application_tracker

alembic history
# Should show all 4 migrations applied in order: 0001 → 0002 → 0003 → 0004
```

### Rollback (if needed)

```bash
# Rollback one step
alembic downgrade base

# Or rollback to specific revision
alembic downgrade 0003_opportunities
```

### Migration Dependencies

The migration chain is strictly linear. Do not skip or reorder migrations. Each migration's `down_revision` points to the previous revision ID.

---

## Deployment Architecture

### Services and Hosting

| Service | Recommendation | Free/Low-Cost Option |
|---|---|---|
| **Backend (FastAPI)** | Any Python/WSGI-capable host (Gunicorn + Uvicorn) | Render.com Free tier, PythonAnywhere Free tier, Fly.io Shared VM |
| **Frontend (Next.js)** | Static-site host with Edge Functions | Vercel (Free), Netlify (Free), Cloudflare Pages (Free) |
| **Database (PostgreSQL)** | Managed PostgreSQL with RLS support | Supabase Free tier (PostgreSQL + Auth), Neon Free tier, ElephantSQL |
| **Firecrawl API** | External API (no hosting needed) | Pay-as-you-go, free tier available |
| **Supabase Auth** | External auth service (included with Supabase DB) | Supabase Free project |

### Production Topology

```
+----------------+      +------------------+      +---------------------+
|   Frontend     | <--> |   Backend API    | <--> |   PostgreSQL DB     |
| (Vercel/Netlify) |     | (FastAPI + uvicorn) |   | (Supabase/Neon)   |
+----------------+      +------------------+      +---------------------+
        ^                      ^
        |                      |
        +--------------------+
           Supabase JWT Auth
```

### Process Flow

1. **User onboarding**: Frontend → `/api/v1/auth` → Supabase JWT verification
2. **Firecrawl credential setup**: Authenticated user → `/api/v1/credentials/firecrawl` → encrypt & store per-user key
3. **Discovery**: Authenticated user → `/api/v1/discovery` → create job → orchestrator crawls approved domains
4. **Extraction**: Orchestrator → extraction_orchestrator → parse opportunities → store in DB
5. **Public listings**: `GET /api/v1/public/opportunities` → only `is_public=true` opportunities
6. **Application tracking**: Authenticated user → `/api/v1/applications` → create/update application records

---

## Security Configuration Review

### CORS (Production)

- Set `CORS_ORIGINS` to your exact production frontend domain(s), e.g.:
  ```
  CORS_ORIGINS=https://app.example.com,https://example.com
  ```
- Do not include `http://localhost` or `127.0.0.1` in production
- The backend uses FastAPI's `CORSMiddleware` with `allow_credentials=True`

### JWT Authentication

- `SUPABASE_JWT_SECRET` **must** match the secret in your Supabase project dashboard
- Tokens are verified server-side using HS256 algorithm
- Required claims: `exp`, `sub`, `iss`, `aud`
- Token audience must be `authenticated` (or configured via `SUPABASE_JWT_AUDIENCE`)
- Missing/invalid tokens return `401`/`403` errors
- If `SUPABASE_JWT_SECRET` is not set, all authenticated endpoints return `503`

### AES-256-GCM Encryption

- `FIRECRAWL_ENCRYPTION_KEY` must be exactly 32 bytes (64 hex characters)
- Each user's Firecrawl API key is encrypted with the same key but unique nonce + AAD (`firecrawl:{user_id}`)
- AAD prevents cross-user decryption even with the same key
- If `FIRECRAWL_ENCRYPTION_KEY` is not set, credential endpoints return `503`
- Secret redaction is active: `redact_secret()` masks values before logging

### Firecrawl BYOK (Bring Your Own Key)

- Each user provides their own Firecrawl API key
- Keys are never stored in plaintext — encrypted via AES-256-GCM per user
- On credential save, key format is validated and optionally live-validated against `/health`
- Credential decryption fails if the encryption key changes or the credential was encrypted by a different key
- `FIRECRAWL_VALIDATE_LIVE=True` adds a `/health` check on save (adds latency)

### SSRF Protections

- **Domain allowlist**: Only these 9 domains are approved for crawling:
  - `linkedin.com`, `wellfound.com`, `remoteok.com`, `workatastartup.com`
  - `internshala.com`, `upwork.com`, `freelancer.com`, `greenhouse.io`, `lever.co`
- `_normalize_sources()` validates all source domains against the allowlist
- URL normalization strips tracking params, www prefix, lowercases, removes trailing slashes
- Input capping: max 20 domains, 300-char keywords, 20 skills/locations
- Private IP ranges and metadata endpoints are blocked in verification service

### Rate Limiting

- **Public opportunities**: 100 requests per minute per client IP (in-memory dictionary)
  - Configured in `public_opportunities.py:_RATE_LIMIT = 100`, `_RATE_WINDOW = 60`
  - Proxied IP support via `X-Forwarded-For` header
  - Returns `429` when exceeded
- **Discovery concurrency**: Max 2 active jobs per user (`discovery_max_concurrent_jobs`)
- **Discovery quota**: Max 10 jobs per user per day (`discovery_daily_quota`)
- **Firecrawl retries**: Configurable via `DISCOVERY_MAX_RETRIES` (default 2), backs off on 5xx errors only

### Secrets in Logs

- `redact_secret()` utility masks `FIRECRAWL_API_KEY`, `DATABASE_URL`, and other secrets
- Health endpoint (`/api/v1/health`) explicitly avoids leaking any secret values
- `SUPABASE_JWT_SECRET` is never logged in plaintext

---

## Deployment Smoke-Test Checklist

### 1. Authentication

- [ ] Deploy `.env` with `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `SUPABASE_JWT_ISSUER`
- [ ] Verify `GET /api/v1/auth/me` returns 401 without Bearer token
- [ ] Verify `GET /api/v1/auth/me` returns 200 with valid Supabase JWT
- [ ] Verify `GET /api/v1/auth/me` returns 401 with expired token
- [ ] Verify `GET /api/v1/auth/me` returns 403 with service_role token
- [ ] Verify `GET /api/v1/auth/profile` requires authentication and returns user-specific data

### 2. Discovery

- [ ] Set `FIRECRAWL_ENCRYPTION_KEY` (32-byte hex) in `.env`
- [ ] Create a Firecrawl API key and save it via `POST /api/v1/credentials/firecrawl`
- [ ] Verify credential is encrypted at rest (check DB — should be base64 ciphertext, not plaintext)
- [ ] Create a discovery job via `POST /api/v1/discovery` with keywords and domains from the supported list
- [ ] Verify job status transitions: `pending` → `running` → `completed`
- [ ] Verify domain allowlist: job fails if disallowed domain is provided
- [ ] Verify concurrency limit: user cannot create more than `discovery_max_concurrent_jobs` active jobs
- [ ] Verify daily quota: user cannot create more than `discovery_daily_quota` jobs per day

### 3. Extraction

- [ ] After discovery job completes, extract opportunities via `POST /api/v1/opportunities/extract/{job_id}`
- [ ] Verify extracted opportunities appear in `GET /api/v1/opportunities` (authenticated user only)
- [ ] Verify non-public opportunities are not visible in public listings
- [ ] Verify opportunity fingerprinting: duplicate URLs are deduplicated

### 4. Public Listings

- [ ] `GET /api/v1/public/opportunities` returns 200 without authentication
- [ ] Only opportunities with `is_public=true` are returned in public listings
- [ ] `GET /api/v1/public/opportunities/{id}` returns 200 for public opportunities, 404 for private
- [ ] Rate limiting: >100 requests/minute from same IP returns 429
- [ ] All filter parameters work: category, verification_status, location, remote_preference, experience_level, skills, search

### 5. Application Tracking

- [ ] Create an application via `POST /api/v1/applications` (authenticated)
- [ ] Application is linked to user_id and opportunity_id
- [ ] Application status transitions: `interested` → `saved` → `applied` → `assessment` → `interview` → `offer`
- [ ] User can only view/modify their own applications (ownership enforced by foreign key)
- [ ] Attempting to access another user's application returns 404 or 403

### 6. End-to-End Flow

- [ ] Full cycle: Onboard user → Save Firecrawl credential → Create discovery job → Extract opportunities → Toggle public → View in public listings → Track application
- [ ] Verify `GET /api/v1/health` returns `200` with `database_configured=true`, `firecrawl_configured=true`, `auth_configured=true`
- [ ] Verify no secrets appear in health endpoint response or logs
- [ ] Run existing test suite: `pytest backend/tests/ -v` — all 133 tests must pass

---

## Remaining Manual Deployment Steps

**These must be completed before going live:**

1. [ ] Provision PostgreSQL database (Supabase Free tier, Neon, or similar)
2. [ ] Configure Supabase project with JWT secrets and enable RLS on all tables
3. [ ] Set `FIRECRAWL_ENCRYPTION_KEY` to a secure 32-byte (64 hex char) value kept secret
4. [ ] Set `CORS_ORIGINS` to your exact production frontend domain(s)
5. [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
6. [ ] Set `SUPABASE_JWT_SECRET` to match your Supabase project settings
7. [ ] Run `alembic upgrade head` to apply all 4 migrations
8. [ ] Deploy frontend to Vercel/Netlify with production environment variables
9. [ ] Deploy backend with `.env` containing all required variables
10. [ ] Test the smoke-checklist items above manually or via CI
11. [ ] Monitor logs for `redact_secret` warnings indicating secrets leaking
12. [ ] Configure external monitoring/alerting for rate limits and errors

**Do not deploy without:**
- `DATABASE_URL` pointing to a live PostgreSQL database
- `FIRECRAWL_ENCRYPTION_KEY` set (required for credential encryption)
- `SUPABASE_JWT_SECRET` set (required for auth)
- Production `CORS_ORIGINS` configured

---

## Vercel + Render Deployment

The repository now includes `frontend/vercel.json` and a root `render.yaml` blueprint.

### Vercel (frontend)

1. Import this GitHub repository into Vercel.
2. Set the **Root Directory** to `frontend`.
3. Add these environment variables:
   - `NEXT_PUBLIC_API_URL`: the public Render API origin, without a trailing slash.
   - `NEXT_PUBLIC_SUPABASE_URL`: your Supabase project URL.
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: your Supabase publishable/anon key.
4. Add your Vercel production and preview URLs to Supabase Auth's allowed redirect URLs.
5. Deploy the feature branch as a preview first. Promote only after CI and the smoke tests pass.

### Render (FastAPI backend)

1. In Render, create a Blueprint deployment using the repository root `render.yaml`.
2. Set the secret environment variables in the Render dashboard:
   - `DATABASE_URL`: PostgreSQL connection string using the SQLAlchemy-compatible `postgresql+psycopg2://` scheme.
   - `CORS_ORIGINS`: exact Vercel production origin(s), comma-separated.
   - `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, and `SUPABASE_JWT_ISSUER`.
   - `FIRECRAWL_ENCRYPTION_KEY`: generate with `openssl rand -hex 32`.
3. Apply the Alembic migrations before accepting traffic. The Blueprint build command runs `alembic upgrade head`; verify the migration logs before going live.
4. Confirm `GET /api/v1/health` returns healthy status and that CORS permits the deployed frontend origin.

### Important authentication compatibility note

The backend currently validates Supabase access tokens using the legacy HS256 JWT secret. Confirm that the Supabase project issues HS256 tokens and that `SUPABASE_JWT_SECRET` matches the project's JWT secret. Projects using asymmetric signing keys (for example ES256) require backend JWKS-based verification before production rollout; do not weaken signature verification or disable JWT checks to work around this.

### CI

The workflow at `.github/workflows/ci.yml` runs backend pytest, frontend TypeScript checks, and a Next.js production build on pushes to the feature branch and on pull requests. Treat a green workflow as a prerequisite for merging. CI results must be reviewed in GitHub Actions; they are not implied by a successful commit.
