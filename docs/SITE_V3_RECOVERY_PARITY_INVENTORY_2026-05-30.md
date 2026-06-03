# Site V3 Recovery Parity Inventory - Phase 1 Audit - 2026-05-30

Status: PHASE 1 AUDIT ONLY. No code, CSS, UI, game logic, backend, RNG, payout, board, reveal, replay, or GMP-5C changes were made in this phase.

## Scope and Baseline

- CTO Phase 0 backup: `backup/site-v3-codex-run-2026-05-30` at commit `6141c17`; working tree intentionally left intact.
- Baseline truth for this audit: separate worktree on `main`, commit `4715fda`, path `../casinoking-platform-main-baseline`.
- Baseline runtime URL: `http://localhost:3100`, using the old `frontend` service from `main` and the existing local backend on `http://localhost:8000`.
- Current branch runtime URL: `http://localhost:3000`, branch `feature/site-v3-cms-ia-cleanup`, HEAD `8c501e8`.
- Current direct V3 renderer remains available on `http://localhost:3001`.
- Artifact root: `artifacts/site_v3_recovery_parity_inventory_2026-05-30/`.
- Metadata written under `artifacts/site_v3_recovery_parity_inventory_2026-05-30/metadata/`.
- Admin smoke account used: dedicated Codex technical admin only. Michele/admin personal account was not used.
- Player fixture used for account screenshots: `codex.audit.phase1.20260530@example.com`. It was created as an audit fixture during capture; no code or config was changed.

Game capture notes:

- Final game screenshots use explicit boot URLs with `title_code` and `mode=demo`.
- Mines: `mines001b`; HI-LO: `hilo001`; BOXE: `boxe001`.
- Initial direct captures without `title_code` are superseded by the recaptured PNGs and by `metadata/game-recapture-results.json` plus `metadata/game-mines-recapture-results.json`.

## Screenshot Inventory

