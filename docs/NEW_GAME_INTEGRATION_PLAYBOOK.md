Status: ACTIVE
Last meaningful update: 2026-06-01

# New Game Integration Playbook (v3)

## 1. Purpose

This playbook is the reusable execution recipe for adding proprietary games to
CasinoKing after Mines. It tells engineering, CTO, product, and future Codex
agents how to turn a product idea into a game that works in demo, real, bonus,
backoffice, finance, lobby, replay, and visual regression flows.

It is not a game brief. It does not contain BOXE-specific math, assets,
screenshots, or max-win values. Those live in the game-specific brief and then in
`docs/games/<game_code>/SPEC.md`.

The new-game documentation system has three pieces:

| Piece | Purpose | Owner | Example |
| --- | --- | --- | --- |
| Playbook | Reusable recipe, phases, guardrails, anti-patterns, required outputs. | CTO + engineering | This document |
| Template | Input form filled by product before Fase 0. | Product owner | `docs/NEW_GAME_BRIEF_TEMPLATE.md` |
| Game Brief / SPEC | Game-specific application of the template and playbook. | Product + CTO + engineering | `docs/BOXE_PROJECT_BRIEF.md`, then `docs/games/<game_code>/SPEC.md` |

The playbook started at v0 before BOXE Fase 0. It was battle-tested during BOXE,
refined into v1 at first BOXE closure, and promoted to v2 after the BOXE
full-parity audit exposed the real platform lesson: functional game-agnosticity
does not prove visual/product parity. v3 consolidates the Site V3 migration and
game recovery lessons before COINS/game 4. The v3 source lessons are the Site V3
recovery reports, especially
`docs/SITE_V3_RECOVERY_PHASE3_RESIDUAL_ANALYSIS_2026-05-30.md` and
`docs/SITE_V3_GAME_RUNTIME_RECOVERY_AND_FLOW_ANALYSIS_2026-05-31.md`.

## 2. System Prerequisites

Before using this playbook, the platform must have a reusable baseline. Check
`docs/CAPABILITY_INVENTORY_2026-05-17.md` first; it is the current capability map
and should not be duplicated here.

Minimum prerequisites:

| Prerequisite | Status now | Source |
| --- | --- | --- |
| Game runtime shell | STABLE | `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` |
| BOOT-2A.6 decision flow gates | STABLE | `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md` |
| Launch Cashier and lobby launch flow | STABLE | Capability Inventory, `docs/BACKOFFICE_MANUAL.md` |
| Catalog Engine / Title / Site model | STABLE | Capability Inventory |
| Asset registry | STABLE | `docs/ASSET_REGISTRY_PLAN.md` |
| Theme system | STABLE | Capability Inventory |
| i18n/copy manifest pattern | STABLE | Mines atlas, Capability Inventory |
| Access sessions and table sessions | STABLE | Game Runtime atlas, Mines atlas |
| Platform rounds and double-entry ledger | STABLE | Capability Inventory |
| Finance drilldown | STABLE | Capability Inventory |
| Session Recovery Engine | DESIGNED, not fully implemented | `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` |

If a prerequisite is not available or has regressed, do not hide the gap inside
the new game. Open a platform WP first, with a capability matrix.

## 3. Reusable Platform Capabilities

Default rule: reuse platform capabilities first. A game-specific replacement
requires explicit CTO approval.

Mines is the reference implementation for a shipped game module, but not a
template to copy wholesale. Use `docs/ARCHITECTURE_ATLAS_MINES.md` to understand
the separation between wrapper, gameplay, backend engine, platform boundary,
backoffice, skin, replay, and tests.

### Runtime And Shell

Current Site V3 runtime reality:

```text
public /{game}
  -> frontend-v3/app/{game}/page.tsx
  -> GameFramePage public shell
  -> iframe /runtime/{game}
  -> frontend-v3/app/runtime/{game}/page.tsx
  -> standalone runtime in frontend-v3/app/ui/{game}/
```

The public shell and runtime iframe are separate surfaces. Public Site V3 owns
the lobby/header/navigation/account context; the runtime owns only the game
contract inside the iframe. Use `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` as
the architectural source of truth.

| Capability | Default | Where |
| --- | --- | --- |
| `GameBootShell` | Use as the visual boot wrapper. | `frontend-v3/app/ui/game-runtime/game-boot-shell.tsx` |
| `GameBootDecisionFlow` | Use as the composer for pre-game gates. | `frontend-v3/app/ui/game-runtime/game-boot-decision-flow.tsx` |
| `GameProviderIntroGate` | Use the platform brand intro gate unless product explicitly overrides it. | same |
| `GameHowToPlayGate` | Use for game-specific instructions passed as children. | same |
| `GameTableBalanceGate` | Use for real/bonus table entry. | same |
| `GameShortViewportGate` | Use for landscape-short blocking. | `frontend-v3/app/ui/game-runtime/game-short-viewport-gate.tsx` |
| `useGameLaunchContext` | Use for route/storage/launch readiness. | `frontend-v3/app/ui/game-runtime/use-game-launch-context.ts` |
| `useGameAudioPreferences` | Use for FX mute/volume preferences. | `frontend-v3/app/ui/game-runtime/use-game-audio-preferences.ts` |
| `useGameEmbedBridge` | Use for iframe embed/close/fullscreen messaging. | `frontend-v3/app/ui/game-runtime/use-game-embed-bridge.ts` |
| `GameTableBalanceGate` | Use for real/bonus table entry in the same workflow for every game. | `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx` |
| `GameControlRail` | Shared pattern for settings, bet, quick chips, balance and Bet/Collect ergonomics. Consume it or document a CTO-approved exception. | `frontend-v3/app/ui/game-runtime/game-control-rail.tsx` |
| `GameRuntimeTools` | Shared pattern for info, audio, rules modal and replay modal shell. Content remains game-specific. | `frontend-v3/app/ui/game-runtime/game-top-bar.tsx` and game runtime adapters |
| `GameStageHeader` | Shared contract for title, payout slot, close/runtime tools placement. Keep implementation game-scoped until extracted, but preserve identical contract. | game-scoped component plus `frontend-v3/app/ui/game-runtime/` primitives |

Naming convention: shell steps that block gameplay use `Game*Gate`. If a future
component primarily blocks or admits the player into a flow stage, default to the
`Gate` suffix.

### Platform Services

| Domain | Reusable capability | Source |
| --- | --- | --- |
| Catalog | Engine / Title / Site, master/variant titles, archive/restore. | Capability Inventory |
| Lobby | Game library, game card assets, lobby title publication. | Capability Inventory |
| Cashier | Launch Cashier modal and wallet-source routing. | Capability Inventory |
| Wallet | Read-only wallet selection from player UI. Mutations go through platform adapters. | Capability Inventory |
| Ledger | Double-entry ledger and platform rounds. | Capability Inventory |
| Access | Access session, table session, launch token, ping/close. | Game Runtime atlas |
| Assets | Title assets, site assets, upload/delete/version metadata. | Asset Registry plan |
| Theme | Title theme tokens and advanced skin pattern. | Capability Inventory |
| i18n | Manifest + defaults + title locale editor pattern. | Mines atlas |
| Replay | Game-specific replay endpoint using platform/history patterns. | Mines atlas |
| Finance | Round reporting and read-only drilldown. | Capability Inventory |
| Recovery | Designed auto-resolve/quarantine policy. | Session Recovery design |

### Game Adapter Default

The game adapter is the boundary between game logic and platform money/reporting.
For now, Mines is the concrete reference through `round_gateway.py` and
`platform_client.py`. New games must not talk directly to wallet or ledger from
gameplay code.

Expected direction:

```text
Game module -> Game Adapter / platform boundary -> platform_rounds -> ledger
```

Never create a game-specific economic bypass.

### 3.1 GameRuntimeShell As Platform Pattern

The product is not "write a frontend for every game". The product is a
`GameRuntimeShell` with slots/adapters. Mines is the first implementation, BOXE
is the forcing function that showed which parts are still local, and HI-LO
exposed the cost of copied shell behavior. In Site V3 the runtime is launched
through the public iframe model described above; game 4+ must consume or extend
the shell contract instead of copying another game's classes or branching the
host shell.

Target architecture:

| Shell part | Default ownership | Game-specific input |
| --- | --- | --- |
| Pre-game gates | Shared: Provider Intro, How-To layout, Table Balance visual, Short Viewport gate. | How-to cards/visuals, table submit callback, copy. |
| `GameControlRail` | Shared: settings layout, bet input, quick chips, balance/win display, action buttons. | Setting fields and labels such as grid/mines, rows/difficulty, hi/lo options. |
| `GameRuntimeTools` | Shared: info button, audio toggle, rules modal shell, replay modal shell, `game-audio-*` behavior. | Rules sections, replay renderer adapter, audio event map. |
| `GameStageHeader` | Shared: title area, payout slot, close/fullscreen/tools placement. | Payout adapter and game title/copy. |
| Board adapter | Game-specific. | Board geometry, hit targets, reveal semantics, final-state visibility. |
| Payout adapter | Game-specific. | Multiplier ladder/path, current/next state, max-win/cap display. |
| Admin tabs | Shared Title Editor tabs with schema adapters. | Config fields, copy manifest, rules sections, asset kinds, capability flags. |
| Assets/theme/audio | Shared infrastructure. | Game-specific asset kinds, optional audio capability, theme capability flags. |
| Mobile shell | Shared adaptive shell and hard gate. | Board-specific responsive sizing and game-specific action labels. |

