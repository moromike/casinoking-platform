# Backend

FastAPI bootstrap for the CasinoKing modular monolith.

Included here:
- application entrypoint
- API router bootstrap
- health endpoints only
- domain package boundaries for future modules
- database bootstrap boundary
- SQL-first migrations scaffold

Intentionally not implemented:
- auth, wallet, ledger, promotions, games, admin, reporting logic
- database access logic
- definitive schema DDL
- executable financial migrations
