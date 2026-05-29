Status: ACTIVE
Last meaningful update: 2026-05-29

# Site V3 - V1 Retirement Plan

## 0. Goal

Site V3 must become the only player-facing CasinoKing system. V1 and V2 must
not survive as parallel products.

This does not mean deleting working runtime/admin code in one unsafe step. It
means converting every V1 surface into either:

- Site V3-owned public route;
- internal admin/runtime host with explicit temporary contract;
- migrated V3 runtime;
- deleted code after parity tests are green.

## 1. Current Residual V1 Inventory

| Residual | Current owner | Public status | Retirement rule |
| --- | --- | --- | --- |
| Public root `:3000` | Site V3 edge | V3-owned | Keep. |
| Login/register/account on `:3000` | `frontend-v3` | V3-owned | Keep. |
| Game shells `/mines`, `/boxe`, `/hi-lo` on `:3000` | `frontend-v3` | V3-owned | Keep. |
| Admin `/admin/**` | `frontend/` | Proxied behind edge | Migrate or split in a dedicated admin WP. |
| Legacy runtime `/legacy-games/mines` | `frontend/` game runtime | Internal iframe only | Extract/rewrite next. BOXE moved in WP-MIG4D and HI-LO moved in WP-MIG4E. |
| V1 direct `:3002` root | `frontend/` | Internal debug only | WP-MIG4B redirects `/` to `/admin`; no V1 player shell mounted. |
| V1 direct `:3002` auth/account routes | `frontend/` | Direct debug only | WP-MIG4A redirects to Site V3. |
| V1 direct `:3002` game routes | `frontend/` game runtime / handoff | Direct debug/runtime | BOXE and HI-LO redirect to Site V3 after WP-MIG4D/E; Mines stays until its runtime extraction slice. |
| `frontend-v2/` | removed lab | none | Done; do not restore. |

## 2. Non-Negotiables

- No wallet, ledger, settlement, payout, RNG, fairness or game math changes in
  a retirement slice unless that slice is explicitly scoped for them.
- No hidden second login/register/account product.
- No deletion of a game runtime until browser smoke, replay smoke and contract
  parity for that game are green.
- No broad rename that makes Git noisy without reducing runtime ownership.
- Admin and public player UX must remain separate, even if they share the same
  public edge origin locally.

## 3. WP-MIG4A - Direct V1 Player Route Handoff

Status: implemented first slice 2026-05-29.

What changed:

- `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx` and
  `frontend/app/account/page.tsx` now redirect to Site V3 using
  `NEXT_PUBLIC_SITE_V3_BASE_URL`;
- query parameters are preserved, including `return_to`, `locale` and future
  system-page params;
- V1 player auth/account React components are left in place for now because
  deleting them safely requires a follow-up inventory of legacy console/debug
  references.

Why this matters:

- Direct V1 no longer presents login/register/account as a second player
  product;
- public ownership is now unambiguous: Site V3 owns player auth/account shell;
- the V1 app moves closer to a temporary admin + game-runtime host.

Out of scope:

- no game runtime movement;
- no admin movement;
- no backend auth/register changes;
- no document/KYC persistence.

## 4. Retirement Slices

### WP-MIG4B - Admin Host Isolation

Status: implemented first slice 2026-05-29.

Goal: make the remaining `frontend/` app explicit as an internal admin/runtime
host, not "the old site".

What changed:

- `frontend/app/(player)/page.tsx` no longer mounts `PlayerLobbyPage`;
- direct V1 `:3002/` redirects to `/admin`;
- the old `(player)` layout was removed so the direct root no longer wraps a
  player shell;
- `PlayerLobbyPage` remains in the tree as quarantined legacy code because some
  historical/browser tests and old docs still reference it; it is not mounted
  as the V1 direct root anymore;
- doctor/smoke/docs now describe `:3002` as an internal admin/runtime host;
- `/admin/**` remains stable on the public edge and direct V1 host.

Why this matters:

- Site V3 is now the only mounted public player homepage/lobby;
- V1 direct cannot be mistaken for a second player product;
- the next V1 work can focus on runtime extraction instead of visual cleanup.

Out of scope:

- no admin auth, RBAC, finance, wallet, ledger or gameplay changes;
- no deletion of legacy runtime routes;
- no deletion of quarantined V1 player components until their remaining tests
  and references are migrated or retired.

Stop before code if the slice would require changing admin auth, RBAC or
financial admin semantics.

### WP-MIG4C - Runtime Extraction Contract