Rule: a game may implement math, board, payout, copy, assets and state-machine
semantics. It should not invent a new control rail, runtime tools shell, title
editor workflow, launch shell or mobile shell unless product explicitly approves
the divergence.

## 4. The Game Brief Template

The product owner starts with `docs/NEW_GAME_BRIEF_TEMPLATE.md`.

The template must provide:

| Area | Product must fill | Can default |
| --- | --- | --- |
| Identity | game name, code, family, first variant code | demo/real/bonus defaults |
| Visuals | icon, lobby card, animation expectations | provider intro, base theme |
| Math | game type, tunables, payout formula, max win cap | RNG contract if standard |
| Rules and copy | short rules, how-to-play, launch languages | platform edge copy |
| Config limits | bet range, wallet types, title variants, operator settings | cash+bonus if normal |
| Shell overrides | any explicit non-default shell behavior | all runtime shell components |
| Special behavior | game-over reveal, bonus rounds, replay format | session recovery default |
| State machine | states, transitions, concurrency, idempotency | header pattern only |
| Failure UX | player/operator errors | standard messages when applicable |

Open template questions block Fase 0. Do not convert open product questions into
code assumptions.

## 5. Phase 0: Discovery And SPEC

Output: `docs/games/<game_code>/SPEC.md`.

The SPEC is the contract. It turns product input into implementation rules. If a
block is incomplete, stop before code.

| Block | What is needed | Where to look | Closure criterion |
| --- | --- | --- | --- |
| 1. Game rules | RNG model, math, payout, win/loss/cashout, max win cap. | Product brief, GDD, math sheet. | Every outcome and payout is deterministic from server state. |
| 2. Visual layout | Main board/scene proportions, controls, states, animations. | Screenshots, mockups, product notes. | Every visible state has a named layout. |
| 3. Operator settings | What Title Editor can change, what is hardcoded, draft/live behavior. | Template, product config needs. | Every setting has owner, default, validation, publish behavior. |
| 4. Product constraints | Demo, real, bonus, languages, static vs admin-uploaded assets. | Product decision. | No launch mode or language ambiguity remains. |
| 5. Backend state machine | States, legal transitions, illegal transitions, expiry. | Game rules + backend design. | All mutations map to a state transition or explicit rejection. |
| 6. Idempotency contract | Keys, ownership, retry behavior, TTL, duplicate semantics. | API design. | Every mutating endpoint has replay behavior. |
| 7. Rounding, precision, cap | Multiplier precision, chip rounding, cap interaction, cap display. | Math spec. | No payout value depends on frontend rounding. |
| 8. Replay/history contract | What is stored, how final view is reconstructed, finance/player views. | Game design + reporting. | Replay can be rendered after round close without hidden state. |
| 9. Admin config lifecycle | Master defaults, draft vs live, active-round behavior on publish. | Backoffice rules. | Publishing cannot silently alter active rounds. |
| 10. Asset contract | Formats, size caps, dimensions, fit behavior, validation messages. | Asset plan + UI design. | Every upload UI can state format, max size, dimensions, and render mode. |
| 11. Failure UX | Missing config, unpublished title, table expiry, insufficient balance, empty bonus, network/backend errors, closed-round retry. | Product + API errors. | Every visible failure has player/admin copy and expected action. |

The SPEC should be written before implementation. If it exposes platform gaps,
open a platform design/fix WP before Phase 2.

## 6. Phase 1: Architecture Mapping

Output: matrix `common vs game-specific vs platform extension` plus WP list for
Phases 2-7.

Default classification:

| Area | Default classification | Notes |
| --- | --- | --- |
| Runtime shell, gates, launch context | Common | Use `game-runtime/` directly. |
| Wallet, ledger, platform rounds | Common | Game code never mutates wallet/ledger directly. |
| Math, payout, state machine | Game-specific | New backend module per game. |
| Public shell route | Common Site V3 shell | `frontend-v3/app/<game_code>/page.tsx` renders `GameFramePage`. |
| Runtime route | Common iframe contract, game-specific standalone | `frontend-v3/app/runtime/<game_code>/page.tsx` renders the standalone runtime. |
| Gameplay UI | Game-specific | New `frontend-v3/app/ui/<game_code>/`. |
| Theme, audio, assets | Common infrastructure, game-specific asset kinds when needed | New kinds need explicit validation rules. |
| Admin settings | Game-specific editor plugged into common Title Editor shell | Update Backoffice Manual in same PR. |
| Finance, replay, history | Common surfaces, game-specific payload | Wire in Phase 2D. |
| Platform extension | Exceptional | Requires Stop-and-Ask and its own WP. |

Phase 1 must also produce:

- protected file/area list
- contract tests required for import boundaries
- smoke and visual baseline list, including the golden screenshot suite for
  desktop and mobile
- admin manual update plan
- capability matrix skeleton for every planned WP

### 6.1 Mandatory Game-Agnosticity Audits

BOXE surfaced three platform areas that were nominally shared but still
Mines-shaped. New games must run these audits before entering the phase that
would consume the shared area.

| Audit | Run before | Files / areas to inspect | BOXE reference | Required output |
| --- | --- | --- | --- | --- |
| Backend platform adapter game-agnosticity | Phase 2D | `backend/app/modules/platform/rounds/`, `game_launch/`, `table_sessions/`, finance/account serialization. Search for hardcoded `mines`, `*_mines_round_*`, Mines-only payload assumptions. | `WP-PLATFORM-GAME-AGNOSTIC-ADAPTER` introduced `ALLOWED_GAME_CODES` and `open_game_round` / `settle_game_round_*`. | Audit note in architecture mapping. If hardcoding exists, open a platform WP before Phase 2D. |
| Frontend runtime storage game-agnosticity | Phase 3A | `frontend-v3/app/ui/game-runtime/`, especially storage namespace, launch context, boot request, audio, theme and gates. Search for hardcoded namespace/game code. | `WP-FRONTEND-GAME-RUNTIME-AGNOSTIC` introduced `ALLOWED_GAME_NAMESPACES`; current whitelist covers `["mines", "boxe", "hi_lo"]`. | Audit note plus contract tests. If storage or shell is game-coupled, open a frontend platform WP before Phase 3A. |
| Title Editor engine-agnosticity | Phase 4A | `frontend-v3/app/ui/title-editor/`, engine registry, editor props/types, command bar actions, config loading, diagnostics slots, console integration. | `WP-PLATFORM-TITLE-EDITOR-AGNOSTIC` introduced registry, generic `EngineEditorProps<TConfig>`, templated actions and diagnostics slot. | Audit note plus smoke for the new engine editor registration. If shell is game-coupled, open a platform WP before Phase 4A. |

Audit rule: do not work around a shared hardcoding by using another game's
namespace, storage keys, config shape or adapter. That is an anti-pattern.

### 6.2 Pre-Phase Mandatory Audits

v3 keeps these audits as gates. These are not optional checkboxes after coding; they
are gates before a new game consumes a layer.

| Audit | Run before | What to prove | Required output |
| --- | --- | --- | --- |
| Backend platform adapter game-agnosticity | Phase 2D | Platform rounds, launch, table sessions, finance and account serialization accept the new game through explicit game-code adapters, not Mines-shaped payloads. | Audit note and contract tests, or platform WP before game work. |
| Frontend game-runtime storage namespace agnosticity | Phase 3A | `game-runtime/` route, storage, launch context, theme and audio helpers are namespace-based and do not require Mines keys. | Audit note and boundary tests. |
| Title Editor engine-agnosticity | Phase 4A | Registry, editor props, command bar, config loading and diagnostics slot support the new engine without `if mines` branching. | Audit note and smoke for editor registration. |
| Backend lifecycle symmetry | Phase 3A and before real/bonus launch | Access session, table session, launch token, settlement and close/timeout semantics match the reference game or have an explicit product-approved placeholder. | Lifecycle matrix for demo, real cash and real bonus. Stop-and-Ask on asymmetry. |
| GameRuntimeShell consume audit | Before Phase 3A implementation | The reference game and new game actually consume shared components. Existence of `game-runtime/` wrappers is not proof. | Consume table: reference component -> shared component -> new game consumer -> screenshot evidence. |
| Visual reference gate setup | Before Phase 3B | Mockups/screenshots are opened and mapped to DOM regions, components and target baselines. | Visual contract: mockup frame -> DOM region -> component -> reference_match screenshot. |

The BOXE failure mode was not "no shared code existed". It was "shared wrappers
existed while real surfaces remained local or visually wrong". Audits must
therefore verify consumption and rendered evidence, not only namespaces or file
placement.

### 6.3 Parity Audit - 12 Mandatory Entry-Point Surfaces

Distilled 2026-05-20 from a CTO blind spot: the BOXE parity audit dated
2026-05-19 declared "Launch Cashier modal: Aderente" by checking only entry
parameters, but never opened `casinoking-console.tsx`, where an iframe launcher
overlay was wired Mines-specifically. BOXE was launched as a direct route while
Mines was launched in an iframe overlay - and nobody noticed until the product
owner spotted it by eye.

To prevent this class of miss, every parity audit between the reference game
and a new game MUST explicitly list verdicts for the following 12 surfaces. If
a surface is not in the audit table, the audit is incomplete and the CTO must
reject it before approving Parte B.

