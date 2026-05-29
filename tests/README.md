# Tests

Root test layout aligned with Documento 09 v2.

## Planned suites

- `unit/`
  Pure logic tests.
- `integration/`
  Service and database integration tests.
- `contract/`
  API behavior and payload tests.
- `concurrency/`
  Race-condition and idempotency tests.

## Current Status

The test suites now cover:
- contract checks for auth, wallet detail, ledger and Mines API behavior
- contract checks for password reset auth endpoints
- contract checks for Mines fairness current config
- contract checks for owner/admin session and ledger access
- contract checks for owner-only session fairness metadata
- contract checks for admin-only fairness rotate
- contract checks for admin-only fairness verify
- contract checks for admin authorization and idempotency requirements
- contract checks for admin-only suspend authorization
- contract checks for admin-only ledger reporting
- integration checks for signup, wallet detail, ledger, and Mines financial flows
- integration checks for password reset token consumption and credential update
- integration checks for zero wallet/ledger drift after critical flows
- integration checks for seeded fairness metadata persistence
- integration checks for fairness seed rotation and new-session adoption
- integration checks for fairness verification across seed rotations
- integration checks for admin suspend and blocked follow-up access
- integration checks for admin ledger reporting, transaction drill-down, and reconciliation view
- frontend smoke checks on the public edge Site V3 homepage, V1 direct root
  redirect to `/admin`, Site V3 Mines/account routes, V1 direct auth/account
  redirects, and `/admin`
- integration checks for admin bonus grants and manual adjustments
- concurrency checks for duplicate start, duplicate reveal, parallel reveals, double cashout, duplicate admin bonus grant and admin adjustment
- concurrency checks for Mines cashout/start/reveal state coherence across parallel requests
- concurrency checks for duplicate fairness rotation with same idempotency key
- unit checks for migration runner legacy backfill and ordered application
- unit checks for deterministic seeded board derivation

Default local targets:
- API: `http://localhost:8000/api/v1`
- public edge: `http://localhost:3000`
- V1 frontend direct: `http://localhost:3002`
- Site V3 frontend direct: `http://localhost:3001`
- DB: `postgresql://casinoking:casinoking@localhost:5433/casinoking`

When tests run inside the backend container, the suite automatically falls back to `DATABASE_URL` from the service environment.

Optional env vars:
- `CASINOKING_API_BASE_URL`
- `CASINOKING_FRONTEND_BASE_URL`
- `CASINOKING_PUBLIC_EDGE_BASE_URL`
- `CASINOKING_V1_FRONTEND_BASE_URL`
- `CASINOKING_SITE_V3_FRONTEND_BASE_URL`
- `CASINOKING_PUBLIC_V1_BASE_URL`
- `CASINOKING_PUBLIC_SITE_V3_BASE_URL`
- `CASINOKING_TEST_DATABASE_URL`
- `CASINOKING_SITE_ACCESS_PASSWORD`
