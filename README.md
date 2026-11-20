# OpportunityHunter AI

OpportunityHunter AI helps you discover grants, jobs, and growth opportunities that match your
goals — privately, with your own API key, on a free-tier-friendly stack.

> **Current status: Phase 3 — Firecrawl integration & opportunity discovery.** The FastAPI backend,
> database layer, structured logging with secret redaction, Alembic migrations, Supabase Auth,
> per-user encrypted Firecrawl credentials, Firecrawl-powered discovery pipeline, and the Next.js
> frontend with discovery interface are in place.
> **Authentication, credential storage, and opportunity discovery are operational.** See
> [Security](#security) and [Roadmap](#roadmap).

## Architecture

| Layer     | Technology                                        |
| --------- | ------------------------------------------------- |
| Frontend  | Next.js (App Router), React, TypeScript, Tailwind CSS |
| Backend   | Python FastAPI                                     |
| Database  | PostgreSQL / Supabase                              |
| ORM       | SQLAlchemy                                         |
| Migrations| Alembic                                            |
| Testing   | Pytest (backend), Next.js build + `tsc --noEmit` (frontend) |
| License   | Apache-2.0                                         |

### Design decisions

- **Each user supplies their own Firecrawl API key.** No shared project key is stored anywhere.
- **Firecrawl credentials are server-side only.** They are never exposed to browser code, API
  responses, or logs. Phase 2 adds per-user encrypted storage at rest.
- **Discovery runs server-side.** Firecrawl API calls are made exclusively from the backend;
  users only see results, never raw API keys or responses.
- **The backend starts without a database or a Firecrawl key.** Both are optional at startup; the
  health endpoint reports their configuration status as booleans only.
- **Free-tier-first hosting.** PostgreSQL/Supabase free tiers, self-hostable backend, static-friendly
  frontend.

## Repository layout

```
backend/                  FastAPI application
  app/
    main.py               App entry point (lifespan, CORS, exception handlers, router)
    core/                 Settings, exceptions, handlers, JSON logging, secret redaction
    database/             SQLAlchemy base + lazy engine/session management
    models/               SQLAlchemy models (user profiles, credentials, discovery jobs)
    schemas/              Pydantic schemas (request/response validation)
    services/             Business logic (profile, credential, discovery orchestration)
    scrapers/             Firecrawl client, sources, discovery service
    api/routers/          API v1 routers (health, auth, profile, credentials, discovery)
  alembic/                Migration environment
  tests/                  Pytest suite
frontend/                 Next.js application
  app/                    App Router pages (landing, auth, dashboard, opportunities, profile, settings)
  components/             Layout, landing, shared, discovery, and UI components
  hooks/                  Client hooks
  lib/                    Browser-safe API client (no secrets)
  types/                  Shared TypeScript types
docs/                     Project documentation
scripts/                  Automation scripts
```

## Quickstart

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/api/v1/health
# {"status":"ok","app":"OpportunityHunter AI","version":"0.1.0","environment":"development","database_configured":false,"firecrawl_configured":false,"auth_configured":false}
```

Run tests:

```bash
python -m pytest
```

Run migrations (only when `DATABASE_URL` is set):

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
npm run typecheck  # TypeScript check
npm run build      # Production build
```

## Configuration

Copy `.env.example` to `.env` and adjust. All secret fields are empty placeholders; the app runs
without them.

| Variable                        | Where      | Purpose                                        |
| ------------------------------- | ---------- | ---------------------------------------------- |
| `DATABASE_URL`                  | backend    | PostgreSQL connection string (optional)        |
| `SUPABASE_URL` / keys           | backend    | Supabase access (server-side only)             |
| `SUPABASE_JWT_SECRET`           | backend    | JWT secret for verifying user tokens (server-side only) |
| `SUPABASE_JWT_ISSUER`           | backend    | Optional explicit JWT issuer URL               |
| `SUPABASE_JWT_AUDIENCE`         | backend    | JWT audience (default: `authenticated`)        |
| `FIRECRAWL_API_KEY`             | backend    | Firecrawl key — **never** `NEXT_PUBLIC_*`      |
| `FIRECRAWL_BASE_URL`            | backend    | Firecrawl API base URL (default: `https://api.firecrawl.dev`) |
| `FIRECRAWL_TIMEOUT_SECONDS`     | backend    | Request timeout for Firecrawl calls (default: 30) |
| `FIRECRAWL_VALIDATE_LIVE`       | backend    | Live-validate user keys on save (default: `false`) |
| `FIRECRAWL_ENCRYPTION_KEY`      | backend    | Key for Phase 2 encrypted per-user storage     |
| `DISCOVERY_MAX_RESULTS`         | backend    | Max results per discovery request (default: 20) |
| `DISCOVERY_MAX_CONCURRENT_JOBS` | backend    | Max concurrent jobs per user (default: 2)      |
| `DISCOVERY_DAILY_QUOTA`         | backend    | Daily discovery quota per user (default: 10)   |
| `DISCOVERY_MAX_DOMAINS`         | backend    | Max source domains per request (default: 8)    |
| `DISCOVERY_SUPPORTED_DOMAINS`   | backend    | Comma-separated allowed domains for crawling   |
| `DISCOVERY_POLL_SECONDS`        | backend    | Poll interval for crawl status (default: 5)    |
| `DISCOVERY_MAX_WAIT_SECONDS`    | backend    | Max wait time for crawl completion (default: 300) |
| `DISCOVERY_MAX_RESPONSE_BYTES`  | backend    | Max markdown bytes per result (default: 200000) |
| `DISCOVERY_MAX_STORED_RESULTS`  | backend    | Max results stored per job (default: 60)       |
| `DISCOVERY_MAX_RETRIES`         | backend    | Max retries for Firecrawl calls (default: 2)   |
| `NEXT_PUBLIC_API_URL`           | frontend   | Public API base URL only — no secrets here     |

## Security

- Secrets are excluded from Git (`.gitignore`); `.env.example` contains placeholders only.
- Logs never contain tokens, passwords, or API keys; `app/core/redact.py` redacts secret values.
- Browser-side code only ever receives public configuration.
- Firecrawl credentials are encrypted at rest with AES-256-GCM; decryption happens only in
  server-side code paths that need to call Firecrawl.
- Discovery jobs are scoped to the authenticated user; no cross-user access.
- Crawl targets are validated against an allowlist and checked for private IP / metadata endpoints.
- See [SECURITY.md](SECURITY.md) for the vulnerability-reporting process and the Phase 2/3
  credential-encryption and discovery-safety plans.

## Roadmap

- **Phase 1 (done):** Backend foundation, health endpoint, frontend shell, security posture, docs.
- **Phase 2 (done):** Authentication, per-user encrypted Firecrawl credential storage.
- **Phase 3 (done):** Firecrawl-powered opportunity discovery, search API, history, cancellation.
- **Phase 4:** Notifications, dashboards, self-hosting hardening.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Apache-2.0 — see [LICENSE](LICENSE).