Status: ACTIVE
Last meaningful update: 2026-05-23

# HI-LO - Wave Plan

Phase 3 output. This is the proposed implementation sequence after SPEC and
architecture mapping.

No implementation starts until Michele approves the plan or explicitly asks to
start a specific wave.

## 1. Merge Principles

| Principle | Rule |
| --- | --- |
| Platform before local workaround | If a shared surface is hardcoded to Mines/BOXE, fix the platform registry/adapter first. |
| Visual before motor when player-facing | Player stage work starts with fit/reference states and no-scroll gates. |
| Backend math before gameplay money | API/state uses `MATH_SPEC.md`; frontend never rederives payout. |
| Surface 10 decomposed | Admin never marked green unless 10A-F are green. |
| Product owner gate | Critical waves close only after `localhost:3000` walkthrough. |
| No hidden docs questions | Every wave delivery includes chat Decision Brief. |

## 2. Recommended Wave Order

| Wave | Name | Type | Purpose | Merge dependency |
| --- | --- | --- | --- | --- |
| H0 | Platform enablement for third game | Code | Add `hi_lo` to platform registries/lobby/account/title-editor paths without gameplay. | First |
| H1 | Backend math, RNG and fairness | Code | Implement `MATH_SPEC.md` and deterministic card draw. | H0 for registry tests, otherwise isolated |
| H2 | Backend state, schema and API | Code | Persist rounds, start/skip/predict/cashout/replay endpoints. | H1 |
| H3 | Player runtime visual shell | Code | `/hi-lo`, card stage, options, history, rules/how-to, no-scroll. | H0, can use mocked/stubbed API until H2 merge only if isolated |
| H4 | Content and asset pipeline | Code/content | HI-LO i18n, rules, how-to visuals, card asset defaults/registry kinds. | H3 for visual consume, H0 for registry |
| H5 | Backoffice full-depth | Code | Admin engine/detail/config/copy/rules/assets/theme/sound/validation, 10A-F. | H0, H4 content model |
| H6 | Replay, account history and recovery | Code | Replay viewer, account entry point, finance/admin drilldown, access-session recovery. | H2, H3, H5 where admin replay is needed |
| H7 | Closure and distillation | Docs/tests | 12-surface green, PO walkthrough, Playbook/template/replication brief. | All previous |

## 3. Wave H0 - Platform Enablement

### Goal

Make the platform know that `hi_lo` is a first-class game without implementing
HI-LO gameplay.

### Likely Files

| Area | Files |
| --- | --- |
| Backend registry | `backend/app/modules/platform/game_codes.py` |
| Backend routing | `backend/app/api/routes/__init__.py`, future route include placeholder only if needed |
| Frontend lobby | `frontend/app/ui/player-lobby-page.tsx` |
| Frontend account registry | `frontend/app/ui/player-account-page.tsx` or new shared game-history registry |
| Title Editor registry | `frontend/app/ui/title-editor/engine-editor-registry.ts` |
| Catalog seed | New migration for HI-LO engine/master/title/site publication if needed |

### Gate

| Gate | Required |
| --- | --- |
| Build/lint | Pass. |
| Existing Mines/BOXE smoke | Pass. |
| Launch cashier | Mines and BOXE unchanged; HI-LO path cannot bypass real-money cashier once title exists. |
| Boundary | No HI-LO gameplay logic in H0. |
| Decision Brief | Confirm whether platform registry is generalized or explicitly extended. |

## 4. Wave H1 - Backend Math/RNG/Fairness

### Goal

Implement the pure HI-LO math and deterministic draw helpers.

### File Ownership

| Owns | Avoids |
| --- | --- |
| `backend/app/modules/games/hi_lo/math.py` | Wallet/ledger/platform rounds |
| `backend/app/modules/games/hi_lo/randomness.py` | Mines/BOXE math |
| `backend/app/modules/games/hi_lo/fairness.py` | API routes |
| `tests/unit/...hi_lo...` | Schema |

### Gate

- all 13 rank first-step probabilities/multipliers match `MATH_SPEC.md`;
- arbitrary sequence RTP target is 98% before allowed rounding drift;
- active skip EV proof test passes;
- deterministic draw and replacement tests pass;
- no cap branch exists.

## 5. Wave H2 - Backend State, Schema And API

### Goal

Implement server-authoritative round lifecycle.

