# Site V3 Recovery - Game Fix Report - 2026-05-31

Scope: stabilize the residual game launch/layout regressions reported after
Phase 3A. This pass is limited to the public Site V3 game host frame and scoped
runtime control CSS. No module-building work is included.

## Baseline Used

Primary visual baseline is Phase 1 `main`:

- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-mobile.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-mobile.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-mobile.png`

I did not use `artifacts/site_v3_player_game_shell_qa_2026-05-29` as the
visual target because that artifact contains the rejected host topbar/chrome
(`Title`, selector/account/fullscreen/close controls).

## Files Changed In This Pass

Product files:

- `frontend-v3/app/globals.css`
  - `frontend-v3/app/globals.css:2099`: public game host frame only.
  - `frontend-v3/app/globals.css:2100`: desktop shell restored to centered,
    non-scrolling, bounded host.
  - `frontend-v3/app/globals.css:2110`: host uses explicit background, border,
    and `18px` radius instead of unresolved CSS variables.
  - `frontend-v3/app/globals.css:2173`: mobile remains full viewport, matching
    the established mobile runtime behavior.
- `frontend-v3/app/ui/game-runtime/game-runtime.css`
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:352`: table-balance gate
    panel restyled from raw/browser controls to scoped runtime controls.
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:482`: table-balance input
    scoped styling.
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:543`: table-balance submit
    button scoped styling.
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:723`: stable game mode
    badge styling.
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:865`: runtime bet input
    scoped styling.
  - `frontend-v3/app/ui/game-runtime/game-runtime.css:907`: runtime primary and
    secondary action button scoped styling.
  - Removed the generic mobile override that forced `.game-mobile-actions` into
    two columns; Mines mobile is back to stacked main actions like baseline.

Documentation/artifact files:

- `docs/SITE_V3_RECOVERY_GAME_FIX_EXECUTION_GATE_2026-05-31.md`
- `docs/SITE_V3_RECOVERY_GAME_FIX_REPORT_2026-05-31.md`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/capture_game_fix.py`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/metadata/game-fix-capture-results.json`

## Explicit Non-Changes

No changes in this pass to:

- RNG, math, payout, board, reveal, replay logic.
- Backend GMP files.
- Runtime route pages.
- `game-frame-page.tsx`.
- Game host topbar/chrome.
- Registration/account/module-building work.

Important repo-state note: the worktree already contains pre-existing diffs in
some protected backend/GMP/gameplay files from earlier phases. This report does
not claim those files are clean against Git HEAD. It claims this pass did not
edit them.

## Verification Commands

- `docker compose -f infra\docker\docker-compose.yml --env-file infra\docker\.env up -d --build frontend-v3 edge`
- `docker compose -f infra\docker\docker-compose.yml --env-file infra\docker\.env ps`
- `docker compose -f infra\docker\docker-compose.yml --env-file infra\docker\.env exec -T frontend-v3 npm run lint`
- `git diff --check -- frontend-v3/app/globals.css frontend-v3/app/ui/game-runtime/game-runtime.css artifacts/site_v3_recovery_game_fix_2026-05-31/capture_game_fix.py docs/SITE_V3_RECOVERY_GAME_FIX_EXECUTION_GATE_2026-05-31.md`
- `python artifacts\site_v3_recovery_game_fix_2026-05-31\capture_game_fix.py`

Result:

- Services healthy: backend, frontend-v3, edge, postgres, redis.
- Typecheck/lint: pass.
- Diff whitespace check: pass.
- In-app Browser was unavailable in this session (`Browser is not available:
  iab`), so Playwright/Chrome fallback was used for screenshots.

## Screenshot Artifacts

Current captures:

- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-mines-desktop-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-mines-mobile-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-hi-lo-desktop-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-hi-lo-mobile-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-boxe-desktop-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-boxe-mobile-after-gates.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/gate-mines-desktop-table-gate.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/gate-hi-lo-desktop-table-gate.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/current/gate-boxe-desktop-table-gate.png`

Side-by-side with Phase 1 main baseline:

- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-mines-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-mines-mobile-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-hi-lo-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-hi-lo-mobile-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-boxe-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_game_fix_2026-05-31/side-by-side/game-boxe-mobile-after-gates-side-by-side.png`

## Metrics Summary

| Surface | Result | Metrics |
| --- | --- | --- |
| Mines desktop | Pass | Host `1160x818`; not full viewport; no host/runtime scroll; X visible; board `556x556`; DEMO badge separated. |
| Mines mobile | Pass | Host `390x844`; full viewport as mobile baseline; no scroll; main actions stacked again; board `268x268`. |
| HI-LO desktop | Pass with visual delta | Host `1160x818`; not full viewport; no scroll; X visible; input/buttons styled; board/play surface `740x599`. |
| HI-LO mobile | Pass | Host `390x844`; full viewport; no scroll; X visible; controls styled. |
| BOXE desktop | Pass | Host `1160x818`; not full viewport; no scroll; X visible; board `726x487`. |
| BOXE mobile | Pass with visual delta | Host `390x844`; full viewport; no scroll; board `366x323`; content remains inside viewport. |
| Mines real table gate | Pass | Gate `460x566`; input `402x48`; button `402x52`; no raw browser input. |
| HI-LO real table gate | Pass | Gate `460x566`; input `402x48`; button `402x52`; no raw browser input. |
| BOXE real table gate | Pass | Gate `460x566`; input `402x48`; button `402x52`; no raw browser input. |

## Residual Notes

- HI-LO desktop was rechecked after this report and one additional scoped CSS
  fix was applied in `frontend-v3/app/ui/hi-lo/hi-lo.css`: embedded HI-LO now
  keeps `100vh` / `100dvh` height inside the V3 iframe. This removes the bottom
  dark band caused by `.hi-lo-page-shell-embedded` collapsing to content height.
  The follow-up evidence is in
  `docs/SITE_V3_RECOVERY_GAME_FINAL_REVIEW_2026-05-31.md`.
- BOXE mobile is not pixel-perfect against `main`; the remaining delta is
  visual/layout, not a measured scroll/fullscreen or raw control regression.
- Mines mobile still has the title/header overlap that is also visible in the
  Phase 1 baseline screenshot. I did not redesign it in this pass.
- The requested "interrupt running session" control is not part of this CSS
  stabilization. It is a product/session-lifecycle item and should be planned
  separately.
- Replay/account/finance replay entrypoints were not rerun in this specific
  pass. No replay code or replay CSS was edited here.

## Gate Recommendation

Ready for CTO visual gate on `http://localhost:3000` for:

- desktop launch size not full-browser;
- native X visible;
- Mines DEMO spacing restored;
- Mines mobile stacked main actions restored;
- HI-LO input/buttons no longer raw;
- BOXE table-balance gate no longer raw.

If CTO requires strict pixel parity for HI-LO desktop or BOXE mobile, the next
step should be a separate parity pass against the Phase 1 baseline screenshots,
still limited to scoped CSS and still excluding game logic.
