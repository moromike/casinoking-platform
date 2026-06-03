Status: ACTIVE
Last meaningful update: 2026-05-30

# Site V3 Recovery - Phase 2B Batch 2 Report

Scope: B4-B7 only. Goal was game CSS isolation/parity, HI-LO smoke, missing admin surfaces, and final diff report. Backend GMP files and game logic stayed protected.

Baseline: `main` commit `4715fda`, screenshots under `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/`.

Current artifacts root: `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/`.

## Services

Docker services were rebuilt/restarted for `frontend-v3` and `edge` after CSS changes. Final service state was healthy:

- `casinoking-backend-1`: healthy
- `casinoking-frontend-v3-1`: healthy
- `casinoking-edge-1`: healthy
- `casinoking-postgres-1`: healthy
- `casinoking-redis-1`: healthy
- `http://localhost:3000/healthz`: `200`

## Files Touched In This Batch

Runtime/game-shell CSS or visual shell only:

- `frontend-v3/app/ui/game-runtime/game-runtime.css`
- `frontend-v3/app/ui/mines/mines-stage-header.tsx`
- `frontend-v3/app/ui/mines/mines-standalone.tsx`
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`
- `frontend-v3/app/ui/boxe/boxe-standalone.tsx`
- `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`
- `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx`

Admin CSS/root ownership:

- `frontend-v3/app/globals.css`
- `frontend-v3/app/ui/admin-games-page.tsx`

Artifact-only scripts/results:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/phase2_batch2_selector_gate.py`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/phase2_batch2_capture_games.py`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/phase2_batch2_smoke_games.py`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/phase2_batch2_capture_admin_surfaces.py`

## B4 - Selector Gate

Final selector gate: PASS.

Result: no V3/admin/global selector matched inside Mines, HI-LO, or BOXE runtime iframes.

Final metadata:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/selector-gate-final-mobile-actions-parity.json`

Final screenshots:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/selector-gate/mines-final-mobile-actions-parity.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/selector-gate/hi-lo-final-mobile-actions-parity.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/selector-gate/boxe-final-mobile-actions-parity.png`

## B5 - Visual Parity Games

Final capture metadata:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/game-visual-parity-results.json`

| Surface | Side-by-side screenshot | Status | Notes |
| --- | --- | --- | --- |
| Mines desktop | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-mines-desktop-side-by-side.png` | PASS | Native X visible, no host topbar, audio/info visible, board/content aligned to baseline. |
| Mines mobile | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-mines-mobile-side-by-side.png` | PASS | Mobile X absent in both baseline/current. Action buttons restored stacked like baseline. |
| HI-LO desktop | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-hi-lo-desktop-side-by-side.png` | PASS | Native X visible, no host chrome, controls/board restored after scoped runtime CSS. |
| HI-LO mobile | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-hi-lo-mobile-side-by-side.png` | PASS | X visible at top right, controls/board fit viewport, no functional break observed. |
| BOXE desktop | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-boxe-desktop-side-by-side.png` | PASS | Native X visible, board/pyramid/content aligned to baseline. |
| BOXE mobile | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/side-by-side/game-boxe-mobile-side-by-side.png` | PASS | Mobile X absent in both baseline/current. Content fits without host chrome. |

Additional audio/info/replay smoke metadata:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/game-smoke-results.json`

Audio popover screenshots:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/mines-desktop-audio-open.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/mines-mobile-audio-open.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-desktop-audio-open.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-mobile-audio-open.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/boxe-desktop-audio-open.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/boxe-mobile-audio-open.png`

Info/replay modal screenshots:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/mines-desktop-info-replay.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/mines-mobile-info-replay.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-desktop-info-replay.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-mobile-info-replay.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/boxe-desktop-info-replay.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/boxe-mobile-info-replay.png`

Replay note: idle replay tabs are present but disabled for all three games because no terminal/current replay exists in idle state. HI-LO replay was exercised after a terminal round in B5b.

## B5b - HI-LO Functional Smoke

Status: PASS.

Observed and recorded:

- start round: PASS
- red/black prediction: PASS
- up/down prediction: PASS
- skip: PASS
- cashout: PASS
- replay tab enabled after played round: PASS
- replay opened after terminal/cashout round: PASS

Screenshots:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-00-idle.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-01-after-bet.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-01-after-red-black.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-01-after-up-down.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-01-after-skip.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-01-after-cashout.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/smoke/hi-lo-functional-replay.png`

Language note: no in-game language switch control exists in the runtime UI. HI-LO still uses `runtimeConfig.presentation_config.default_locale` and copy resolvers. This is not a Phase 2B break.

## B6 - Missing Admin Surfaces

Final metadata:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/admin-surfaces-results.json`

| Surface | Screenshot | Status | Notes |
| --- | --- | --- | --- |
| Games | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/games-menu-surface.png` | PASS | Initially failed through deprecated `site-v3-admin-page`; fixed to `ck-admin-legacy-page admin-games-page` and restored scoped catalog styling. |
| Site | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/site-menu-surface.png` | PASS WITH PRODUCT DEBT | Uses legacy root, no CMS leakage. Page remains long/dense as existing Site editor debt, not a Phase 2B CSS leak. |
| Site V3 | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/site-v3-menu-surface.png` | PASS | Uses CMS root by design, not legacy root. No deprecated `site-v3-admin-page`. |
| LOG | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/log-menu-surface.png` | PASS | Legacy root, no CMS leakage. |
| Administrators | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/administrators-menu-surface.png` | PASS WITH PRODUCT DEBT | Legacy root, no CMS leakage. Very long list remains a UX/density debt, not a recovery blocker. |
| Platform Settings | `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/platform-settings-menu-surface.png` | PASS | Legacy root, no CMS leakage. |

Direct route checks:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/direct-admin-games.png`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/b6-admin-surfaces/direct-admin-site-v3.png`

## B7 - Protected Diff

Protected hash compare:

- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/protected-hashes-pre.txt`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/protected-hashes-post.txt`
- `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/metadata/protected-hashes-compare.txt`

Result:

- Backend GMP files: UNCHANGED.
- `frontend-v3/app/ui/game-frame-page.tsx`: UNCHANGED.
- Runtime route pages `frontend-v3/app/runtime/{mines,boxe,hi-lo}/page.tsx`: UNCHANGED.
- `frontend-v3/app/ui/game-runtime/game-runtime.css`: CHANGED intentionally for scoped CSS-only runtime control restoration and mobile action parity.

No RNG, math, payout, board, reveal, replay data model, or backend GMP file was touched in this batch.

## Residual Decisions

- Product debt: Site editor and Administrators remain long/dense. They pass the recovery gate but deserve separate UX work if Michele/CTO wants compact operator workflows.
- HI-LO language switching: no runtime switch UI exists to exercise. Current i18n is config/copy based.
- Next step: CTO final gate on this report and screenshots, then Michele manual validation on `http://localhost:3000`.

## Stop State

Batch 2 stops here for CTO final gate. No GMP-5C or new feature work was started.
