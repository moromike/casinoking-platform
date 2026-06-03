Status: EXECUTION GATE - BEFORE CODE
Date: 2026-05-31

# Site V3 Recovery - Game Fix Execution Gate

This document narrows the fix following
`docs/SITE_V3_RECOVERY_GAME_REBREAK_ANALYSIS_2026-05-31.md`.

## Baseline

Visual baseline for games:

- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-desktop.png`
- matching mobile screenshots in the same folder.

`6141c17` is not the visual baseline.

## Allowed Product Changes

Allowed files:

- `frontend-v3/app/globals.css`
  - only `.site-v3-game-*` host frame rules.
- `frontend-v3/app/ui/game-runtime/game-runtime.css`
  - only scoped runtime control rules:
    - `.game-table-balance-*`
    - `.game-mode-badge`
    - `.game-product-shell .game-bet-field`
    - `.game-product-shell .game-action-buttons`
    - `.game-product-shell .button-content/.button-spinner`

Not allowed:

- no RNG/math/payout/board/reveal changes;
- no backend GMP changes;
- no `/runtime/*/page.tsx` changes;
- no game redesign;
- no new host topbar/chrome;
- no gameplay TSX changes in this pass.

## Concrete Acceptance Targets

Desktop viewport: `1280x850`.

- Public Site V3 host:
  - `.site-v3-game-host` width should be about `1160px`;
  - `.site-v3-game-host` height should be about `818px`;
  - host must not be full browser width/height;
  - no document scrollbar for launch/gameplay.
- Mines:
  - `DEMO` badge remains a separate pill;
  - info/audio controls are not attached to the badge;
  - board/cells are not cut.
- HI-LO:
  - left rail input is styled, not browser-default;
  - `Punta`/`Incassa` are pill buttons, not raw rectangles;
  - stage remains centered/bounded like baseline.
- BOXE:
  - gameplay rail remains aligned with Mines style;
  - table balance gate input and submit button are styled by `game-runtime.css`, not browser defaults.
- Mobile `390x844`:
  - host remains full viewport;
  - game remains usable, no desktop bounding applied.

## Micro-Step Gate

1. Patch host frame only.
2. Patch runtime controls only.
3. Rebuild/restart `frontend-v3` and `edge`.
4. Capture Mines/HI-LO/BOXE desktop and mobile launch/gameplay.
5. Capture table-balance gate where reachable.
6. Produce side-by-side screenshots vs baseline main.
7. Confirm protected areas have no diff:
   - backend GMP files;
   - game logic/RNG/math/payout/board/reveal files.

Stop condition: if visual parity requires changing gameplay logic, backend GMP,
or a non-scoped redesign, stop and report instead of compensating in code.
