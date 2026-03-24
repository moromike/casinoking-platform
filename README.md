# CasinoKing

Initial repository bootstrap aligned with the project documents in `docs/`.

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

## Structure

- `backend/`
  FastAPI application skeleton for the modular monolith.
  Includes initial database bootstrap boundaries and SQL-first migration scaffold.
- `frontend/`
  Next.js application skeleton for the web UI.
- `infra/docker/`
  Local Docker bootstrap for backend, frontend, PostgreSQL, and Redis.
- `games/mines/`
  Separable game module scaffold for Mines.
- `tests/`
  Root test layout for unit, integration, contract, and concurrency suites.
- `docs/`
  Canonical and operational project documentation.

## Intentionally Empty In This Bootstrap

- Wallet and ledger business logic
- Auth flows
- Database schema and migrations content
- Definitive financial schema DDL
- Promotions, admin, and reporting logic
- Mines session engine, payout engine, and runtime integration
- API contracts beyond minimal health bootstrap
- Frontend product screens and game UI behavior

This pass prepares only the technical skeleton and module boundaries required to start implementation incrementally.