### File Ownership

| Owns | Notes |
| --- | --- |
| `backend/app/modules/games/hi_lo/service.py` | Start, idle skip, active skip, predict, cashout, replay. |
| `backend/app/modules/games/hi_lo/state_machine.py` | Legal/illegal transitions. |
| `backend/app/modules/games/hi_lo/repository.py` | SQL persistence. |
| `backend/app/api/routes/hi_lo.py` | Public game API. |
| `backend/migrations/sql/00xx__hi_lo_*.sql` | New tables/seed only. |

### Gate

- demo start/predict/win/loss/cashout PASS;
- real cash table-session path PASS in focused test;
- idempotency duplicate/conflict tests PASS;
- no frontend math dependency;
- Mines/BOXE backend tests unchanged.

## 6. Wave H3 - Player Runtime Visual Shell

### Goal

Create `/hi-lo` player runtime with card stage, options, skip and history.

### File Ownership

| Owns | Avoids |
| --- | --- |
| `frontend/app/hi-lo/page.tsx` | Mines/BOXE UI |
| `frontend/app/ui/hi-lo/*` | `game-runtime/*` unless a platform gap is isolated |
| `frontend/app/ui/hi-lo/hi-lo.css` | Global CSS |

### Visual Gate

Screenshots/DOM metrics:

- idle desktop;
- active desktop;
- correct prediction;
- wrong prediction;
- cashout;
- A edge;
- K edge;
- mobile portrait;
- short landscape/rotation.

No gameplay scrollbars. No clipped card/options/history. If the stage cannot fit
in a viewport, use shared short-viewport gate.

### H3 Implementation Update - 2026-05-23

H3 now provides the first playable HI-LO runtime shell on top of the H2 backend
API.

| Capability | Status | Evidence |
| --- | --- | --- |
| `/hi-lo` route | Implemented | `frontend/app/hi-lo/page.tsx` renders `HiLoStandalone`. |
| Shared boot gates | Implemented | `HiLoStandalone` consumes `GameBootShell`, provider intro, how-to and table-balance gate. |
| Real-money guard | Implemented at player shell level | Real/bonus mode enters `GameTableBalanceGate` before gameplay and uses explicit table-session amount. |
| Backend runtime consume | Implemented | `use-hi-lo-runtime.ts` calls `/games/hi-lo/config`, start, predict, skip and cashout. |
| Gameplay shell | Implemented | `hi-lo-gameplay.tsx` renders card, predictions, skip, collect, history and seed hash. |
| No-scroll layout | Implemented CSS guard | `hi-lo.css` uses fixed viewport product shell, hidden overflow and responsive compression. |
| Rules/how-to content | Partial by design | H3 supplies shell-level content only; rich localized HI-LO content is H4. |
| Replay/account/admin | Not in H3 | Remains H5/H6. |

H3 gate result so far:

- `npm run build`: PASS.
- `python -m pytest tests/contract/test_title_editor_agnostic.py tests/contract/test_game_runtime_frontend_boundary.py -q`: PASS via Docker runner, 18 tests.
- `python -m pytest tests/integration/test_hi_lo_service.py tests/unit/test_hi_lo_math_randomness.py -q`: PASS via Docker runner, 16 tests.
- Browser visual walkthrough on `localhost:3000` remains the product-owner gate before any surface is declared fully green.

## 7. Wave H4 - Content And Asset Pipeline

### Goal

Provide HI-LO-specific copy/rules/how-to and owned/registry-compatible assets.

### File Ownership

| Owns | Notes |
| --- | --- |
| `frontend/app/ui/hi-lo/hi-lo-i18n/*` | it/en/de/es content. |
| `frontend/app/ui/hi-lo/hi-lo-rules-modal.tsx` | Shared modal consumer. |
| `frontend/app/ui/hi-lo/*how-to*` | Card-based tutorial visuals. |
| `frontend/public/game-assets/hi-lo/*` or asset registry seed | Only owned/generated/licensed assets. |

### Gate

- info modal has rich HI-LO content, not container-only;
- how-to-play has 3 HI-LO-specific card visuals;
- card deck/background/suit icon source is documented;
- asset runtime consume proof exists.

### H4 Implementation Update - 2026-05-23

H4 now replaces the temporary rules/how-to copy from H3 with HI-LO-owned
content and assets.

