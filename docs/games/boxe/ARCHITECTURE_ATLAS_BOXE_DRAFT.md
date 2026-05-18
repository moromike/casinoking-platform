# BOXE Architecture Atlas Draft

Status: DRAFT
Last meaningful update: 2026-05-18

This draft records the backend foundation produced by `WP-BOXE-2B-SCHEMA-STATE`.
The final atlas remains a Phase 6 deliverable.

## 1. Scope

| Area | Status |
| --- | --- |
| Schema | New BOXE-owned tables only |
| Repository | New BOXE repository module |
| State machine | New pure BOXE state machine |
| API | Game-specific endpoints added in WP-BOXE-2C |
| Wallet/ledger | Out of scope |
| Platform shared schema | Not modified |
| Frontend | Out of scope |

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
| `/api/v1/games/boxe/start` | POST | Player bearer | Required | Money-neutral round/session creation for Fase 2C. |
| `/api/v1/games/boxe/reveal` | POST | Player bearer | Required | Deterministic pick reveal through 2A RNG/fairness. |
| `/api/v1/games/boxe/cashout` | POST | Player bearer | Required | State transition to completed cashout without wallet settlement. |
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
| Provider intro | BOXE-local boot overlay; no game-runtime or Mines changes. |
| How-to-play | `boxe-how-to-play-content.tsx` implements Bet / Pick / Collect. |
| Table balance gate | `boxe-table-balance-config.ts` provides provisional demo amounts; real cashier remains Fase 5. |
| Gameplay placeholder | `boxe-gameplay.tsx` renders runtime config summary, placeholder pyramid, multiplier path, and short-landscape gate. |
| CSS | `frontend/app/ui/boxe/boxe.css`, imported once from app layout. |
| Smoke | `tests/integration/test_boxe_smoke.py` opens demo boot and verifies short-landscape rotation gate. |

3A intentionally does not implement start/reveal/cashout controls, board logic,
animations, real cashier integration, admin config, lobby publication, or replay
viewer. Those remain in Fasi 3B-7.

Boot flow:

```text
/boxe?title_code=boxe001&mode=demo
  -> useGameLaunchContext(namespace="boxe")
  -> load BOXE public config
  -> TitleThemeProvider resolves default theme
  -> Provider intro
  -> How-to-play
  -> provisional table balance gate
  -> BoxeGameplay placeholder
```

Protected in WP-3A:

| Area | Verification |
| --- | --- |
| `frontend/app/ui/game-runtime/` | No edits in BOXE 3A; consumed only through public APIs. |
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
| Settings panel | `boxe-settings-panel.tsx` exposes rows and difficulty from runtime config; controls lock during an active round. |
| Bet/collect panel | `boxe-bet-panel.tsx` owns free bet input, read-only balance display, BET/COLLECT action switching, disabled states. |
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
