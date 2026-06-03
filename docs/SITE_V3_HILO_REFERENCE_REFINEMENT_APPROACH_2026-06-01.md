Status: PROPOSED - PART A ONLY
Last meaningful update: 2026-06-01

# Site V3 HI-LO Reference Refinement Approach

## 1. Scope

This is Parte A only: audit and approach. No product code, CSS, backend,
gameplay, RNG, math, payout, board, reveal or replay logic has been changed.

Goal: make HI-LO the clean Site V3 reference game before COINS/game 4. This is
not a redesign. The target is a clean v3 example for CSS scoping, shell
uniformity, mobile gating and golden screenshots.

Source rules:

- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:1111` Rule 26, CSS encapsulation.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:1131` Rule 27, golden screenshot suite.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:1150` Rule 28, uniform shell contract.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:1167` Rule 29, mobile is a gate.
- `docs/SITE_V3_GAME_RUNTIME_RECOVERY_AND_FLOW_ANALYSIS_2026-05-31.md:301`
  HI-LO current flow summary.

## 2. Architecture Boundary Observed

HI-LO follows the current Site V3 public-shell/iframe/runtime model:

| Boundary | Evidence | Finding |
| --- | --- | --- |
| Public route | `frontend-v3/app/hi-lo/page.tsx:14` renders `GameFramePage`; `frontend-v3/app/hi-lo/page.tsx:20` points to `/runtime/hi-lo`. | Correct public shell boundary. |
| Runtime route | `frontend-v3/app/runtime/hi-lo/page.tsx:1` imports `HiLoStandalone`; `frontend-v3/app/runtime/hi-lo/page.tsx:6` renders it. | Correct runtime entry. |
| CSS load model | `frontend-v3/app/layout.tsx:3-9` imports globals, runtime CSS, Mines CSS, BOXE CSS and HI-LO CSS globally for the app. | Important: iframe isolation prevents parent CSS from leaking into host, but inside the runtime document all imported game CSS can match any class that is reused. Class naming is therefore the real scoping boundary. |

## 3. CSS Scoping Audit

### 3.1 HI-LO Own Scope

HI-LO has a strong game-specific namespace for the main runtime surface:

| Area | Evidence | Finding |
| --- | --- | --- |
| Page shell | `frontend-v3/app/ui/hi-lo/hi-lo.css:1` `.hi-lo-page-shell`; `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:184-188` applies `page-shell hi-lo-page-shell`. | Scoped to HI-LO plus shared runtime base. |
| Product shell | `frontend-v3/app/ui/hi-lo/hi-lo.css:14` `.hi-lo-product-shell`; `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:189-196` applies `game-product-shell game-visual-product-shell hi-lo-product-shell`. | Correct: shared runtime class + HI-LO class. |
| Embedded optimization | `frontend-v3/app/ui/hi-lo/hi-lo.css:23-35`; `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:187` and `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:194`. | Correct: HI-LO uses its own embedded classes, not Mines/BOXE classes. |
| Gameplay grid | `frontend-v3/app/ui/hi-lo/hi-lo.css:46-64`; `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:699-705`. | Scoped to `.hi-lo-*`, with shared `GameControlRail` classes intentionally consumed. |
| Stage/header/X | `frontend-v3/app/ui/hi-lo/hi-lo.css:171-229`; `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:721-737`. | X is native inside stage, transparent, HI-LO scoped. |
| Replay styles | `frontend-v3/app/ui/hi-lo/hi-lo.css:666-858`; `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:829-840`. | HI-LO replay viewer has its own CSS namespace. |
| How-to visual | `frontend-v3/app/ui/hi-lo/hi-lo.css:873-923`; `frontend-v3/app/ui/hi-lo/hi-lo-how-to-visual.tsx:18-26`. | HI-LO scoped. |

Static search found no `boxe-*` class use inside HI-LO. It did find one concrete
cross-game class debt:

| Debt | Evidence | Severity |
| --- | --- | --- |
| HI-LO rules modal body still reuses `mines-rules-body` / `mines-rules-replay-body`. | `frontend-v3/app/ui/hi-lo/hi-lo-rules-modal.tsx:77` and `frontend-v3/app/ui/hi-lo/hi-lo-rules-modal.tsx:81`. | MEDIUM/HIGH for reference cleanliness: not known to break HI-LO today, but it violates Playbook v3 Rule 26 and would teach COINS the wrong pattern. |

