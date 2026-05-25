Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Registry Audit - Finance / Replay / Account

Scope: prerequisite before COINS. The goal is to remove the third-game hard
branch pattern from account history, admin finance replay routing, and finance
summary dispatch so COINS does not become a fourth `if game === ...` branch.

## 1. Inventory

| Area | Before | Classification | Resolution |
| --- | --- | --- | --- |
| Player account history fetch | `player-account-page.tsx` fetched Mines, BOXE and HI-LO through three explicit calls. | convert to registry now | `GAME_ACCOUNT_HISTORY_DESCRIPTORS` now drives endpoint fan-out and per-game mapping. |
| Player replay endpoint | `readReplayEndpoint()` branched on `round.game_code`. | convert to registry now | `readPlayerGameReplayEndpoint()` delegates to `GAME_REPORTING_REGISTRY`. |
| Player replay renderer | `renderRoundReplay()` branched on BOXE / HI-LO / Mines. | convert to registry now | `renderPlayerGameReplay()` delegates to the registered descriptor. |
| Account config/progress labels | `readRoundConfigLabel()` and `readRoundRevealLabel()` branched on game code. | convert to registry now | Descriptor methods provide game-specific labels. |
| Admin finance replay availability | `gameCode === "boxe" || gameCode === "hi_lo"`. | convert to registry now | `hasAdminGameReplay(gameCode)`; Mines is now registered too. |
| Admin finance replay endpoint | HI-LO branch with implicit BOXE fallback. | convert to registry now | `readAdminGameReplayEndpoint()` returns `null` for unknown games, no fallback. |
| Admin finance replay renderer | HI-LO branch with implicit BOXE fallback. | convert to registry now | `renderAdminGameReplay()` delegates to descriptor. |
| Backend admin finance enrichment | `_build_game_enrichment()` branched on BOXE / HI-LO / Mines. | convert to registry now | `_GAME_ENRICHMENT_BUILDERS`. |
| Backend account statement summary | `_build_game_detail_summary()` branched on Mines / BOXE / HI-LO. | convert to registry now | `_GAME_DETAIL_SUMMARY_BUILDERS`. |
| Access session auto-settle dispatch | `_auto_settle_active_round_for_access_session()` branched on game code. | convert to registry now | `_AUTO_SETTLE_ACTIVE_ROUND_HANDLERS`. |
| Game-specific math/state internals | Per-game modules contain game semantics. | keep game-specific | Not touched; these are not platform dispatch debt. |
| Admin title-editor engine registry | Already registry-based. | keep | `engine-editor-registry.ts` remains the canonical title editor registration point. |

## 2. Implemented Pattern

Frontend reporting registry:

- file: `frontend/app/ui/game-reporting-registry.tsx`;
- descriptor key: `gameCode`;
- responsibilities: player history endpoint, raw-to-normalized account history
  mapper, player replay endpoint, admin replay endpoint, replay renderers, account
  config/progress labels;
- registered games: Mines, BOXE, HI-LO.

Backend lightweight dispatch registries:

- `backend/app/modules/admin/service.py` uses `_GAME_ENRICHMENT_BUILDERS`;
- `backend/app/modules/account/service.py` uses `_GAME_DETAIL_SUMMARY_BUILDERS`;
- `backend/app/modules/platform/access_sessions/service.py` uses
  `_AUTO_SETTLE_ACTIVE_ROUND_HANDLERS`.

Unknown game behavior:

- frontend replay endpoint lookup returns `null`;
- admin/player UI shows replay unavailable/error instead of calling another
  game's endpoint;
- no implicit fallback to BOXE remains.

## 3. Contract Tests

Added `tests/contract/test_game_reporting_registry.py`.

The test asserts:

- Mines / BOXE / HI-LO are registered in `GAME_REPORTING_REGISTRY`;
- account history consumes descriptor fan-out;
- admin finance consumes descriptor replay routing/rendering;
- old player/admin branch helpers are absent;
- backend finance/account/access-session dispatch has registry tables.

## 4. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Game registry pattern - account history | n/a | unchanged | unchanged | n/a | REFACTOR | n/a | NEW | UPDATE | green | Fetch/mapping/rendering registry-driven. |
| Game registry pattern - admin finance | n/a | REFACTOR | unchanged | REFACTOR | n/a | n/a | NEW | UPDATE | green | Mines/BOXE/HI-LO registered; unknown = no replay. |
| Game registry pattern - replay routing | n/a | unchanged | unchanged | REFACTOR | REFACTOR | n/a | NEW | UPDATE | green | No BOXE fallback. |
| Backend summary dispatch | n/a | REFACTOR | unchanged | n/a | n/a | n/a | NEW | UPDATE | green | Builder registries replace `if game_code`. |
| Access-session auto-settle dispatch | n/a | REFACTOR | unchanged | n/a | n/a | n/a | NEW | UPDATE | green | Handler registry preserves per-game settlement logic. |

## 5. Residual Scope

This WP closes the narrow Rule 18 prerequisite for account/finance/replay
routing. It does not close the broader platform finance-retention workstream
tracked in `ACTIVE_OPEN_LOOPS.md` (`settlement taxonomy`, forward metadata,
retention policy and reconciliation reporting). That broader WP remains a CTO
scope item.

