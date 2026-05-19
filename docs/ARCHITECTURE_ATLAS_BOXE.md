# BOXE Architecture Atlas

Status: ACTIVE
Last meaningful update: 2026-05-19

Architecture atlas for the BOXE game implementation. This is the active Phase 6
atlas and supersedes `docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`.

## 1. Scope

| Area | Status |
| --- | --- |
| Schema | New BOXE-owned tables only |
| Repository | New BOXE repository module |
| State machine | New pure BOXE state machine |
| API | Game-specific endpoints added in WP-BOXE-2C |
| Wallet/ledger | Integrated through platform adapter; no direct BOXE wallet/ledger mutation |
| Platform shared schema | Not modified |
| Frontend | Implemented in BOXE-local UI, consumed through shared runtime shell |

## 2. Schema Overview

```text
boxe_sessions
  id PK
  player_id
  access_session_id -> game_access_sessions.id nullable
  table_session_id  -> game_table_sessions.id nullable
  title_code/site_code/status

boxe_rounds
  id PK
  session_id -> boxe_sessions.id
  platform_round_id -> platform_rounds.id nullable unique
  rows_count/difficulty/config snapshot
  status/current_step/safe_picks_count
  bet/multiplier/payout/final payout
  fairness seed/hash/client_seed/nonce/path hash
  start idempotency key/request fingerprint

boxe_picks
  id PK
  round_id -> boxe_rounds.id
  step/row_index/selected_box_index
  safe/outcome math snapshot/rng material
  idempotency key/request fingerprint/response snapshot

boxe_idempotency_keys
  id PK
  optional session_id/round_id owner
  operation/idempotency key/request fingerprint
  response snapshot/TTL
```

## 3. State Machine

Implemented statuses:

| Status | Terminal |
| --- | --- |
| `created` | No |
| `active` | No |
| `row_revealed` | No |
| `cashout_pending` | No |
| `completed_cashout` | Yes |
| `completed_top_row` | Yes |
| `failed_mine` | Yes |
| `expired` | Yes |
| `quarantined` | Yes |

The legal transition table is implemented in
`backend/app/modules/games/boxe/state_machine.py` and mirrors `SPEC.md` section
5.3. Illegal attempts raise `BoxeStateTransitionError`, except terminal replay
cases that intentionally return the terminal state for no-duplicate behavior.

## 4. Repository

`backend/app/modules/games/boxe/repository.py` owns:

| Capability | Method family |
| --- | --- |
| Session CRUD | `create_session` |
| Round CRUD | `create_round`, `get_round`, `update_round_status` |
| Round lock | `lock_round` using `SELECT ... FOR UPDATE` |
| Pick storage | `record_pick`, `get_pick_by_idempotency_key` |
| Idempotency primitive | `save_idempotency_result`, `get_idempotency_result` |

The repository consumes the 2A math module for multiplier ladders and payout
snapshots. It does not call wallet, ledger, API, frontend, or Mines code.

## 5. Concurrency

Concurrency is per-round:

| Race | Primitive |
| --- | --- |
| Two reveals same row | `SELECT ... FOR UPDATE` on `boxe_rounds` |
| Reveal retry | Pick idempotency key lookup |
| Cashout retry | Generic idempotency key lookup |
| Reveal vs cashout | Same round lock decides order |
| Recovery vs player action | Future recovery engine must use the same lock |

## 6. API Surface

Implemented in `backend/app/api/routes/boxe.py` with backend behavior in
`backend/app/modules/games/boxe/service.py`.

| Endpoint | Method | Auth | Idempotency | Purpose |
| --- | --- | --- | --- | --- |
| `/api/v1/games/boxe/config` | GET | Public | n/a | Runtime config, rows/difficulty/multiplier paths. |
| `/api/v1/games/boxe/start` | POST | Player bearer | Required | Creates BOXE session/round; demo is isolated, real/bonus opens `platform_rounds` and debits the selected wallet through the adapter. |
| `/api/v1/games/boxe/reveal` | POST | Player bearer | Required | Deterministic pick reveal through 2A RNG/fairness. |
| `/api/v1/games/boxe/cashout` | POST | Player bearer | Required | State transition to completed cashout; real/bonus settles platform win through the adapter. |
| `/api/v1/games/boxe/session/{session_id}` | GET | Player bearer | n/a | Session detail plus latest round. |
| `/api/v1/games/boxe/round/{round_id}/replay` | GET | Player bearer | n/a | Terminal replay only; active rounds rejected. |
| `/api/v1/games/boxe/sessions` | GET | Player bearer | n/a | Paginated terminal session history. |

