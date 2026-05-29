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
| Admin `/admin/**` | `frontend-v3` | V3-owned | Keep; generic `/admin`, `/admin/site-v3` and `/admin/games/**` are V3-owned after WP-MIG5E. |
| Game runtimes `/runtime/mines`, `/runtime/boxe`, `/runtime/hi-lo` | `frontend-v3` runtime islands | V3-owned internal iframe routes | Keep; BOXE moved in WP-MIG4D, HI-LO in WP-MIG4E, Mines in WP-MIG4F. |
| Static app assets `/_next`, favicon, `/game-assets`, `/brand` | `frontend-v3/public` plus V3 Next output | V3-owned | WP-MIG5F moved the remaining public static routes away from V1. |
| V1 direct `:3002` service | removed from Docker stack | none | WP-MIG6 first slice removes the service, port and doctor/smoke checks. `frontend/` remains only as quarantined legacy source. |
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
- `/admin/**` remains stable on the public edge; direct V1 admin routes are
  temporary redirects once their V3 owner exists.

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

WP-MIG4F first slice is implemented for Mines:

- `frontend-v3/app/runtime/mines/page.tsx` mounts the Mines runtime island;
- `frontend-v3/app/mines/page.tsx` keeps the public Site V3 shell and points
  its iframe to `/runtime/mines`;
- public edge removes `/legacy-games/mines` and serves `/runtime/mines` from
  `frontend-v3`;
- direct V1 `/mines` redirects to Site V3 preserving query parameters;
- backend Mines endpoints, wallet, ledger, payout, RNG, fairness and math are
  unchanged.

Each game slice must:

- move the runtime route away from `frontend/`;
- keep API calls unchanged unless explicitly scoped;
- keep storage namespace compatibility or provide migration;
- pass browser smoke for demo, real/table gate, close/back-to-site and replay;
- only then remove the corresponding `/legacy-games/{game}` edge route.

### WP-MIG5 - Admin-Only V1 Retirement

Status: code slices through WP-MIG5F implemented 2026-05-29 after
WP-MIG4F/WP-MIG5A. `/admin/**` and the remaining public static asset routes
are now V3-owned on the public edge.

Decision:

- the final local stack must have one frontend product app: `frontend-v3`;
- the public admin URL remains `/admin`;
- the implementation target is `frontend-v3/app/admin/**`, not a third
  frontend app;
- `frontend/` remains only as quarantined legacy source until WP-MIG6B retires
  or archives the remaining source references;
- the local Docker stack exposes no V1 direct frontend port after WP-MIG6.

This is a route-by-route strangler migration. Do not rewrite every admin screen
in one branch. Keep the backend APIs and admin semantics stable unless a slice
explicitly says otherwise.

#### Residual Admin Inventory

| Area | Current V1 entry/files | Migration target | Notes |
| --- | --- | --- | --- |
| Admin shell/home | `frontend-v3/app/admin/page.tsx`, `CasinoKingConsole`, `admin-shell-panel`, `admin-management`, `admin-my-space` | V3-owned | Implemented first slice. Edge routes generic `/admin` to V3; direct V1 `:3002/admin` redirects to the public edge route. |
| Site V3 CMS builder | `frontend-v3/app/admin/site-v3/page.tsx`, `frontend-v3/app/ui/site-v3-admin/**` | V3-owned | Implemented first. Edge routes `/admin/site-v3` to V3 before generic `/admin`; direct V1 `:3002/admin/site-v3` redirects to the public edge route. |
| Game catalog/title editor | `frontend-v3/app/admin/games/**`, `platform-catalog-panel`, `games/**`, `title-editor/**`, per-game backoffice editors | V3-owned | Implemented first slice. Edge routes `/admin/games/**` to V3 before generic `/admin`; direct V1 `:3002/admin/games/**` redirects to the public edge route. Backoffice editor folders are admin-only (`boxe-backoffice`, `hi-lo-backoffice`, `mines-backoffice`) and do not change game math/runtime APIs. |
| Finance/player/replay/settings/audit | `admin-finance-panel`, `player-admin-panel`, `admin-platform-settings-panel`, `audit/admin-audit-log` | V3-owned through generic `/admin` shell | Implemented first slice by moving the existing frontend panels and preserving existing backend APIs/read-only semantics. |
| Static app assets | `frontend-v3/public` plus V3 Next output | V3-owned | Implemented in WP-MIG5F. Edge now routes `/_next`, `/game-assets`, `/brand` and favicon to `frontend-v3`; game runtime image paths keep working under `:3000`. |
| Direct debug host | removed from compose | none | Implemented in WP-MIG6 first slice; no public edge route depends on V1 after WP-MIG5F. |

