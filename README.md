# CasinoKing

Repository bootstrap aligned with the project documents in `docs/`.

Before starting the local stack, copy `infra/docker/.env.example` to a local `.env` file for Docker Compose usage.

## Local Bootstrap

Start:
- `cp infra/docker/.env.example infra/docker/.env`
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up --build`

Stop:
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env down`

Default local entry points:
- frontend: `http://localhost:3000`
- backend docs: `http://localhost:8000/docs`
- backend health: `http://localhost:8000/api/v1/health/live`

Local admin bootstrap:
- `docker exec casinoking-backend-1 python -m app.tools.bootstrap_local_admin --email admin@example.com --password StrongPass-Local123`
- This creates a local admin if missing, or promotes an existing user to admin and resets its password.

## Structure

- `backend/`
  FastAPI modular monolith base with auth, wallet/ledger read APIs and Mines MVP backend flows.
- `frontend/`
  Next.js frontend base with player auth, wallet snapshot, ledger list and Mines MVP console.
- `infra/docker/`
  Local Docker bootstrap for backend, frontend, PostgreSQL, and Redis.
- `games/mines/`
  Separable game module scaffold for Mines.
- `tests/`
  Contract, integration and concurrency suites for the critical backend flows.
- `docs/`
  Canonical and operational project documentation.

## Current MVP Scope

- register and login player
- wallet snapshot materialized + ledger source of truth
- signup credit bootstrap
- Mines start, reveal, cashout and session recovery
- minimal admin backoffice console for users, ledger report, fairness, bonus grant and adjustment
- local Docker development environment
- backend test coverage on contract, integration and concurrency scenarios

## Intentionally Still Outside Scope

- full admin interface and role-specific admin auth UX
- promotions and bonus workflows beyond bootstrap placeholders
- reporting and reconciliation views
- advanced fairness evolution and board reveal policy
- production-grade frontend UX and navigation
