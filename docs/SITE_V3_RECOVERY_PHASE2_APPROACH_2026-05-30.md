# Site V3 Recovery - Phase 2A CSS Isolation Approach - 2026-05-30

Status: PROPOSAL ONLY. No code, CSS, UI, backend, game runtime, game logic, RNG, math, payout, board, reveal, replay, or GMP backend changes are authorized or made by this document.

Decision gate: stop after this document. Phase 2B must not start until CTO approval.

## Inputs Read

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ACTIVE_OPEN_LOOPS.md`
- `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md`

Phase 1 baseline/report inputs:

- Baseline truth remains `main`, commit `4715fda`, captured from the separate worktree documented in Phase 1.
- Current branch in Phase 1 was `feature/site-v3-cms-ia-cleanup`, current Site V3 public edge `http://localhost:3000`.
- Screenshot artifact root remains `artifacts/site_v3_recovery_parity_inventory_2026-05-30/`.
- Phase 1 measured `frontend-v3/app/globals.css` as 766 lines on `main` and 3869 lines on the current branch. If the CTO brief references an intermediate 3165-line snapshot, the current working value must be rechecked in Phase 2B before code starts.
- `frontend-v3/app/ui/game-runtime/game-runtime.css` is absent on `main` and 935 lines on the current branch.

Protected in this phase and in the first CSS isolation pass:

