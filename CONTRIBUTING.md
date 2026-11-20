# Contributing to OpportunityHunter AI

Thanks for your interest in contributing! This project is in **Phase 1 (foundation)** —
authentication and opportunity discovery are not yet implemented. Contributions that strengthen the
foundation (tests, docs, accessibility, deployment automation) are especially welcome.

## Getting started

1. Fork and clone the repository.
2. Set up the backend:

   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:

   ```bash
   cd frontend
   npm install
   ```

4. Copy `.env.example` to `.env` and fill in placeholders. Never commit real values.

## Development workflow

- Backend tests: `cd backend && python -m pytest`
- Frontend checks: `cd frontend && npm run typecheck && npm run build`
- The backend must start without `DATABASE_URL` or `FIRECRAWL_API_KEY` set. Keep it that way.
- Keep secrets server-side. Never add credentials to frontend code, `NEXT_PUBLIC_*` variables,
  logs, or tests.

## Pull request process

1. Create a branch named `feat/<topic>`, `fix/<topic>`, or `docs/<topic>`.
2. Make small, focused changes with tests where applicable.
3. Ensure `pytest`, `tsc --noEmit`, and `next build` all pass.
4. Update README/docs if behavior or setup changes.
5. Open a PR describing what changed, why, and how it was verified.

## Style

- Python: type hints, structured JSON logging, `AppException` subclasses for domain errors.
- TypeScript/React: App Router, function components, Tailwind utilities, `"use client"` only where
  interactivity requires it.
- Docs: Markdown, concise, honest about what is and is not implemented.

## License

By contributing, you agree your contributions are licensed under Apache-2.0.
