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
| Admin `/admin/**` | `frontend/` | Proxied behind edge | Migrate by WP-MIG5 route slices into `frontend-v3/app/admin/**`; do not remove `frontend` until every admin slice is green. |
| Game runtimes `/runtime/mines`, `/runtime/boxe`, `/runtime/hi-lo` | `frontend-v3` runtime islands | V3-owned internal iframe routes | Keep; BOXE moved in WP-MIG4D, HI-LO in WP-MIG4E, Mines in WP-MIG4F. |
| V1 direct `:3002` root | `frontend/` | Internal debug only | WP-MIG4B redirects `/` to `/admin`; no V1 player shell mounted. |
| V1 direct `:3002` auth/account routes | `frontend/` | Direct debug only | WP-MIG4A redirects to Site V3. |
| V1 direct `:3002` game routes | `frontend/` handoff | Direct debug only | Mines, BOXE and HI-LO redirect to Site V3 after WP-MIG4D/E/F. |
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

Status: planned 2026-05-29 after WP-MIG4F. This is the next real block.

Decision:

- the final local stack must have one frontend product app: `frontend-v3`;
- the public admin URL remains `/admin`;
- the implementation target is `frontend-v3/app/admin/**`, not a third
  frontend app;
- `frontend/` remains temporarily only while specific admin route families are
  migrated and verified;
- `:3002` remains a debug/admin host until the last admin route family is gone.

This is a route-by-route strangler migration. Do not rewrite every admin screen
in one branch. Keep the backend APIs and admin semantics stable unless a slice
explicitly says otherwise.

#### Residual Admin Inventory

| Area | Current V1 entry/files | Migration target | Notes |
| --- | --- | --- | --- |
| Admin shell/home | `frontend/app/admin/page.tsx`, `CasinoKingConsole`, `admin-shell-panel`, `admin-management`, `admin-my-space` | `frontend-v3/app/admin/page.tsx` + V3 admin shell | Needs auth/token handling, navigation and base layout first. |
| Site V3 CMS builder | `frontend/app/admin/site-v3/page.tsx`, `frontend/app/ui/site-v3-admin/**` | `frontend-v3/app/admin/site-v3/**`, `frontend-v3/app/ui/site-v3-admin/**` | First code slice: it manages V3 and is the least conceptually tied to V1 player UI. |
| Game catalog/title editor | `frontend/app/admin/games/**`, `platform-catalog-panel`, `games/**`, `title-editor/**`, per-game backoffice editors | `frontend-v3/app/admin/games/**` + copied/adapted admin UI | Larger slice; touches game config editors but must not change math/runtime APIs. |
| Finance/player/replay/settings/audit | `admin-finance-panel`, `player-admin-panel`, `admin-platform-settings-panel`, `audit/admin-audit-log` | `frontend-v3/app/admin/...` | Highest-risk admin slice because finance/replay/settings semantics must stay read-only/unchanged. |
| Static app assets | edge `/_next`, `/game-assets`, `/brand`, favicon currently served from V1 | V3 public/static or backend/static asset host | Must be solved before removing `frontend`; game runtime image paths depend on it. |
| Direct debug host | `:3002` | removed from stack after parity | Keep only until all admin and static dependencies are migrated. |

#### Work Packages

WP-MIG5A - Admin Ownership Contract And Route Map

- output: this admin-only plan plus tests that make the remaining V1 dependency
  explicit;
- define the admin route families and final owners;
- assert no player public route is V1-owned;
- assert `/legacy-games/*` is gone;
- assert `/admin/**` is the only public edge route still allowed to proxy to
  `frontend`.

WP-MIG5B - V3 Admin Shell Foundation

- create the V3 admin route foundation under `frontend-v3/app/admin/**`;
- add a minimal admin shell, navigation container and API/auth helper parity;
- keep `/admin` public URL stable;
- initially route only a harmless diagnostics/landing/admin entry to V3, or use
  a prefixed slice such as `/admin/site-v3` if route safety requires it;
- no finance, wallet, ledger, game math, payout or RNG changes.

WP-MIG5C - Move Site V3 CMS Admin First

- move `site-v3-admin/**` from `frontend/` to `frontend-v3/`;
- route `/admin/site-v3` to `frontend-v3` from edge before the generic
  `/admin` V1 proxy;
- make direct V1 `:3002/admin/site-v3` redirect to the public edge route;
- verify draft save, validation, publish, Module Studio, asset upload/picker
  and preview live;
- after green QA, delete the V1 mounted Site V3 admin route.

WP-MIG5D - Move Game Catalog And Title Editors

- move `/admin/games`, `/admin/games/{engine}` and title editor routes;
- migrate `platform-catalog-panel`, `games/**`, `title-editor/**` and
  per-game backoffice editor dependencies;
- preserve existing backend endpoints and title config payloads;
- add contract/smoke coverage for Mines, BOXE and HI-LO title editor entry;
- do not change game runtime semantics.

WP-MIG5E - Move Finance, Player Admin, Settings And Audit

- move finance/replay, player admin, platform settings and audit views;
- treat this as the highest-risk admin UI slice;
- require read-only finance/replay smoke and existing settings contracts;
- do not alter wallet, ledger, settlement, payout or retention behavior.

WP-MIG5F - Static Asset Ownership Extraction

- remove remaining dependency on V1 for `/_next`, favicon, `/game-assets` and
  `/brand`;
- choose one explicit owner per asset class:
  `frontend-v3/public`, backend static storage, or nginx static volume;
- verify game runtime images and public CMS media still load under `:3000`;
- only then prepare the service removal diff.

WP-MIG6 - Remove V1 Service

Only after WP-MIG5B-F are green:

- remove `frontend` from the public stack;
- remove `:3002` direct frontend from doctor/smoke;
- remove the public edge upstream `casinoking_frontend_v1`;
- delete obsolete V1 player shell code;
- delete obsolete V1 game runtime code and any remaining `/legacy-games/*`
  references;
- update architecture atlas, README, local smoke suite and roadmap.

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
| Admin ownership contract | none | none | route family inventory | no player route change | contract/doc check | this plan + roadmap | Planned | WP-MIG5A defines the only safe path to remove `frontend`. |
| V3 admin shell foundation | none | existing admin APIs | V3 `/admin` shell | none | build + browser smoke | README/atlas/manual | Planned | First code slice before moving real admin features. |
| Site V3 CMS admin migration | none | existing Site V3 admin APIs | `/admin/site-v3` in `frontend-v3` | none | draft/validate/publish/preview smoke | manual + roadmap | Planned | Recommended first migrated admin feature family. |
| Game catalog/title editor admin migration | no game math/schema change | existing title/admin APIs | `/admin/games/**` in `frontend-v3` | none | title editor smoke per game | atlas + manual | Planned | Must preserve Mines/BOXE/HI-LO title config semantics. |
| Finance/player/settings/audit admin migration | no wallet/ledger change | existing finance/settings APIs | V3 admin views | none | read-only finance/settings smoke | atlas + manual | Planned | Highest-risk admin UI family; keep read-only semantics stable. |
| Static asset ownership extraction | none | maybe static serving only | admin/public assets load from non-V1 owner | game images still load | HTTP + browser asset checks | README/atlas | Planned | Required before removing the V1 service. |
| V1 service removal | none | none | migrated to `frontend-v3` | no legacy iframe | doctor/smoke/build | README/atlas | Blocked by WP-MIG5 | Game runtimes no longer block it; admin/static assets remain the residual owners. |
