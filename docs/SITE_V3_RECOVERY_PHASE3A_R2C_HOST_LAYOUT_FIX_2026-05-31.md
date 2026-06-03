Status: R2C DONE - STOP FOR CTO / MICHELE VALIDATION
Date: 2026-05-31 Europe/Rome
Executor: Codex
Target: `http://localhost:3000`

# Site V3 Recovery Phase 3A-R2C Host Layout Fix

## CTO-Style Verdict

The user report was valid: after Phase 3A, the desktop public game launch and
game host still felt too close to full browser size. The runtime game itself was
not the root cause of the launch size; the Site V3 host iframe was. The iframe
host made the runtime consume almost the whole browser viewport, so the provider
bootstrap and game surface looked fullscreen on desktop.

R2C fixes the host/container boundary only. It does not touch game logic, game
runtime pages, replay components, RNG, payout, board, reveal, backend GMP, or
the game chrome/X implementation.

## Product Files Changed In R2C

- `frontend-v3/app/globals.css`
  - `frontend-v3/app/globals.css:2092`: `.site-v3-game-shell` now centers the
    desktop iframe host with padding.
  - `frontend-v3/app/globals.css:2106`: `.site-v3-game-host` now has a desktop
    bounded size (`max-width: 1160px`, `height: min(820px, calc(100dvh - 32px))`)
    instead of full-viewport desktop hosting.
  - `frontend-v3/app/globals.css:2169`: mobile keeps full-viewport behavior.
  - `frontend-v3/app/globals.css:2512`: CMS nav now has internal scroll with
    `max-height: min(520px, calc(100dvh - 2rem))`.
  - `frontend-v3/app/globals.css:3007`: mobile CMS nav resets to normal static
    flow.

Artifact-only files:

- `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/r2c_cms_nav_check.py`
- `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/r2c-cms-nav-check.json`
- `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/protected-hashes-r2c-post-exact-phase3a-list.txt`
- `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/protected-hashes-r2c-compare-exact-phase3a-list.txt`

## What Was Not Changed

- No game logic.
- No RNG/math/payout/board/reveal.
- No replay component rewrite.
- No `game-frame-page.tsx`.
- No `/runtime/*/page.tsx`.
- No backend GMP files.
- No `game-runtime.css`.
- No host topbar/chrome added above games.
- No Michele personal admin account used.

## Game Host Result

The same Playwright audit script from R2B was re-run after R2C and rebuilt
Docker services. Latest JSON:

- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/metadata/r2b-host-layout-results.json`

Desktop result: host/iframe are no longer full viewport.

| Game | Desktop host | Desktop iframe | Host full viewport | Iframe full viewport | Host scroll |
| --- | ---: | ---: | --- | --- | --- |
| Mines | 1160x818 | 1158x816 | false | false | 850/850 |
| HI-LO | 1160x818 | 1158x816 | false | false | 850/850 |
| BOXE | 1160x818 | 1158x816 | false | false | 850/850 |

Mobile result: still full viewport, as intended for phone layout.

| Game | Mobile host | Mobile iframe | Host full viewport | Iframe full viewport | Host scroll |
| --- | ---: | ---: | --- | --- | --- |
| Mines | 390x844 | 390x844 | true | true | 844/844 |
| HI-LO | 390x844 | 390x844 | true | true | 844/844 |
| BOXE | 390x844 | 390x844 | true | true | 844/844 |

## Game Screenshots

Current launch screenshots:

- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-mines-desktop-launch.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-hi-lo-desktop-launch.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/current/game-boxe-desktop-launch.png`

Side-by-side after gates vs Phase 1 main baseline:

- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-mines-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-hi-lo-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-boxe-desktop-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-mines-mobile-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-hi-lo-mobile-after-gates-side-by-side.png`
- `artifacts/site_v3_recovery_phase3a_r2b_2026-05-31/side-by-side/game-boxe-mobile-after-gates-side-by-side.png`

Visual note: R2C removes the desktop full-viewport host regression. Final
pixel-perfect acceptance still belongs to CTO/Michele validation on `:3000`.
If the product decision is to make the desktop host even smaller, that should be
a dimension decision on the host wrapper only, not a game runtime rewrite.

## CMS Menu Result

The CMS menu problem was real: a sticky menu with many entries could extend
below the first viewport. R2C keeps the same CMS navigation and adds an internal
scroll window.

Check output:

- JSON: `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/r2c-cms-nav-check.json`
- Normal screenshot: `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/admin/cms-dashboard-nav-viewport.png`
- Scrolled nav screenshot: `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/admin/cms-dashboard-nav-scrolled.png`

Measured result:

| Metric | Value |
| --- | --- |
| nav height | 520 |
| clientHeight | 518 |
| scrollHeight | 1254 |
| overflow-y | auto |
| max-height | 520px |
| scrollTop after programmatic scroll | 736 |
| status | pass |

## Verification

| Check | Result |
| --- | --- |
| Docker rebuild/restart | PASS: backend, frontend-v3, edge, postgres, redis healthy |
| Game host Playwright audit | PASS: desktop no longer full viewport; mobile unchanged full viewport |
| CMS nav Playwright audit | PASS: internal scroll active and measurable |
| `docker compose ... exec -T frontend-v3 npm run lint` | PASS (`tsc --noEmit`) |
| `git diff --check` on R2C touched files | PASS |
| Protected hash compare vs Phase 3A final list | PASS (`MATCH`) |

Protected hash exact compare:

- `artifacts/site_v3_recovery_phase3a_r2c_2026-05-31/metadata/protected-hashes-r2c-compare-exact-phase3a-list.txt`

## Current Stop Point

R2C is ready for CTO gate and Michele validation on `http://localhost:3000`.
No further module building, game redesign, or runtime/game logic work should be
started from this checkpoint without explicit approval.
