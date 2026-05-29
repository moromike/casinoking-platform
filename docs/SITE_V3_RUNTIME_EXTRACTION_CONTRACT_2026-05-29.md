Status: ACTIVE
Last meaningful update: 2026-05-29

# Site V3 - Runtime Extraction Contract

## 0. Scope

WP-MIG4C defines how CasinoKing moves Mines, BOXE and HI-LO runtime code out of
the remaining V1 frontend without changing gameplay semantics.

WP-MIG4D moved BOXE to the Site V3 runtime target. WP-MIG4E moved HI-LO to the
same target. Mines still follows this contract.

## 1. Non-Negotiables

- No backend wallet, ledger, settlement, payout, RNG, fairness or game math
  change in a runtime extraction slice.
- The public game shell stays Site V3-owned on `/mines`, `/boxe` and `/hi-lo`.
- The iframe host contract stays same-origin unless a later provider/integration
  WP explicitly changes it.
- A game runtime may leave V1 only after its demo, real/table gate,
  close/back-to-site and replay/account-history checks are green.
- Remove one `/legacy-games/{game}` edge route at a time, only after that game
  is served by a V3 runtime route and parity is verified.
- Do not keep two public products for the same game. During migration, one route
  is public shell, one route is internal runtime.

## 2. Target Placement Decision

Default target for the first migration: `frontend-v3`.

Target shape:

```text
frontend-v3/app/{game}/page.tsx
  -> Site V3 public shell
  -> iframe src /runtime/{game}

frontend-v3/app/runtime/{game}/page.tsx
  -> migrated game runtime island
```

Why this target:

- Site V3 already owns the public player/game shell;
- same-origin iframe remains simple through the existing edge;
- no third frontend service is needed before we know the real runtime split
  pressure;
- the V1 service can shrink game by game.

Temporary duplicate shared runtime helpers are allowed only as migration
scaffolding: a migrated V3 game may need a V3-local copy/promotion of the shared
boot helpers while non-migrated games still consume the V1 copy. The duplicate
must be deleted or consolidated when the last game leaves V1.

Do not introduce a workspace package or a new runtime service in the first game
slice unless `frontend-v3` cannot build or the bundle boundary becomes
materially unsafe.

## 3. Current Runtime Inventory

