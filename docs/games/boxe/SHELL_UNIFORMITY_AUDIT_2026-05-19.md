Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Shell Uniformity Audit - 2026-05-19

## Scope

WP: `WP-BOXE-SHELL-UNIFORMITY-FIX`

Protected equality zone:

```text
Lobby card -> Launch Cashier -> table balance gate -> provider intro -> how-to-play gate -> gameplay ready
```

Product decision, 2026-05-19: in this zone Mines and BOXE must render the same
platform shell. Game-specific content is allowed only inside the how-to-play
steps; structure, layout and shell visuals must stay identical.

## Executive Finding

BOXE does consume `GameBootShell`, but it does not consume the same pre-game
surfaces as Mines. The shared `game-runtime` layer currently wraps React nodes;
it does not own the visual implementation of Provider Intro, How-To-Play content
layout, or Table Balance content.

This means the divergence is structural, not a small CSS drift:

- Mines passes `MinesProviderBootstrap`, `MinesHowToPlayGate`, and a full
  `mines-launch-gate` table balance surface into `GameBootShell`.
- BOXE passes local `boxe-provider-intro`, `BoxeHowToPlayContent`, and a local
  placeholder `boxe-table-balance` surface into the same shell.

Root-cause count:

| Root cause category | Count | Notes |
| --- | ---: | --- |
| BOXE fork / local version of shell surface | 3 | Provider Intro, How-To-Play layout, Table Balance surface. |
| Props/class names alter shared shell rendering | 3 | BOXE passes `boxe-*` page/product/table classes instead of Mines reference classes. |
| BOXE-scoped CSS alters shell area | 1 | `boxe.css` styles pre-game shell and gates directly. |
| Theme token drift | 0 active default drift found | BOXE seed uses empty tokens; shared provider loads tokens per title. |
| Container/layout divergence | 2 | BOXE product/table gates use local grid/centering containers. |

Stop-and-Ask trigger: this audit finds BOXE-local forks of protected shell
surfaces. Fixing them cleanly requires either a platform/shared extraction or
explicit authorization to reuse Mines-owned components/classes from BOXE, which
conflicts with current WP constraints and boundary tests.

## Phase Audit

### 1. Lobby Card -> Click -> Cashier Modal

Mines path:

- `frontend/app/ui/player-lobby-page.tsx:323` renders every catalog title with
  the same `PlayerGameCard`.
- `frontend/app/ui/player-lobby-page.tsx:347` opens the same
  `LaunchCashierModal`.
- `frontend/app/ui/player-lobby-page.tsx:611` builds launch URLs.
- `frontend/app/ui/player-lobby-page.tsx:645` uses Mines runtime copy only for
  `engine_code === "mines"`.

BOXE path:

- Same card and same modal component.
- `frontend/app/ui/player-lobby-page.tsx:617` adds BOXE-specific `mode=real_cash`
  for real launch.
- `frontend/app/ui/player-lobby-page.tsx:623` adds BOXE-specific
  `mode=real_bonus` for bonus launch.
- `frontend/app/ui/player-lobby-page.tsx:652` uses default cashier copy for
  non-Mines engines.

Divergence concrete:

- Cashier visual structure is shared.
- Launch URL params diverge for BOXE real/bonus.
- Cashier copy source diverges: Mines can use published Mines copy, BOXE uses
  hardcoded default cashier copy.

Root cause:

- Props / route behavior divergence.

Fix proposed:

- Leave route params only if BOXE backend requires them. This is behavioral, not
  visual.
- If cashier copy must be identical to Mines, move Launch Cashier copy into a
  game-agnostic platform source. Do not import Mines copy into BOXE.

### 2. Launch Cashier Modal

Mines path:

- Same `LaunchCashierModal` in `frontend/app/ui/player-lobby-page.tsx:477`.

BOXE path:

- Same `LaunchCashierModal`.

Divergence concrete:

- No component fork found.
- Copy source differs as noted above.

Root cause:

- Props/copy provider divergence.

Fix proposed:

- No BOXE-side visual fix required for structure.
- Platformize cashier copy if product requires text identity.

### 3. Provider Intro Gate

Mines path:

