Status: FINAL REVIEW READY FOR CTO / MICHELE GATE
Date: 2026-05-31 Europe/Rome
Executor: Codex
Target: http://localhost:3000

# Site V3 Recovery - Game Final Review

## Scope

This review closes the current games recovery pass after the R2/R3 follow-ups.

Allowed work in this pass:
- review current Mines / HI-LO / BOXE rendering against Phase 1 `main` screenshots;
- verify runtime, account, and Finance replay entrypoints;
- apply only safe scoped CSS if a replay/container regression is proven.

Not allowed and not done:
- no game logic changes;
- no RNG/math/payout/board/reveal changes;
- no backend GMP changes;
- no host chrome/topbar redesign;
- no module-building work.

The in-app browser was still unavailable in this chat session, so verification
used local Playwright/Chrome scripts against `http://localhost:3000`.

## Product Changes Made In This Final Pass

Two product fixes were applied:

- `frontend-v3/app/ui/mines/mines.css`
  - Added scoped generic CSS for `.mines-replay-viewer` and its children.
  - Reason: Mines replay was readable inside the runtime modal, but in Finance it
    inherited dark text from the light report context and became low contrast.
  - This is replay presentation CSS only. It does not touch Mines board logic,
    reveal logic, payout logic, RNG, backend, or runtime routes.
- `frontend-v3/app/ui/hi-lo/hi-lo.css`
  - Added scoped embedded-height CSS for `.hi-lo-page-shell-embedded`.
  - Reason: V3 launches HI-LO inside an iframe. The copied `main` HI-LO CSS had
    `.hi-lo-page-shell-embedded { min-height: 0; height: 100%; }`; inside the
    iframe this collapsed to the content height (`715px`) and left the visible
    empty dark band below the game. The patch restores full iframe height
    (`100vh` / `100dvh`) only for embedded HI-LO.
  - This is container presentation CSS only. It does not touch HI-LO card logic,
    predictions, payout logic, RNG, backend, or runtime routes.

Existing modified CSS from earlier recovery steps remains in the working tree:

- `frontend-v3/app/globals.css`
- `frontend-v3/app/ui/game-runtime/game-runtime.css`

Those were reviewed through screenshots here but not expanded further in this
final pass, except for the HI-LO embedded-height fix listed above.

## Services And Build

Docker stack status after rebuild:

- backend: healthy
- frontend-v3: healthy
- edge: healthy
- postgres: healthy
- redis: healthy

Checks:

| Check | Result |
| --- | --- |
| `docker compose ... up -d --build frontend-v3 edge` | PASS, call timed out but containers rebuilt and became healthy |
| `docker compose ... exec -T frontend-v3 npm run lint` | PASS (`tsc --noEmit`) |
| `git diff --check` on touched review/CSS files | PASS |

Build warning still present and pre-existing in `globals.css`:

- autoprefixer warning at `globals.css:1612`: `start` has mixed support; use `flex-start`.

## Game Surface Review

Baseline: `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/`

Current screenshots:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-mines-desktop.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-mines-mobile.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-hi-lo-desktop.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-hi-lo-mobile.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-boxe-desktop.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-boxe-mobile.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-mines-desktop-1920-after-gates.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-hi-lo-desktop-1920-after-gates.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/current/game-boxe-desktop-1920-after-gates.png`

Side-by-side:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-mines-desktop-side-by-side.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-mines-mobile-side-by-side.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-hi-lo-desktop-side-by-side.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-hi-lo-mobile-side-by-side.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-boxe-desktop-side-by-side.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/side-by-side/game-boxe-mobile-side-by-side.png`

Result:

| Surface | Result | Notes |
| --- | --- | --- |
| Mines desktop | PASS | Host bounded; cells not clipped; DEMO/info no longer attached; X visible. |
| Mines mobile | PASS with baseline-known title overlap | Current is aligned with Phase 1 mobile shape; top title/audio overlap also exists in baseline. |
| HI-LO desktop | PASS after embedded-height fix | Host bounded; no bottom dark band; controls styled; X visible. Not declared pixel-perfect, but the proven layout break is fixed. |
| HI-LO mobile | PASS with visual delta | Usable and in viewport; not pixel-identical. |
| BOXE desktop | PASS | Host bounded; board visible; X visible. |
| BOXE mobile | PASS with visual delta | In viewport; bottom controls remain tight but no destructive overflow observed. |

