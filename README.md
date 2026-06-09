# CasinoKing

Start here.

If you remember one file, remember this root `README.md`. It is the stable entry
point for humans, Codex Desktop, Codex in VS Code, Codex CLI, and future AI
handoffs.

Next:

1. Fresh AI / handoff guide: `docs/AI_BOOTSTRAP_RUNBOOK.md`
2. Documentation index: `docs/README.md`
3. Local smoke suite: `docs/LOCAL_SMOKE_SUITE.md`

## Current Handoff - Site V3 / Games 2026-06-03

Site V3 recovery is closed. Phase 2B, Phase 3A, R2B/R2C and the follow-up
micro-fixes are no longer paused work. The public edge on `http://localhost:3000`
serves Site V3, player shell, admin shell and game shells from `frontend-v3`.

The consolidation Phase A is also closed: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
is aligned to v3 and HI-LO has a reference refinement report in
`docs/SITE_V3_HILO_REFERENCE_REFINEMENT_REPORT_2026-06-01.md`.

Next product work: COINS, game 4. Start with the documented gate only; do not
write COINS game code before the COINS document packet/spec gate is approved.

Before starting the local stack, copy `infra/docker/.env.example` to a local `.env` file for Docker Compose usage.

## Local Bootstrap

Start:
- copy `infra/docker/.env.example` to `infra/docker/.env` if the local env file does not exist
- `.\scripts\ck-up.ps1`
- `.\scripts\ck-doctor.ps1`
- `.\scripts\ck-test-smoke.ps1`

Manual fallback:
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up --build`

Local note:
- the backend now applies repository SQL migrations automatically before startup
- on older local volumes already initialized without migration tracking, the first startup backfills migration state conservatively if the schema already matches the full local MVP baseline

Stop:
- `.\scripts\ck-down.ps1`

Manual fallback:
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env down`

Default local entry points:
- public website edge: `http://localhost:3000` (Site V3 root and routed app)
- frontend-v3 direct renderer: `http://localhost:3001`
- backend docs: `http://localhost:8000/docs`
- backend health: `http://localhost:8000/api/v1/health/live`

Local routing stance:
- Site V3 is the public website root on `http://localhost:3000`.
- `frontend-v3` is the only local application frontend.
- The local edge service routes `/login`, `/register`, `/account`, `/admin/**`,
  `/mines`, `/boxe`, `/hi-lo`, `/runtime/*`, `/_next`, favicon,
  `/game-assets` and `/brand` to `frontend-v3`.
- The old frontend service, Dockerfile and source folder have been removed by
  WP-MIG6/WP-MIG6B.

Technical local admin bootstrap:
- `docker exec casinoking-backend-1 python -m app.tools.bootstrap_local_admin --email codex.agent@example.com --password <password-from-.local/codex-admin-login.md>`
- Use this only for the dedicated technical admin account. Do not bootstrap or reset `admin@example.com`, which is reserved as the human/local admin account.

Local test workflow:
- canonical smoke: `.\scripts\ck-test-smoke.ps1`
- `docker run --rm --network casinoking_default -v "${PWD}:/workspace" -w /workspace/backend -e CASINOKING_API_BASE_URL=http://backend:8000/api/v1 -e CASINOKING_TEST_DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking -e CASINOKING_SITE_ACCESS_PASSWORD=change-me casinoking-backend python -m pytest /workspace/tests -q`

## Structure

For a mentally ordered VS Code view without renaming physical folders, open `CasinoKing.code-workspace`.
The printable logical map is `docs/PROJECT_ROOT_TREE_EXPLAINED.csv`.

- `backend/`
  FastAPI modular monolith base with auth, wallet/ledger read APIs and Mines MVP backend flows.
- `frontend-v3/`
  The only application frontend: Site V3 public renderer, player auth/account,
  admin/backoffice shell, game shells and same-origin game runtimes.
- `infra/docker/`
  Local Docker bootstrap for backend, frontend-v3, public edge, PostgreSQL, and Redis.
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
- Mines, BOXE and HI-LO public game shell/runtime routes under Site V3
- minimal admin backoffice console for users, ledger report, fairness, bonus grant and adjustment
- Mines backoffice draft/publish flow for rules HTML, published grid/mine subsets, mode labels and board assets
- local Docker development environment
- backend test coverage on contract, integration and concurrency scenarios

## Current Architecture Notes

- The platform backend already contains explicit boundaries for game launch and round settlement under `backend/app/modules/platform/`.
- Mines remains server-authoritative and uses the official runtime payout tables in `docs/runtime/`.
- `frontend-v3` is the only application frontend:
  - `frontend-v3/app/ui/casinoking-console.tsx` hosts the V3 admin/backoffice shell
  - `frontend-v3/app/ui/mines/mines-standalone.tsx` powers the Mines runtime
  - `frontend-v3/app/ui/mines/mines-board.tsx` is the extracted board renderer for Mines
  - BOXE and HI-LO runtimes live under `frontend-v3/app/runtime/*`
- The admin Mines backoffice is hosted inside the V3 admin shell.

## Current Documentation Entry Points

- Remembered project entry point: root `README.md`
- Fresh AI / handoff guide: `docs/AI_BOOTSTRAP_RUNBOOK.md`
- Project documentation map: `docs/README.md`
- Source hierarchy: `docs/SOURCE_OF_TRUTH.md`
- Task guardrails: `docs/TASK_EXECUTION_GUARDRAILS.md`
- Local smoke suite: `docs/LOCAL_SMOKE_SUITE.md`
- Mines architecture atlas: `docs/ARCHITECTURE_ATLAS_MINES.md`
- Platform/frontend architecture atlas: `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- Documentation maintenance rules: `docs/DOCUMENTATION_MAINTENANCE.md`

## Intentionally Still Outside Scope

- full admin interface and role-specific admin auth UX
- promotions and bonus workflows beyond bootstrap placeholders
- reporting and reconciliation views
- advanced fairness evolution and board reveal policy
- production-grade frontend UX and navigation