Each surface is classified as **P** (player-facing, hard parity gate) or **A**
(admin-tool-facing, lower priority, backoffice parity).

| # | Class | Surface | What to verify |
| --- | --- | --- | --- |
| 1 | P | Lobby card / catalog (`PlayerLobbyPage`) | Same card shell, copy, artwork slot, status badge logic |
| 2 | P | Launch Cashier modal (`LaunchCashierModal`) | Same modal shell, wallet picker, amount input, validation |
| 3 | A | Admin/backoffice game preview launcher (e.g. iframe overlay in `casinoking-console.tsx`) | Admin-only preview parity. Not a player-experience gate. Backlog item, not Wave-1 blocker. |
| 4 | P | Provider intro gate | Same `GameProviderBootstrap` consume, same video, same skip behavior |
| 5 | P | How-to-play gate | Same `GameHowToPlayGate` consume, content via prop |
| 6 | P | Table balance gate | Same `GameTableBalanceGate` consume, limits via prop |
| 7 | P | Gameplay shell (control rail, settings, bet, balance, action, board) | Left rail identical pattern, board game-specific. See WP-B Control Rail Shared Extraction precedent. |
| 8 | P | Mobile rotation gate / landscape behavior | Same rotation gate logic, same mobile DOM/sheet pattern |
| 9 | P | Embed mode (`?embed=1` query param, if used by lobby flow) | Same query param contract, same standalone behavior in embed vs full page |
| 10 | A | Backoffice editor (overview, config, copy, rules, assets, theme, sounds) | Same `title-editor/` consume, capability flags drive game differences |
| 11 | P | Replay viewer | Same replay shell, game-specific board renderer |
| 12 | P | Disconnect/resume | Same disconnect detection, same resume affordance |

CTO review must walk every row. P rows that diverge are hard gates and must be
fixed in the current Wave. A rows that diverge go to admin-tool parity backlog
and do not block Wave closure unless the product owner explicitly elevates them.

**Diagnostic rule** (added 2026-05-20 after a CTO misdiagnosis): before
declaring "Mines launches differently from BOXE", verify which file is actually
serving the player route. `casinoking-console.tsx` is admin-only (mounted under
`/admin/...`). `PlayerLobbyPage` is player (mounted under `(player)`). Confusing
the two leads to opening a player-facing WP for what is actually an
admin-tool gap.

For each row the audit must produce: reference game state, new game current
state, product expectation, verdict (Adherent / Non-adherent / To clarify),
recommended correction.

**Hard rule for CTO reviewing the audit**: before approving any Parte B brief
that consumes the audit's verdicts, walk the 12-row table. A missing row is a
blind spot. An audit that visits only gameplay and admin is incomplete by
construction.

Linked memory: `feedback_audit_entry_points_coverage.md`.

## 7. Phase 2: Backend Foundation

Backend work is split to keep money, math, and API boundaries reviewable.

### Phase 2A: Math / RNG / Fairness

Scope:

- pure math module
- server-side RNG/fairness artifacts
- payout calculation
- max win cap and rounding rules
- fixed-seed tests

Out of scope:

- wallet
- ledger
- API routing
- frontend preview math

Closure:

- math tests cover normal, edge, cap, and rounding cases
- fairness proof is deterministic and documented
- RTP targets are explicit per environment (`demo`, `production`) or the
  production value is explicitly deferred to a pre-launch WP
- no frontend decides outcome

