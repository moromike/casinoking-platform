# BOXE Replay Parity Approach

Status: ACTIVE - Wave 4 Parte A
Last meaningful update: 2026-05-21

Parte A is doc-only. Product decision is locked: BOXE replay inherits the Mines replay feature 1:1 across player view and backoffice management.

## 1. Problem

Replay is Surface 11 of the 12-surface check. Mines has a replay stack. BOXE has backend pieces but no complete player/runtime/backoffice replay experience. This gap slipped through multiple waves and now blocks BOXE parity.

## 2. Sources Audited

| Source | Finding |
| --- | --- |
| `docs/MINES_REPLAY_VIEWER_PLAN.md:36` | Replay is designed as game-module owned with reusable account/runtime/backoffice entry points. |
| `docs/MINES_REPLAY_VIEWER_PLAN.md:67` | Shared replay contract was intended beyond Mines. |
| `backend/app/api/routes/mines.py:296` | Mines routes include replay/history style endpoints. |
| `backend/app/api/routes/mines.py:735` | Mines session history endpoint area. |
| `backend/app/api/routes/mines.py:801` | Mines replay/session detail route area. |
| `backend/app/api/routes/mines.py:885` | Mines fairness/replay support route area. |
| `backend/app/api/routes/mines.py:946` | Mines additional replay/history route area. |
| `backend/app/modules/games/mines/service.py:740` | Mines replay payload hides mines until round closed, then exposes terminal state. |
| `frontend/app/ui/mines/mines-standalone.tsx:990` | Mines runtime loads latest/session replay data. |
| `frontend/app/ui/mines/mines-standalone.tsx:1019` | Mines runtime session/replay fetch wiring. |
| `frontend/app/ui/mines/mines-replay-viewer.tsx:7` | Mines replay viewer types. |
| `frontend/app/ui/mines/mines-replay-viewer.tsx:71` | Mines replay viewer render/control surface. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:11` | Mines rules modal includes replay tab type surface. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:132` | Mines replay tab body. |
| `frontend/app/ui/player-account-page.tsx:280` | Account page has Mines-specific history/replay assumptions. |
| `frontend/app/ui/player-account-page.tsx:374` | Account session detail/replay navigation area. |
| `frontend/app/ui/player-account-page.tsx:628` | Account replay drilldown area. |
| `frontend/app/ui/admin-finance-panel.tsx:344` | Admin finance drilldown is ledger/session detail, not a game replay viewer. |
| `backend/app/api/routes/boxe.py:211` | BOXE backend replay endpoint exists. |
| `backend/app/modules/games/boxe/service.py:566` | BOXE replay service rejects active rounds and returns terminal payload. |
| `backend/app/modules/games/boxe/service.py:721` | BOXE replay payload includes picks/safe path/current reveal, not full pyramid. |
| `backend/migrations/sql/0039__boxe_session_tables.sql:45` | BOXE session schema. |
| `backend/migrations/sql/0039__boxe_session_tables.sql:136` | BOXE picks schema. |
| `tests/integration/test_boxe_api.py:272` | BOXE replay API test coverage exists. |
| `tests/integration/test_boxe_api.py:344` | BOXE replay/fairness test area. |
| `frontend/app/ui/boxe/use-boxe-runtime.ts:66` | BOXE replay type/fetch helper exists. |
| `frontend/app/ui/boxe/use-boxe-runtime.ts:287` | BOXE replay fetch helper is not consumed by runtime UI. |
| `frontend/app/ui/boxe/boxe-standalone.tsx:379` | BOXE info button opens HTP, not replay/rules modal. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx:720` | No replay viewer render path in gameplay shell. |
| `docs/games/boxe/SPEC.md:700` | BOXE spec requires replay/history. |
| `docs/games/boxe/SPEC.md:753` | BOXE spec references replay/fairness needs. |
| `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md:84` | Earlier audit recorded replay missing. |
| `docs/games/boxe/MANUAL_PLAYTHROUGH_CHECKLIST.md:71` | Replay remains manual/open. |

## 3. Mines Replay Stack

| Layer | Mines capability | BOXE target |
| --- | --- | --- |
| Backend replay endpoint | Closed-session replay payload with fairness state. | Game-specific BOXE endpoint with same platform shape. |
| Runtime player view | Replay viewer and modal/tab entry point. | BOXE replay viewer rendered in same shell. |
| Account/session history | Player can drill into past sessions. | Polymorphic account replay; no Mines hardcode. |
| Backoffice management | Session drilldown support exists, but game replay admin needs formalization. | BOXE management inherits shared pattern, not a one-off. |
| Fairness visibility | Hidden until terminal, then reveal authoritative board. | Full pyramid payload from WP-REVEAL. |

## 4. BOXE Current State

BOXE is partially wired on the backend and unconsumed on the frontend.

| Area | Current status | Gap |
| --- | --- | --- |
| API route | Exists | Payload not full-pyramid ready. |
| Service payload | Exists | Uses picks/current reveal, not terminal full reveal. |
| Frontend fetch helper | Exists | No runtime consumer. |
| Runtime viewer | Missing | Need `BoxeReplayViewer`. |
| Rules/info modal tab | Missing | Coordinate with WP-INFO. |
| Account history | Mines-specific hardcodes remain | Need game-agnostic replay registry. |
| Backoffice management | No BOXE replay management UI | Need shared admin replay pattern. |

## 5. Architecture Decision

Replay should become a shared platform pattern with game-specific board renderers.

Proposed structure:

| Primitive | Responsibility |
| --- | --- |
| `GameReplayShell` | Shared container, controls, metadata, loading/error/empty states. |
| `GameReplayControls` | Play/pause/step/skip/speed controls. |
| `GameReplayTimeline` | Shared event timeline and active-step model. |
| Mines adapter | Renders grid cells from Mines payload. |
| BOXE adapter | Renders pyramid rows from BOXE payload. |
| Replay registry | Maps game slug to fetcher, viewer adapter, account/admin labels. |

The backend remains game-specific because fairness and board models differ, but the response envelope should be aligned.

## 6. BOXE Replay Payload Target

BOXE replay must include enough data to reproduce the round deterministically:

| Field | Purpose |
| --- | --- |
| `session_id` / public replay id | Lookup and share surface. |
| `rows`, `difficulty`, `bet_amount`, `currency` | Reconstruct settings. |
| `multiplier_ladder` | Show payout progression. |
| `picks` | Ordered row/position actions. |
| `outcome` / `terminal_status` | Loss/cashout/win. |
| `cashout_multiplier` / `payout` | Financial result. |
| `pyramid_full_reveal` | Full terminal board from WP-REVEAL. |
| `fairness` | Seed/hash/nonce/proof fields already available to backend. |
| `created_at`, `closed_at` | Timeline/account display. |

The payload shape should align with WP-REVEAL. Replay cannot be completed cleanly while terminal full reveal is missing.

## 7. Player Runtime Plan

| Step | Scope |
| --- | --- |
| 1 | Add `BoxeReplayViewer` using existing pyramid board rendering in read-only mode. |
| 2 | Wire `getBoxeReplay` into `boxe-standalone.tsx`/runtime state. |
| 3 | Expose replay through the shared info/rules modal tab once WP-INFO creates the modal shell. |
| 4 | Support latest session and explicit replay id flows like Mines. |
| 5 | Keep active gameplay untouched; replay is a read-only surface. |

## 8. Account and Backoffice Plan

| Area | Decision |
| --- | --- |
| Player account | Replace Mines-specific replay hardcodes with a game replay registry. BOXE registers its fetcher/viewer. |
| Backoffice replay management | Extract shared replay/session drilldown tab or module. BOXE consumes it with pyramid adapter. |
| Admin finance | Keep ledger/session detail, but add game replay drilldown where appropriate. |
| Search/filter | Reuse account/admin session list patterns; add game filter if missing. |

## 9. Dependency on WP-REVEAL and WP-INFO

Replay depends on both:

| Dependency | Reason |
| --- | --- |
| WP-REVEAL | Replay must show full terminal pyramid, not current-row-only inferred cells. |
| WP-INFO | Runtime modal/tab host should expose replay consistently with Mines. |
| WP-BO | Backoffice replay management should reuse the shared title-editor/admin shell direction. |

Recommended ordering:

1. Lock reveal payload contract.
2. Build BOXE backend replay payload to that contract.
3. Build player replay viewer.
4. Add account/backoffice management.

## 10. Parte B Granularity

| Sub-WP | Scope | Estimate |
| --- | --- | --- |
| REPLAY-B1 shared replay shell | Extract reusable shell/controls/timeline without Mines drift. | 4-6 prompts |
| REPLAY-B2 BOXE backend payload | Align endpoint with full pyramid and fairness envelope. | 4-6 prompts |
| REPLAY-B3 BOXE player viewer | Pyramid playback, controls, runtime modal integration. | 4-6 prompts |
| REPLAY-B4 account replay registry | Remove Mines hardcode and register BOXE. | 3-5 prompts |
| REPLAY-B5 backoffice replay management | Shared admin/session drilldown plus BOXE adapter. | 4-6 prompts |
| REPLAY-B6 tests/evidence | API contracts, player screenshots, account/admin flows. | 3-4 prompts |

Total expected effort: 22-33 prompts, likely 3-5 engineering days depending on how much Mines replay shell can be extracted without drift.

## 11. Stop-and-Ask

| Trigger | Category | Ask |
| --- | --- | --- |
| Mines replay shell is too Mines-specific for zero-diff extraction. | B/C | Stop and decide whether to first build shared shell or implement BOXE adapter with duplicated shell pending cleanup. |
| Full pyramid reveal payload is not available. | D | Coordinate with WP-REVEAL; replay should not ship with synthetic terminal cells. |
| Account page ownership is unclear. | D | Ask whether account replay registry belongs to player account WP or game runtime WP. |
| Backoffice replay management requires a new top-level admin nav. | D | Ask product/CTO for placement. |
| Fairness fields expose sensitive seed data too early. | C/D | Stop and align reveal/proof timing. |

## 12. Capability Matrix

| Capability | Mines | BOXE current | BOXE target |
| --- | --- | --- | --- |
| Backend replay endpoint | Yes | Partial yes | Yes, aligned payload |
| Closed-session terminal board | Yes | Current-row partial | Full pyramid |
| Runtime replay viewer | Yes | No | Yes |
| Replay controls | Yes | No | Shared |
| Rules modal replay tab | Yes | No | Yes after WP-INFO |
| Player account replay | Mines-specific | No BOXE | Game registry with BOXE |
| Backoffice replay management | Partial/session detail | No BOXE | Shared admin replay management |
| Fairness verification | Yes | Partial backend | Yes |

## 13. 12-Surface Impact

| Surface | Impact |
| --- | --- |
| 11 Replay | Direct. Current BOXE status is red. |
| 7 Gameplay shell | Direct. Runtime replay entry point and viewer. |
| 10 Backoffice editor | Direct. Replay management must exist for BOXE. |
| 12 Resume/disconnect | Direct. Replay/session restoration depends on stable payloads. |
| 5 Info/rules | Indirect. Replay tab host is shared with info modal. |

## 14. Parte B Delivery - 2026-05-21

Status: PASS after serialization on top of WP-REVEAL, WP-INFO, and WP-BO.

### Delivered Capability Matrix

| Capability | Result | Evidence |
| --- | --- | --- |
| Backend BOXE replay endpoint | PASS | `GET /games/boxe/round/{round_id}/replay` returns active snapshots and terminal full-pyramid payloads. |
| Admin replay endpoint | PASS | `GET /games/boxe/admin/round/{round_id}/replay` accepts BOXE round ids and platform round ids. |
| Full-pyramid replay determinism | PASS | Replay payload uses the server-authoritative `pyramid_full_reveal` contract from WP-REVEAL, with deterministic fallback for older rows. |
| Runtime info modal replay tab | PASS | BOXE consumes `GameInfoRulesModal` through `BoxeRulesModal`; local `boxe-info-modal.tsx` duplicate was removed. |
| Player replay viewer | PASS | `BoxeReplayViewer` renders pyramid playback controls and fairness fields in the runtime modal. |
| Account history entry point | PASS | Player account history merges Mines and BOXE rounds and dispatches to the game-specific replay viewer. |
| Backoffice replay management | PASS | Admin finance drilldown exposes BOXE replay for finance/session review. |
| Fairness visibility | PASS | Player/admin replay shows server seed hash, client seed, nonce, and outcome verification without exposing plaintext server seed. |
| Smoke modernization | PASS | BOXE smoke selectors updated for Wave 2/4 shared footer, mobile settings sheet, and shared rotation gate copy. |

### Gate Results

| Gate | Result |
| --- | --- |
| Frontend build + i18n lint | PASS |
| `tests/integration/test_boxe_api.py` | PASS |
| `tests/contract/test_game_runtime_frontend_boundary.py` | PASS |
| Full `tests/integration/test_boxe_smoke.py` | PASS |
| Runtime replay viewer smoke | PASS, covered by `test_boxe_demo_safe_sequence_cashout_resets_to_bet` opening the REPLAY tab and asserting viewer/fairness content. |
| Mines functional/visual ownership | PASS: no Mines runtime code changed; account integration remains polymorphic. |

### Stop-and-Ask Outcome

No remaining Stop-and-Ask. The serialization decisions were applied: REPLAY consumes
`GameInfoRulesModal` from WP-INFO and the `pyramid_full_reveal` contract from
WP-REVEAL; the duplicated local info modal was removed.