POST idempotency uses `boxe_idempotency_keys`. Same key and same payload returns
the stored response; same key and different payload returns
`IDEMPOTENCY_CONFLICT`.

Error mapping follows `SPEC.md` section 11. Business failures return structured
`{ success: false, error: { code, message } }` payloads and must not surface as
500 responses.

| SPEC §11.2 scenario | HTTP/code |
| --- | --- |
| Config missing | `404 TITLE_NOT_PUBLISHED` / `404 CONFIG_MISSING` where config row is absent |
| Title not published | `404 TITLE_NOT_PUBLISHED` |
| Master title launch | `403 LAUNCH_REJECTED_MASTER` |
| Table session expired | `409 TABLE_SESSION_EXPIRED` |
| Balance < bet | `422 INSUFFICIENT_BALANCE` |
| Bonus wallet empty | `422 BONUS_WALLET_EMPTY` |
| Network intermittent | Client retry same idempotency key; stored response replayed |
| Backend unreachable | Transport failure outside app response; client retry/resume |
| Round already closed, cashout retry | Same key: replay; new key: `409 ROUND_ALREADY_CLOSED` |
| Disconnect safe multiplier | Future recovery engine consumes `recovery_auto_cashout` transition |
| Loss response missed | Same reveal key replays stored loss; terminal replay confirms loss |

Backoffice manual update: not applicable in WP-BOXE-2C because no admin UI or
admin workflow changed.

## 7. Platform Adapter, Finance, Replay, i18n

Implemented in WP-BOXE-2D after the prerequisite
`WP-PLATFORM-GAME-AGNOSTIC-ADAPTER` made the platform round adapter
game-agnostic.

| Capability | Implementation |
| --- | --- |
| BOXE platform adapter | `backend/app/modules/games/boxe/platform_client.py` consumes `open_game_round`, `settle_game_round_win`, `settle_game_round_loss` with `game_code="boxe"`. |
| Round gateway | `backend/app/modules/games/boxe/round_gateway.py` exposes the BOXE-owned adapter boundary for service code. |
| Platform round storage | `repository.create_platform_round` inserts `platform_rounds` with `game_code="boxe"` after platform bet debit and before `boxe_rounds` FK creation. |
| Settlement close | `repository.close_platform_round` marks won/lost and records settlement transaction id for cashout/top-row wins. |
| Demo isolation | `wallet_source="demo"` creates only BOXE-owned session/round state; no `platform_rounds`, wallet, or ledger mutation. |
| Finance drilldown | Platform polymorphic serialization joins `boxe_rounds` by `platform_round_id` and exposes rows/difficulty/safe picks as optional extras. |
| Account statement | Player statement labels BOXE game movements as `BOXE` and includes BOXE-specific round details. |
| Replay enrichment | Terminal replay includes `platform_round_id`, final payout, and fairness artifacts without exposing active hidden state. |
| Backend i18n manifest | `backend/app/modules/games/boxe/i18n_manifest.py` validates required copy keys for `it`, `en`, `de`, `es`. |

Settlement behavior:

| Flow | Platform behavior |
| --- | --- |
| Real cashout | Bet debited at start, win credited through `settle_game_round_win`, platform round closed `won`. |
| Bonus cashout | Same flow with `wallet_type="bonus"`. |
| Loss | Bet debited at start, no win credit, reserved exposure consumed, platform round closed `lost`. |
| Top-row auto-collect | Final safe reveal settles through the same win path without a cashout request. |
| Cashout retry | BOXE idempotency replays the stored response; platform win idempotency prevents double credit. |

Adapter mapping:

| BOXE value | Platform adapter field |
| --- | --- |
| `rows` | `grid_size` ledger metadata |
| `difficulty` | risk index stored through `mine_count` ledger metadata (`easy=1`, `medium=2`, `hard=3`) |
| `round_id` | `game_session_id` / `platform_rounds.id` |
| `wallet_source` | `wallet_type`, except `demo` which bypasses platform settlement |

The `grid_size` and `mine_count` field names remain platform legacy metadata
from Mines. BOXE treats them as opaque finance metadata only; game math and RNG
stay in BOXE-owned modules.

Backoffice manual update: not applicable in WP-BOXE-2D because no admin UI or
admin workflow changed. Existing finance/account endpoints are wired through
backend serialization only.

## 8. Protected Boundaries

Verified untouched in WP-2D:

