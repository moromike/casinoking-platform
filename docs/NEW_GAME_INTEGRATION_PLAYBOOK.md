Status: ACTIVE
Last meaningful update: 2026-05-19

# New Game Integration Playbook (v1)

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

The playbook started at v0 before BOXE Fase 0. It was battle-tested during BOXE
and refined into v1 at BOXE closure. v1 is the baseline for HI-LO and later
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

Do not use it for generic "tests passed" status. That belongs in PR delivery.

At project closure, distill log entries into:

- this Playbook
- `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- the game atlas

## 16. Playbook Update Protocol

This document evolves by game.

| Version | Timing | Required change |
| --- | --- | --- |
| v0 | Before BOXE Phase 0 | Initial recipe, checklists, anti-patterns, phase model. |
| v1 | After BOXE closes | Battle-tested lessons, three game-agnosticity audits, atlas verification, improved template defaults. |
| v2 | After game 3 closes | Reduce repeated Phase 0/1 questions; promote stable patterns. |
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
| Closure Distillation | 5-8 | 3 | Docs-only Playbook v1 and Template v1. |

Expected effect for game 3: the three platform prerequisite WPs should not
repeat. Phase 0-1 and Phase 3A/4A should start with richer checklists, reducing
methodology prompts by roughly 40-50% if the game follows the same shell model.

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