Additional desktop-wide check (`1920x980`):

| Surface | Result | Metrics |
| --- | --- | --- |
| Mines desktop 1920 | PASS | Host `1160x820`, centered, no document scroll; DEMO pill separated. |
| HI-LO desktop 1920 | PASS | Host `1160x820`, product shell `1158x818`, no bottom dark band. |
| BOXE desktop 1920 | PASS | Host `1160x820`, board visible, table controls styled. |

## Replay Verification

### Runtime Replay

Screenshots:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/runtime-post-round-mines.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/runtime-post-round-hi-lo.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/runtime-post-round-boxe.png`

Result:

| Game | Result | Notes |
| --- | --- | --- |
| Mines | PASS | Replay modal opens; board and outcome visible. |
| HI-LO | PASS | Replay modal opens; card, timeline, payout, fairness visible. |
| BOXE | PARTIAL | Replay modal opens and viewer is styled, but the runtime capture caught an active snapshot, not a terminal post-round replay. Terminal BOXE replay is verified via Account and Finance below. |

Additional stricter runtime script:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/metadata/runtime-replay-verified-results.json`

This script is not counted as product failure for Mines/HI-LO because it failed
to drive the current UI flow reliably and opened rules with disabled replay. It
is kept as evidence of the verifier limitation.

### Account "Storico gioco" Replay

Screenshots:

- HI-LO: `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/account-by-game-hi-lo-replay.png`
- BOXE: `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/account-light-boxe-replay.png`
- Mines: `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/account-light-mines-replay.png`

Metadata:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/metadata/account-replay-by-game-light-results.json`

Result:

| Game | Result | Notes |
| --- | --- | --- |
| HI-LO | PASS | Captured in the first account-by-game run before timeout. |
| BOXE | PASS | Replay panel opens from account history. |
| Mines | PASS | Replay panel opens from account history. |

The first account-by-game run timed out after capturing HI-LO because full-page
account screenshots were very long. A lighter follow-up captured BOXE and Mines.

### Finance "Round Detail" Replay

Post-fix metadata:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/metadata/finance-replay-review-post-mines-css-results.json`

Screenshots:

- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/finance-round-detail-1-replay.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/finance-round-detail-2-replay.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/finance-round-detail-3-replay.png`
- `artifacts/site_v3_recovery_game_final_review_2026-05-31/replay/finance-round-detail-4-replay.png`

Result:

| Game | Result | Notes |
| --- | --- | --- |
| HI-LO | PASS | Finance replay opens with readable card/timeline/fairness. |
| BOXE | PASS | Finance replay opens for both cashout and loss states. |
| Mines | PASS after final CSS fix | Replay is now readable in Finance; metadata and fairness no longer inherit the wrong dark text color. |

Finance smoke counts:

- round detail buttons: 4
- replay buttons found: 7
- admin account used: `codex.agent@example.com`
- Michele personal admin account was not used.

## Protected Files

No backend GMP or game logic files were edited in this final pass.

`git diff --name-only` still reports pre-existing dirty files from earlier
approved work/recovery:

- `backend/app/api/routes/boxe.py`
- `backend/app/api/routes/demo.py`
- `backend/app/modules/games/boxe/platform_client.py`
- `backend/app/modules/games/boxe/service.py`
- `backend/app/modules/platform/game_launch/service.py`
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`
- `frontend-v3/app/ui/game-frame-page.tsx`
- `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`
- `frontend-v3/app/ui/mines/mines-stage-header.tsx`

Those were not modified by this final review pass. They remain dirty in the
shared working tree and should be judged against the earlier CTO gates.

## Remaining Decision Points

1. BOXE runtime replay entrypoint opens, but this review did not produce a
   terminal BOXE runtime post-round screenshot. Account and Finance terminal
   BOXE replays are verified. If CTO wants runtime BOXE terminal proof too, the
   next step is to fix the Playwright driver only, not game logic.

2. Mobile is usable in the captured 390x844 viewport, but final mobile acceptance
   still needs human validation on real device sizes.

## Verdict

This pass materially improves the replay situation by fixing the proven Mines
Finance replay contrast regression and fixes the proven HI-LO embedded desktop
height regression without touching game logic.

Do not proceed to module building from here. Next gate should be CTO/Michele
validation on `http://localhost:3000`, with special attention to BOXE runtime
terminal replay proof if that exact runtime evidence is required in addition to
the already verified Account and Finance BOXE replays.