| Area | Policy |
| --- | --- |
| Wallet service | No imports, no edits; consumed only through platform adapter. |
| Ledger service | No imports, no edits; settlement flows through `platform_rounds` service. |
| `platform_rounds` schema | No migration or schema edits. |
| `game_access_sessions` | No schema or lifecycle edits. |
| `game_table_sessions` | No schema edits; consumed through platform adapter. |
| Mines | Reference-only reading; no edits/imports. |
| Frontend | No changes |

## 9. Frontend Standalone Boot

Implemented in WP-BOXE-3A after the prerequisite
`WP-FRONTEND-GAME-RUNTIME-AGNOSTIC` made game-runtime storage namespace
whitelist-based.

| Capability | Implementation |
| --- | --- |
| Route | `frontend/app/boxe/page.tsx` renders `BoxeStandalone`. |
| Standalone wrapper | `frontend/app/ui/boxe/boxe-standalone.tsx` consumes `useGameLaunchContext` with `BOXE_GAME_STORAGE_NAMESPACE`. |
| Runtime config | `frontend/app/ui/boxe/use-boxe-runtime.ts` loads `/games/boxe/config?title_code=...`. |
| Provider intro | Shared `GameProviderBootstrap` in `game-runtime/`; BOXE consumes the same moromike lab video/poster/progress as Mines. |
| How-to-play | Shared `GameHowToPlayGate` in `game-runtime/`; BOXE passes Bet / Pick / Collect content and BOXE-specific visual cards. |
| Table balance gate | Shared `GameTableBalanceGate` in `game-runtime/`; BOXE passes quick amounts and a placeholder `onConfirm` that preserves current demo/boot behavior. Backend table-session wiring is deferred to `WP-BOXE-TABLE-SESSION-INTEGRATION`. |
| Gameplay checkpoint | 3A introduced a placeholder; WP-3B replaced it with full `boxe-gameplay.tsx` gameplay, covered in section 10. |
| CSS | `frontend/app/ui/boxe/boxe.css`, imported once from app layout. |
| Smoke | `tests/integration/test_boxe_smoke.py` opens demo boot and verifies short-landscape rotation gate. |

At the 3A checkpoint, start/reveal/cashout controls, board logic, animations,
real cashier integration, admin config, lobby publication, and final validation
were intentionally deferred. The final active implementation is covered in
sections 10-15.

Boot flow:

```text
/boxe?title_code=boxe001&mode=demo
  -> useGameLaunchContext(namespace="boxe")
  -> load BOXE public config
  -> TitleThemeProvider resolves default theme
  -> Provider intro
  -> How-to-play
  -> shared table balance gate
  -> BoxeGameplay
```

Protected in WP-3A:

| Area | Verification |
| --- | --- |
| `frontend/app/ui/game-runtime/` | Consumed through public APIs; WP-PLATFORM-PREGAME-SHELL-EXTRACTION added shared provider/how-to/table-balance implementations without BOXE-specific imports. |
| `frontend/app/ui/mines/` | No edits/imports. |
| Backend | No production backend changes; smoke seeds catalog data in test setup only. |
| Gameplay math/state | No frontend payout or outcome logic. |

## 10. Frontend Gameplay

Implemented in WP-BOXE-3B. Gameplay remains BOXE-local and consumes the backend
contracts introduced in Fasi 2A-2D.

| Capability | Implementation |
| --- | --- |
| Pyramid board | `boxe-pyramid-board.tsx` renders 4-8 rows, bottom-to-top progression, one active row, covered/safe/mine/opaque states. |
| Payout display | `boxe-payout-display.tsx` renders backend multiplier ladders and highlights reached/current/next steps. |
| Settings panel | `boxe-settings-panel.tsx` exposes rows and difficulty from runtime config inside shared `GameSettingsPanel`; controls lock during an active round. |
| Bet/collect panel | Shared `GameControlRail` / `GameBetPanel` / `GameQuickChips` / `GameActionButtons` / `GameBalanceFooter` own the Mines-like left rail ergonomics; BOXE passes rows/difficulty settings and game-specific labels/state. |
| Runtime actions | `use-boxe-runtime.ts` exposes config, start, reveal, cashout, replay, wallet read and demo-player provisioning helpers. |
| Copy defaults | `boxe-i18n/boxe-copy-defaults.ts` defines minimal `it/en/de/es` gameplay copy keys. |
| Gameplay composer | `boxe-gameplay.tsx` holds frontend-only UI state and calls backend APIs with UUID idempotency keys. |
| Smoke | `tests/integration/test_boxe_smoke.py` covers boot, cashout, loss, top-row auto-collect, retry and short-landscape gate. |