Capability matrix expected:

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<Game> math/RNG/fairness` | n/a | NEW | n/a | n/a | n/a | n/a | NEW | SPEC/atlas draft | NEW |

### Phase 2B: Schema / Repository / State Machine

Scope:

- migrations for game-specific state tables
- repository layer
- state machine
- illegal transitions
- concurrency primitives

Closure:

- migration up/down tested
- state transitions match SPEC block 5
- concurrent reveal/cashout behavior is covered

### Phase 2C: API Endpoints

Scope:

- start
- action/reveal/step
- cashout or equivalent settlement action
- session read/resume
- replay read
- error mapping from SPEC block 11

Closure:

- every endpoint has success and error tests
- every mutating endpoint has idempotency behavior
- any payload extension gets CTO Stop-and-Ask before implementation

### Phase 2D: Adapter / Finance / Replay Wiring

Scope:

- game adapter to platform rounds
- no direct wallet/ledger mutation from game code
- finance drilldown payload
- player history / replay payload
- i18n manifest and defaults

Closure:

- round appears in finance
- replay can render a closed round
- demo, real, bonus paths are separate tests
- wallet/ledger/RNG/payout/fairness/math platform invariants remain untouched

## 8. Phase 3: Frontend Gameplay

### Phase 3A: Standalone Bootstrap

Scope:

- `<Game>Standalone`
- route/query integration
- `GameBootShell`
- `useGameLaunchContext`
- shell gates with game-specific children
- minimal demo smoke

Closure:

- game opens from route with a published title
- runtime config loads before gameplay mounts
- contract test prevents `game-runtime/` importing game-specific code

### Phase 3B: Gameplay Specific

Scope:

- game board/scene
- player controls
- active/won/lost/reveal states
- copy keys
- action API calls

Closure:

- demo round playable end-to-end without polish animations
- no math/payout decisions in frontend
- no imports from Mines unless a component has been promoted with CTO approval
- no reuse of another game's scoped CSS classes; shared CSS must live in an
  explicit runtime contract
- visual contract exists before coding: mockup frame -> DOM region -> component
  -> reference_match target screenshot
- golden screenshot suite exists before the first CSS/UI change: desktop and
  mobile screenshots for demo gameplay, real table-balance gate, replay, audio
  popover, close X and DEMO/REAL/BONUS mode badge
- left/control rail decision is explicit: ergonomic Mines-like, pixel-perfect
  or custom with product approval

### Phase 3C: Animations And Polish

Scope:

- reveal animations
- win/loss feedback
- reduced-motion behavior
- audio event hooks

Closure:

- animations do not change gameplay state
- visual smoke remains stable
- mobile portrait and short-landscape behavior verified
- reference_match visual suite exists separately from regression baselines
- side-by-side Playwright evidence compares reference game and new game for
  shell phases and compares mockup states for game-specific gameplay

### Phase 3B/3C Visual Gates

Visual gates are product gates, not just screenshot regression.

| Gate | Required evidence |
| --- | --- |
| Mockups are binding inputs | Every reference mockup path is opened and listed in the SPEC. If a mockup is composition-only rather than pixel-perfect, write that product decision before coding. |
| Visual contract | For each required state: mockup frame -> DOM region -> component -> baseline screenshot. |
| Left rail decision | Product decides one of: ergonomic Mines-like, pixel-perfect Mines, or custom. The default is ergonomic Mines-like. |
| Shell side-by-side | Provider Intro, How-To layout, Table Balance, Launch Cashier and demo/real sequencing are captured side-by-side against Mines. |
| `reference_match` suite | Separate visual target suite that asks "does this match product reference?" Normal regression baselines ask only "did current UI change?". |
| Mobile portrait gate | Mobile is an acceptance gate, not deferred polish, unless product explicitly defers it. |
| Runtime tools gate | In-game info/rules/replay/audio shell is present by default. Sounds may be capability-flagged off, but the runtime tools affordance is not skipped silently. |

Anti-rule: do not refresh a baseline for a UI that never matched the reference
target. That freezes the wrong product.

## 9. Phase 4: Title Editor Integration

Admin work is split because config/copy and assets/theme have different failure
modes.

### Phase 4A: Config / Copy / Rules

Scope:

- game-specific config editor
- copy/i18n editor entries
- rules HTML editor
- validation and draft/live behavior
- Backoffice Manual update in the same PR

Closure:

- operator can save draft and publish live
- invalid config is blocked with readable errors
- active-round behavior on publish matches SPEC

### Phase 4B: Assets / Sounds / Theme / Lobby Card

Scope:

- game-specific asset kinds where needed
- sounds
- theme tokens or advanced skin reuse
- lobby card
- upload guidance beside every upload control
- Backoffice Manual update in the same PR

Closure:

- upload/preview/delete works
- frontend and backend validation agree
- every upload states formats, max size, dimensions, and render behavior

## 10. Phase 5: Site / Lobby Integration

Scope:

- engine/title seeding
- site title publication
- lobby card render
- Launch Cashier launch path
- route ownership for `/<game_code>`

Closure:

- player can launch demo, real, and bonus from the lobby
- hidden/archived/unpublished titles cannot launch publicly
- master titles remain blocked from public launch
- Game library payload includes required game card information

## 11. Phase 6: Documentation

Required output: `docs/ARCHITECTURE_ATLAS_<GAME>.md`.

Update docs only where behavior changed:

| Change | Required docs |
| --- | --- |
| New game architecture | `ARCHITECTURE_ATLAS_<GAME>.md` |
| Game runtime extension | `ARCHITECTURE_ATLAS_GAME_RUNTIME.md` |
| Admin UI capability | `BACKOFFICE_MANUAL.md` in same PR |
| Asset upload UI | `BACKOFFICE_MANUAL.md` and relevant asset plan |
| Capability state | `CAPABILITY_INVENTORY_2026-05-17.md` or successor |
| Lessons learned | This Playbook and `NEW_GAME_BRIEF_TEMPLATE.md` |

No game is complete if its atlas is missing.

## 12. Phase 7: End-To-End Validation

Required validation:

| Validation | Minimum |
| --- | --- |
| Browser smoke | boot, launch, demo play, real play, bonus play |
| Visual regression | game baseline, key states, responsive viewports |
| Manual playthrough | backoffice publish -> lobby -> cashier -> play -> finance -> replay |
| Finance | round visible and read-only drilldown coherent |
| Replay/history | player and admin can inspect closed round |
| Regression protection | Mines full browser smoke stays green |
| Contract tests | runtime cannot import game-specific modules; game does not import Mines |
| Atlas verification | active game atlas matches delivered behavior and no longer describes historical placeholders as current state |

Demo, real, and bonus are not "same flow with a wallet switch". They are tested
separately.

If atlas verification finds minor drift, fix the atlas in Phase 7. If it finds a
substantive behavior mismatch with SPEC or delivered code, Stop-and-Ask before
changing implementation.

## 13. Anti-Pattern Catalog

Add new anti-patterns as soon as they are discovered.

### Architectural Anti-Patterns

| Anti-pattern | Correct behavior |
| --- | --- |
| Copying `MinesStandalone` into a new standalone. | Build a new wrapper using the Game Runtime checklist. |
| Duplicating decision flow. | Use `GameBootDecisionFlow`. |
| Duplicating cashier. | Use Launch Cashier. |
| Duplicating audio, i18n, or theme infrastructure. | Reuse platform infra and add game-specific content only. |
| Using Mines config shape as implicit base for a new game. | Define a game-specific SPEC and config schema. |
| Adding `if game === "<code>"` inside platform components. | Use adapters, props, children, registry, or a designed platform extension. |
| Creating game-specific economic endpoints parallel to the Game Adapter. | Route economic mutations through platform rounds/adapter. |
| Extending the platform shell during feature coding. | Stop-and-Ask; open a platform WP. |
| Importing game code from `game-runtime/`. | Runtime stays game-agnostic; enforce with contract tests. |
| Using another game's namespace or adapter as a workaround. | Run the relevant game-agnosticity audit and refactor shared shell/platform first. |
| Reusing another game's scoped CSS classes. | Each game owns its scoped CSS; shared CSS lives only in an explicit runtime contract. The known BOXE reuse of `mines-page-shell` / `mines-product-shell` is recovery debt and must not be copied. |
| Extracting scaffolding without extracting shared implementations. | Promote real surfaces, CSS and behavior to shared components, then make both games consume them. |
| Treating `GameBootShell` usage as proof of shared visual implementation. | Verify rendered surfaces and consume paths for Provider, How-To, Table Balance, control rail and runtime tools. |
| Forking local game-specific UI when a shared shell primitive exists. | Use the shared primitive with adapters/props; fork only with product and CTO approval. |
| Discovering backend lifecycle asymmetry in a frontend WP. | Run lifecycle symmetry before Phase 3A and before any real/bonus launch claim. |
| Inventing gate sequencing for the new game. | Replicate the reference game sequencing for demo, real cash and real bonus unless product approves a difference. |

### Implementation Anti-Patterns

| Anti-pattern | Correct behavior |
| --- | --- |
| Putting math or payout in frontend "for preview". | Backend owns outcome and payout; frontend displays. |
| Reusing asset kind names with different meaning. | Add explicit game-specific kinds or document shared semantics. |
| Silent fallback on `title_code`, config, or difficulty. | Fail visibly or use an approved default. |
| Hardcoding operator-configurable settings. | Put them in Title Editor config if SPEC says operator-owned. |
| Treating demo/real/bonus as identical. | Test and implement as separate launch/wallet modes. |
| Deferring replay/history as polish. | Treat replay/history as a contract from Phase 0. |
| Changing wallet/ledger from game code. | Use platform adapter only. |
| Leaving upload constraints implicit. | Show formats, size, dimensions, and render mode beside upload controls. |
| Letting runtime math diverge from math docs. | Investigate, obtain product decision, update runtime/spec/simulator/stress tests together. BOXE found this retroactively in Mines RTP. |
| Refreshing visual baseline in a later unrelated WP. | Refresh baseline in the WP that intentionally changes math or UI, and document why. |
| Treating mockups as background inspiration instead of visual acceptance gates. | Map mockups to DOM/component/baseline targets before Phase 3B. |
| Using visual regression against current state as proof of target fidelity. | Maintain a separate `reference_match` visual suite against product targets. |
| Using a game-specific palette override by default. | Default to Mines/platform palette; require product decision for a variant. |

### Process Anti-Patterns

| Anti-pattern | Correct behavior |
| --- | --- |
| Skipping capability matrix. | Every WP has one. |
| Updating backoffice manual later. | Admin capability changes update manual in the same PR. |
| Closing a phase without updating the Playbook. | Phase closure includes lesson distillation. |
| Saying "done" without delivery state. | Use branch / merged / visible-on-localhost state. |
| Carrying open product decisions into code. | Stop before code and close SPEC. |
| Reusing old branch diffs without capability reconciliation. | Audit by capability end-to-end first. |
| Letting active atlas drift from delivered behavior. | Phase 7 includes atlas verification and correction before closure. |
| Writing a task-only brief with no current context. | Every CTO brief starts with current repo/product context and latest decisions. |
| Running a critical cross-cutting WP in one execution prompt. | Use Parte A approach validation, then Parte B execution after CTO approval. |
| Treating Stop-and-Ask as delay. | Aggressive Stop-and-Ask is expected partner behavior when scope/product risk is real. |

## 13.1 Pattern Operativo CTO

For critical WPs, Codex is a thought partner, not a blind executor.

### Agent Roles

- **Claude = CTO**: analysis, sequencing decisions, gate on PRs, brief authoring,
  memory management, estimates, exploratory answers, lightweight refinements.
- **Codex = CTO assistant + code writer**:
  - **CTO assistant** in Parte A: validates approach, names risks, runs
    Stop-and-Ask, may counter-propose. Codex is expected to push back when scope
    creep, hidden coupling or implicit product expectations are detected. A
    "yes-man" Codex that executes whatever the brief says without challenge is a
    regression to the BOXE shell disaster (2026-05-19) baseline.
  - **Code writer** in Parte B: executes the approved brief, implements,
    writes tests, runs builds, performs merges/rebases.

Every CTO brief for a critical WP must open with "You are CTO assistant. Parte A:
validate approach, counter-propose if you see a gap" rather than "implement X".

Rules:

- Every CTO brief includes current context: branch/state, latest product
  decisions, relevant incidents and exact scope.
- Critical WPs use **Parte A / Parte B**:
  - Parte A: Codex validates approach, names risks, asks targeted questions and
    may counter-propose.
  - Parte B: execution starts only after CTO accepts the approach.
- Stop-and-Ask is success behavior when it catches a blocker: backend lifecycle
  asymmetry, gate sequencing mismatch, shared consume gap or product ambiguity.
- Post-closure fixes classify each divergence as:
  - A: game-specific bug;
  - B: cross-game pattern;
  - C: platform shell limit;
  - D: implicit product expectation.
  B/C/D items must be distilled into Playbook, Template or atlas before the
  next game starts.

### Multiagent Mode

Multiagent mode = N parallel Codex chats/agents working on independent WPs.

Activate when:

- N WPs have file-isolated write scopes (zero overlap on the same files)
- Each WP has a complete CTO brief and Parte A validated
- Each WP has a dedicated git worktree (`git worktree add`) - no branch switching
  on the primary worktree
- A merge orchestration plan declares order (which WP merges first and why)

Do NOT activate when:

- WPs overlap on shared files - force serial execution to avoid merge conflict
  roulette
- Parte A not closed for the WP - keep one WP at a time until approach is
  validated
- Exploratory work or unclear approach - single agent, small scope

Operational pattern (validated 2026-05-19→20 with Wave 1 WP-A/B/C):

1. CTO defines a Wave with N independent WPs, each with Parte A brief.
2. Codex opens N worktrees (`casinoking-<wp-tag>-worktree`) to avoid branch
   switching.
3. Codex runs Parte A in parallel, returns N approach docs.
4. CTO validates each approach independently and unblocks Parte B per WP.
5. Codex runs Parte B in parallel inside the worktrees.
6. Merge orchestration: CTO declares order (e.g. "merge WP-A → rebase WP-B on
   updated main → gate WP-B → merge → rebase WP-C → gate WP-C → merge").
7. A dirty working tree from one WP must NOT be touched during the merge of
   another WP. This is a hard gate.

Cross-agent communication: each parallel agent reports only to CTO. No direct
Codex↔Codex traffic. CTO is the hub.

#### Rule 13 - Two-step audit (auditor + verifier) for critical surfaces

When auditing surfaces declared "green" by a previous Wave for parity with
the reference game, use a TWO-STEP audit pattern, especially for admin /
backoffice / content-heavy / multi-tab surfaces.

Step 1 — auditor:
- Codex audits point by point with mandatory verdict: "equal" / "different,
  game-specific (with product document citation)" / "different, gap" /
  "different, debt"
- File:line citations mandatory for every verdict
- "Game-specific" without product citation is rejected as laziness — fallback
  to "gap"

Step 2 — verifier mode:
- AFTER step 1, Codex switches mentally to verifier role
- Reopens filesystem from scratch, does independent audit WITHOUT reading
  step 1 first
- Then compares with step 1 and marks each point as OK / WEAK / MISSED /
  WRONG
- If step 1 is severely incomplete (>30% weak/missed/wrong), force step 1
  reopening before closure

Output: two docs (step 1 + step 2) + consolidated final verdict table +
recommended scope for fix WPs.

Why mandatory for critical surfaces: Codex tends to declare green after
"shared component extraction + consume" but content/visual/functional may
remain partial. Validated 2026-05-21 on BOXE backoffice post Wave 4: WP-BO
declared Surface 10 green, two-step audit revealed actual verdict "partial"
with 7 gap entries (rules HTML 1 vs 7 sections, copy manifest 17 vs 40
keys, validation partial, diagnostics missing, theme/assets not visually
specular, legacy-labels debt not fully closed).

Verifier severity is mandatory: the prompt must explicitly state that "game
specific" without product citation is rejected, and that step 2 must
proactively flag skipped or superficial step 1 entries. Without severity,
verifier becomes rubber-stamp.

When step 1 audit is sufficient (no two-step needed):
- Simple gameplay-specific surface (e.g. game board geometry — already
  obviously different per game)
- Single-file extraction with no content/copy involved
- Visual primitive without business logic

When two-step is mandatory:
- Admin / backoffice closure
- Content/copy manifest parity (rules HTML, i18n keys, ecc.)
- Multi-tab admin editor with 5+ sub-editors
- Surface declared green by a previous Wave that the product owner suspects

#### Rule 14 - No scrollbar on gameplay board, cell adaptive on container

Gameplay boards (Mines grid, BOXE pyramid, HI-LO board, future games) must
NEVER show inner scrollbars or clip cells to the edge. Cells must adapt to
the container so the entire board is visible at once, replicating the Mines
3×3→7×7 pattern: smaller grid = bigger cells, bigger grid = smaller cells,
always all visible.

Mandatory implementation rules:
- No `overflow: auto` / `scroll` on board container
- No `overflow: hidden` used as a mask to hide cells that would otherwise
  overflow
- No fixed cell pixel size that ignores container size
- Cell size formula must subtract: board padding + gap*(n-1) + buffer for
  border/border-radius/box-shadow/glow. Buffer ≥ 4-8px.
- Mobile and landscape orientations follow the same formula with reduced
  container.

Closure gate (mandatory for any board change):
- Browser smoke matrix on ALL N configurations of the new game, not spot
  check
- Per configuration, measure: `cell.getBoundingClientRect()`, `board.scrollWidth
  > clientWidth`, `board.scrollHeight > clientHeight`, minimum margin
  between outer cell and board edge
- All configurations must report `overflow=false` AND `minMargin ≥ buffer`
- Single failure on any configuration = FAIL gate

Validated 2026-05-22 with BOXE: matrix of 15 configurations (5 rows × 3
difficulties) + mobile portrait + landscape, all overflow=false, minMargin
≥ 7.8px in extreme landscape.

#### Rule 15 - Gameplay configuration matrix browser audit

Any board gameplay with N user-selectable configurations requires browser
audit on TUTTE le N combinations, with real DOM measurements. Spot-check on
1-2 configurations is forbidden.

Per game:
- BOXE: 5 rows (4/5/6/7/8) × 3 difficulty (EASY/MEDIUM/HARD) = 15 combos
  obligatory
- Mines: 5 grid sizes × applicable mine counts (already stable as
  reference)
- HI-LO and future: configurations defined at Wave Parte A

Measurements per combo (record in `tests/visual/artifacts/<wave>/<feature>/`):
- Cell width/height (verifies cell adaptive)
- `board.scrollWidth > clientWidth` (must be false)
- `board.scrollHeight > clientHeight` (must be false)
- Minimum margin between outermost cell and board container edge (must
  be ≥ buffer)
- Plus screenshot for visual evidence

Anti-pattern: "I tested 4 rows EASY and it works" — spot check, NOT
sufficient. Mathematical correctness without DOM evidence is NOT sufficient.

#### Rule 16 - Surface 10 Backoffice decomposition + Wave 7 closure lessons

Surface 10 Backoffice in the 12-surface check (section 6.3) is a multi-layer
surface. Audit it decomposed:

- 10A — Admin engine page (`/admin/games/<engine>`): master/variant grouping,
  Editable Titles section, Create variant button, filters
  (Active/Inactive/Archived/All + Test only), inline actions per row
  (Save/Preview/Archive), status badges, lobby publication badges,
  display_name inline editing
- 10B — Title detail page shell (`/admin/games/<engine>/titles/<title_code>`)
- 10C — Sub-editor tabs existence (overview, copy, rules, config, assets,
  theme, sound, validation, with documented game-specific exceptions)
- 10D — Field depth per sub-editor tab (every Mines field has a new-game
  equivalent including theme depth, copy manifest depth, rules HTML depth,
  validation breadth)
- 10E — Workflow draft/save/publish (draft persistence, locale/rules saved,
  uploaded assets actually consumed at runtime)
- 10F — Adjacent admin pages (asset library, copy manifest preview,
  finance drilldown)

A single sub-layer red = Surface 10 red.

Wave 7 closure lessons (validated 2026-05-22 BOXE):
- End-to-end closure gate: admin save → backend persist → runtime consume →
  player sees. BOXE failed this gate twice silently: theme saved skin in
  wrong payload shape, BOXE backend did not preserve all copy keys, uploaded
  board symbols were not consumed runtime, create-variant failed in
  backend. All must be tested at admin closure.
- Admin RBAC canonicalization at multi-engine point: when platform moves
  from single proprietary game to multi (Mines → Mines+BOXE → +HI-LO), area
  names should be canonical (e.g. `games`) with legacy single-engine
  aliases for backward compat. Plan BEFORE adding third game.
- Architecture map update per commit (Mermaid code map): every commit that
  changes module ownership, admin routing, runtime inheritance, API/domain
  boundaries, persistence responsibilities, or shared-vs-game-specific split
  must update the map in same commit or document follow-up.

Mandatory artifact at Surface 10 closure for any game:
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_<GAME>_<DATE>.md`
  produced as handoff for the next game's CTO. Records concrete failure
  modes observed + how to skip them.

