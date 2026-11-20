# Security Policy

## Supported versions

OpportunityHunter AI is in Phase 3 (Firecrawl integration & opportunity discovery). The current
`master` branch is the only supported version.

## Reporting a vulnerability

Email **dev@opportunityhunter.ai** with:

- A description of the issue and affected component.
- Steps to reproduce (if applicable).
- Impact assessment.

Please do **not** open a public issue for security reports. We will acknowledge within 72 hours and
coordinate disclosure.

## Secret handling rules

- No real credentials in source code, tests, docs, or screenshots.
- `.env` and all environment files are Git-ignored; `.env.example` contains placeholders only.
- Firecrawl and Supabase credentials are server-side only. Browser code receives only
  `NEXT_PUBLIC_*` non-secret values.
- Logs are structured JSON and redact secrets (`app/core/redact.py`). Tokens, passwords, and API
  keys must never appear in log output.
- The `/api/v1/health` endpoint reports configuration booleans only — never key material.

## Credential storage (Phase 2)

- Each user supplies their own Firecrawl API key; the platform never shares one project-wide key.
- Keys are encrypted at rest with AES-256-GCM via the `cryptography` library.
- The encryption key comes from `FIRECRAWL_ENCRYPTION_KEY` (32-byte hex), rotated out of band.
- Decryption happens only in server-side code paths that need to call Firecrawl; plaintext keys are
  never returned by any API route, logged, or sent to the browser.
- Supabase service-role keys remain server-only; the anon key is the only client-facing Supabase
  value.

## Discovery safety (Phase 3)

- Firecrawl API calls are made **exclusively from the backend**. Users only see results, never
  raw API keys or Firecrawl responses.
- Discovery jobs are scoped to the authenticated user; no cross-user access to jobs or results.
- Crawl targets are validated against a configurable allowlist (`DISCOVERY_SUPPORTED_DOMAINS`).
  Only approved domains may be crawled.
- All target URLs are validated to prevent SSRF:
  - Only `http`/`https` schemes allowed.
  - Hostnames are resolved and checked against private IP ranges (RFC 1918, loopback, link-local,
    cloud metadata endpoints like `169.254.169.254`).
  - Redirect destinations are validated the same way.
- Usage limits enforced per user:
  - Maximum concurrent discovery jobs (`DISCOVERY_MAX_CONCURRENT_JOBS`, default 2).
  - Daily discovery quota (`DISCOVERY_DAILY_QUOTA`, default 10).
  - Maximum results per request (`DISCOVERY_MAX_RESULTS`, default 20).
  - Maximum source domains per request (`DISCOVERY_MAX_DOMAINS`, default 8).
  - Maximum crawl wait time (`DISCOVERY_MAX_WAIT_SECONDS`, default 300s).
  - Maximum stored results per job (`DISCOVERY_MAX_STORED_RESULTS`, default 60).
- Firecrawl client implements bounded retries with exponential backoff:
  - Retries only on transient failures (timeouts, network errors, 5xx).
  - **Never retries** on authentication errors (401/403), rate limits (429), or validation errors.
- Firecrawl API keys are never logged, returned in API responses, or exposed to the browser.
- Discovery results are truncated to a configurable byte limit (`DISCOVERY_MAX_RESPONSE_BYTES`).

## Dependency security

- Pin and regularly update backend (`requirements.txt`) and frontend (`package.json`) dependencies.
- Review advisory databases before upgrades.

## Scope

This policy covers the OpportunityHunter AI repository and its self-hosted deployments.