#### Work Packages

WP-MIG5A - Admin Ownership Contract And Route Map

- output: this admin-only plan plus tests that make the remaining V1 dependency
  explicit;
- define the admin route families and final owners;
- assert no player public route is V1-owned;
- assert `/legacy-games/*` is gone;
- assert `/admin/**` is no longer allowed to proxy to `frontend` after the
  final admin slice.

WP-MIG5B - V3 Admin Shell Foundation

Status: first slice implemented 2026-05-29 for `/admin/site-v3`.

- created the V3 admin route foundation under `frontend-v3/app/admin/site-v3`;
- added a minimal admin session/login shell using the existing
  `/admin/auth/login` and `/admin/auth/me` APIs plus isolated admin storage
  keys;
- kept `/admin/site-v3` stable on the public edge;
- did not move the generic `/admin` landing yet in this slice;
- no finance, wallet, ledger, game math, payout or RNG changes.

WP-MIG5C - Move Site V3 CMS Admin First

Status: first slice implemented 2026-05-29.

- `site-v3-admin/**` now exists in `frontend-v3/app/ui/site-v3-admin/**`;
- `/admin/site-v3` routes to `frontend-v3` from edge before the generic
  `/admin` V1 proxy;
- direct V1 `:3002/admin/site-v3` redirects to the public edge route;
- V3 API client supports the Site V3 asset upload form request path;
- contract coverage asserts that the public renderer remains public-only while
  the admin sources live in explicit admin folders;
- Docker/browser smoke remains required after each served rebuild before
  deleting the old copied V1 UI files.

WP-MIG5D - Move Game Catalog And Title Editors

Status: first slice implemented 2026-05-29.

- `/admin/games`, `/admin/games/{engine}` and
  `/admin/games/{engine}/titles/{title_code}` live in `frontend-v3`;
- `platform-catalog-panel`, `games/**`, `title-editor/**`,
  `boxe-backoffice/**`, `hi-lo-backoffice/**` and `mines-backoffice/**` live
  in explicit admin UI folders under `frontend-v3/app/ui`;
- the V3 admin games shell uses the existing `/admin/auth/login` and
  `/admin/auth/me` APIs and the existing title/catalog/admin game endpoints;
- direct V1 `:3002/admin/games/**` routes redirect to the public Site V3 edge;
- the public renderer contract excludes the admin-only folders and keeps
  `frontend-v3/app/ui/mines` runtime-only;
- backend endpoints, title config payloads, wallet, ledger, payout, RNG,
  fairness and game runtime semantics were not changed.

WP-MIG5E - Move Finance, Player Admin, Settings And Audit

Status: first slice implemented 2026-05-29.

- generic `/admin` lives in `frontend-v3/app/admin/page.tsx`;
- finance/replay, player admin, platform settings, operational audit, My Space
  and Administrators panels live in `frontend-v3/app/ui/**`;
- edge routes `/admin` to `frontend-v3`;
- direct V1 `:3002/admin` redirects to the public Site V3 edge;
- existing backend endpoints and admin storage keys are reused;
- wallet, ledger, settlement, payout, retention, RBAC, RNG and fairness
  semantics were not changed.

WP-MIG5F - Static Asset Ownership Extraction

Status: implemented first slice 2026-05-29.