Frontend state model:

```text
idle
  -> starting
  -> active / row_revealed
  -> cashout_pending
  -> completed_cashout | completed_top_row | failed_mine
```

The frontend does not calculate outcome, multiplier, payout, success
probability, or hidden row content. It displays `multipliers`, `outcome`,
`payout`, `status`, and `next_step_options` returned by BOXE backend endpoints.
On loss, only the selected mine is shown; unpicked boxes in the same row are
rendered as opaque because the backend does not expose hidden row contents.

Idempotency:

| Operation | Frontend behavior |
| --- | --- |
| Start | Generate UUID key; retry reuses the same key/body. |
| Reveal | Generate UUID key per pick; network retry reuses the same row/position/key. |
| Cashout | Generate UUID key; retry reuses the same key. |

Protected in WP-3B:

| Area | Verification |
| --- | --- |
| `frontend/app/ui/game-runtime/` | No edits; imported only by wrapper/gameplay for public shell/rotation gate APIs. |
| `frontend/app/ui/mines/` | No edits/imports; boundary test remains authoritative. |
| Backend | No production backend changes. |
| Math/fairness | Display-only in frontend; backend remains owner. |

## 11. Animations And Polish

Implemented in WP-BOXE-3C. Animations are BOXE-local and purely presentational:
they do not change backend outcomes, frontend state transitions, idempotency
keys, or API timing.

| Capability | Implementation |
| --- | --- |
| Reveal animations | `boxe-animations.css` adds scoped `.boxe-*` safe flip, diamond glow, mine pulse/explosion, and current-row opaque reveal states. |
| Payout pill slide | `boxe-payout-display.tsx` marks the current step and CSS animates the highlighted pill on multiplier progression. |
| Win celebration | `boxe-win-celebration.tsx` shows a short auto-dismiss overlay for cashout/top-row wins with static fallback under reduced motion. |
| Audio hook | `use-boxe-audio.ts` consumes platform audio preferences passed from `BoxeStandalone` and emits BOXE audio events with silent placeholder assets. |
| Reduced motion | `boxe-animations.css` disables transform/transition animations under `prefers-reduced-motion: reduce`. |
| Visual baseline | `tests/integration/test_boxe_visual_regression.py` captures idle, active-safe, loss, cashout-win and top-row-win at desktop and mobile sizes. |
| Smoke extension | `tests/integration/test_boxe_smoke.py` verifies gameplay still flows through animations, audio events fire, and reduced-motion reveal is instant. |

Animation contract:

| Event | Visual feedback | Max timing |
| --- | --- | --- |
| Safe reveal | Box flip plus diamond scale/glow | 400ms |
| Mine reveal | Red pulse/explosion on selected mine | 400ms |
| Loss row reveal | Current-row opaque cells fade in with 50ms stagger | 400ms per cell |
| Step progression | Current multiplier pill slides/highlights | 400ms |
| Cashout/top-row win | Non-blocking overlay, click or auto-dismiss | 2600ms overlay lifetime |

Audio event contract:

| Event | Trigger |
| --- | --- |
| `bet_placed` | Start round success |
| `safe_reveal` | Reveal returns `safe` |
| `mine_reveal` | Reveal returns `mine` |
| `cashout_won` | Cashout succeeds |
| `top_row_won` | Reveal returns `top_row` |

The hook currently dispatches silent `boxe:audio-event` events with
`muted`, `volume`, and `hasSoundAsset=false`. Real sound files remain a future
asset/config concern; no game-runtime audio infrastructure extension was needed.

Visual baseline set:

| Scenario | Viewports | Baseline path |
| --- | --- | --- |
| Idle | Desktop, mobile | `tests/visual/baselines/boxe_3c/idle/` |
| Active safe pick | Desktop, mobile | `tests/visual/baselines/boxe_3c/active_safe/` |
| Loss | Desktop, mobile | `tests/visual/baselines/boxe_3c/loss/` |
| Cashout win | Desktop, mobile | `tests/visual/baselines/boxe_3c/cashout_win/` |
| Top-row win | Desktop, mobile | `tests/visual/baselines/boxe_3c/top_row_win/` |

Protected in WP-3C:

| Area | Verification |
| --- | --- |
| `frontend/app/ui/game-runtime/` | No edits; audio preferences consumed through public hook only. |
| `frontend/app/ui/mines/` | No edits/imports; Mines animation/audio patterns used reference-only. |
| Backend | No production backend changes. |
| Gameplay state machine | No state transition changes; animations react to existing state only. |