| Game | Public Site V3 shell | Current internal iframe route | V1 direct route | V1 runtime entry | Main runtime helpers |
| --- | --- | --- | --- | --- | --- |
| Mines | `frontend-v3/app/mines/page.tsx` | `/legacy-games/mines -> frontend:3000/mines` | `frontend/app/mines/page.tsx` | `frontend/app/ui/mines/mines-standalone.tsx` | `frontend/app/ui/mines/mines-gameplay.tsx`, `frontend/app/ui/mines/mines-replay-viewer.tsx`, `frontend/app/ui/game-runtime/**` |
| BOXE | `frontend-v3/app/boxe/page.tsx` | `/runtime/boxe -> frontend-v3:3001/runtime/boxe` | `frontend/app/boxe/page.tsx` redirects to Site V3 | `frontend-v3/app/runtime/boxe/page.tsx` -> `frontend-v3/app/ui/boxe/boxe-standalone.tsx` | `frontend-v3/app/ui/boxe/use-boxe-runtime.ts`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`, `frontend-v3/app/ui/boxe/boxe-replay-viewer.tsx`, `frontend-v3/app/ui/game-runtime/**` |
| HI-LO | `frontend-v3/app/hi-lo/page.tsx` | `/runtime/hi-lo -> frontend-v3:3001/runtime/hi-lo` | `frontend/app/hi-lo/page.tsx` redirects to Site V3 | `frontend-v3/app/runtime/hi-lo/page.tsx` -> `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx` | `frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts`, `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`, `frontend-v3/app/ui/hi-lo/hi-lo-replay-viewer.tsx`, `frontend-v3/app/ui/game-runtime/**` |

Shared runtime primitives currently still owned by V1 for Mines:

- `frontend/app/ui/game-runtime/game-boot-request.ts`
- `frontend/app/ui/game-runtime/game-storage.ts`
- `frontend/app/ui/game-runtime/use-game-launch-context.ts`
- `frontend/app/ui/game-runtime/use-game-embed-bridge.ts`
- `frontend/app/ui/game-runtime/game-boot-shell.tsx`
- `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx`
- `frontend/app/ui/game-runtime/game-table-balance-gate.tsx`
- `frontend/app/ui/game-runtime/game-control-rail.tsx`
- `frontend/app/ui/game-runtime/game-info-rules-modal.tsx`
- `frontend/app/ui/game-runtime/use-game-audio-preferences.ts`

BOXE and HI-LO now have V3-local copies under `frontend-v3/app/ui/game-runtime/**`,
`frontend-v3/app/ui/boxe/**` and `frontend-v3/app/ui/hi-lo/**`. That copy is
migration scaffolding until all game runtimes leave V1 or the shared runtime is
promoted into a real package.

Current storage namespaces are `mines`, `boxe` and `hi_lo`. Mines keeps its
legacy localStorage keys; BOXE and HI-LO use game-specific keys in both V1
legacy code and the V3-local runtime copies.

## 4. Iframe And Return Contract

The Site V3 shell must keep forwarding these query params into the runtime:

```text
mode
wallet_source
preview
preview_token
return_to
title_code
embed=1
embed_origin=<site-v3-origin>
```

The migrated runtime must continue to read:

- `title_code` through the existing boot request normalizer;
- `mode=demo` and `preview=1` as demo/preview mode;
- `wallet_source=real|bonus` for table gate hinting;
- `return_to` through the existing sanitized return helper;
- `embed=1` to enable iframe mode;
- `embed_origin` to scope postMessage.

Embed messages that must remain compatible:

| Direction | Message | Required payload |
| --- | --- | --- |
| game -> Site V3 host | `casinoking:game-close` | `{ type, gameCode }` |
| Site V3 host -> game | `casinoking:game-fullscreen-state` | `{ type, gameCode, active }` |
| legacy compatibility | `casinoking:{game}-close`, `casinoking:{game}-fullscreen-state` | Kept while admin/debug legacy launchers exist. |

## 5. Backend/API Contract

Runtime extraction does not move or rename backend endpoints.

Mines runtime APIs stay under:

- `/games/mines/config`
- `/games/mines/fairness/current`
- `/games/mines/launch-token`
- `/games/mines/launch/validate`
- `/games/mines/start`
- `/games/mines/reveal`
- `/games/mines/cashout`
- `/games/mines/sessions`
- `/games/mines/session/{id}`
- `/games/mines/session/{id}/fairness`
- `/games/mines/session/{id}/replay`
- `/table-sessions*`
- `/demo/token`, `/demo/launch`

BOXE runtime APIs stay under:

- `/games/boxe/config`
- `/games/boxe/start`
- `/games/boxe/reveal`
- `/games/boxe/cashout`
- `/games/boxe/sessions`
- `/games/boxe/round/{id}/replay`
- `/table-sessions*` with `game_code=boxe`
- `/auth/demo`
- `/wallets`

HI-LO runtime APIs stay under:

- `/games/hi-lo/config`
- `/games/hi-lo/active-round`
- `/games/hi-lo/start`
- `/games/hi-lo/predict`
- `/games/hi-lo/skip`
- `/games/hi-lo/cashout`
- `/games/hi-lo/sessions`
- `/games/hi-lo/round/{id}/replay`
- `/table-sessions*` with `game_code=hi_lo`
- `/auth/demo`
- `/wallets`

Account replay stays Site V3-owned and continues to call the same replay
endpoints from `frontend-v3/app/ui/player-account-page.tsx`.

## 6. Migration Order

Recommended order:

Current state:

1. BOXE - migrated in WP-MIG4D.
2. HI-LO - migrated in WP-MIG4E.
3. Mines - next remaining V1 game runtime.

Reasoning:

- BOXE is materially smaller than Mines but still exercises table gate, demo,
  real mode, close/back-to-site and replay/account history;
- BOXE replay visual debt was recently closed with a focused browser smoke, so
  it is a good first parity candidate;
- HI-LO followed once the first runtime island pattern was proven;
- Mines has the strongest and broadest smoke suite, but it is much larger and
  should move after the extraction pattern is stable.

This order can change only after a new evidence-based inventory, not because a
game "feels" simpler.

## 7. Required Gates Per Game

Each WP-MIG4D/E/F game migration must include:

- V3 runtime route exists under `/runtime/{game}`;
- Site V3 game shell iframe source switches from `/legacy-games/{game}` to
  `/runtime/{game}`;
- edge `/legacy-games/{game}` route is removed after parity is green;
- V1 direct `/{game}` route is deleted or redirected away from player runtime;
- no backend API endpoint is renamed;
- no storage key migration is required, or a scoped compatibility adapter is
  documented and tested;
- browser smoke for demo launch, real/table gate, close/back-to-site and replay
  passes;
- account-history replay smoke for that game passes;
- contract tests verify no `frontend-v3` runtime imports from `frontend/app`.

## 8. Legacy Test Debt

Several historical browser tests still point at `/mines` as if it were a direct
V1 runtime page. Since WP-MIG2, public `/mines` is the Site V3 shell and the V1
runtime is internal behind `/legacy-games/mines`.

Before migrating Mines, those tests must be split into:

- Site V3 shell tests, targeting `/mines`;
- internal runtime tests, targeting `/legacy-games/mines` while Mines remains
  V1-owned, then `/runtime/mines` after migration.

Do not use failing legacy direct-runtime tests as a reason to restore a V1
public player surface.

## 9. Capability Matrix

| Capability | DB | Backend/API | Admin UI | Public UI | Tests | Docs | State | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Runtime extraction contract | none | no semantic change | none | target `/runtime/{game}` decided | contract | this doc + retirement plan | Green first slice | Contract locked before moving games. |
| BOXE runtime migration | no schema/math change | existing endpoints | none | `/boxe` shell iframe -> `/runtime/boxe` | browser + account replay | atlas + this doc | Green first slice | Edge `/legacy-games/boxe` removed; V1 direct `/boxe` redirects to Site V3. |
| HI-LO runtime migration | no schema/math change | existing endpoints | none | `/hi-lo` shell iframe -> `/runtime/hi-lo` | browser + account replay | atlas + this doc | Green first slice | Edge `/legacy-games/hi-lo` removed; V1 direct `/hi-lo` redirects to Site V3. |
| Mines runtime migration | no schema/math change | existing endpoints | none | `/mines` shell iframe -> `/runtime/mines` | broad Mines browser + replay | Mines atlas + this doc | Next recommended | Largest runtime and broadest test debt. |
| Remove V1 game runtime routes | none | none | none | no `/legacy-games/{game}` for migrated game | doctor/smoke/build | README/atlas | Blocked per game | Only after each game is migrated. |

## 10. Next Prompt

Recommended next execution prompt:

```text
Implement WP-MIG4F first slice for Mines runtime extraction. Follow
docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md. Move only Mines runtime
to a Site V3 internal /runtime/mines route, keep backend endpoints unchanged,
split legacy Mines browser tests between Site V3 shell and internal runtime
coverage first, switch the Site V3 Mines shell iframe source only after parity
is green, remove only the Mines legacy edge route, and do not touch
wallet/ledger/payout/RNG.
```