The reason this matters is structural: `GameInfoRulesModal` is shared, but emits
Mines-named shell classes:

- `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx:47`
  `.mines-rules-overlay`
- `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx:49`
  `.mines-rules-modal`
- `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx:55`
  `.mines-rules-header`
- `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx:61`
  `.mines-rules-close`
- `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx:70-73`
  `.mines-rules-tabs` / `.mines-rules-tab`

These classes are styled by Mines CSS, because Mines CSS is globally imported by
the root layout. That is the main scoping problem to solve in Parte B.

### 3.2 Can HI-LO CSS Escape Or Be Entered?

| Question | Audit answer |
| --- | --- |
| Can HI-LO CSS escape the game iframe into the public shell? | No at browser boundary level: iframe CSS cannot style parent DOM. |
| Can public/global CSS enter the HI-LO runtime iframe? | Yes by design inside the iframe document: `globals.css`, `runtime-base.css`, `game-runtime.css`, Mines CSS, BOXE CSS and HI-LO CSS are all imported in `frontend-v3/app/layout.tsx:3-9`. |
| Is that automatically bad? | Not if selectors are scoped and documented. Runtime-base selectors such as `.page-shell`, `.panel`, `.button-secondary`, `.button-ghost`, `.list-muted` are shared runtime contracts from `frontend-v3/app/ui/game-runtime/runtime-base.css:14-115`. |
| What is not acceptable for a reference game? | Depending on `mines-rules-*` classes for a HI-LO modal, because those are not neutral runtime contract names. |

Current verdict: HI-LO is mostly scoped, but not fully reference-clean until the
rules modal no longer consumes Mines-named classes.

## 4. Shell Uniformity Check

| Contract | Evidence | Verdict |
| --- | --- | --- |
| DEMO/REAL/BONUS badge | `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:190-194` computes mode label; `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:606-608` renders `game-mode-badge hi-lo-mode-badge`; copy keys at `frontend-v3/app/ui/hi-lo/hi-lo-i18n/hi-lo-copy-defaults.ts:225-227`. | PASS. This is aligned with v3 contract. |
| GameTableBalanceGate | Imported at `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:20-25`; rendered at `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:432-475`; shared component emits `game-table-balance-*` at `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx:117-176`. | PASS. HI-LO uses the shared gate. |
| Real-mode gating | `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:197-199` gates table balance when not demo; `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:365-395` confirms table entry. | PASS by structure; no behavior change proposed. |
| Embed bridge | `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx:180-183` calls `useGameEmbedBridge({ gameCode: "hi_lo", enabled: isEmbeddedView })`; bridge implementation at `frontend-v3/app/ui/game-runtime/use-game-embed-bridge.ts:22-87`. | PASS. |
| Audio UI | `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:589-604` uses `GameRuntimeTools`; audio component emits `game-audio-*` at `frontend-v3/app/ui/game-runtime/game-top-bar.tsx:108-154`; CSS at `frontend-v3/app/ui/game-runtime/game-runtime.css:650-722`. | PASS. |
| Info/rules/replay modal | HI-LO uses `HiLoRulesModal` at `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:829-840`, which wraps `GameInfoRulesModal` at `frontend-v3/app/ui/hi-lo/hi-lo-rules-modal.tsx:64-90`. | AMBER. Behavior is shared, but class names are still Mines-named. |
| Close X | HI-LO X is inside stage at `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:730-737`; CSS transparent X at `frontend-v3/app/ui/hi-lo/hi-lo.css:199-227`. | PASS for desktop/current structure; mobile must be golden-captured. |

Uniformity verdict: HI-LO is a good candidate for reference game, but Parte B
must clean the shared rules modal class naming before calling it exemplary.

## 5. Mobile AMBER Audit

Evidence from previous recovery:

- HI-LO mobile had no technical overflow in the flow analysis:
  `docs/SITE_V3_GAME_RUNTIME_RECOVERY_AND_FLOW_ANALYSIS_2026-05-31.md:145-146`.
