# Backend

FastAPI bootstrap for the CasinoKing modular monolith.

Included here:
- application entrypoint
- API router bootstrap
- health endpoints only
- site access public endpoint
- register and login public endpoints
- bearer-authenticated wallet read endpoints
- bearer-authenticated ledger read endpoints
- Mines config/start/reveal/cashout/session endpoints
- Mines fairness current endpoint
- Mines session fairness endpoint
- Mines fairness rotate endpoint (admin only)
- Mines fairness verify endpoint (admin only)
- admin users list endpoint
- admin ledger report endpoint
- admin wallet adjustment endpoint
- admin bonus grant endpoint
- local admin bootstrap tool
- domain package boundaries for future modules
- database bootstrap boundary
- SQL-first migrations scaffold
- first users/auth schema migration
- first financial-core schema migration
- initial system ledger account seed
- admin action audit schema foundation
- reconciliation-oriented integration and concurrency test support
- internal seeded fairness metadata persisted on game_sessions
- internal fairness seed rotations persisted for Mines

Intentionally not implemented:
- full promotions lifecycle, admin suspend flows and extended reporting logic
- general repository/query layer extraction
- audit_event table details beyond admin_actions
- JWT/session persistence
- password reset delivery flow
- admin UI and executable non-MVP posting flows

Local admin bootstrap:
- `docker exec casinoking-backend-1 python -m app.tools.bootstrap_local_admin --email admin@example.com --password StrongPass-Local123`
- If the user does not exist, the tool creates an admin with bootstrap wallets and signup credit.
- If the user already exists, the tool promotes it to `admin` and resets its password.
