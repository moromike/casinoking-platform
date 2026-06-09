Status: PHASE 3A DONE - STOP FOR CTO GATE
Date: 2026-05-30 / final capture 2026-05-31 00:40 Europe/Rome
Owner: CTO gate - Executor: Codex - Validation target: Michele on `http://localhost:3000`

# Site V3 Recovery Phase 3A Report

## Scope

Phase 3A was limited to residual stabilization:

- R2: restore embedded layout classes for the 3 game standalone shells.
- R1: restore missing scoped public player CSS from backup `6141c17`.
- R3: scoped admin/CMS polish for action alignment and compactness.
- Explicit replay verification for Mines, BOXE and HI-LO from runtime, player account history and Finance round detail.

Out of scope and not done:

- no module building / module editing feature work;
- no redesign;
- no host topbar/chrome above games;
- no game logic, RNG, payout, board, reveal, replay component rewrite;
- no backend GMP changes;
- no use of Michele's personal admin account.

## Baselines

| Surface | Baseline used |
| --- | --- |
| Public player login/register/account | backup `6141c17` worktree on `http://127.0.0.1:3101` |
| Admin / Finance / games | `main` screenshots from Phase 1 inventory |

Main artifact root:

- `artifacts/site_v3_recovery_phase3a_2026-05-30/`
- final JSON: `artifacts/site_v3_recovery_phase3a_2026-05-30/metadata/phase3a-capture-results.json`

## Files

Product files involved in Phase 3A:

- `frontend-v3/app/globals.css`
  - R1 public player CSS restored under `.site-v3-player-shell`.
  - R3 admin/CMS polish kept scoped under `.ck-admin-legacy-page` and `.site-v3-cms-admin-page`.
- `frontend-v3/app/ui/mines/mines-standalone.tsx`
  - R2 embedded classes present at lines 380 and 389.
- `frontend-v3/app/ui/boxe/boxe-standalone.tsx`
  - R2 embedded classes present at lines 162 and 170.
- `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx`
  - R2 embedded classes present at lines 187 and 194.

Artifact-only file:

- `artifacts/site_v3_recovery_phase3a_2026-05-30/metadata/phase3a_capture.py`

Note on final diff state: the 3 standalone files are marked modified by Git because of EOL/mixed working-tree state, but `git diff` shows no text hunk for them at final verification. The R2 lines above are present and were verified at runtime. `globals.css` contains the actual product CSS content diff for this phase.

## R2 - Games Embedded Layout

Fix target: use existing `*-page-shell-embedded` and `*-product-shell-embedded` classes only when `isEmbeddedView`, without reintroducing host topbar/chrome and without touching X styling.

| Game | Desktop | Mobile | Evidence | Status |
| --- | --- | --- | --- | --- |
| Mines | fits host/runtime viewport, audio visible, X visible | fits host/runtime viewport, audio visible, X detected by current selector scan | `side-by-side/game-mines-desktop-side-by-side.png`, `side-by-side/game-mines-mobile-side-by-side.png` | PASS |
| HI-LO | fits host/runtime viewport, audio visible, X visible | fits host/runtime viewport, audio visible, X visible | `side-by-side/game-hi-lo-desktop-side-by-side.png`, `side-by-side/game-hi-lo-mobile-side-by-side.png` | PASS |
| BOXE | fits host/runtime viewport, audio visible, X visible | fits host/runtime viewport, audio visible; X not detected on mobile, matching Phase 1 baseline screenshot | `side-by-side/game-boxe-desktop-side-by-side.png`, `side-by-side/game-boxe-mobile-side-by-side.png` | PASS for baseline parity; CTO decision if mobile X must differ from main |

The strict "X presente" check is green on desktop for all games and on mobile for Mines/HI-LO. BOXE mobile remains baseline-parity with `main`, where the X is not visible in the captured viewport. I did not alter X behavior because Phase 3A explicitly forbids touching the X and the games baseline is `main`.

## R1 - Public Player Login/Register/Account

Scoped player CSS was restored under `.site-v3-player-shell`:

- player shell tokens and layout: `frontend-v3/app/globals.css:770`, `:816`, `:1686`;
- login/register panel/form/text-link: `frontend-v3/app/globals.css:1748`, `:1766`, `:1819`, `:1825`;
- public account layout still keeps the "Dettagli account" strip removed per CTO decision.

| Surface | Evidence | Status |
| --- | --- | --- |
| Login | `side-by-side/player-login-desktop-side-by-side.png` | PASS vs backup `6141c17` |
| Register | `side-by-side/player-register-desktop-side-by-side.png` | PASS vs backup `6141c17` |
| Account overview | `side-by-side/player-account-desktop-side-by-side.png` | PASS with accepted delta: removed strip stays removed |

## R3 - Admin / CMS Polish

Scoped polish stayed under:

- `.ck-admin-legacy-page` from `frontend-v3/app/globals.css:769`;
- `.site-v3-cms-admin-page` from `frontend-v3/app/globals.css:2171`;
- CMS action alignment around `frontend-v3/app/globals.css:2382-2409`.

| Surface | Evidence | Status |
| --- | --- | --- |
| Admin shell/menu | `side-by-side/admin-shell-menu-desktop-side-by-side.png` | PASS vs main |
| Finance filters + bank report | `side-by-side/finance-filtered-desktop-side-by-side.png` | PASS vs main layout family |
| Player admin | `admin/player-admin-desktop.png` | CAPTURED; no CSS leakage from CMS root observed |
| Site V3 builder action bar | `admin/builder-action-bar-desktop.png` | PASS: actions right-aligned/readable, no new buttons |
| Module Studio | `admin/module-studio-desktop.png` | CAPTURED; feature work not part of 3A |