| Item | H4 Status |
| --- | --- |
| Copy defaults | `frontend/app/ui/hi-lo/hi-lo-i18n/hi-lo-copy-defaults.ts` defines it/en/de/es runtime copy. |
| Rules modal | `hi-lo-rules-modal.tsx` consumes shared `GameInfoRulesModal` and renders 7 rich HI-LO sections. |
| How-to visuals | `hi-lo-how-to-visual.tsx` provides 3 card/prediction/collect visuals through `GameHowToPlayGate`. |
| Runtime asset | `frontend/public/game-assets/hi-lo/card-back.v1.svg` is repo-authored and consumed by `hi-lo.css`. |
| Asset source note | `frontend/public/game-assets/hi-lo/README.md` records that analysis screenshots are not shipped runtime assets. |
| Tests | `test_game_runtime_frontend_boundary.py` asserts shared-modal boundary, 7 section content, 98%/server-authoritative copy and asset consume. |

H4 gate result so far:

- `npm run build`: PASS.
- `python -m pytest tests/contract/test_game_runtime_frontend_boundary.py -q`: PASS via Docker runner.
- `python -m pytest tests/integration/test_hi_lo_service.py tests/unit/test_hi_lo_math_randomness.py -q`: PASS via Docker runner from repo root.
- Browser screenshots are collected under `artifacts/hi-lo/h4-content-assets/` when local `:3000` is refreshed.
- Product-owner `localhost:3000` walkthrough remains required before Surface 5 is declared fully green.

## 8. Wave H5 - Backoffice Full-Depth

### Goal

Surface 10 green from the start, using the BOXE replication brief.

### File Ownership

| Owns | Notes |
| --- | --- |
| `frontend/app/ui/hi-lo-backoffice/*` | HI-LO admin adapter. |
| `frontend/app/ui/title-editor/engine-editor-registry.ts` | Registration if not completed in H0. |
| Backend title config/i18n manifest | Only if needed for persistence. |
| Admin tests | 10A-F coverage. |

### Required 10A-F Gate

| Layer | Proof |
| --- | --- |
| 10A Engine page | Side-by-side Mines vs HI-LO: master/variant, editable titles, filters, create variant, inline actions, lobby toggles. |
| 10B Detail shell | Shared command/status/tab shell. |
| 10C Tabs | Overview/copy/rules/config/assets/theme/sound/validation. |
| 10D Field depth | Card assets, background, theme skin, title presentation, copy/rules, validators. |
| 10E Workflow | Draft save on every change, publish, reload, runtime consume. |
| 10F Adjacent pages | Asset library, copy preview, finance/replay where applicable. |

Two-step audit mandatory: auditor + verifier.

### H5 Implementation Update - 2026-05-23

H5 replaces the placeholder HI-LO editor with a real Title Editor adapter. It
uses the shared admin engine page and shared title-editor primitives, while
keeping HI-LO-specific content and card/table semantics local.

| Layer | H5 Status | Evidence |
| --- | --- | --- |
| 10A Engine page | Inherited | `/admin/games/hi_lo` uses the shared games category page: master/variant grouping, editable titles, create variant, filters, inline actions and lobby toggles are platform-level. |
| 10B Detail shell | Implemented | `frontend/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx` consumes `TitleEditorCommandBar`, status banner and `TitleEditorTabFrame`. |
| 10C Tabs | Implemented | Overview, Copy i18n, Rules HTML, Gameplay config, Assets, Sounds, Theme and Validation tabs. |
| 10D Field depth | Implemented | `hi-lo-assets-editor.tsx`, `hi-lo-theme-editor.tsx` and `hi-lo-config-overview.tsx` cover lobby card, title logo, table background, card-back texture, advanced skin, sounds, copy/rules and validators. |
| 10E Workflow | Implemented | Admin endpoints `/admin/games/hi-lo/config`, `/draft`, `/publish` persist through `title_configs`; runtime `/games/hi-lo/config` consumes published presentation config. |
| 10F Adjacent pages | Inherited | Title assets/theme endpoints remain generic; replay/account adjacent closure remains H6. |

H5 gate result so far:

- `npm run build`: PASS.
- `python -m pytest tests/contract/test_title_editor_agnostic.py tests/contract/test_game_runtime_frontend_boundary.py -q`: PASS, 20 tests.
- `python -m pytest tests/integration/test_hi_lo_admin_config.py -q`: PASS, 2 tests.
- `python -m pytest tests/integration/test_hi_lo_service.py tests/unit/test_hi_lo_math_randomness.py -q`: PASS, 16 tests.

Surface 10 is seven-layer green for implemented H5 scope. It remains product
owner pending until Michele walks `/admin/games/hi_lo` and the HI-LO Title
detail on `localhost:3000`.

## 9. Wave H6 - Replay, Account History And Recovery

### Goal

Close replay/account/session recovery surfaces.

### Scope

| Surface | Requirement |
| --- | --- |
| Replay endpoint | Deterministic payload from persisted seed/draw/actions. |
| Player replay | Card playback with play/pause/skip. |
| Account history | HI-LO rounds appear with Mines/BOXE, not hidden in a separate hack. |
| Finance/admin drilldown | Platform round and HI-LO round visible. |
| Recovery | Active collectible round resumes or auto-resolves by approved platform policy. |

### Gate

- replay backend integration PASS;
- frontend replay smoke PASS;
- account history shows HI-LO;
- access-session close/recovery test PASS;
- no silent loss on disconnect.

## 10. Wave H7 - Closure And Distillation

### Goal

Close HI-LO and make game 4 easier.

### Required Outputs

| Output | Required |
| --- | --- |
| 12-surface tracker | 12/12 green or explicit approved residual. |
| Eight-layer table | Per affected surface. |
| Product owner walkthrough | `localhost:3000` player/admin. |
| Closure report | `docs/games/hi-lo/CLOSURE_REPORT.md`. |
| Next-game brief | `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_<DATE>.md`. |
| Backoffice brief | Required if Surface 10 produced any new lesson. |
| Playbook/template/map updates | Same wave if reusable lessons appear. |

## 11. Parallelization Plan

Safe parallelization after H0:

| Parallel set | Conditions |
| --- | --- |
| H1 math + H4 content draft | No shared code overlap; content may use SPEC only. |
| H2 backend + H3 visual shell | Allowed only if H3 uses typed mock/stub and merges after H2 API contract. |
| H5 backoffice + H6 replay | Only after H2/H4; avoid overlap in account/replay files. |

Default merge order:

1. H0 platform enablement.
2. H1 math.
3. H2 backend API/state.
4. H3 player visual.
5. H4 content/assets.
6. H5 backoffice.
7. H6 replay/recovery.
8. H7 closure.

If H3 and H4 are done in parallel, merge H3 first, then rebase H4 and verify
runtime consume.

## 12. Worktree Plan

| Wave | Branch | Worktree | Port |
| --- | --- | --- | --- |
| H0 | `feature/hilo-platform-enablement` | `casinoking-hilo-platform-worktree` | 3100 |
| H1 | `feature/hilo-backend-math` | `casinoking-hilo-math-worktree` | 3101 |
| H2 | `feature/hilo-backend-api` | `casinoking-hilo-api-worktree` | 3102 |
| H3 | `feature/hilo-player-runtime` | `casinoking-hilo-player-worktree` | 3103 |
| H4 | `feature/hilo-content-assets` | `casinoking-hilo-content-worktree` | 3104 |
| H5 | `feature/hilo-backoffice` | `casinoking-hilo-admin-worktree` | 3105 |
| H6 | `feature/hilo-replay-recovery` | `casinoking-hilo-replay-worktree` | 3106 |

Use fewer parallel worktrees if context/load gets noisy. Multiagent is useful
only when file ownership is clean.

## 13. Capability Matrix Skeleton

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H0 platform enablement | yes | n/a | maybe | placeholder only | placeholder only | n/a | required | update | implemented | Third-game registry/lobby/account/admin enabling, no gameplay. |
| H1 math/RNG | n/a | new | n/a | n/a | n/a | n/a | pass | update | implemented | Pure math/fairness helpers. |
| H2 state/API | new | new | new | n/a | n/a | n/a | pass focused | update | implemented | Rounds, idempotency, demo lifecycle, cashout and replay API. |
| H3 player runtime | n/a | consume | consume | n/a | new | new | pass | update | implemented | Visual shell and stage. |
| H4 content/assets | n/a | n/a | consume optional presentation config | n/a | consume | new | pass | update | implemented | Rules, how-to, owned card-back asset. |
| H5 backoffice | maybe | maybe | maybe | new | consume | maybe | required | update | planned | Surface 10 10A-F. |
| H6 replay/recovery | maybe | new | new | maybe | new | maybe | required | update | planned | Replay/account/recovery. |
| H7 closure | n/a | n/a | n/a | evidence | evidence | evidence | required | new/update | planned | 12/12 + PO walkthrough. |

