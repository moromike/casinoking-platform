Status: ACTIVE
Last meaningful update: 2026-05-19

# New Game Integration Playbook (v2)

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
does not prove visual/product parity. v2 is the baseline for HI-LO and later
proprietary games.

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

| Capability | Default | Where |
| --- | --- | --- |
| `GameBootShell` | Use as the visual boot wrapper. | `frontend/app/ui/game-runtime/game-boot-shell.tsx` |
| `GameBootDecisionFlow` | Use as the composer for pre-game gates. | `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx` |
| `GameProviderIntroGate` | Use the platform brand intro gate unless product explicitly overrides it. | same |
| `GameHowToPlayGate` | Use for game-specific instructions passed as children. | same |
| `GameTableBalanceGate` | Use for real/bonus table entry. | same |
| `GameShortViewportGate` | Use for landscape-short blocking. | `frontend/app/ui/game-runtime/game-short-viewport-gate.tsx` |
| `useGameLaunchContext` | Use for route/storage/launch readiness. | `frontend/app/ui/game-runtime/use-game-launch-context.ts` |
| `useGameAudioPreferences` | Use for FX mute/volume preferences. | `frontend/app/ui/game-runtime/use-game-audio-preferences.ts` |
| `GameControlRail` | Target v2 platform pattern: shared settings, bet, quick chips, balance and Bet/Collect ergonomics. Extract from Mines before HI-LO if still local. | planned `game-runtime/` extraction |
| `GameRuntimeTools` | Target v2 platform pattern: info, audio, rules modal and replay modal shell. Content remains game-specific. | planned `game-runtime/` extraction |
| `GameStageHeader` | Target v2 platform pattern: title, payout slot, close/fullscreen/runtime tools placement. | planned `game-runtime/` extraction |

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
is the forcing function that showed which parts are still local, and HI-LO must
consume the extracted shell instead of copying Mines or patching BOXE.

Target architecture:

| Shell part | Default ownership | Game-specific input |
| --- | --- | --- |
| Pre-game gates | Shared: Provider Intro, How-To layout, Table Balance visual, Short Viewport gate. | How-to cards/visuals, table submit callback, copy. |
| `GameControlRail` | Shared: settings layout, bet input, quick chips, balance/win display, action buttons. | Setting fields and labels such as grid/mines, rows/difficulty, hi/lo options. |
| `GameRuntimeTools` | Shared: info button, audio toggle, rules modal shell, replay modal shell. | Rules sections, replay renderer adapter, audio event map. |
| `GameStageHeader` | Shared: title area, payout slot, close/fullscreen/tools placement. | Payout adapter and game title/copy. |
| Board adapter | Game-specific. | Board geometry, hit targets, reveal semantics, final-state visibility. |
| Payout adapter | Game-specific. | Multiplier ladder/path, current/next state, max-win/cap display. |
| Admin tabs | Shared Title Editor tabs with schema adapters. | Config fields, copy manifest, rules sections, asset kinds, capability flags. |
| Assets/theme/audio | Shared infrastructure. | Game-specific asset kinds, optional audio capability, theme capability flags. |
| Mobile shell | Shared adaptive shell. | Board-specific responsive sizing and game-specific action labels. |

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
| Gameplay UI | Game-specific | New `frontend/app/ui/<game_code>/`. |
| Theme, audio, assets | Common infrastructure, game-specific asset kinds when needed | New kinds need explicit validation rules. |
| Admin settings | Game-specific editor plugged into common Title Editor shell | Update Backoffice Manual in same PR. |
| Finance, replay, history | Common surfaces, game-specific payload | Wire in Phase 2D. |
| Platform extension | Exceptional | Requires Stop-and-Ask and its own WP. |

Phase 1 must also produce:

- protected file/area list
- contract tests required for import boundaries
- smoke and visual baseline list
- admin manual update plan
- capability matrix skeleton for every planned WP

### 6.1 Mandatory Game-Agnosticity Audits

BOXE surfaced three platform areas that were nominally shared but still
Mines-shaped. New games must run these audits before entering the phase that
would consume the shared area.

| Audit | Run before | Files / areas to inspect | BOXE reference | Required output |
| --- | --- | --- | --- | --- |
| Backend platform adapter game-agnosticity | Phase 2D | `backend/app/modules/platform/rounds/`, `game_launch/`, `table_sessions/`, finance/account serialization. Search for hardcoded `mines`, `*_mines_round_*`, Mines-only payload assumptions. | `WP-PLATFORM-GAME-AGNOSTIC-ADAPTER` introduced `ALLOWED_GAME_CODES` and `open_game_round` / `settle_game_round_*`. | Audit note in architecture mapping. If hardcoding exists, open a platform WP before Phase 2D. |
| Frontend runtime storage game-agnosticity | Phase 3A | `frontend/app/ui/game-runtime/`, especially storage namespace, launch context, boot request, audio, theme and gates. Search for hardcoded namespace/game code. | `WP-FRONTEND-GAME-RUNTIME-AGNOSTIC` introduced `ALLOWED_GAME_NAMESPACES = ["mines", "boxe"]`. | Audit note plus contract tests. If storage or shell is game-coupled, open a frontend platform WP before Phase 3A. |
| Title Editor engine-agnosticity | Phase 4A | `frontend/app/ui/title-editor/`, engine registry, editor props/types, command bar actions, config loading, diagnostics slots, console integration. | `WP-PLATFORM-TITLE-EDITOR-AGNOSTIC` introduced registry, generic `EngineEditorProps<TConfig>`, templated actions and diagnostics slot. | Audit note plus smoke for the new engine editor registration. If shell is game-coupled, open a platform WP before Phase 4A. |

Audit rule: do not work around a shared hardcoding by using another game's
namespace, storage keys, config shape or adapter. That is an anti-pattern.

### 6.2 Pre-Phase Mandatory Audits

v2 expands the audit set. These are not optional checkboxes after coding; they
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
- visual contract exists before coding: mockup frame -> DOM region -> component
  -> reference_match target screenshot
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
| v3 | After game 3 closes | Reduce repeated Phase 0/1 questions; promote stable patterns actually proven by HI-LO. |
| vN | After later games | Keep only reusable process, not game-specific anecdotes. |

Closure rule: every completed game must produce at least one of these outcomes:

- no playbook changes needed, explicitly stated with reason
- playbook refined
- template refined
- platform capability extracted and documented

If the same question appears in two game projects, it belongs in the Template. If
the same engineering decision appears in two projects, it belongs in the
Playbook or platform.

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