- The same document says there is no golden matrix yet:
  `docs/SITE_V3_GAME_RUNTIME_RECOVERY_AND_FLOW_ANALYSIS_2026-05-31.md:395`.
- The recommended mobile WP target is explicit:
  `docs/SITE_V3_GAME_RUNTIME_RECOVERY_AND_FLOW_ANALYSIS_2026-05-31.md:424-427`.

Static CSS state:

| Viewport state | Evidence | Finding |
| --- | --- | --- |
| Desktop/large tablet | `frontend-v3/app/ui/hi-lo/hi-lo.css:52-59` two-column grid; `frontend-v3/app/ui/hi-lo/hi-lo.css:171-229` centered title + native X. | Good base. |
| <= 1060px | `frontend-v3/app/ui/hi-lo/hi-lo.css:927-961` compresses columns and moves history. | Intentional responsive compression. |
| <= 720px portrait | `frontend-v3/app/ui/hi-lo/hi-lo.css:963-1187` fixes shell to viewport, stage first, rail second, hides metrics, reduces card/actions/rail controls. | Likely functional, but dense; needs golden capture before any claim. |
| Short landscape <= 520px | `frontend-v3/app/ui/hi-lo/hi-lo.css:1189-1293` full viewport, smaller rail/stage, compressed card/action columns. | Acceptable target area for refinement; must avoid gameplay changes. |
| Very short <= 420px | `frontend-v3/app/ui/hi-lo/hi-lo.css:1295-1305` hides `.hi-lo-rail-header`. | AMBER: this can hide info/audio/mode badge in very short states. It may be intentional emergency compression, but it is not a clean reference behavior until golden-approved. |

Parte B mobile approach:

- no new layout concept;
- no gameplay reorder beyond existing CSS grid areas;
- keep X, card, prediction buttons and control rail semantics unchanged;
- adjust spacing, header preservation and density only where screenshots prove
  overlap, hidden controls or illegible state;
- if preserving all controls in <=420px is impossible without redesign, stop and
  ask CTO/Michele whether short-landscape should show `GameShortViewportGate`
  instead of compressing further.

## 6. Golden Screenshot Suite Proposal

Create the first HI-LO golden suite here:

```text
artifacts/site_v3_hilo_reference_refinement_2026-06-01/
  golden/
    desktop/
    mobile/
  current/
    desktop/
    mobile/
  side-by-side/
  metadata/
```

Viewport set:

- Desktop: `1365x768`, public route `http://localhost:3000/hi-lo`.
- Mobile portrait: `390x844`, public route `http://localhost:3000/hi-lo`.
- Short landscape check: `844x390`, not part of the six required golden pairs
  unless CTO wants it promoted; recommended as metadata because AMBER risk lives
  there.

Primary capture rule: capture the public page and the iframe runtime bounding
box metadata. If a screenshot is cropped to iframe only, save metadata with
iframe rect, viewport, route, query and selected mode.

Required six surfaces, desktop + mobile:

| Surface | State to capture | Suggested filenames |
| --- | --- | --- |
| 1. Demo gameplay | Demo mode after provider/how-to gates, idle ready-to-bet card state visible. | `golden/desktop/hi-lo-demo-gameplay.png`, `golden/mobile/hi-lo-demo-gameplay.png` |
| 2. Real table-balance gate | Real mode before entering table amount; shared `GameTableBalanceGate` visible. Use technical smoke account, not Michele personal account. | `hi-lo-real-table-gate.png` |
| 3. Replay | Runtime info modal on Replay tab after a terminal round, replay viewer visible. | `hi-lo-replay-modal.png` |
| 4. Audio popover | Gameplay with audio popover open from `GameRuntimeTools`. | `hi-lo-audio-popover.png` |
| 5. X close | Gameplay with native X visible; plus metadata that click posts close/return event, but do not change golden on click. | `hi-lo-close-x.png` |
| 6. Mode badge | Badge visible for DEMO, REAL and BONUS. If BONUS setup is not available in automated smoke, mark BONUS as `pending-fixture`, not skipped silently. | `hi-lo-mode-badge-demo.png`, `hi-lo-mode-badge-real.png`, `hi-lo-mode-badge-bonus.png` |