## 14. Stop-And-Ask Triggers

Stop before implementation or merge if:

- platform registry cannot support `hi_lo` without broad refactor;
- real-money launch cashier cannot be guaranteed for HI-LO;
- asset ownership for card deck/background remains unresolved before visual closure;
- recovery cannot prevent silent loss;
- Surface 10 admin page cannot match Mines without platform admin refactor;
- any Wave wants to change Mines/BOXE visuals without zero-diff gate;
- no-scroll DOM matrix fails.

## 15. Decision Brief For Michele

Recommendation:

Approve H0 first. It is the unlocker. It does not implement the game, but makes
the platform capable of hosting a third proprietary game safely.

After H0, backend math/API and player visual/content can be parallelized more
aggressively.

## 16. H0 Implementation Note - 2026-05-23

H0 uses explicit platform registration rather than a broad registry refactor.
That is deliberate: it keeps the first HI-LO code small while removing the
dangerous two-game assumptions found in Phase 3.

Implemented H0 boundaries:

| Boundary | H0 behavior |
| --- | --- |
| Backend game code | `hi_lo` is an allowed game code. |
| Catalog seed | Hidden master `hi_lo` and first variant `hilo001` are seeded with generic title config only. |
| Player lobby route | `hi_lo` resolves to `/hi-lo`, not `/hi_lo`. |
| Player account label | `hi_lo` resolves to `HI-LO`; replay remains unavailable until H6. |
| Title Editor registry | HI-LO has a placeholder editor so admin detail does not look unsupported. |
| Player route | `/hi-lo` exists as non-playable placeholder until H3. |

Explicitly not implemented in H0:

- HI-LO math;
- round state;
- game API;
- player gameplay;
- real-money round execution;
- replay;
- full backoffice editor.

## 17. H1 Implementation Note - 2026-05-23

H1 is implemented as a pure backend nucleus:

| Boundary | H1 behavior |
| --- | --- |
| Math | 13-rank probability table, A/K edge labels, 98% cumulative multiplier, payout rounding. |
| RNG | Deterministic card draw from server seed, client seed, nonce, draw index and draw purpose. |
| Fairness | Server seed hash, draw sequence hash, replayable draw payload and verification helper. |
| Tests | Unit tests cover probability/multiplier contract, skip EV, no cap, uniformity smoke, replacement and tamper detection. |

H1 intentionally leaves these for later waves:

- H2: persistence, state machine and API;
- H3: player runtime consume;
- H5: backoffice consume;
- H6: replay/account consume.

## 18. H2 Implementation Note - 2026-05-23

H2 implements the backend lifecycle and API contract. It remains deliberately
backend-only: player runtime, visual no-scroll gates and product owner
walkthrough are still H3/H7 deliverables.

| Boundary | H2 behavior |
| --- | --- |
| Schema | `hi_lo_rounds`, `hi_lo_actions`, `hi_lo_idempotency_keys`. |
| State machine | Created, active, cashout pending and terminal loss/cashout/expired/quarantined states. |
| API | `/games/hi-lo/config`, `/start`, `/predict`, `/skip`, `/cashout`, `/session`, `/sessions`, player/admin replay. |
| Demo wallet | Demo start debits chips; cashout credits chips; loss records demo loss. |
| Real-money guard | Cash/bonus start requires table session and uses platform round/table-session reservation. |
| Idempotency | Start, predict, skip and cashout replay duplicate requests and reject fingerprint conflicts. |
| Replay | Persisted actions expose deterministic card sequence, server seed hash and draw sequence hash; admin replay includes server seed. |
| Tests | Focused integration tests cover demo start/predict/cashout/replay, route start, real-money table guard, idempotency conflict, loss and active skip limit. |

H2 intentionally leaves these for later waves:

- H3: player runtime consume and no-scroll visual gates;
- H4: HI-LO rules/how-to/card asset content;
- H5: full backoffice consume/config;
- H6: account-history UI, replay viewer and recovery UX.
