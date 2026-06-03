Status: R2B AUDIT DONE - NO PRODUCT CODE CHANGED
Date: 2026-05-31
Owner: CTO gate - Executor: Codex - Validation target: Michele on `http://localhost:3000`

# Site V3 Recovery Phase 3A R2B - Game Host Layout Audit

## Executive Verdict

The Phase 3A game layout gate is **not approvable for desktop**.

The previous Phase 3A report used the wrong acceptance criterion for R2: it verified
"no document overflow / fits viewport". Michele's validation is correct: the desktop
game host now renders as full-viewport, while the baseline desktop layout was a
centered optimized game surface, not a full-screen shell.

No product code was changed in this audit. I only added artifact capture:

- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/r2b_host_layout_audit.py`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/metadata/r2b-host-layout-results.json`

## Evidence

Artifacts:

- Launch/splash current desktop:
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-mines-desktop-launch.png`
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-hi-lo-desktop-launch.png`
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-boxe-desktop-launch.png`
- After-gates side-by-side vs Phase 1 baseline main:
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-mines-desktop-after-gates-side-by-side.png`
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-hi-lo-desktop-after-gates-side-by-side.png`
  - `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-boxe-desktop-after-gates-side-by-side.png`

Measured result on current `localhost:3000`:

| Game | Viewport | Host height | Iframe height | Runtime product height | Verdict |
| --- | --- | ---: | ---: | ---: | --- |
| Mines | desktop 1280x850 | 100% | 100% | 100% | FAIL for desktop optimized parity |
| HI-LO | desktop 1280x850 | 100% | 100% | 89.6% | FAIL for desktop optimized parity |
| BOXE | desktop 1280x850 | 100% | 100% | 100% | FAIL for desktop optimized parity |
| Mines | mobile 390x844 | 100% | 100% | 100% | likely intended, keep under mobile QA |
| HI-LO | mobile 390x844 | 100% | 100% | 100% | likely intended, keep under mobile QA |
| BOXE | mobile 390x844 | 100% | 100% | 100% | likely intended, keep under mobile QA |

Important distinction: "100% viewport" is acceptable and probably required on
mobile. On desktop it is the regression Michele reported.

## Root Cause

### 1. Baseline main did not use the V3 iframe host

Phase 1 baseline metadata shows baseline game routes on `main` were direct game
runtime pages on `http://localhost:3100/...`, with no iframe layer:

- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/metadata/game-recapture-results.json`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/metadata/game-dom-class-snapshots.json`

Baseline screenshots:

- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-desktop.png`

### 2. Current V3 host forces full viewport

`frontend-v3/app/ui/game-frame-page.tsx:122-148` wraps every public game route
inside:

- `.site-v3-game-shell`
- `.site-v3-game-host`
- `.site-v3-game-frame-wrap`
- `iframe.site-v3-game-frame`

`frontend-v3/app/globals.css:2092-2132` then makes that host full viewport:

- `.site-v3-game-shell` has `min-height: 100vh`, `overflow: hidden`, no padding.
- `.site-v3-game-host` has `height: 100vh`, `max-width: none`, `border-radius: 0`.
- `.site-v3-game-frame` has `height: 100%`, `width: 100%`.

This is the real desktop host regression. It does not require touching game
logic. It probably does not require changing `game-frame-page.tsx`; a scoped CSS
host fix should be enough.

### 3. Runtime embedded classes now correctly fill their iframe, but the iframe is too large on desktop

R2 in Phase 3A restored embedded classes, but those classes are designed to fill
the iframe they are given:

- Mines embedded full-iframe shell:
  - `frontend-v3/app/ui/mines/mines.css:1325-1352`
  - `frontend-v3/app/ui/mines/mines.css:1355-1475`
- BOXE uses the Mines shell class names in the standalone wrapper:
  - `frontend-v3/app/ui/boxe/boxe-standalone.tsx:162`
  - `frontend-v3/app/ui/boxe/boxe-standalone.tsx:170`
  - plus BOXE embedded-specific compacting in `frontend-v3/app/ui/boxe/boxe.css:916-1027`
- HI-LO embedded shell fills its container:
  - `frontend-v3/app/ui/hi-lo/hi-lo.css:23-29`

So the next fix should constrain the desktop iframe host, not rewrite the game
runtime internals.

### 4. Splash/intro is also full viewport because it is fixed inside the iframe

`frontend-v3/app/ui/game-runtime/game-runtime.css:1-18` defines
`.game-provider-bootstrap` as `position: fixed; inset: 0`.

`frontend-v3/app/ui/game-runtime/game-runtime.css:28-65` also fixes the progress
bar and skip button to the iframe viewport.

`frontend-v3/app/ui/game-runtime/game-runtime.css:81-99` uses fixed overlay for
How To Play.

Those rules are fine if the iframe is desktop-optimized. They become visually
full-browser because the host iframe is full-browser.

## CTO-Level Fix Proposal

Do **not** touch game logic, RNG, payout, board, reveal, replay viewers, backend
GMP, or runtime route pages.

Recommended fix: CSS-only desktop host constraint in `frontend-v3/app/globals.css`,
scoped only to public game host selectors:

- Desktop:
  - center `.site-v3-game-host`;
  - restore an optimized bounded surface: `width: min(<baseline-ish width>, calc(100vw - margins))`;
  - restore bounded height: `height: min(<baseline-ish height>, calc(100dvh - margins))`;
  - restore border/radius/background similar to baseline container;
  - keep iframe `width: 100%; height: 100%`.
- Mobile:
  - keep current full-viewport behavior under `@media (max-width: 640px)`.

Recommended first values for a micro-fix trial, to be verified by screenshots,
not declared final upfront:

- width: `min(1160px, calc(100vw - 48px))`
- height: `min(820px, calc(100dvh - 32px))`
- shell: grid center with modest padding on desktop
- mobile: unchanged full viewport

Why this is the safest next move:

- it fixes the host level where the regression is proven;
- it avoids game runtime code and protected game logic;
- it should automatically make splash/intro smaller because the fixed overlay is
  fixed to the iframe viewport, not the browser viewport;
- it keeps the iframe architecture needed for Site V3-owned shell.

Stop condition for the fix: if constraining the host breaks mobile, close/X,
audio, replay, or any board fit, revert the CSS hunk and do not compensate inside
game logic.

## Proposed Phase 3A-R2C Micro-Fix Gate

1. Patch only `frontend-v3/app/globals.css` under `.site-v3-game-*` selectors.
2. Rebuild/restart only `frontend-v3` and `edge` if needed.
3. Capture:
   - desktop launch and after-gates for Mines/HI-LO/BOXE;
   - mobile launch and after-gates for Mines/HI-LO/BOXE;
   - side-by-side vs Phase 1 baseline main.
4. Pass/fail:
   - desktop no full-browser host;
   - desktop game surface centered/bounded like baseline;
   - splash/intro bounded to the optimized game surface;
   - mobile still fills viewport and remains usable;
   - X/audio visible as before;
   - no game logic/protected hash diff.

## CMS Menu Usability Note

Michele also reported that the CMS menu goes far down and the top becomes hard
to keep in view.

Current CSS:

- `.site-v3-cms-shell` is a two-column grid at `frontend-v3/app/globals.css:2490-2495`.
- `.site-v3-cms-nav` is sticky at `frontend-v3/app/globals.css:2497-2504`.
- But the nav has no `max-height` and no internal `overflow-y`.
- On narrower layouts, nav becomes static at `frontend-v3/app/globals.css:2987-2990`.

Recommended solution for a separate CMS polish task, not part of the game fix:

1. **CSS-only sticky nav with internal scroll** (recommended first)
   - keep `.site-v3-cms-nav` sticky;
   - add `max-height: calc(100dvh - 2rem)`;
   - add `overflow-y: auto`;
   - keep the title/current page block visible if possible.
   - Minimal risk, no IA redesign.

2. **Collapsible groups**
   - make `Site`, `Pages`, `Modules`, `Categories` collapsible.
   - Better operator UX, but it is behavior/UI work, not recovery CSS.

3. **Top-level tabs**
   - split `Site / Pages / Modules` into a segmented/top nav and reduce sidebar depth.
   - Bigger IA change; should be planned, not slipped into recovery.

CTO recommendation: do option 1 as a small scoped polish after R2C, then consider
option 2 only if Michele still finds the menu too long.

## What Was Not Done

- No product CSS/TSX changed in this R2B audit.
- No game logic touched.
- No backend/GMP touched.
- No module building started.
- No CMS menu fix applied.

## Next Step

Proceed to Phase 3A-R2C only if CTO approves the CSS-only desktop host constraint
approach above. The change should be one small hunk in `frontend-v3/app/globals.css`
plus screenshots and protected-hash confirmation.