#### Rule 17 - Eight-layer green check at every Wave closure

Rules are not useful if they are only present in docs. They must be applied at
each Wave closure.

For every new-game Wave closure, Codex must produce an explicit table proving
that each affected surface is green across all eight layers:

| Layer | Meaning |
| --- | --- |
| Container | Shared shell/component is mounted where expected. |
| Content | Game-specific copy, rules, headings, labels, sections and admin fields are complete. |
| Visual | Screenshots or reference-match evidence prove expected appearance. |
| Functional | Player/admin flow works end-to-end. |
| Persistence | Admin/backend state saves, publishes and reloads where applicable. |
| Runtime consume | Player runtime consumes saved/admin-uploaded data. |
| Tests | Focused automated tests cover the behavior. |
| Product owner | Michele validates critical flows on `localhost:3000`. |

The Product Owner row is a hard gate for critical player-facing and admin
surfaces. A Wave cannot be called green if the first seven layers are green but
the product owner has not walked the result on `localhost:3000`.

BOXE failure pattern: multiple surfaces were declared green after shared
containers, content, screenshots, tests and internal review, but Michele later
found product-visible gaps on `localhost:3000`. The fix is not more prose; it is
requiring this eight-layer table at closure every time.

#### Rule 18 - Third-game hard-branch expiry

HI-LO proved that a third explicit game branch can be an acceptable bridge, but
it also marks the expiry point for that pattern. After Mines, BOXE and HI-LO,
new code must not add a fourth explicit game branch in account history, admin
finance replay, launch routing, title-editor registration or runtime config
selection when a registry/adapter can represent the same decision.

Required action before game 4:

- audit every `mines` / `boxe` / `hi_lo` conditional in player account,
  admin finance, replay, launch and title-editor code;
- classify each as `keep game-specific`, `convert to registry now`, or
  `accepted temporary bridge`;
- do not implement the next game by appending `else if new_game`;
- for game 4+, extend the registry/bridge contract before adding new runtime
  behavior.

This rule comes from HI-LO H6: player account history and admin finance replay
were made functional, but still by explicit three-game fan-out. That was an
acceptable game-3 bridge, not the architecture for games 4+.

Implementation checkpoint 2026-05-25:

- frontend account/admin replay routing now goes through
  `frontend-v3/app/ui/game-reporting-registry.tsx`;
- backend finance/account/access-session summary and auto-settle dispatch use
  builder/handler registries;
- embed mode close/fullscreen-state now uses
  `frontend-v3/app/ui/game-runtime/use-game-embed-bridge.ts`;
- game 4 must extend these registries/bridges, not add fourth branches.

#### Rule 19 - Lobby/CMS testability before product walkthrough

A new game is not ready for Product Owner walkthrough if it is only playable by
direct deep link. Before asking Michele to validate on `localhost:3000`, Codex
must prove the game is reachable through the same CMS/lobby publication path a
tester would use.

Mandatory checks:

- the canonical variant exists in `/admin/games/<engine>` and can be opened from
  the game engine page;
- the Site CMS publication panel can make the variant visible, demo-enabled and,
  when applicable, real-enabled without backend validation errors;
- `/games/library` returns the variant with the expected engine/game code,
  `title_code`, display name, description, demo flag and real flag;
- the player lobby card launches demo through the platform-approved demo
  bootstrap flow for that engine, not by a hidden hand-written test URL;
- real mode follows the legal money gate: anonymous users are sent to login,
  authenticated users see the explicit table-balance selection, and no path
  opens a real game with the whole wallet by accident;