- `backend/app/modules/games/boxe/service.py`
- `backend/app/modules/games/boxe/platform_client.py`
- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/api/routes/boxe.py`
- `backend/app/api/routes/demo.py`

These are CTO-approved GMP/backend changes and must not be reverted by Phase 2 CSS recovery.

## A1. Isolation Strategy

### Recommended Strategy: Option 1, `revert+re-scope`

Use `main`'s `frontend-v3/app/globals.css` as the baseline CSS anchor, then reintroduce only the CSS needed by new Site V3 CMS surfaces under explicit Site V3 CMS roots. The objective is not to redesign; it is to restore parity toward `main` first and then add back CMS/builder/Module Studio styling without leaking into games, Finance, or legacy admin reports.

This is the recommended path because Phase 1 proved that the current CSS contamination is broad and mixed:

- Game host selectors were added globally: `.site-v3-game-shell`, `.site-v3-game-host`, `.site-v3-game-frame-wrap`, `.site-v3-game-frame` at `frontend-v3/app/globals.css:2109-2141`, with responsive continuation at `frontend-v3/app/globals.css:2215-2219`.
- Admin-wide selectors were added globally: `.site-v3-admin-page` and generic form descendants at `frontend-v3/app/globals.css:2302-2333`.
- Generic selectors now affect many surfaces: `.button-secondary`, `.button-ghost` at `frontend-v3/app/globals.css:3017-3072`; `.field input`, `.field select` at `frontend-v3/app/globals.css:3267-3268`; `.field-grid` at `frontend-v3/app/globals.css:3366-3374`.
- Legacy admin/Finance surfaces are wrapped into the new Site V3 admin skin through `frontend-v3/app/ui/casinoking-console.tsx:2235`.

The current CSS file is therefore not a safe base for surgical edits. It already encodes the regression.

| Option | What it saves | What it breaks or risks | Effort | Reversibility | Verdict |
| --- | --- | --- | --- | --- | --- |
| Option 1: `revert+re-scope` | Restores the known `main` visual contract first; reduces unknown cascade; gives Finance/admin reports a path back to dark compact parity; makes game iframe selector gates easier to prove. | Temporarily removes newer Site V3 CMS/builder/Module Studio styling until it is reintroduced under scoped roots. Some player Site V3 pages may need explicitly scoped re-additions. | Medium-high, but deterministic: baseline first, then scoped additions with screenshot gates. | High. The baseline CSS anchor is a known file, and each reintroduced block can be reviewed and reverted independently. | Recommended. |
| Option 2: `scope-in-place` | Preserves more of the current Site V3 CMS/builder look at the start; fewer immediate visual breakages in new CMS surfaces. | Keeps the polluted cascade as the working base; every missed generic selector can keep breaking games/Finance/admin; hard to prove that no V3/admin/global selectors still match inside game iframes. | High and open-ended: requires auditing/namespacing thousands of lines while preserving behavior. | Medium-low. The resulting file still contains mixed legacy, Site V3, player, admin, and game concerns, so regressions remain hard to isolate. | Rejected for Phase 2 recovery. |

Reason for rejecting Option 2: it optimizes for preserving the current broken file instead of restoring the known-good boundary. The Phase 2 objective is containment and parity, not rescuing every current CSS rule.

## A2. Game Boundary

### Current State

The current Next root layout imports shared CSS globally:

- `frontend-v3/app/layout.tsx:3` imports `./globals.css`.
- `frontend-v3/app/layout.tsx:4` imports `./ui/game-runtime/runtime-base.css`.
- `frontend-v3/app/layout.tsx:5` imports `./ui/game-runtime/game-runtime.css`.
- `frontend-v3/app/layout.tsx:6-9` imports Mines, BOXE and HI-LO CSS.

The game runtime pages render standalone game components:

- Mines: `frontend-v3/app/runtime/mines/page.tsx:1` and `frontend-v3/app/runtime/mines/page.tsx:4`.
- BOXE: `frontend-v3/app/runtime/boxe/page.tsx:1` and `frontend-v3/app/runtime/boxe/page.tsx:6`.
- HI-LO: `frontend-v3/app/runtime/hi-lo/page.tsx:1` and `frontend-v3/app/runtime/hi-lo/page.tsx:6`.

The public Site V3 game host builds iframe URLs and embeds them here:

- Runtime path type: `frontend-v3/app/ui/game-frame-page.tsx:13`.
- Forced embed query: `frontend-v3/app/ui/game-frame-page.tsx:58-60`.
- Host shell/iframe classes: `frontend-v3/app/ui/game-frame-page.tsx:122-132`.

Phase 1 confirmed that the visual baseline for games is the old frontend on `main`. The games now in `frontend-v3/app/runtime/*` are reimplementations/migrations of that baseline, so Phase 2B must verify parity against the captured `main` screenshots, not against the current V3 rendering.

### Boundary Rule For Phase 2B

No Site V3 CMS/admin/global selector may match DOM inside a game runtime iframe.

Allowed:

- Host-only iframe shell selectors, limited to the parent document: `.site-v3-game-shell`, `.site-v3-game-host`, `.site-v3-game-frame-wrap`, `.site-v3-game-frame`.
- Game-owned selectors from game CSS/runtime CSS, only if parity screenshots pass.

Not allowed:

- Bare/global selectors from `globals.css` that match runtime iframe DOM, such as `.button`, `.button-secondary`, `.button-ghost`, `.field`, `.field input`, `.field select`, `.stack`, `.status-badge`, `.admin-card`, `.field-grid`.
- Any Site V3 CMS/admin selector matching inside `/runtime/mines`, `/runtime/boxe`, or `/runtime/hi-lo` iframe DOM.

Phase 2B verification must include a DOM selector gate like the Phase 1 metadata in `artifacts/site_v3_recovery_parity_inventory_2026-05-30/metadata/css-actual-selector-matches-v2.json`: for each runtime iframe, introduced V3/admin/global selectors must return zero matches.

### Treatment Of `game-runtime.css`

`frontend-v3/app/ui/game-runtime/game-runtime.css` is game-owned compatibility CSS, not CMS/admin CSS. It is new relative to `main`, so it remains suspect for visual parity, but it must not be treated as an admin/CMS leak.

Known matching groups from Phase 1 include:

- Short viewport gate: `frontend-v3/app/ui/game-runtime/game-runtime.css:109-165`.
- Runtime chrome/control layer: `.game-control-rail`, `.game-product-shell`, `.game-runtime-tools`, `.game-icon-button`, `.game-audio-control` at `frontend-v3/app/ui/game-runtime/game-runtime.css:512-596`.
- Settings/action/balance layer: `.game-settings-panel`, `.game-action-buttons`, `.game-balance-footer` at `frontend-v3/app/ui/game-runtime/game-runtime.css:792-825`.

Phase 2B should not delete or rewrite this file as a first move. The proposed order is:

1. Freeze it while removing global/admin leakage from `globals.css`.
2. Re-test game parity against `main`.
3. If a remaining difference is proven to come from `game-runtime.css`, reduce or quarantine only the proven selector group.
4. Never touch game logic files, RNG, math, payout, board, reveal, or backend GMP files.

The game close/X parity must be verified by screenshots for Mines, BOXE and HI-LO on desktop and mobile against Phase 1 baseline artifacts.

## A3. Admin And Finance Boundary

### Current Contamination

Legacy admin/Finance/player admin surfaces are currently routed through the Site V3 admin wrapper:

- `frontend-v3/app/ui/casinoking-console.tsx:2235`:

```tsx
<main className={isAdminArea ? "site-v3-admin-page admin-console-page" : "page-shell"}>
```

The section model includes the migrated admin areas:

- `frontend-v3/app/ui/casinoking-console.tsx:103-113`.
- Labels and section names around `frontend-v3/app/ui/casinoking-console.tsx:746-759`.
- `AdminShellPanel` render area: `frontend-v3/app/ui/casinoking-console.tsx:3244-3518`.
- Finance render begins at `frontend-v3/app/ui/casinoking-console.tsx:3272`.
- Site V3 render: `frontend-v3/app/ui/casinoking-console.tsx:3493`.
- LOG render: `frontend-v3/app/ui/casinoking-console.tsx:3497`.
- Platform Settings render: `frontend-v3/app/ui/casinoking-console.tsx:3515`.

The admin shell component uses generic button classes:

- `frontend-v3/app/ui/admin-shell-panel.tsx:39-59` component start.
- `frontend-v3/app/ui/admin-shell-panel.tsx:73-145` nav/action buttons.

The Site V3 CMS/builder legitimately uses Site V3-specific classes:

- Admin Site V3 page roots: `frontend-v3/app/ui/admin-site-v3-page.tsx:119-190`.
- Builder root and hero: `frontend-v3/app/ui/site-v3-admin/site-v3-admin-builder.tsx:817-847`.
- CMS shell/main: `frontend-v3/app/ui/site-v3-admin/site-v3-admin-builder.tsx:847-857`.
- Composition screen card: `frontend-v3/app/ui/site-v3-admin/screens/site-v3-composition-screen.tsx:46`.
- Module Studio screen: `frontend-v3/app/ui/site-v3-admin/screens/site-v3-module-studio-screen.tsx:243-247`.
- CMS nav: `frontend-v3/app/ui/site-v3-admin/screens/site-v3-admin-nav.tsx:21-28`, module studio labels at `frontend-v3/app/ui/site-v3-admin/screens/site-v3-admin-nav.tsx:85-98`, public link at `frontend-v3/app/ui/site-v3-admin/screens/site-v3-admin-nav.tsx:110`.

### Proposed Boundary

Phase 2B should split the CSS ownership explicitly:

1. Legacy admin/Finance/player admin must not inherit `site-v3-admin-page admin-console-page`.
   - The target is parity with `main`: dark, compact, report-first, not a new light Site V3 CMS skin.
   - Finance filters, ledger report, bank session report and round detail must return to the compact report contract captured in Phase 1.

2. Site V3 CMS/builder/Module Studio may keep its own visual system, but only under a dedicated Site V3 CMS root.
   - Candidate root should be explicit and unique to CMS/builder, not shared with Finance or admin menu.
   - Generic classes such as `.admin-card`, `.field-grid`, `.button-secondary`, `.button-ghost`, `.field input`, and `.field select` must either become CMS-scoped or return to the legacy `main` behavior.

3. The current broad CSS blocks are not acceptable as shared globals:
   - `.site-v3-admin-page` at `frontend-v3/app/globals.css:2302`.
   - `.site-v3-admin-page button/input/select/textarea` at `frontend-v3/app/globals.css:2330-2333`.
   - `.admin-card` at `frontend-v3/app/globals.css:2512` and `frontend-v3/app/globals.css:2535`.
   - `.admin-console-page` block at `frontend-v3/app/globals.css:3106-3219`.
   - `.admin-card h3/h4/label/p/span/strong` and form controls at `frontend-v3/app/globals.css:3253-3268`.
   - `.field-grid` at `frontend-v3/app/globals.css:3366-3374`.

4. Site V3 CMS CSS to preserve/re-scope includes:
   - `.site-v3-admin-login` at `frontend-v3/app/globals.css:2337`.
   - `.site-v3-admin-topbar` around `frontend-v3/app/globals.css:2415`.
   - `.site-v3-cms-nav` at `frontend-v3/app/globals.css:2513`.
   - `.site-v3-cms-shell` at `frontend-v3/app/globals.css:2605`.
   - `.site-v3-studio-field-builder` at `frontend-v3/app/globals.css:2749`.
   - Responsive CMS/admin additions at `frontend-v3/app/globals.css:3768-3813`.

The isolation should not be a redesign. Finance/admin parity is toward `main`; Site V3 CMS preservation is scoped and verified separately.

## A4. Admin Surfaces To Add In Phase 2B Verification

Phase 1 did not fully screenshot these six admin surfaces. They must be included in Phase 2B before the CSS recovery is called complete:

- Games
- Site
- Site V3
- LOG
- Administrators
- Platform Settings

Each must be captured after the admin/Finance boundary split and after Site V3 CMS scoped CSS is restored.

## A5. Ambiguities To Resolve Without Fixing In Phase 2A

### 1. HI-LO: visual/container break vs functional break

Known from Phase 1:

- HI-LO desktop current capture: X is visible; current is visually close but iframe-hosted and has margin/input differences. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:29`.
- HI-LO mobile current capture: baseline mobile shows native X, current mobile loses it and changes control/input treatment. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:30`.

State of evidence: Phase 1 proves a visual/container regression, especially mobile X and control treatment. It does not prove a game-mechanics break because Phase 1 did not run a full HI-LO action/replay/i18n functional smoke.

Phase 2B should classify HI-LO as:

- Confirmed: visual/container regression.
- Not yet proven: RNG/math/payout/round/replay functional break.
- Required gate if CTO wants functional classification: start round, choose red/black/up/down where possible, skip/cashout path, replay open, language/i18n smoke. This must not touch game logic.

### 2. Game close/X: current reality vs previous native close artifact

Previous artifact:

- `artifacts/site_v3_native_game_close_restore_2026-05-30/native_close_verified4_metrics.json:2` reports `"pass": true`.
- Mines reported no outer host close/topbar at lines `7-8`, native close class/text at `14-17`.
- BOXE reported no outer host close/topbar at lines `32-33`, native close class/text at `39-42`.
- HI-LO reported no outer host close/topbar at lines `57-58`, native close class/text at `64-67`.

Current Phase 1 parity evidence conflicts with relying on that artifact alone:

- Mines desktop: baseline has native X, current public V3 shell removes visible X. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:27`.
- BOXE desktop: baseline has native X, current public V3 shell removes visible X. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:31`.
- HI-LO mobile: baseline has native X, current public V3 shell loses it. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:30`.
- HI-LO desktop: X is visible in current capture. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:29`.

Conclusion: the prior native close artifact is insufficient for Phase 2B sign-off. It may have tested a different surface, viewport, timing, or direct runtime state. Phase 2B must verify the public Site V3 routes on `http://localhost:3000/mines`, `/boxe`, `/hi-lo` desktop and mobile against `main` screenshots.

### 3. Player account bottom "Dettagli account" strip

Phase 1 evidence:

- Current player account removes the bottom "Dettagli account" strip and is more compact. See `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md:40`.
- Phase 1 marked it as `P2 / CTO decision`, not an automatic bug.

This is a product decision, not a CSS isolation decision.

Required decision label for Phase 2B:

- `DECISIONE CTO/Michele`: restore strict `main` parity, or keep the removal because it follows prior Michele feedback about redundant account repetition.

Until that decision is explicit, Phase 2B should not re-add or further remove that strip.

## A6. Proposed Phase 2B Execution Order

Every micro-step must be gated with screenshots and a short result note before continuing.

### B0. Pre-flight guard

- Confirm branch, dirty files and protected backend GMP files.
- Confirm no edits to game logic paths.
- Re-run or reuse Phase 1 artifact manifest to know exact baseline screenshot names.
- Gate: report says "no code changed yet" and lists protected files untouched.

### B1. Baseline CSS anchor

- Restore `frontend-v3/app/globals.css` to the `main` baseline as the controlled anchor.
- Do not modify `game-runtime.css` in this step.
- Capture Finance filters/report, admin shell, admin login, player login/account, and three games desktop/mobile.
- Gate: identify which regressions improve, and which new Site V3 CMS surfaces lose styling because CMS CSS is not yet reintroduced.

### B2. Legacy admin/Finance root split

- Remove legacy admin/Finance/player admin dependence on the Site V3 CMS wrapper contract.
- Restore dark compact admin/report behavior toward `main`.
- Capture Finance filters + bank session report, ledger report, round detail, admin shell/menu, admin login, My Space, player admin list.
- Gate: Finance/report/admin screenshots must match `main` in theme, compactness, and readability; no Site V3 CMS styling is allowed to leak into these reports.

### B3. Reintroduce Site V3 CMS CSS under scoped root only

- Reintroduce CMS/builder/Module Studio styling under a dedicated CMS root.
- Keep generic helpers such as `.admin-card`, `.field-grid`, `.button-secondary`, `.button-ghost`, `.field input`, `.field select` scoped to CMS or legacy roots as appropriate.
- Capture `/admin/site-v3` dashboard, settings, composition, module library, Module Studio, preview live.
- Gate: CMS/builder usable and visually coherent; Finance/admin screenshots from B2 remain unchanged.

### B4. Game iframe selector gate

- Run selector matching inside runtime iframes for Mines, BOXE and HI-LO.
- Gate: no Site V3 CMS/admin/global selectors match game iframe DOM.
- Allowed matches must be game-owned selectors only.

### B5. Game visual parity pass

- Capture Mines, HI-LO and BOXE desktop/mobile on public Site V3 routes.
- Verify close/X, sound control, compactness, board/content positioning and mobile layout against Phase 1 `main` baseline screenshots.
- Only if a remaining regression is proven to come from `game-runtime.css`, make the minimum scoped CSS adjustment in that file.
- Gate: no game logic/backend file diffs; screenshot parity accepted or remaining deltas explicitly classified.

### B6. Admin surfaces not captured in Phase 1

- Capture and verify Games, Site, Site V3, LOG, Administrators and Platform Settings.
- Gate: each surface must be classified as pass, acceptable delta, or regression with suspect file.

### B7. Final diff and recovery report

- Confirm touched files are limited to CSS/root ownership needed for isolation.
- Confirm protected GMP backend files untouched.
- Confirm no RNG/math/payout/board/reveal/replay logic touched.
- Produce a Phase 2B implementation report with screenshot artifact paths, pass/fail by surface, and remaining CTO/Michele decisions.

## Stop Conditions

Stop immediately and ask CTO if any of these happen in Phase 2B:

- CSS isolation requires touching game logic, RNG, math, payout, board, reveal, replay, or backend GMP files.
- Restoring `main` CSS breaks a critical CMS/admin capability in a way that cannot be re-scoped without code ownership changes.
- The selector gate still finds V3/admin/global matches inside game iframes after the scoped CSS pass.
- Player account "Dettagli account" requires product decision and no CTO/Michele decision is available.

## Delivery Status For This Document

- Done: Phase 2A approach written.
- Done: one strategy selected and justified.
- Done: game boundary, admin/Finance boundary, six missing admin surfaces, three ambiguities and Phase 2B gated order documented.
- Not done by design: no code, no CSS, no UI, no backend, no screenshots, no Phase 2B implementation.
- Next required action: CTO approval or requested changes to this approach.