Acceptance checks attached to every capture:

- no unexpected scrollbar in page or iframe;
- no clipped card/prediction/action controls;
- X visible where expected;
- info/audio/mode badge visible unless CTO explicitly accepts short-landscape
  gate behavior;
- audio popover stays inside viewport;
- replay modal content is readable and not using Mines-specific visual debt
  after Parte B.

## 7. Parte B Micro-Step Plan

Each step is gated. If a step requires backend or game logic changes, stop.

### B0 - Freeze Baseline And Protected Areas

Actions:

- capture current HI-LO golden suite as `current/`;
- record hashes/diff status for protected HI-LO backend and game logic files;
- confirm no changes to RNG/math/payout/board/reveal/replay logic.

Gate:

- screenshot inventory exists;
- protected diff is zero before CSS/scoping work.

### B1 - Selector And Class Reuse Gate

Actions:

- run selector/class audit for `hi-lo`, `mines`, `boxe`, `game-*`, `button-*`,
  `panel`, `page-shell`;
- confirm no `boxe-*` in HI-LO;
- remove the HI-LO dependency on `mines-rules-*` only if CTO approves Parte B.

Preferred Parte B direction:

- promote the shared rules modal shell from `mines-rules-*` names to neutral
  `game-info-rules-*` names in the shared runtime contract; or
- if CTO wants zero shared modal impact, create HI-LO-specific modal shell
  classes and stop using `mines-rules-*` in HI-LO only.

Gate:

- `rg "mines-|boxe-" frontend-v3/app/ui/hi-lo` returns no cross-game CSS class
  dependency, except textual documentation if any;
- rules modal screenshot still matches current accepted look.

### B2 - Shell Uniformity Screenshot Gate

Actions:

- verify badge DEMO/REAL/BONUS, `GameTableBalanceGate`, `useGameEmbedBridge`,
  `game-audio-*`, X and replay modal from the golden suite;
- fix only class scoping or CSS contract naming if needed.

Gate:

- all six surfaces pass desktop;
- all six surfaces pass mobile portrait;
- short landscape either passes or explicitly routes through a CTO-approved
  gate decision.

### B3 - Mobile Reference Cleanup

Actions:

- adjust only HI-LO scoped CSS spacing/layout if screenshots prove compression,
  overlap, hidden essential controls or popover overflow;
- prioritize preserving info/audio/mode badge visibility over squeezing content
  into impossible height;
- no gameplay state, action logic, card math or payout changes.

Gate:

- mobile portrait and short landscape screenshots show no clipping, no hidden
  essential controls and no unexpected scrollbar;
- if `.hi-lo-rail-header` remains hidden at <=420px, the report must call it a
  product/CTO decision, not a silent pass.

### B4 - Golden Suite Commit/Report

Actions:

- save final `golden/`, `current/`, `side-by-side/` and `metadata/`;
- document exact routes, viewport sizes, fixtures and test account class used;
- update only documentation/test artifacts required for the golden suite.

Gate:

- CTO can inspect one folder and see every required HI-LO state;
- no product backend/game logic files changed;
- HI-LO can be used as the template for COINS Parte A/B.

## 8. Stop Conditions

Stop and ask CTO/Michele if:

- fixing mobile requires changing gameplay DOM semantics, action flow or board
  logic;
- fixing rules modal scoping would require broad Mines/BOXE redesign;
- BONUS mode cannot be fixture-created without backend changes;
- short landscape cannot keep controls readable without either hiding the rail
  header or showing a short-viewport gate.

## 9. Parte A Conclusion

HI-LO is the best current candidate for a clean reference game because its page
shell, product shell, gameplay, replay and mobile CSS mostly use `hi-lo-*`
selectors. It is not yet fully v3-clean because the shared rules modal still
uses `mines-rules-*` classes and HI-LO consumes them.

Recommended Parte B: first clean the rules-modal scoping debt, then freeze the
golden suite, then perform only screenshot-driven mobile spacing cleanup. No
backend and no HI-LO game logic changes.