Status: implemented first slice 2026-05-29 in
`docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md`.

Goal: define the exact contract for moving one game runtime out of V1 without
changing gameplay semantics.

Output first slice:

- per-game file inventory for Mines, BOXE and HI-LO frontend runtime;
- iframe/embed message parity contract;
- launch token/table-session/account-return parity gates;
- replay and account-history parity gates;
- target placement decision: migrate runtime islands into `frontend-v3` under
  `/runtime/{game}`, one game at a time;
- recommended migration order: BOXE first, then HI-LO, then Mines.

Default CTO recommendation: extract one game at a time. Start with BOXE because
it is much smaller than Mines but still exercises launch, demo, real mode, table
gate, close and replay/account history. Mines moves last because it has the
largest runtime and broadest legacy test debt.

### WP-MIG4D/E/F - Game Runtime Migration

Order decided by WP-MIG4C: BOXE first, then HI-LO, then Mines.

WP-MIG4D first slice is implemented for BOXE:

- `frontend-v3/app/runtime/boxe/page.tsx` mounts the BOXE runtime island;
- `frontend-v3/app/boxe/page.tsx` keeps the public Site V3 shell and points its
  iframe to `/runtime/boxe`;
- public edge removes `/legacy-games/boxe` and serves `/runtime/boxe` from
  `frontend-v3`;
- direct V1 `/boxe` redirects to Site V3 preserving query parameters;
- backend BOXE endpoints, wallet, ledger, payout, RNG, fairness and math are
  unchanged.

WP-MIG4E first slice is implemented for HI-LO:

- `frontend-v3/app/runtime/hi-lo/page.tsx` mounts the HI-LO runtime island;
- `frontend-v3/app/hi-lo/page.tsx` keeps the public Site V3 shell and points
  its iframe to `/runtime/hi-lo`;
- public edge removes `/legacy-games/hi-lo` and serves `/runtime/hi-lo` from
  `frontend-v3`;
- direct V1 `/hi-lo` redirects to Site V3 preserving query parameters;
- backend HI-LO endpoints, wallet, ledger, payout, RNG, fairness and math are
  unchanged.

Each game slice must:

- move the runtime route away from `frontend/`;
- keep API calls unchanged unless explicitly scoped;
- keep storage namespace compatibility or provide migration;
- pass browser smoke for demo, real/table gate, close/back-to-site and replay;
- only then remove the corresponding `/legacy-games/{game}` edge route.

### WP-MIG4G - Remove V1 Service

Only after admin and all game runtimes are migrated:

- remove `frontend` from the public stack;
- remove `:3002` direct frontend from doctor/smoke;
- delete obsolete V1 player shell code;
- delete `/legacy-games/*` routes;
- update architecture atlas, README, local smoke suite and roadmap.

## 5. Registration And Account Roadmap

Registration is already a Site V3 system page:

- `/register` lives in `frontend-v3`;
- the `register` CMS system page can mount `system_registration_form`;
- the module controls copy, optional field visibility, document-step gate,
  legal note and post-register path;
- submit still uses `/auth/register`.

Future identity/KYC work is a separate WP:

- real document upload/storage;
- consent checkboxes with audit;
- backoffice review states;
- player profile editing;
- admin-safe identity view.

Do not hide those future features inside the current registration CMS slice.

## 6. Capability Matrix

| Capability | DB | Backend/API | Admin UI | Public UI | Test | Docs | State | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1 direct auth/account handoff | none | none | none | V1 direct redirects to V3 | contract + smoke | this plan + roadmap | Green first slice | Removes second player product without deleting runtime/admin. |
| Admin host isolation | none | none | V1 admin host clarified | V1 direct root redirects to `/admin` | contract/smoke/doctor | atlas + README + smoke docs | Green first slice | `PlayerLobbyPage` quarantined, not mounted as direct root; no RBAC/finance change. |
| Runtime extraction contract | none | no semantic change | none | target `/runtime/{game}` chosen | contract tests | runtime contract + game atlas + this plan | Green first slice | Required before moving any game. |
| Mines runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Next recommended | Largest runtime and broadest legacy test debt. |
| BOXE runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Green first slice | Runtime island lives in `frontend-v3`; no backend/game math change. |
| HI-LO runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Green first slice | Runtime island lives in `frontend-v3`; no backend/game math change. |
| V1 service removal | none | none | migrated admin | no legacy iframe | doctor/smoke/build | README/atlas | Blocked | Last step only. |