- admin preview uses the public player route for the engine, including
  dash/underscore route aliases such as `hi_lo -> /hi-lo`.

Direct links remain useful for development, but they are not a closure gate.
This rule comes from HI-LO H7: the game was technically playable and internally
tested, but Product Owner testing required the title to be visible and launchable
from the local site/CMS.

#### Rule 20 - Replay belongs in the info/rules surface by default

Replay is an inspection/fairness tool, not a primary gameplay action. For new
games, the default player entry point is the game info modal (`i`) with a
dedicated Replay tab next to rules/fairness content. Account history and admin
replay remain canonical audit paths.

Do not add a permanent `Replay hand` button to the live gameplay surface unless
product explicitly approves that game-specific exception. If replay is not yet
available for the current round, the info modal may show a disabled/empty Replay
tab with clear copy.

This rule comes from HI-LO H8: adding a terminal replay CTA to the card table
made the play surface noisy and contradicted the established games pattern.

#### Rule 21 - Backoffice visual quality is a closure gate, not polish

Every new game's backoffice must be visually inspected tab by tab before a
surface is called green. "Feature exists" is not enough.

Mandatory admin checks:

- no clipped labels, overflowing pills, overlapping previews, or crushed inputs;
- asset rows have aligned preview/copy/action columns and readable guidance;
- theme/token/skin fields match the reference admin hierarchy and do not fall
  into ad hoc white panels or unstyled grids;
- shared/player chrome such as close buttons stays visually static on hover;
  local absolute positioning must not combine with global button hover movement;
- save draft activates after each relevant edit and the saved value reloads;
- Product Owner walks `/admin` on `localhost:3000` for game engine page and
  title detail tabs.

This rule comes from BOXE Surface 10 and HI-LO H8: admin gaps that looked small
in code were product-blocking when opened visually.

#### Rule 22 - Real-money access close must have game-specific auto-settlement

Every real-money game must define session close and timeout semantics before it
is tested by the Product Owner. This is a platform invariant, but not a
one-size-fits-all gameplay rule: each game owns its own settlement image/model
and must declare how the generic close/timeout policy maps to its mechanics.

Mandatory behavior:

- the player close button must call the platform access-session close endpoint;
  naked navigation is not enough;
- the game must declare its own "no meaningful progress yet" condition; in that
  state, platform close/timeout refunds the reserved bet;
- the game must declare its own "collectible exposure" condition and current
  payout source; in that state, platform close/timeout performs an automatic
  cashout using the game-owned current payout;
- if the round is already terminal, close does not create another settlement;
- the auto settlement must be idempotent, ledger-backed, table-session-safe and
  visible in replay/history;
- explicit close and the backend timeout sweeper must execute the same
  settlement policy;
- the behavior must be tested for explicit close and for access-session timeout.

Examples of game-specific mapping:

- Mines: no revealed safe cell means refund; at least one safe reveal means
  auto-cashout using `payout_current`;
- BOXE: no safe pick means refund; at least one safe pick means auto-cashout
  using `payout_current`;
- HI-LO: no correct prediction means refund; at least one correct prediction
  means auto-cashout using `payout_current`.

This is a legal/money invariant, not UI polish. HI-LO exposed the gap after a
real-money crash: Mines had auto-cashout/refund behavior, while BOXE and HI-LO
needed the same platform dispatcher with game-specific settlement adapters.

#### Rule 23 - Provider intro must own the screen before runtime gameplay mounts

The provider intro/video is a hard boot gate. A new game must never show the
player gameplay surface for even one frame before the provider intro has either
completed or been explicitly skipped.

Mandatory behavior:

- `GameBootDecisionFlow` must not mount runtime children while
  `showProviderIntroGate` is active;
- game-specific bootstrap checks such as active-round resume, launch-token
  recovery, table-session lookup or theme loading must not temporarily disable
  the provider intro;
- the intro may show progress while those checks run, but it stays above the
  game surface until the boot decision is final;
- browser smoke for demo, real and bonus launch must verify there is no
  gameplay flash between clicking the lobby card and seeing provider intro or
  table-balance gate.

This rule comes from HI-LO: its active-round resume check briefly set
`showProviderIntroGate` false while `runtime_ready` was already true, causing a
one-frame flash of gameplay before the provider video.

#### Rule 24 - Finance, replay and reporting are a game contract

Every new game must declare how it appears in financial reporting before it is
called playable. Replay is not only a player inspection feature: it is also an
admin/audit explanation of what happened to money.

Mandatory behavior:

- each game provides a reporting descriptor for player account, admin finance,
  replay endpoint, replay viewer, finance summary and account summary;
- no new game may add another hardcoded branch in account history or admin
  finance; use a registry/adapter;
- unknown/unregistered games must not fall back to another game's replay
  endpoint;
- finance detail copy must explain the round in product language: configuration,
  actions, outcome, bet, payout and settlement;
- admin replay and player replay may expose different audit fields, but both
  must reconstruct the same deterministic round;
- retention must separate ledger retention, replay/audit payload retention and
  UI pagination;
- physical deletion/anonymization of replay data requires explicit product/legal
  policy, not an incidental UI limit.

Required reference:

- `docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`

This rule comes from the post-HI-LO finance audit: player account had Mines,
BOXE and HI-LO replay paths, while admin finance still had partial BOXE/HI-LO
branches and a dangerous implicit BOXE fallback.

#### Rule 25 - Runtime and error copy must not be hardcoded

Player-facing runtime copy, error dialogs, retry actions, table-balance gates,
replay labels and gameplay button labels must live in the game copy manifest
for every supported locale.

Mandatory behavior:

- do not hardcode visible runtime strings in `*-standalone.tsx`,
  `*-gameplay.tsx`, replay viewers, error adapters or table-balance flows;
- add every new key to all supported locales in the game copy defaults;
- use local copy adapters to map technical backend failures into user-facing
  messages;
- backend error strings, enum names and internal ids must never be rendered as
  player copy;
- exceptions are limited to test ids, internal enum values, route names and
  developer-only diagnostics that are not visible to players or admins.

Gate:

- run a targeted hardcoded-copy audit with `rg` for each touched game runtime;
- build and i18n lint must pass;
- if a one-off UI fix introduces a visible string, the fix is incomplete until
  the copy manifest and all locales are updated.

This rule comes from the HI-LO current-multiplier and action-error cleanup:
the UI behavior was corrected first, but several visible strings were still
embedded in runtime components instead of the manifest.

#### Rule 26 - CSS encapsulation and no cross-game class reuse

Each game owns its own scoped CSS. A class created for Mines, BOXE, HI-LO or a
future game is not a reusable platform primitive unless it has been promoted to
`frontend-v3/app/ui/game-runtime/` and documented as part of the runtime
contract.

Mandatory behavior:

- never style a new game by reusing another game's scoped selectors;
- never use `globals.css` as a hidden game styling layer;
- keep runtime shared CSS explicit, reviewed and limited to game-runtime
  contracts such as shell, gate and audio primitives;
- treat selector leakage into `/runtime/{game}` iframes as a release blocker;
- close existing cross-game CSS reuse as debt instead of using it as precedent.

Concrete recovery debt: BOXE currently reuses `mines-page-shell` and
`mines-product-shell`. That is an anti-pattern discovered during Site V3
recovery, not an approved design. COINS/game 4 must not inherit it.

#### Rule 27 - Golden screenshot suite is mandatory

Every game needs frozen desktop and mobile golden screenshots before and after
game UI/CSS work. This replaces "recover by eye" and "looks roughly close".

Minimum suite per game:

- demo gameplay;
- real table-balance gate;
- replay;
- audio popover/dropdown;
- close X;
- DEMO / REAL / BONUS mode badge.

Any game CSS or UI change must compare against this suite. If the intended
change modifies the golden baseline, the WP must state why, refresh the baseline
inside the same WP and get CTO/product approval. Do not defer baseline refresh
to a later cleanup.

#### Rule 28 - Uniform shell contract

All proprietary games share the same player shell contract. The differences are
the gameplay board, rules, payout, copy, assets and engine state machine; the
shell behavior is not game-specific by default.

Mandatory uniform contract:

- badges for DEMO, REAL and BONUS mode;
- `GameTableBalanceGate` for real/bonus table entry;
- iframe embed lifecycle through `useGameEmbedBridge`;
- audio behavior and selectors through the `game-audio-*` runtime contract;
- close X behavior and placement;
- replay launch surface and history/reporting registry hooks.

If a game must diverge, write a product decision record before implementation.

#### Rule 29 - Mobile is a gate, not deferred polish

Mobile desktop-parity is a closure gate. It is not an optional polish pass after
desktop is green.

Mandatory behavior:

- every golden screenshot in Rule 27 has a mobile equivalent;
- short-landscape and portrait behavior are tested before closure;
- header compression is either visually accepted or tracked as a blocking debt;
- the previous AMBER pattern for compressed headers is not inherited by new
  games as "acceptable enough";
- no game closes with mobile-only clipping, scrollbars or hidden controls unless
  CTO/product explicitly accepts a temporary exception.

#### Rule 30 - Site V3 runtime boundary is the baseline

New games live in `frontend-v3`, not the removed `frontend/` source tree. The
public player route, runtime iframe route and standalone runtime are separate
boundaries and must be reviewed separately.

Mandatory path model:

```text
frontend-v3/app/<game_code>/page.tsx
frontend-v3/app/runtime/<game_code>/page.tsx
frontend-v3/app/ui/<game_code>/
frontend-v3/app/ui/game-runtime/
```

The public shell may pass launch/embed context into the iframe; game-specific
runtime components must not assume CasinoKing host chrome beyond the documented
runtime contract. This is the starting point for future host-neutral packaging
and the parked externalization plan.

## 14. Mandatory Capability Matrix

Every WP must include the guardrails matrix from
`docs/TASK_EXECUTION_GUARDRAILS.md`.

Template:

```text
Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes
```

For new games, include one row per capability, not one row per file. If a WP is
docs-only, state that explicitly: `Doc methodology only, no production code
touched, no architecture changes.`

## 15. Implementation Log Rule

Every multi-phase game project keeps an Implementation Log in its game brief or
SPEC, using the format in `docs/TASK_EXECUTION_GUARDRAILS.md` section
`Project Implementation Log`.

Use the log for:

- surprises
- deviations from brief
- discovered edge cases
- anti-patterns
- naming conventions
- unexpected dependencies
- product-impacting discoveries that require an explicit CTO/product owner
  decision before more code is written

Do not use it for generic "tests passed" status. That belongs in PR delivery.

At project closure, distill log entries into:

- this Playbook
- `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- the game atlas
- a product decision record when the discovery changes scope, visual target,
  economics, lifecycle or launch readiness

## 16. Playbook Update Protocol

This document evolves by game.

| Version | Timing | Required change |
| --- | --- | --- |
| v0 | Before BOXE Phase 0 | Initial recipe, checklists, anti-patterns, phase model. |
| v1 | After BOXE closes | Battle-tested lessons, three game-agnosticity audits, atlas verification, improved template defaults. |
| v2 | After BOXE full-parity audit | Visual parity gates, GameRuntimeShell platform pattern, lifecycle symmetry, mockup/reference_match and CTO operating pattern. |
| v3 | After Site V3 migration/recovery and before COINS/game 4 | `frontend-v3` runtime reality, public shell/iframe/runtime boundary, CSS encapsulation, golden screenshot suite, uniform shell contract, mobile as gate, and Rule 18 registry enforcement. |
| v3.1 | During Cross-Game Bonifica 2026-06-05 (Mines/BOXE/HI-LO retroactive parity) | Parity audit on TWO levels (backend DB/arch + frontend/UX), re-run after every migration; no single game-template (canonical per axis); mobile = AI job; parallelization by disjoint domains; decide technical/process choices by owner principles. See 16.2bis. |
| v3.2 | During Cross-Game Bonifica 2026-06-06 | Demo canonical = anonymous/no-login for ALL games; money-flow concurrency hardening (host-owned platform_rounds incl. admin paths, cross-table serialization, ON CONFLICT idempotency, 0-amount ledger guard, optimistic close); "drop-a-constraint-to-pass-a-test" anti-pattern. See 16.2ter. |
| v3.3 | During Cross-Game Bonifica 2026-06-07 | Fairness-model parity as an audit dimension (per-round vs shared seed); provably-fair PLAYER-SIDE as a game requirement; different-model independent verifier on money/security/fairness; admin/operator paths game-agnostic + correct terminal status semantics. See 16.2quater. |
| v3.4 | During Cross-Game Bonifica 2026-06-08 (B6 regression + B7 closure) | Test-infra gate discipline: marker seriali, xdist isolato, schema drift guard, SSR real-setup, demo-anonymous impact su browser smoke, product contract Homepage Slot CTA → Launch Cashier, URL real canonico `mode=real`. See 16.2quinquies. |
| vN | After later games | Keep only reusable process, not game-specific anecdotes. |

Closure rule: every completed game must produce at least one of these outcomes:

- no playbook changes needed, explicitly stated with reason
- playbook refined
- template refined
- platform capability extracted and documented

If the same question appears in two game projects, it belongs in the Template. If
the same engineering decision appears in two projects, it belongs in the
Playbook or platform.

### 16.2bis Cross-Game Bonifica Learnings (2026-06-05)

Distilled from the retroactive Mines/BOXE/HI-LO parity program. These are reusable process rules, not game anecdotes.

1. **Parity audit on TWO levels.** Backend audit (DB schema, demo model, service architecture, launch-token, settlement/access-session, layering) AND frontend/UX audit (the 12 surfaces of §6.3). The 2026-06-04 backend audit missed frontend divergences (BOXE missing close-X in embedded; replay-history absent in BOXE/HI-LO) because frontend was out of scope. Both are mandatory.
2. **Re-run the parity audit after every migration/recovery.** The big Site V3 migration regressed surfaces (X button, replay history, replay CSS) unnoticed because §6.3 was not re-executed cross-game post-migration. "We never noticed" is the real failure, not the divergence itself.
3. **No single game-template.** The canonical reference changes per axis. Example: on the frontend Mines is the most complete (close-X, replay-history browser); on the backend Mines is the outlier (bespoke demo tables/functions, no repository/state_machine). Pick the canonical per surface, never assume one game is "the template".
4. **Mobile validation is the AI/CTO job.** The product owner validates desktop only; the AI verifies mobile (Playwright at mobile viewport, DOM geometry, no scrollbar/clipping, screenshots).
5. **Money-flow discipline.** Demo must be server-authoritative and never touch real `platform_rounds`/ledger (BOXE demo was frontend-only — fixed to HI-LO's shared `demo_wallet`). Access-session is mandatory on real start (auto-settlement safety net). Platform round (`platform_rounds`) must be host-owned (one adapter opens/settles), not inserted by each game repo (drift risk). Prove-before-remove on any money control.
6. **Parallelization by disjoint domains.** Run executors in parallel only on non-overlapping file domains (frontend vs tests/ vs backend) or read-only analyses. The CTO is the single merge hub; gate each delivery separately; never let two streams edit the same hot file (e.g., `hi_lo.py`, `*-gameplay.tsx`).
7. **Decide technical/process choices by owner principles.** Do not escalate non-product decisions (schema removal, checkpoint commits, test-infra) to a non-developer owner; decide them by his known principles (clean architecture, zero debt, disposable local DB) and report the decision. Reserve questions for product/business/priority/visual-desktop.
8. **Gate discipline.** Verify executor claims by running, not by reading the summary. Catch vacuous asserts (`>= 0`), false positives (a flagged "money-adjacent debt" that is actually correct), and "pre-existing debt" mislabels (failures that only appear in the full suite = test isolation, not a WP defect).

### 16.2ter Cross-Game Bonifica Learnings (2026-06-06 — demo identity + money concurrency)

9. **Demo canonical = ANONYMOUS (try-without-signup) for ALL games.** Product decision (Michele 2026-06-06) that REVERSES the earlier "demo = HI-LO provisioned-user" assumption. Canonical demo model: `anonymous_id` (NOT a row in `users`) + shared `demo_wallet` service (`open_demo_session`/`debit_for_bet`/`credit_for_win`/`record_loss`) + `demo_session_id` on the game-specific round + **no `user_id`→users FK on round/idempotency tables** (REAL integrity is guaranteed upstream by `platform_rounds`→`wallet_accounts`→`users`). New games: demo must be playable without login. (Note: a constraint failure on demo rounds is expected because demo identities aren't in `users` — see anti-pattern 11.)

10. **Money-flow concurrency hardening** (real races found under load in DIV-02/06):
   - **platform_rounds host-owned**: a SINGLE writer = the platform service (open/settle inserts/updates `platform_rounds` in the same tx as the ledger). Game repos store only game state + the returned `platform_round_id` ref. This applies to ADMIN paths too (force-close must go through the platform service, not write `platform_rounds` directly).
   - **Cross-table serialization**: concurrent terminal actions on the same round (e.g. reveal-mine vs cashout) MUST serialize (pg_advisory_xact_lock on the round id, or a consistent FOR UPDATE lock-order) → never inconsistent terminal states like `platform_rounds=won` & game round `=lost` (an exploitable money leak).
   - **Idempotency tables need ON CONFLICT**: concurrent insert on the same key → replay the existing response, never a 500.
   - **0-amount ledger guard**: a settlement with payout<=0 must NOT create a 0-amount ledger entry (violates the `amount>0` check); close the round without a transaction.
   - **Optimistic close**: `UPDATE ... WHERE status='active'` so a round already closed by a concurrent tx raises a conflict instead of being silently overwritten.

11. **Anti-pattern: "drop a constraint to make a test pass".** When a test fails on a FK/constraint, INVESTIGATE whether the constraint is wrong (then it's a canonical change, with proof) or the DATA is wrong (then the constraint is MASKING a bug). Never drop the constraint blind. (DIV-02 case: dropping `mines_game_rounds` user FK was correct ONLY after proving BOXE has no such FK + that anonymous demo is the wanted canonical — not before.)

### 16.2quater Cross-Game Bonifica Learnings (2026-06-07 — fairness, verifier, admin voids)

12. **Fairness-model parity è una dimensione d'audit cross-game.** Verificare per ogni gioco: seed PER-ROUND (BOXE/HI-LO) vs seed di rotazione CONDIVISO (Mines = outlier, `fairness_seed_rotations`). Un seed condiviso tra round IMPEDISCE la disclosure provably-fair per-round (svelarlo espone gli outcome di altri round con lo stesso hash → exploit). Canonico = **seed per-round**. L'audit di parità cross-game DEVE includere il modello fairness/RNG (era un blind-spot: l'audit 2026-06-04 non lo copriva).

13. **Provably-fair PLAYER-SIDE è un requisito di gioco** (non solo admin-verifiable). Standard per OGNI gioco: (a) commitment `server_seed_hash` allo start; (b) seed per-round; (c) `server_seed` svelato al GIOCATORE SOLO dopo il round terminale (MAI su round attivo → leak dell'outcome); (d) `user_verifiable=True` nel payload player; (e) endpoint/funzione verify + UI frontend che ricostruisce l'outcome da server_seed+client_seed+nonce. Anti-pattern: `user_verifiable` hardcoded False / seed esposto solo all'admin (scatola nera per il giocatore).

14. **Verifier indipendente di MODELLO DIVERSO** (un secondo modello — Gemini/Codex — read-only) su money + security + fairness dopo refactor grossi: ha trovato bug reali che il gate primario + il CTO avevano MANCATO (DIV-06c money-integrity orfano, gap provably-fair player-side, divergenza fairness-seed Mines) e confermato il resto. Costo ~zero (read-only, parallelo, domini disgiunti). Da fare prima della chiusura programma / pre-produzione. Vedi [[feedback_two_step_audit_verifier]].

15. **Admin/operator paths: game-agnostici + semantica terminale corretta.** I path admin (es. force-close) devono: (a) NON scrivere `platform_rounds` fuori dal platform service; (b) essere game-agnostici (dispatch per `game_code`, MAI hardcode di una tabella di un gioco — bug DIV-06c: `UPDATE mines_game_rounds` hardcoded → game-round orfano per BOXE/HI-LO); (c) usare uno status terminale SEMANTICAMENTE corretto: un void/refund admin = `'cancelled'`, NON `'completed_cashout'` (altrimenti falsa player-history e report finance).

### 16.2quinquies Cross-Game Bonifica Learnings (2026-06-08 — B6 regression + test infra closure)

16. **Suite monolitica non è gate affidabile.** La full-suite integration va in timeout e maschera leak cross-file. Gate canonico = marker seriali espliciti (`unit`, `api_service`, `money_admin`, `catalog`, `browser_smoke`, `visual`, `concurrency`, `migration_schema`, `stress`) eseguiti in sequenza controllata. Il pass globale "tutto verde" è la somma dei pass marker, non una singola run senza filtri.

17. **xdist solo su marker isolati.** pytest-xdist è sicuro SOLO quando il marker non tocca backend/DB condiviso (es. `unit` con fixture no-op). Full DB-per-worker + backend-per-worker è un WP infra a sé; finché non esiste, tutti gli altri marker restano seriali. Non forzare xdist su `api_service` o `browser_smoke` con DB shared.

18. **Schema drift guard prima e dopo ogni batch che tocca migrations.** `tests/integration/test_schema_drift_guard.py` verifica che lo schema finale sia canonico. Qualsiasi test che droppa/ricrea tabelle (es. `test_boxe_state_machine`) deve usare l'helper canonico che riapplica la chain completa, non una sotto-chain. Manual DROP/CREATE schema nei test = proibito; drift guard deve rimanere verde.

19. **Browser smoke: round_id va letto dalla risposta API, non dal DB by `player_id`.** Dopo demo-anonymous, `anonymous_id` ≠ `user_id`; query su `boxe_rounds.player_id` può tornare NULL o round sbagliato. Il round_id affidabile è `data.round_id` (o `data.session_id`) del JSON response di `/games/{game}/start`.

20. **Homepage Slot CTA → Launch Cashier è contratto product, non navigazione diretta.** Un CTA hero/slot che punta a un game title DEVE aprire il Launch Cashier (modal con scelta Real/Bonus/Demo), non linkare direttamente `/{game}?mode=...`. Verificare in `HeroBanner`/`GameCard` e in ogni nuovo modulo CMS che referenzi titoli.

21. **URL real canonico: `mode=real` + `wallet_source=real`, mai `mode=real_cash`.** Il launcher pubblico risolve `real` come modalità; `real_cash` è obsoleto e rompe gli smoke. Test e frontend devono usare il valore canonico attuale (`site-v3-render-helpers.ts:147` e `backend/app/api/public/site_v3.py`).

### 16.1 BOXE Effort Baseline

Prompt counts below are handoff-level counts reconstructed from BOXE briefs,
Stop-and-Ask decisions and gate updates. They are meant for future estimation,
not as a transcript audit.

| Work package | Original estimate | Actual handoff prompts | Notes |
| --- | --- | --- | --- |
| Phase 0 SPEC | 5-7 | 3 | No product Stop-and-Ask after SPEC draft. |
| Phase 1 Architecture Mapping | 3-5 | 3 | Title Editor risk marked watchpoint. |
| Phase 2A Math/RNG/Fairness | 8-12 | 3 | Product Option C resolved math upfront. |
| Phase 2B Schema/State | 6-9 | 3 | No platform schema change. |
| Phase 2C API | 6-9 | 3 | Idempotency and error mapping stayed game-specific. |
| Backend platform adapter WP | 9-13 | 3 | Unplanned prerequisite before 2D. |
| Phase 2D Adapter/Finance/Replay | 8-12 | 4 | Paused then resumed after platform adapter. |
| Frontend runtime agnostic WP | 4-6 | 3 | Unplanned prerequisite before 3A. |
| Phase 3A Standalone Boot | 5-7 | 4 | Paused then resumed after frontend runtime refactor. |
| Phase 3B Gameplay | 8-12 | 3 | Large frontend WP, no platform extension. |
| Phase 3C Animations/Polish | 5-8 | 3 | Visual baseline added. |
| Title Editor agnostic WP | 5-9 | 3 | Unplanned prerequisite before 4A. |
| Phase 4A Admin Config/Copy | 5-8 | 4 | Paused then resumed after Title Editor refactor. |
| Phase 4B+5+6 Combined | 12-19 | 3 | Combined after backend/frontend/admin patterns stabilized. |
| Phase 7 E2E Validation | 5-8 | 3 | Atlas drift and Mines baseline refresh handled in validation. |
| Closure Distillation | 5-8 | 3 | Docs-only first-closure Playbook v1 and Template v1. |

Expected effect for game 3: the three platform prerequisite WPs should not
repeat. Phase 0-1 and Phase 3A/4A should start with richer checklists, reducing
methodology prompts by roughly 40-50% if the game follows the same shell model.

### 16.2 Effort Baseline Post-BOXE For HI-LO

This is a planning baseline, not a promise. It assumes BOXE is used as the
forcing function to extract the real runtime/admin shell before or alongside
HI-LO, and that HI-LO does not require a novel economy/lifecycle model.

| Area | Expected HI-LO effort | Assumption |
| --- | ---: | --- |
| Backend math/RNG/fairness/state/API/adapter | 10-15 prompts | BOXE backend pattern reused; new math/state still game-specific. |
| Frontend gameplay | 8-12 prompts | `GameControlRail`, `GameRuntimeTools`, `GameStageHeader` and mobile shell are shared before heavy HI-LO UI work. |
| Admin | 2-4 prompts | Title Editor tabs are shared with schema adapters; HI-LO only supplies config/copy/assets/rules metadata. |
| Visual fidelity | 2-4 prompts | Mockups are composition references with a visual contract before coding. |
| Validation | 2-3 prompts | Demo/real/bonus, side-by-side shell, reference_match and regression suites are already standard. |
| Total | 24-38 prompts | Compared with BOXE actual 150+ including all refactors and rework. |

Risk: if BOXE is fixed with local patches instead of shared extractions, HI-LO
will not hit this baseline. It will pay BOXE's frontend/admin cost again.

## 17. Known Structural Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Backend multi-game adapter is not fully battle-tested. | Mines is the only real implementation so far. | Phase 1 maps adapter needs; Phase 2D validates with finance/replay. |
| Frontend runtime storage may still be game-coupled. | New games need their own namespace and launch storage. | Mandatory pre-Phase 3A audit; use whitelist and contract tests. |
| Title Editor may still be Mines-shaped. | New games may need settings unlike grid/mines. | Mandatory pre-Phase 4A audit; platform extension only by CTO decision. |
| Replay and finance discovered too late. | Schema may be insufficient if reporting is delayed. | SPEC block 8 and Phase 2D force early wiring. |
| Atlas may drift from delivered code. | Future agents may implement against stale docs. | Phase 7 atlas verification is mandatory. |
| Math docs may drift from runtime tables. | RTP/certification material becomes unreliable. | Treat divergence as investigation + product decision, then update runtime/spec/simulator/tests together. |
| Phase 0 may feel bureaucratic. | Missing product decisions become expensive code disputes. | Treat SPEC as the contract; no code until open decisions close. |
| Playbook may become a document written after the fact. | Lessons are lost if not captured while implementing. | v0 exists before Phase 0; Implementation Log is mandatory. |

## 18. Success Measures

A game is successful when:

- demo, real, and bonus work end-to-end
- the game is configurable from backoffice where SPEC says it should be
- player lobby launch uses platform cashier and access/session flow
- finance sees the round
- replay/history is readable
- visual regression baseline exists
- Mines smoke remains green
- docs and manual are updated
- capability matrix shows no hidden gaps

The Playbook is successful when Phase 0 and Phase 1 become faster over time. BOXE
sets the baseline. Game 3 should require fewer methodology discussions. If it
does not, update this Playbook and the Template until it does.