## Replay Verification

Final smoke created this technical player:

- `phase3a-player-15da684a6ee3@example.com`

Rounds generated:

- Mines: `04934286-1a65-4bdd-8641-01403db89be3`, status `won`
- BOXE: `00f88435-527c-49c7-9073-770822c1252b`, status `completed_cashout`
- HI-LO: `f5782d0c-c99e-4432-8a47-c1bcb059b4d0`, status `completed_cashout`

Runtime post-round replay:

| Game | Evidence | Status |
| --- | --- | --- |
| Mines | `replay/runtime-post-round-mines.png` | PASS |
| BOXE | `replay/runtime-post-round-boxe.png` | PASS |
| HI-LO | `replay/runtime-post-round-hi-lo.png` | PASS |

Player account / Storico gioco replay:

| Evidence | Status |
| --- | --- |
| `replay/account-history-expanded-before-replay.png` | details expanded for all 3 games |
| `replay/account-history-replay-1.png`, `account-history-replay-2.png`, `account-history-replay-3.png` | PASS: replay panels visible for HI-LO, BOXE and Mines |

Finance / Round detail replay:

| Detail index | Game order in report | Evidence | Status |
| --- | --- | --- | --- |
| 0 | HI-LO | `replay/finance-round-detail-1-replay.png` | PASS |
| 1 | BOXE | `replay/finance-round-detail-2-replay.png` | PASS |
| 2 | Mines | `replay/finance-round-detail-3-replay.png` | PASS |

Replay residual note: account and Finance expose replay buttons on multiple ledger rows, so the screenshots can show duplicate replay panels for the same round after opening more than one row. This is visible/readable and not a game-logic failure. It is a UX/product cleanup candidate, not changed in Phase 3A because it would alter account/Finance behavior beyond CSS/container stabilization.

## Protected Files / Hashes

Protected hash files:

- pre: `artifacts/site_v3_recovery_phase3a_2026-05-30/metadata/protected-hashes-pre.txt`
- post: `artifacts/site_v3_recovery_phase3a_2026-05-30/metadata/protected-hashes-post.txt`
- compare: `artifacts/site_v3_recovery_phase3a_2026-05-30/metadata/protected-hashes-compare.txt`

Compare result: `MATCH`.

Confirmed 0 diff by hash on:

- backend GMP files:
  - `backend/app/modules/games/boxe/service.py`
  - `backend/app/modules/games/boxe/platform_client.py`
  - `backend/app/modules/platform/game_launch/service.py`
  - `backend/app/api/routes/boxe.py`
  - `backend/app/api/routes/demo.py`
- runtime host/route protected files:
  - `frontend-v3/app/ui/game-frame-page.tsx`
  - `frontend-v3/app/runtime/mines/page.tsx`
  - `frontend-v3/app/runtime/boxe/page.tsx`
  - `frontend-v3/app/runtime/hi-lo/page.tsx`
- game logic/replay protected files:
  - `frontend-v3/app/ui/mines/mines-gameplay.tsx`
  - `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`
  - `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`
  - `frontend-v3/app/ui/mines/mines-replay-viewer.tsx`
  - `frontend-v3/app/ui/boxe/boxe-replay-viewer.tsx`
  - `frontend-v3/app/ui/hi-lo/hi-lo-replay-viewer.tsx`

## Verification Commands

| Check | Result |
| --- | --- |
| Docker stack | backend, frontend-v3, edge, postgres, redis healthy |
| `http://localhost:3000/login` | 200 |
| backup `http://127.0.0.1:3101/login` | 200 |
| `docker compose ... exec -T frontend-v3 npm run lint` | PASS (`tsc --noEmit`) |
| `git diff --check` on Phase 3A product files | PASS |
| protected hash compare | PASS (`MATCH`) |

Browser plugin note: the in-app browser backend was attempted for a quick sanity check, but no `iab` browser session was available in this chat. The deliverable verification therefore uses the reproducible Playwright artifact script and saved screenshots above.

## Artifacts Summary

Generated/captured in `artifacts/site_v3_recovery_phase3a_2026-05-30/`:

- `side-by-side/`: 12 comparison screenshots
- `current/`: 9 current-state screenshots
- `admin/`: 12 admin/Finance/CMS screenshots
- `replay/`: 14 replay screenshots
- `metadata/phase3a-capture-results.json`: final machine-readable run output

## Final Status

| Area | Status | Notes |
| --- | --- | --- |
| R2 games embedded sizing | PASS | No overflow detected; games fit host/runtime viewport. |
| R1 public player CSS | PASS | Login/register/account restored vs backup baseline; accepted account strip delta preserved. |
| R3 admin polish | PASS with visual gate | Admin/Finance/CMS scoped; no redesign. |
| Runtime replay | PASS | Mines/BOXE/HI-LO. |
| Account replay | PASS with UX residual | Replays visible/readable; duplicate row affordance remains. |
| Finance replay | PASS with UX residual | Replays visible/readable for HI-LO/BOXE/Mines; duplicate ledger-row affordance remains. |
| Protected backend/GMP/game logic | PASS | Hash compare `MATCH`. |
| Module building | NOT DONE | Explicitly out of scope for Phase 3A. |

Stop condition: Phase 3A is ready for CTO gate and Michele validation on `http://localhost:3000`. Do not proceed to module building / Phase 3B without approval.

## Documents Actually Read

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ACTIVE_OPEN_LOOPS.md`
- `docs/SITE_V3_RECOVERY_PHASE3_RESIDUAL_ANALYSIS_2026-05-30.md`