- `frontend/app/ui/mines/mines-standalone.tsx:1501` passes
  `MinesProviderBootstrap` into `GameBootShell`.
- `frontend/app/ui/mines/mines-provider-bootstrap.tsx:17` implements the intro:
  MP4/poster, 8s duration, preload, progress bar, skip behavior.
- CSS lives in `frontend/app/ui/mines/mines.css:26`.

BOXE path:

- `frontend/app/ui/boxe/boxe-standalone.tsx:99` creates a local
  `<article className="boxe-provider-intro">`.
- CSS lives in `frontend/app/ui/boxe/boxe.css:23`.

Divergence concrete:

- BOXE does not show the provider video/poster/progress implementation.
- BOXE shows a local centered text/button intro.
- BOXE completion is manual button click; Mines completion is media/progress
  driven with skip only when ready.

Root cause:

- BOXE fork / local version of protected shell surface.

Fix proposed:

- Clean fix: promote `MinesProviderBootstrap` to a game-agnostic shared
  provider intro component outside `frontend/app/ui/mines/`, then make both
  Mines and BOXE consume it.
- This requires editing shared/platform or Mines call sites, which is outside
  current WP constraints.
- BOXE-only alternatives would be hidden forks and should be rejected.

### 4. How-To-Play Gate

Mines path:

- `frontend/app/ui/mines/mines-standalone.tsx:1508` passes
  `MinesHowToPlayGate` into `GameBootShell`.
- `frontend/app/ui/mines/mines-how-to-play-gate.tsx:18` implements overlay,
  panel, heading, card grid, visuals, step badges and continue button.
- CSS lives in `frontend/app/ui/mines/mines.css:106`.

BOXE path:

- `frontend/app/ui/boxe/boxe-standalone.tsx:113` passes
  `BoxeHowToPlayContent`.
- `frontend/app/ui/boxe/boxe-how-to-play-content.tsx:3` implements its own
  article, heading, grid, cards and continue button.
- CSS lives in `frontend/app/ui/boxe/boxe.css:54`.

Divergence concrete:

- BOXE layout is not the Mines overlay/panel layout.
- BOXE omits the Mines visual card structure and uses simpler numbered
  sections.
- BOXE content can diverge by product decision, but the shell structure/layout
  currently diverges too.

Root cause:

- BOXE fork / local version of protected shell surface.

Fix proposed:

- Clean fix: create/promote a shared how-to-play shell layout that accepts
  game-specific step content/visuals as data or children. Mines and BOXE should
  consume the same layout.
- Current WP forbids editing `game-runtime` and Mines, so a clean fix cannot be
  completed only in BOXE.

### 5. Table Balance Gate

Mines path:

- `frontend/app/ui/mines/mines-standalone.tsx:336` shows table entry before
  provider intro for authenticated real play with no active table session.
- `frontend/app/ui/mines/mines-standalone.tsx:1536` renders
  `<section className="panel mines-launch-gate">`.
- The gate includes `MinesProviderBootstrapPreload`, close button, wallet source,
  available/max metrics, table entry input, quick chips and submit.
- CSS lives in `frontend/app/ui/mines/mines.css:2343`.

BOXE path:

- `frontend/app/ui/boxe/boxe-standalone.tsx:93` shows table balance after intro
  and how-to-play, for demo too.
- `frontend/app/ui/boxe/boxe-standalone.tsx:117` renders
  `<section className="boxe-gate boxe-table-balance">`.
- `frontend/app/ui/boxe/boxe-table-balance-config.ts:1` hardcodes quick amounts.
- BOXE gate includes placeholder copy: "Demo boot usa il balance runtime
  provvisorio. Il cashier reale arriva in Fase 5."
- CSS lives in `frontend/app/ui/boxe/boxe.css:99`.

Divergence concrete:

- Order differs: Mines real flow table gate comes before provider intro; BOXE
  table gate comes after provider intro and how-to-play.
- Eligibility differs: Mines table gate is real/auth/table-session-specific;
  BOXE shows a local gate based only on local completion flags.
- Visual surface differs completely.
- BOXE still contains stale implementation text saying real cashier arrives in
  Fase 5, although BOXE Fase 5 is closed.

Root cause:

