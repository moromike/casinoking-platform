Status: ACTIVE
Last meaningful update: 2026-05-29

# CasinoKing Local Smoke Suite

## Purpose

This document defines the canonical local smoke suite used by the
self-bootstrapping workflow.

The smoke suite is intentionally small. It verifies that the Dockerized local
stack can serve the public edge, the remaining V1 direct debug/admin/runtime
host, Site V3 player/game shells and the Site V3 direct renderer through the backend test image and Docker
network. It is not a replacement for contract, integration,
concurrency, browser, visual, wallet, ledger, or game-runtime test suites.

## Canonical Command

Run the local doctor first:

```powershell
.\scripts\ck-doctor.ps1
```

Then run the canonical smoke suite:

```powershell
.\scripts\ck-test-smoke.ps1
```

Both commands must pass before a fresh local environment is considered
bootstrap-verified.

## Canonical Target

The canonical smoke target is:

```text
tests/integration/test_frontend_smoke.py
```

The script runs this target inside the `casinoking-backend` Docker image on the
`casinoking_default` network, with:

```text
CASINOKING_API_BASE_URL=http://backend:8000/api/v1
CASINOKING_FRONTEND_BASE_URL=http://edge
CASINOKING_PUBLIC_EDGE_BASE_URL=http://edge
CASINOKING_V1_FRONTEND_BASE_URL=http://frontend:3000
CASINOKING_SITE_V3_FRONTEND_BASE_URL=http://frontend-v3:3001
CASINOKING_PUBLIC_V1_BASE_URL=http://localhost:3000
CASINOKING_PUBLIC_SITE_V3_BASE_URL=http://localhost:3000
CASINOKING_TEST_DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking
CASINOKING_SITE_ACCESS_PASSWORD=change-me
```

## What It Covers

The smoke suite verifies:

- the public edge homepage returns HTTP 200 and serves Site V3;
- the direct V1 frontend root redirects to `/admin`, confirming it is an
  internal admin/runtime host and not a player homepage;
- the Site V3 public renderer homepage and `/pages/home` alias return HTTP 200;
- the Site V3 public header links to same-origin login with a `return_to`
  target back to the public Site V3 origin;
- contract tests lock that Site V3 player login/register/account routes preserve
  sanitized `return_to`, while V1 direct login/register/account redirect to
  Site V3 and preserve query parameters;
- a focused Playwright browser smoke verifies the real Site V3 login ->
  Site V3 account-aware header -> Site V3 account logout -> Site V3 guest return
  flow with a temporary player;
- the same focused browser smoke verifies that Site V3 game launch links carry a
  `return_to` target and open the Site V3 game shell with a same-origin legacy
  runtime iframe;
- main Site V3 player/account/admin route shells return HTTP 200 through the
  public edge;
- V1 direct `/login`, `/register` and `/account` return redirects to Site V3;
- V1 direct `/` returns a redirect to `/admin`;
- Mines public game shell and legacy runtime route shells return HTTP 200 and
  stay isolated from player/admin shell copy;
- register route does not expose the default site access password;
- favicon route is served.

## What It Does Not Cover

The smoke suite does not verify:

- hydrated browser behavior;
- Playwright visual or interaction flows;
- wallet, ledger, payout, settlement, RNG, or fairness correctness;
- full admin authentication flows;
- Site V3 product walkthrough beyond route-shell availability;
- Mines legacy full browser smoke debt;
- production readiness.

Those checks belong to their dedicated suites or work packages.

## Maintenance Rules

Update this document and `scripts/ck-test-smoke.ps1` together when the canonical
smoke target changes.

Keep the canonical smoke suite stable and fast. It should fail only when local
bootstrap-critical route shells are unavailable or when a deliberate route-shell
contract changes without the test being updated.

Do not add broad browser, visual, accounting, or game-runtime assertions here.
Open a dedicated suite or work package for those surfaces.