## 12. Admin Config And Copy

Implemented in WP-BOXE-4A after
`WP-PLATFORM-TITLE-EDITOR-AGNOSTIC` made the Title Editor shell engine
whitelist-based and generic.

| Capability | Implementation |
| --- | --- |
| Admin config schema | `backend/migrations/sql/0040__boxe_admin_config.sql` creates `boxe_admin_config`. |
| Backend config module | `backend/app/modules/games/boxe/admin_config.py` validates rows, difficulty, copy, rules and draft/live payloads. |
| Admin API | `GET /api/v1/admin/games/boxe/config`, `PUT /api/v1/admin/games/boxe/config/draft`, `POST /api/v1/admin/games/boxe/config/publish`. |
| Runtime config | `backend/app/modules/games/boxe/service.py` reads published BOXE config for `/api/v1/games/boxe/config`. |
| Audit | Publish writes an admin audit event with `engine_code="boxe"` and the title code. |
| Editor UI | `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx` expands the platform stub into the BOXE plugin. |
| Manual | `docs/BACKOFFICE_MANUAL.md` documents Games / BOXE configuration. |
| Tests | `tests/integration/test_boxe_admin_config.py` covers draft, publish, validation, audit and active-round config snapshots. |

Config data model:

| Field | Contract |
| --- | --- |
| `rows_enabled` | Non-empty subset of `4, 5, 6, 7, 8`; persisted sorted. |
| `default_rows` | Must be present in `rows_enabled`. |
| `difficulty_enabled` | Non-empty subset of `easy`, `medium`, `hard`; persisted in canonical order. |
| `default_difficulty` | Must be present in `difficulty_enabled`. |
| `copy` | Required BOXE copy keys for `it`, `en`, `de`, `es`; max lengths enforced. |
| `rules_html` | Required `bet_collect` rules section for every locale; backend sanitizes before persistence. |
| `draft_payload_json` | Working draft used by the admin editor. |
| `published_payload_json` | Live config used by runtime start/config endpoints. |

Admin workflow:

```text
Title Editor (engineCode="boxe")
  -> load BOXE draft via admin API
  -> validate rows/difficulty/copy/rules client-side
  -> save draft
  -> publish draft to live
  -> runtime config serves published payload
```

Runtime behavior:

| Scenario | Behavior |
| --- | --- |
| No BOXE admin row yet | Backend returns BOXE product defaults without persisting a row until draft save/publish. |
| Public config request | Returns published rows/difficulty plus presentation config. |
| Start round | Rejects rows/difficulty not enabled in the current published payload. |
| Active round during publish | Existing round keeps its stored `rows`/`difficulty` config snapshot. |
| Future round after publish | Uses the newly published rows/difficulty constraints. |

Protected in WP-4A:

| Area | Verification |
| --- | --- |
| `frontend/app/ui/title-editor/` | No 4A shell edits; platform refactor happened in the prerequisite WP. |
| `frontend/app/ui/mines/` | No Mines admin/runtime edits. |
| BOXE gameplay components | No gameplay state, board, payout, animation or bet-panel edits. |
| `frontend/app/ui/game-runtime/` | No edits. |
| Wallet/ledger/platform schema | No edits; admin config is BOXE-owned. |

## 13. Admin Assets, Sounds And Theme

Implemented in WP-BOXE-4B as an expansion of the BOXE Title Editor plugin.

Asset kind decision:

| BOXE need | Asset kind | Decision |
| --- | --- | --- |
| Lobby card | `game_card` | Reuse shared title card semantics; rendered in player lobby. |
| Safe symbol | `symbol_safe` | Reuse Mines-safe semantic kind; BOXE safe cell means the same player-facing concept. |
| Mine symbol | `symbol_mine` | Reuse Mines-mine semantic kind; no new registry kind needed. |
| Sounds | n/a | BOXE v1 keeps platform/default silent placeholders; no custom Sounds tab in 4B. |
| Theme | Shared title theme tokens | Reuse platform token allowlist; no advanced skin v1. |

Admin implementation:

| Capability | Implementation |
| --- | --- |
| Assets tab | `frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx`. |
| Theme tab | `frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx`. |
| Upload/list/delete API | Shared `/api/v1/admin/titles/{title_code}/assets`. |
| Theme draft/publish API | Shared `/api/v1/admin/titles/{title_code}/theme`. |
| Runtime theme | Shared `/api/v1/titles/{title_code}/theme`, consumed by `GameBootShell`. |
| Audit | Asset upload/delete and theme publish write `admin_audit_log`. |
| Tests | `tests/integration/test_boxe_admin_assets.py`. |

