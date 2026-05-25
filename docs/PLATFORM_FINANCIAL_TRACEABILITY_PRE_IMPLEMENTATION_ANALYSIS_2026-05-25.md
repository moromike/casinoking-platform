Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Financial Traceability - Pre-Implementation Analysis

## Verdict

Status: not green.

This is the highest business-risk platform theme in the current set. The
ledger foundation exists, but finance/replay/reporting still grows through
hardcoded branches and fallback behavior. That is not acceptable for future
games or real-money support.

Recommended implementation WP:

`WP-FINANCE-REPLAY-REGISTRY-RETENTION`

This WP should start only after `WP-ERROR-REQUEST-FOUNDATION-MVP` is approved,
or in parallel as doc/test scaffolding without touching settlement semantics.

## Scope Of This Analysis

This analysis closes pre-development discovery for finance traceability,
replay/reporting registry and retention. It does not authorize ledger rewrites,
financial auto-repair or historical backfill.

Read before implementation:

- `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_PLAN_2026-05-24.md`
- `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- `docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`
- this document

## Current Code Evidence

| Area | Current state | Evidence | Risk |
| --- | --- | --- | --- |
| Ledger tables | Ledger has transaction metadata JSON and double-entry entries. | `backend/migrations/sql/0002__financial_core_foundations.sql:44`, `backend/migrations/sql/0002__financial_core_foundations.sql:55` | Foundation exists, but metadata is not complete enough. |
| Round start metadata | Start ledger metadata includes game/title/site/wallet/grid/mines. | `backend/app/modules/platform/rounds/service.py:126`, `backend/app/modules/platform/rounds/service.py:146` | Still Mines-shaped (`grid_size`, `mine_count`) for all games. |
| Round settlement metadata | Win metadata only includes game code and safe reveal count. | `backend/app/modules/platform/rounds/service.py:379`, `backend/app/modules/platform/rounds/service.py:399` | Missing title/site/wallet/platform round/replay/settlement kind. |
| Ledger detail endpoint | Ledger detail returns transaction header and entries, not metadata JSON. | `backend/app/modules/ledger/service.py:48`, `backend/app/modules/ledger/service.py:108` | Support cannot see the explanation chain from ledger detail. |
| Admin finance events | Detail emits transaction id, round id, type, wallet, amounts and enrichment string. | `backend/app/modules/admin/service.py:890`, `backend/app/modules/admin/service.py:918` | No structured settlement/replay/anomaly fields. |
| Admin finance backend | Query/enrichment logic branches explicitly across Mines/BOXE/HI-LO. | `backend/app/modules/admin/service.py:1444`, `backend/app/modules/admin/service.py:1668`, `backend/app/modules/admin/service.py:2031` | Fourth game will require more branching unless registry lands. |
| Admin replay frontend | Admin finance imports BOXE and HI-LO replay viewers only. | `frontend/app/ui/admin-finance-panel.tsx:7`, `frontend/app/ui/admin-finance-panel.tsx:9` | Mines admin replay is not registered. |
| Admin replay availability | Replay button appears only for BOXE/HI-LO. | `frontend/app/ui/admin-finance-panel.tsx:540` | Mines finance replay gap remains. |
| Admin replay fallback | Non-HI-LO admin replay endpoint falls back to BOXE. | `frontend/app/ui/admin-finance-panel.tsx:614`, `frontend/app/ui/admin-finance-panel.tsx:618` | Unknown/new game opens wrong replay endpoint. |
| Admin replay renderer | Non-HI-LO replay renders BOXE viewer. | `frontend/app/ui/admin-finance-panel.tsx:621`, `frontend/app/ui/admin-finance-panel.tsx:625` | Wrong visual explanation for unknown/new game. |
| Player replay endpoint | Unknown/non-BOXE/non-HI-LO falls back to Mines. | `frontend/app/ui/player-account-page.tsx:1636`, `frontend/app/ui/player-account-page.tsx:1643` | Future games can silently use wrong replay. |
| Player history fanout | Player account loads histories through explicit game branches. | `frontend/app/ui/player-account-page.tsx:316`, `frontend/app/ui/player-account-page.tsx:350` | Registry contract is not enforced at the account layer. |
| Player replay viewer | Viewer renders BOXE, HI-LO, otherwise Mines. | `frontend/app/ui/player-account-page.tsx:717`, `frontend/app/ui/player-account-page.tsx:736` | Unknown game can render wrong viewer. |
| Player game labels | Missing/empty game falls back to Mines label. | `frontend/app/ui/player-game-registry.ts:27`, `frontend/app/ui/player-game-registry.ts:29` | Dirty data can look like Mines instead of "unknown game". |
| BOXE history mapping | BOXE player history forces `wallet_type: cash`. | `frontend/app/ui/player-account-page.tsx:1581`, `frontend/app/ui/player-account-page.tsx:1587` | Demo/real/wallet source can be mis-explained. |
| BOXE backend history | BOXE history does not expose wallet source strongly enough for player mapping. | `backend/app/modules/games/boxe/service.py:647`, `backend/app/modules/games/boxe/service.py:904` | Frontend is forced to guess. |
| Platform auto-settlement | Access-session timeout branches per game. | `backend/app/modules/platform/access_sessions/service.py:577`, `backend/app/modules/platform/access_sessions/service.py:586` | Settlement semantics are not descriptor-driven. |
| Auto cashout modes | Mines/BOXE/HI-LO each infer refund/cashout locally. | `backend/app/modules/platform/access_sessions/service.py:649`, `backend/app/modules/platform/access_sessions/service.py:723`, `backend/app/modules/platform/access_sessions/service.py:817` | Correct behavior exists, but reporting needs structured common taxonomy. |
| Game platform clients | BOXE/HI-LO squeeze game-specific data into Mines-shaped `grid_size`/`mine_count`. | `backend/app/modules/games/boxe/platform_client.py:63`, `backend/app/modules/games/hi_lo/platform_client.py:25` | Reporting inherits wrong conceptual names. |
| Admin force close | Admin void/force-close is effectively Mines-specific today. | `backend/app/modules/admin/session_force_close.py:180`, `backend/app/modules/admin/session_force_close.py:476` | Do not call it platform-wide until game semantics exist. |
| Mines admin replay endpoint | Backend admin replay exists. | `backend/app/api/routes/mines.py:801` | Frontend registry should wire it before claiming parity. |
| Table limits | Table default/max are hardcoded in service. | `backend/app/modules/platform/table_sessions/service.py:13`, `backend/app/modules/platform/table_sessions/service.py:36` | Settings/read-only inventory must classify them as high-risk. |
| Game code registry | Backend game codes are a tuple; frontend has separate registries. | `backend/app/modules/platform/game_codes.py:1`, `frontend/app/ui/player-game-registry.ts:1`, `frontend/app/ui/title-editor/engine-editor-registry.ts:35` | No single finance/replay/reporting descriptor. |

## Business Risk

This theme is not cosmetic. It controls how the platform explains money.

Failures here can cause:

- wrong replay shown to player/admin;
- real-money movement not explainable from one chain;
- future games missing replay/finance because no registry forces them;
- settlement mode hidden inside status strings;
- demo and real histories mixed conceptually;
- support unable to answer "why did this balance change?"

## Required Registry

Introduce a game finance/replay/reporting descriptor.

Minimum descriptor:

```text
game_code
display_name
player_replay_endpoint(round)
admin_replay_endpoint(round)
player_replay_viewer
admin_replay_viewer
account_summary_builder(row)
admin_finance_summary_builder(row)
settlement_explainer(row)
supported_wallet_modes
metadata_completeness
unknown_game_behavior
```

Unknown game behavior must be explicit:

- no fallback to Mines;
- no fallback to BOXE;
- show "Replay unavailable for game_code";
- log/report descriptor gap after logging foundation exists.

## Metadata Forward Contract

Do not rewrite history in this WP. Add forward-only metadata for new
transactions/rounds where safe.

Minimum future metadata fields:

| Field | Required on | Notes |
| --- | --- | --- |
| `game_code` | bet/win/void | Already present in some paths. |
| `title_code` | bet/win/void | Missing on settlement metadata. |
| `site_code` | bet/win/void | Missing on settlement metadata. |
| `wallet_type` | bet/win/void | Missing on settlement metadata. |
| `platform_round_id` | bet/win/void | Critical for chain navigation. |
| `game_round_id` | bet/win/void | May equal platform round today. |
| `access_session_id` | real-money game transactions | Needed for table/session reports. |
| `settlement_kind` | win/void/auto | `manual_cashout`, `auto_cashout`, `refund_no_progress`, etc. |
| `idempotency_key_hash` | all financial mutations | Do not expose raw client key unless already allowed. |
| `replay_ref` | terminal round | Endpoint/id reference, not full payload. |
| `metadata_schema_version` | all new metadata | Enables legacy/partial display. |

## Settlement Taxonomy

Use these values consistently:

| Settlement kind | Meaning |
| --- | --- |
| `manual_cashout` | Player explicitly cashes out. |
| `auto_cashout` | System cashes out because the game had meaningful progress. |
| `refund_no_progress` | Bet started but no meaningful progress happened. |
| `loss` | Round lost, no payout. |
| `admin_void` | Admin/operator forced closure/void. |
| `expired_no_settlement` | No balance movement needed. |
| `quarantined` | Financial state uncertain, no automatic repair. |

Each game defines meaningful progress:

- Mines: at least one safe reveal;
- BOXE: at least one safe pick;
- HI-LO: at least one correct prediction.

## Implementation Slices

### Slice F1 - Registry And Unknown-Game Guard

- frontend descriptor registry;
- player account replay uses registry;
- admin finance replay uses registry;
- account history fanout uses registry or explicit descriptor list;
- unknown game shows unavailable state, not fallback;
- contract test forbids fallback to another game.

### Slice F2 - Mines Admin Replay Parity

- wire Mines admin replay viewer into admin finance;
- verify backend Mines admin replay endpoint already exists;
- add admin finance test/screenshot.

### Slice F3 - Metadata Completeness Forward Contract

- update platform round settlement metadata for future transactions only;
- add `metadata_schema_version`;
- add/persist `settlement_kind` at least in ledger metadata, and decide if it
  also belongs in `platform_rounds`;
- expose metadata completeness in admin finance detail;
- do not mutate historical rows.

### Slice F4 - Retention MVP

- document replay retention policy;
- expose read-only status in Platform Settings later;
- no deletion job until legal/product approves.

### Slice F5 - Reconciliation Read-Only Report

Later:

- bet ledger without round;
- terminal round without expected settlement;
- replay missing for terminal real-money round;
- unknown game descriptor.

No auto-repair.

## Stop-and-Ask

Stop before code if:

- a fix would rewrite historical ledger metadata;
- a fix would move money outside ledger services;
- replay cannot be deterministic for a game;
- retention duration is legally/product sensitive;
- unknown game behavior is disputed;
- `settlement_kind` needs schema migration beyond metadata JSON;
- BOXE wallet source needs schema/API changes beyond an adapter;
- admin force-close/void is requested as a platform capability before game
  semantics are defined;
- demo/real wallet semantics are unclear for a game.

## Test Gates

Automated:

- registry contains Mines, BOXE and HI-LO;
- player account replay endpoint uses registry;
- admin finance replay endpoint uses registry;
- unknown game does not call Mines/BOXE/HI-LO replay;
- Mines admin replay is available in admin finance;
- ledger metadata forward path includes new required fields for one controlled flow;
- BOXE history exposes wallet source or the adapter marks it legacy/unknown, not
  silently cash;
- old/legacy rows display `metadata_completeness = legacy` or equivalent.

Manual:

- player account opens replay for Mines/BOXE/HI-LO;
- admin finance detail opens replay for Mines/BOXE/HI-LO;
- unknown game shows unavailable message;
- admin can understand settlement kind and amount chain.

## CTO Development Recommendation

Do not start by changing ledger schema broadly. Start with the descriptor
registry and fallback removal. That immediately prevents the worst future-game
failure and gives every subsequent finance/replay fix a platform home.

## Analysis Completeness

Closed for pre-development:

- replay fallback audit;
- admin/player finance registry gap;
- metadata gap;
- settlement taxonomy;
- retention policy gap;
- unknown-game behavior;
- implementation slices;
- gates and Stop-and-Ask.

No further analysis is required before writing the implementation prompt,
unless the CTO wants a legal retention number before any registry work starts.