- removed the remaining public edge dependency on V1 for `/_next`, favicon,
  `/game-assets` and `/brand`;
- selected `frontend-v3/public` as the explicit owner for favicon, provider
  brand media and game runtime image assets;
- kept V3 Next build assets owned by `frontend-v3` through the existing
  `/site-v3-assets/_next/` prefix and routed root `/_next/` to V3 as a
  compatibility/static fallback;
- removed `casinoking_frontend_v1` from the edge config and removed the edge
  dependency on the `frontend` service;
- added contract and smoke coverage for V3-owned static assets.

WP-MIG6 - Remove V1 Service

Status: implemented first slice 2026-05-29.

- removed `frontend` from the Docker Compose stack;
- deleted the obsolete `infra/docker/frontend.Dockerfile`;
- removed `FRONTEND_PORT` and `NEXT_PUBLIC_V1_BASE_URL` from the local env
  template and V3 runtime config;
- removed `:3002` direct frontend checks from doctor and smoke;
- kept `frontend/` source as quarantined legacy source because several
  contracts still read redirect helper files and legacy source inventory.

WP-MIG6B - Retire Or Archive Legacy Source

Next slice after WP-MIG6 first slice:

- migrate or delete contract assertions that still read `frontend/app/**`;
- archive/delete obsolete V1 player shell code after proving no runtime/admin
  route uses it;
- delete obsolete V1 game runtime code and any remaining source-only
  `/legacy-games/*` references;
- update architecture atlas, README, local smoke suite and roadmap again.

#### Stop Before Code

Stop before implementation if a slice would require any of the following
without a dedicated plan:

- changing admin auth/RBAC semantics;
- changing wallet, ledger, settlement, payout, RNG or fairness;
- changing title config schema or game math;
- deleting static game assets before their new owner is verified;
- replacing the whole admin UI at once instead of migrating route families.

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
| Mines runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Green first slice | Last player-facing game runtime moved out of V1. |
| BOXE runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Green first slice | Runtime island lives in `frontend-v3`; no backend/game math change. |
| HI-LO runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Green first slice | Runtime island lives in `frontend-v3`; no backend/game math change. |
| Admin ownership contract | none | none | route family inventory | no player route change | contract/doc check | this plan + roadmap | Green first slice | WP-MIG5A defines the only safe path to remove `frontend`. |
| V3 admin shell foundation | none | existing admin APIs | V3 `/admin/site-v3` auth shell | none | build + contract + smoke | README/atlas/manual | Green first slice | Uses existing admin login/me APIs and admin storage keys. |
| Site V3 CMS admin migration | none | existing Site V3 admin APIs | `/admin/site-v3` in `frontend-v3` | none | contract green | manual + roadmap | Green first slice | Edge routes this admin family to V3; V1 direct route redirects. |
| Game catalog/title editor admin migration | no game math/schema change | existing title/admin APIs | `/admin/games/**` in `frontend-v3` | none | frontend-v3 build + contract green; browser smoke after rebuild | atlas + manual | Green first slice | Mines/BOXE/HI-LO title config editors moved as admin-only UI; runtime folders stay separate. |
| Finance/player/settings/audit admin migration | no wallet/ledger change | existing finance/settings APIs | generic `/admin` in `frontend-v3` | none | frontend-v3 build + route/redirect contract; smoke after rebuild | atlas + manual | Green first slice | Existing admin panels moved as frontend ownership only; no finance/RBAC semantics changed. |
| Static asset ownership extraction | none | static serving only | admin/public assets load from V3 owner | game images still load | contract + HTTP smoke | README/atlas | Green first slice | `/_next`, favicon, `/game-assets` and `/brand` no longer proxy to V1; files live in `frontend-v3/public` where applicable. |
| V1 service removal | none | none | migrated to `frontend-v3` | no legacy iframe and no `:3002` service | doctor/smoke/build | README/atlas | Green first slice | Public edge no longer depends on V1 and the local stack no longer starts `frontend`; remaining work is source quarantine cleanup in WP-MIG6B. |