Operator upload contract:

| Asset | Formats | Limit | Recommended dimensions | Render mode |
| --- | --- | --- | --- | --- |
| Lobby card | PNG, JPEG, WebP | 300 KB | 512x512 square | Cover, center |
| Safe symbol | PNG, SVG | 150 KB operator guidance, shared hard cap 512 KB | 256x256 transparent | Contain |
| Mine symbol | PNG, SVG | 150 KB operator guidance, shared hard cap 512 KB | 256x256 transparent | Contain |

Protected in WP-4B:

| Area | Verification |
| --- | --- |
| Asset registry schema | No schema extension; existing asset kinds reused. |
| `frontend/app/ui/title-editor/` | No shell edits; BOXE remains plugin-only. |
| `frontend/app/ui/mines/` | No Mines asset/theme edits. |
| BOXE gameplay | No gameplay state or visual behavior changes. |

## 14. Site, Lobby And Launch

Implemented in WP-BOXE-5. BOXE becomes a normal catalog title that can be
published by the operator and launched through the player lobby cashier.

Catalog seed:

| Object | Code | Notes |
| --- | --- | --- |
| Engine | `boxe` | Registered by `backend/migrations/sql/0041__boxe_catalog_seed.sql`. |
| Master title | `boxe` | Public launch blocked by platform launch validation. |
| First variant | `boxe001` | Seeded hidden by default; operator publishes from Site/Lobby. |
| Theme row | `title_configs` for `boxe`, `boxe001` | Required by shared theme service. |

Site/lobby flow:

```text
Admin Games -> BOXE title config/assets/theme
  -> Admin Site -> publish boxe001 visible + demo/real
  -> GET /api/v1/games/library includes boxe001
  -> Player lobby renders BOXE card with game_card/fallback
  -> Launch Cashier routes:
       demo  -> /boxe?title_code=boxe001&mode=demo
       cash  -> /boxe?title_code=boxe001&mode=real_cash&wallet_source=real
       bonus -> /boxe?title_code=boxe001&mode=real_bonus&wallet_source=bonus
```

Runtime launch behavior:

| Scenario | Behavior |
| --- | --- |
| Hidden BOXE title | Not returned by `/games/library`; public launch rejected. |
| Visible demo BOXE title | Demo launch succeeds for `game_code="boxe"`. |
| Visible real BOXE title | Player lobby routes with `wallet_source=real`; BOXE gameplay uses player auth token. |
| Visible bonus BOXE title | Player lobby routes with `wallet_source=bonus`; BOXE gameplay uses bonus wallet source. |
| Master title `boxe` | Public launch returns `LAUNCH_REJECTED_MASTER`. |

Protected in WP-5:

| Area | Verification |
| --- | --- |
| Launch cashier shell | No new shared shell capability; player lobby route mapping handles BOXE. |
| `frontend/app/ui/game-runtime/` | No edits. |
| Wallet/ledger/platform rounds | No edits. |
| Mines frontend/backend | No edits. |

## 15. Documentation Closure

Implemented in WP-BOXE-6.

| Document | Status |
| --- | --- |
| `docs/ARCHITECTURE_ATLAS_BOXE.md` | ACTIVE final atlas. |
| `docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md` | Historical redirect to the active atlas. |
| `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` | Updated with BOXE as second runtime consumer. |
| `docs/BACKOFFICE_MANUAL.md` | Updated for BOXE config, assets/theme and Site/Lobby publishing. |
| `docs/README.md` | Indexes the active BOXE atlas. |
| `docs/games/boxe/CLOSURE_REPORT.md` | Distills BOXE learnings into Playbook v1 / Template v1. |

Canonical BOXE references:

| Topic | Document |
| --- | --- |
| Product contract | `docs/games/boxe/SPEC.md` |
| Architecture mapping | `docs/games/boxe/ARCHITECTURE_MAPPING.md` |
| Math/RNG/fairness | `docs/games/boxe/MATH_SPEC.md` |
| Implementation log | `docs/games/boxe/BOXE_BRIEF.md` |
| Backoffice operator workflow | `docs/BACKOFFICE_MANUAL.md` |
| Closure and HI-LO memo | `docs/games/boxe/CLOSURE_REPORT.md` |