| Surface | Baseline main screenshot | Current branch screenshot | Current observation | Regression type | Suspect files | Severity |
| --- | --- | --- | --- | --- | --- | --- |
| Mines desktop | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-mines-desktop.png` | Baseline direct runtime shows native top-right X. Current V3 iframe shell removes that X from visible gameplay. Board/content remain visible. | container + functional | `frontend-v3/app/ui/game-frame-page.tsx:58-59`, `frontend-v3/app/ui/game-frame-page.tsx:122-132`, `frontend-v3/app/globals.css:2109-2141`, `frontend-v3/app/ui/game-runtime/game-runtime.css:512-830` | P0 |
| Mines mobile | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-mobile.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-mines-mobile.png` | Current is broadly similar but tighter/clipped in header/payout row; current remains iframe-hosted. | container | same as Mines desktop | P1 |
| HI-LO desktop | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-hi-lo-desktop.png` | Current is close visually; still iframe-hosted and slightly different in margins/input treatment. X is visible on desktop in this capture. | container | `frontend-v3/app/ui/game-frame-page.tsx`, `frontend-v3/app/globals.css`, `frontend-v3/app/ui/game-runtime/game-runtime.css` | P2 |
| HI-LO mobile | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-mobile.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-hi-lo-mobile.png` | Baseline mobile shows native X. Current mobile loses the X and changes control/input treatment. | container + functional | `frontend-v3/app/ui/game-frame-page.tsx`, `frontend-v3/app/globals.css`, `frontend-v3/app/ui/game-runtime/game-runtime.css` | P0 |
| BOXE desktop | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-boxe-desktop.png` | Baseline direct runtime shows native top-right X. Current V3 iframe shell removes it. Pyramid/content remain visible. | container + functional | `frontend-v3/app/ui/game-frame-page.tsx`, `frontend-v3/app/globals.css`, `frontend-v3/app/ui/game-runtime/game-runtime.css` | P0 |
| BOXE mobile | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-mobile.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/game-boxe-mobile.png` | Both are close; current has slightly tighter payout row and hosted container differences. | container | same as BOXE desktop | P2 |
| Finance filters + bank session report | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/finance-filters-bank-session-report-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/finance-filters-bank-session-report-desktop.png` | Baseline is compact dark shell with filters in two rows and report visible. Current is white, oversized, single-column filters; report content is pushed below fold. | container + content | `frontend-v3/app/globals.css:2302-2333`, `frontend-v3/app/globals.css:3106-3374`, `frontend-v3/app/ui/casinoking-console.tsx:2235`, `frontend-v3/app/ui/admin-finance-panel.tsx:174-288` | P0 |
| Finance ledger/wallet report surface | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/finance-ledger-report-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/finance-ledger-report-desktop.png` | Baseline preserves card rows and dark shell. Current collapses labels/values into run-on text, loses spacing, and switches to white shell. | container + content | `frontend-v3/app/globals.css:2302-2333`, `frontend-v3/app/globals.css:3106-3374`, `frontend-v3/app/ui/player-admin-panel.tsx:186-288` | P0 |
| Finance round detail | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/finance-round-detail-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/finance-round-detail-desktop.png` | Current still expands detail, but the light shell and oversized filters make the report less compact; replay buttons are dark/low-readability. | container + content | `frontend-v3/app/globals.css`, `frontend-v3/app/ui/admin-finance-panel.tsx:285-418`, `frontend-v3/app/ui/admin-finance-panel.tsx:475-623` | P1 |
| Admin login | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/admin-login-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/admin-login-desktop.png` | Baseline dark full-width admin panel. Current white centered card, different visual system and button color. | container + content | `frontend-v3/app/globals.css`, `frontend-v3/app/admin/page.tsx`, `frontend-v3/app/ui/casinoking-console.tsx` | P1 |
| Admin shell/menu | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/admin-shell-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/admin-shell-desktop.png` | Baseline dark compact shell with blue action grid. Current white shell with green buttons and large empty background. | container + content | `frontend-v3/app/ui/casinoking-console.tsx:2235`, `frontend-v3/app/ui/admin-shell-panel.tsx:59-113`, `frontend-v3/app/globals.css:3106-3219` | P0 |
| Admin account / My Space | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/admin-account-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/admin-account-desktop.png` | Baseline dark shell with compact cards. Current white shell and flatter forms; label/value spacing differs. | container + content | `frontend-v3/app/ui/casinoking-console.tsx:2235`, `frontend-v3/app/globals.css:3106-3374` | P1 |
| Player login | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/player-login-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/player-login-desktop.png` | Current keeps dark player surface but changes copy, scale, button color, and field layout. | content + container | `frontend-v3/app/ui/player-login-page.tsx`, `frontend-v3/app/globals.css:1554-1655` | P2 |
| Player account | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/player-account-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/player-account-desktop.png` | Current removes the bottom "Dettagli account" strip and keeps a more compact account view. This may be intentional from user feedback, but it diverges from main baseline. | content | `frontend-v3/app/ui/player-account-page.tsx`, `frontend-v3/app/globals.css:1554-1655` | P2 / CTO decision |
| Player admin list | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/admin-player-ledger-surface-desktop.png` | `artifacts/site_v3_recovery_parity_inventory_2026-05-30/current-branch/admin-player-ledger-surface-desktop.png` | Baseline list remains inside dark shell with large cards. Current is light/white and looser. | container + content | `frontend-v3/app/ui/player-admin-panel.tsx`, `frontend-v3/app/globals.css:3106-3374` | P1 |

Artifact manifest:

- `metadata/artifact-manifest.json` lists all PNGs, dimensions and byte sizes.
- Current inventory contains 30 PNG screenshots: 15 baseline and 15 current.

## CSS Contamination Map

Line counts observed in this phase:

- `frontend-v3/app/globals.css`: `main` has 766 lines; current branch has 3869 lines.
- `frontend-v3/app/ui/game-runtime/game-runtime.css`: absent on `main`; current branch has 935 lines.

Exact selector match metadata:

- `metadata/css-actual-selector-matches-v2.json`: actual `querySelectorAll` matches on current game/admin/finance DOM, including iframe runtime frames.
- `metadata/css-contamination-candidates.json`: candidate selector/class-token analysis.

### globals.css selectors that match game DOM

These are introduced relative to `main` and matched current game host or runtime DOM:

- Host iframe/container selectors: `.site-v3-game-shell`, `.site-v3-game-host`, `.site-v3-game-frame-wrap`, `.site-v3-game-frame` (`frontend-v3/app/globals.css:2109-2141`, responsive continuation at `2215-2219`).
- Generic selectors that also match runtime game DOM inside frames: `.button`, `.button-secondary`, `.button-ghost`, `.button-secondary:disabled`, `.status-badge`, `.status-badge.info`, `.stack`, `.field`, `.field input`, `.field span` (`frontend-v3/app/globals.css:3016-3072`, `3267-3280`).

Risk: these selectors are not game-specific and can override or interact with shared game class names. They are suspects for button, input, and spacing differences visible in HI-LO/Mines/BOXE captures.

### globals.css selectors that match finance/admin DOM

These introduced selectors matched Finance, Player admin ledger/wallet surface, admin menu, or My Space DOM:

- Admin page wrapper: `.site-v3-admin-page`, `.site-v3-admin-page button`, `.site-v3-admin-page input`, `.site-v3-admin-page select` (`frontend-v3/app/globals.css:2302-2333`).
- Admin console wrapper: `.admin-console-page`, `.admin-console-page .dashboard-grid-admin`, `.admin-console-page .stack`, `.admin-console-page .panel`, `.admin-console-page .panel-header`, `.admin-console-page .panel-header h2`, `.admin-console-page .panel-header p`, `.admin-console-page .actions`, `.admin-console-page .inline-actions`, `.admin-console-page .admin-shell-nav-actions`, `.admin-console-page .admin-menu-grid`, `.admin-console-page .admin-menu-grid .button`, `.admin-console-page .field label` (`frontend-v3/app/globals.css:3106-3219`).
- Broad admin/card/form selectors: `.admin-card`, `.admin-card h3`, `.admin-card label`, `.admin-card input`, `.admin-card select`, `.admin-card span`, `.admin-card strong`, `.admin-card .mono`, `.field`, `.field input`, `.field select`, `.field-grid`, `.helper`, `.meta-pill`, `.mono`, `.status-inline`, `.status-inline.info`, `.status-inline.success`, `.button-secondary`, `.button-secondary:disabled`, `.button-ghost`, `.button-ghost:disabled`, `.stack` (`frontend-v3/app/globals.css:3231-3374`).

Risk: this is the primary CSS contamination for INC-11. It replaces the dark compact admin/report styling with a light, large, generic admin layer across Finance, Player admin, My Space, and the admin menu.

### game-runtime.css selectors that match game DOM

The whole file is new relative to `main`. These introduced selectors matched current game runtime DOM:

- Viewport/short-height gate: `.game-short-viewport-gate`, `.game-short-viewport-gate__panel`, `.game-short-viewport-gate__icon`, `.game-short-viewport-gate__icon span`, `.game-short-viewport-gate__copy`, `.game-short-viewport-gate__copy strong`, `.game-short-viewport-gate__copy span` (`frontend-v3/app/ui/game-runtime/game-runtime.css:109-165`).
- Generic runtime chrome/control selectors: `.game-control-rail`, `.game-product-shell`, `.game-visual-product-shell`, `.game-visual-control-rail`, `.game-runtime-tools`, `.game-icon-button`, `.game-info-button`, `.game-runtime-clock`, `.game-runtime-clock span`, `.game-runtime-clock strong`, `.game-audio-control`, `.game-audio-icon`, `.game-mode-badge` (`frontend-v3/app/ui/game-runtime/game-runtime.css:512-596`).
- Generic chip/action/balance selectors: `.game-chip-row`, `.game-chip`, `.game-chip.active`, `.game-action-primary.button`, `.game-settings-panel`, `.game-bet-field`, `.game-quick-chip-row`, `.game-quick-chip`, `.game-action-buttons`, `.game-balance-footer`, `.game-balance-footer > div`, `.game-visual-balance-footer`, `.game-visual-balance-footer > div`, `.game-visual-balance-footer strong`, `.game-mobile-control-stack`, `.game-mobile-control-stack.mines-mobile-play-stack`, `.mines-mobile-settings-summary .mines-mobile-settings-chip.choice-chip` (`frontend-v3/app/ui/game-runtime/game-runtime.css:723-849`).

Risk: this file introduces a shared game-runtime CSS layer that did not exist on `main`. It is not RNG/math/board logic, but it does affect runtime layout/chrome and is therefore in scope for visual parity recovery only after CTO approval.

## CasinoKingConsole Admin Wrapper Map

The current branch routes multiple admin areas through:

`frontend-v3/app/ui/casinoking-console.tsx:2235`

```tsx
<main className={isAdminArea ? "site-v3-admin-page admin-console-page" : "page-shell"}>
```

Admin sections declared in `CasinoKingConsole` (`frontend-v3/app/ui/casinoking-console.tsx:105-113`) and rendered through `AdminShellPanel` (`frontend-v3/app/ui/casinoking-console.tsx:3244-3518`, `frontend-v3/app/ui/admin-shell-panel.tsx:59-145`):

| Section key | UI label | Current status for INC-11 |
| --- | --- | --- |
| `menu` | Backoffice menu | Passes through `site-v3-admin-page admin-console-page`; current visual regression confirmed. |
| `casino_king` | Finance | Passes through wrapper; Finance filters/report regression confirmed. |
| `players` | Player admin | Passes through wrapper; list/detail/ledger-wallet surface regression confirmed. |
| `games` | Games | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |
| `site` | Site | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |
| `site_v3` | Site V3 | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |
| `audit_log` | LOG | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |
| `my_space` | My Space | Passes through wrapper; admin account regression confirmed. |
| `admins` | Administrators | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |
| `platform_settings` | Platform Settings | Passes through wrapper; not fully screenshot-audited in this Phase 1 set. |

Important: admin login is captured as a separate surface and visually regressed to the same light style, but it is not listed above as an `AdminShellPanel` section.

## What Was Not Done

- No code changes.
- No CSS changes.
- No game UI changes.
- No backend changes.
- No revert of CTO-approved backend GMP work.
- No RNG/math/payout/board/reveal/replay logic changes.
- No GMP-5C.
- No Phase 2 recovery.
- No redesign.
- No use of Michele's personal/admin account.
- No claim that parity is fixed; this is inventory only.

## Phase 1 Result By Surface

| Area | Phase 1 audit status |
| --- | --- |
| Mines desktop/mobile | Captured baseline and current. Desktop close/X regression confirmed; mobile container/header differences documented. |
| HI-LO desktop/mobile | Captured baseline and current. Desktop close/X visible in current capture; mobile close/X regression confirmed. |
| BOXE desktop/mobile | Captured baseline and current. Desktop close/X regression confirmed; mobile close/X not visible in either baseline or current capture. |
| Finance filters/bank report | Captured baseline and current. Current compactness/theme regression confirmed. |
| Finance ledger/wallet surface | Captured baseline and current. Current label/value spacing and theme regression confirmed. |
| Finance round detail | Captured baseline and current. Detail expands; current readability/compactness regression documented. |
| Admin shell/menu | Captured baseline and current. Current theme/spacing/button-color regression confirmed. |
| Admin login | Captured baseline and current. Current theme/layout regression confirmed. |
| Admin account/My Space | Captured baseline and current. Current theme/form regression confirmed. |
| Player login/account | Captured baseline and current. Differences documented; account bottom detail removal requires CTO/product decision because it diverges from main baseline but also reflects prior user feedback. |

## Next Step

Stop here until CTO approval. The next approved phase should be a Phase 2 recovery plan that restores parity toward `main` by first isolating/removing the broad admin/global CSS contamination, then restoring game shell close/X parity without touching game logic or the CTO-approved backend GMP files.