- BOXE fork / local version of protected shell surface.
- Container/layout divergence.

Fix proposed:

- Clean fix requires BOXE to use the same table-session/table-balance surface as
  Mines, but that surface is Mines-owned code today.
- Do not copy the Mines gate into BOXE. Promote the table gate to a shared
  platform component or open a platform WP to make the shell own the visual.

### 6. Theme Tokens BOXE vs Mines

Mines path:

- `frontend/app/ui/mines/mines-standalone.tsx:259` reads theme assets/skin and
  applies Mines skin class modifiers.
- `frontend/app/ui/game-runtime/game-boot-shell.tsx:71` wraps both games in
  `TitleThemeProvider`.
- `frontend/app/lib/theme/title-theme-provider.tsx:54` uses shared
  `mines-theme-scope` for all titles.

BOXE path:

- `frontend/app/ui/boxe/boxe-standalone.tsx:37` only marks the theme resolved;
  it does not consume assets/skin for gameplay shell modifiers.
- `backend/migrations/sql/0041__boxe_catalog_seed.sql:98` seeds BOXE
  `title_configs` without explicit theme token overrides.

Divergence concrete:

- No default BOXE token drift found in seed. Empty BOXE tokens resolve through
  the shared theme service defaults.
- BOXE does not apply advanced Mines skin modifiers, but those are gameplay
  shell modifiers and not necessarily part of pre-game protected shell unless a
  published BOXE theme diverges.

Root cause:

- No active theme-token drift found.
- Potential props/class divergence if BOXE title theme is changed from
  backoffice.

Fix proposed:

- No theme-token fix in this WP unless product confirms BOXE published tokens
  should be reset to Mines/default.
- Keep a runtime check in manual verification: compare `/titles/mines_classic/theme`
  and `/titles/boxe001/theme` if visual drift persists after shell fix.

### 7. BOXE CSS

BOXE paths:

- `frontend/app/ui/boxe/boxe.css`
- `frontend/app/ui/boxe/boxe-animations.css`

Divergence concrete:

- `boxe.css:1` styles `.boxe-page-shell`.
- `boxe.css:8` styles `.boxe-product-shell` and `.boxe-gate`.
- `boxe.css:23` styles `.boxe-provider-intro`.
- `boxe.css:54` styles `.boxe-how-to-grid`.
- `boxe.css:99` styles `.boxe-table-balance-options`.
- These selectors do not hijack Mines classes globally, but they create a
  separate BOXE visual shell for the protected zone.
- `boxe-animations.css` is gameplay-specific; no protected shell selector found.

Root cause:

- BOXE-scoped CSS creates a local shell visual instead of consuming shared
  shell visuals.

Fix proposed:

- Remove or stop using BOXE pre-game shell selectors after a shared/platform
  pre-game shell exists.
- Keep BOXE gameplay selectors for gameplay-only surfaces.

## Stop Recommendation

Do not proceed with a BOXE-only Step 2 fix under the current constraints.

Reason:

1. The audit found BOXE-local forks of protected shell surfaces.
2. The clean fix requires extracting/promoting shared components or changing
   Mines to consume newly shared components.
3. The WP explicitly forbids edits to:
   - `frontend/app/ui/mines/`
   - `frontend/app/ui/game-runtime/`
   - shared shell platform
4. Importing Mines components from BOXE would violate the contract boundary:
   `tests/contract/test_game_runtime_frontend_boundary.py` forbids BOXE importing
   Mines.
5. Copying Mines markup/classes into BOXE would be a hidden fork, explicitly
   rejected by the WP.

Recommended next WP:

```text
WP-PLATFORM-PREGAME-SHELL-EXTRACTION
```

Allowed changes for that WP:

- Move provider intro from Mines-owned path to shared platform/runtime UI.
- Move how-to-play layout shell to shared platform/runtime UI, with
  game-specific step content passed as data/children.
- Move table balance visual shell to shared platform/runtime UI or a platform
  launch module, with game-specific callbacks/config passed as props.
- Update Mines and BOXE to consume those shared surfaces.
- Re-run Mines visual baseline and BOXE visual baseline.

Current branch state after Step 1:

- Audit doc only.
- No code changes applied.
