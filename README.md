# CasinoKing

Repository bootstrap aligned with the project documents in `docs/`.

Before starting the local stack, copy `infra/docker/.env.example` to a local `.env` file for Docker Compose usage.

## Local Bootstrap

Start:
- `cp infra/docker/.env.example infra/docker/.env`
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up --build`

Local note:
- the backend now applies repository SQL migrations automatically before startup
- on older local volumes already initialized without migration tracking, the first startup backfills migration state conservatively if the schema already matches the full local MVP baseline

Stop:
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env down`

Default local entry points:
- frontend: `http://localhost:3000`
- backend docs: `http://localhost:8000/docs`
- backend health: `http://localhost:8000/api/v1/health/live`

Local admin bootstrap:
- `docker exec casinoking-backend-1 python -m app.tools.bootstrap_local_admin --email admin@example.com --password StrongPass-Local123`
- This creates a local admin if missing, or promotes an existing user to admin and resets its password.

Local test workflow:
- `docker run --rm --network casinoking_default -v "${PWD}:/workspace" -w /workspace/backend -e CASINOKING_API_BASE_URL=http://backend:8000/api/v1 -e CASINOKING_TEST_DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking -e CASINOKING_SITE_ACCESS_PASSWORD=change-me casinoking-backend python -m pytest /workspace/tests -q`

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
- Mines dedicated route at `/mines` plus desktop embedded launcher from the web shell
- minimal admin backoffice console for users, ledger report, fairness, bonus grant and adjustment
- Mines backoffice draft/publish flow for rules HTML, published grid/mine subsets, mode labels and board assets
- local Docker development environment
- backend test coverage on contract, integration and concurrency scenarios

## Current Architecture Notes

- The platform backend already contains explicit boundaries for game launch and round settlement under `backend/app/modules/platform/`.
- Mines remains server-authoritative and uses the official runtime payout tables in `docs/runtime/`.
- The web frontend is still transitional:
  - `frontend/app/ui/casinoking-console.tsx` remains the legacy shared shell for lobby/account/admin
  - `frontend/app/ui/mines-standalone.tsx` powers the dedicated Mines product route
  - `frontend/app/ui/mines-board.tsx` is the extracted board renderer for Mines
- The admin Mines backoffice is functionally present but still hosted inside the legacy admin shell.

## Current Documentation Entry Points

- Project documentation map: `docs/README.md`
- Source hierarchy: `docs/SOURCE_OF_TRUTH.md`
- Task guardrails: `docs/TASK_EXECUTION_GUARDRAILS.md`
- Mines architecture atlas: `docs/ARCHITECTURE_ATLAS_MINES.md`
- Platform/frontend architecture atlas: `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- Documentation maintenance rules: `docs/DOCUMENTATION_MAINTENANCE.md`

## Intentionally Still Outside Scope

- full admin interface and role-specific admin auth UX
- promotions and bonus workflows beyond bootstrap placeholders
- reporting and reconciliation views
- advanced fairness evolution and board reveal policy
- production-grade frontend UX and navigation
