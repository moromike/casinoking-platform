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
| Legacy runtime `/legacy-games/*` | `frontend/` game runtime | Internal iframe only | Extract/rewrite one game at a time. |
| V1 direct `:3002` auth/account routes | `frontend/` | Direct debug only | WP-MIG4A redirects to Site V3. |
| V1 direct `:3002` game routes | `frontend/` game runtime | Direct debug/runtime | Keep until runtime extraction. |
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

## 4. Next Slices

### WP-MIG4B - Admin Host Isolation

Goal: make the remaining `frontend/` app explicit as an internal admin/runtime
host, not "the old site".

Expected work:

- inventory `frontend/app/ui/casinoking-console.tsx`, admin routes and player
  leftovers;
- remove or quarantine V1 public-player navigation that is no longer reachable
  through the public edge;
- update doctor/smoke wording so `:3002` is documented as internal debug host;
- keep `/admin/**` stable on the public edge.

Stop before code if the slice would require changing admin auth, RBAC or
financial admin semantics.

### WP-MIG4C - Runtime Extraction Contract

Goal: define the exact contract for moving one game runtime out of V1 without
changing gameplay semantics.

Expected work:

- per-game file inventory for Mines, BOXE and HI-LO frontend runtime;
- iframe/embed message parity contract;
- launch token/table-session/account-return parity tests;
- replay and account-history parity tests;
- target placement decision: `frontend-v3` runtime area or a dedicated internal
  runtime app behind the same V3 edge.

Default CTO recommendation: extract one game at a time. Mines first only if its
test surface is strongest; otherwise start with the smallest runtime that still
exercises launch, demo, real mode, close and replay.

### WP-MIG4D/E/F - Game Runtime Migration

Order should be decided after WP-MIG4C inventory.

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
| Admin host isolation | none expected | none expected | V1 admin host clarified | none | contract/smoke | atlas/manual if UI changes | Planned | Must not change RBAC/finance semantics. |
| Runtime extraction contract | none | no semantic change | none | game runtime target chosen | parity tests | game atlas + this plan | Planned | Required before moving any game. |
| Mines runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Planned | Only after contract. |
| BOXE runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Planned | Keep BOXE replay debt closed. |
| HI-LO runtime migration | no math/schema change | existing endpoints | none | V3/runtime route | browser + replay | atlas/game docs | Planned | Preserve current multiplier UX. |
| V1 service removal | none | none | migrated admin | no legacy iframe | doctor/smoke/build | README/atlas | Blocked | Last step only. |
