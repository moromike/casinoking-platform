Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Financial Audit Traceability - Current-State CTO Review

Reviewed plan: `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_PLAN_2026-05-24.md`

This review is per-plan only. It is not a cross-plan review and it does not
authorize implementation.

## CTO Verdict

Status: not green.

The accounting foundation exists: real-money rounds are linked to
`platform_rounds` and ledger transactions. However, finance/replay/reporting is
still implemented through explicit game branches and fallback behavior instead
of a game descriptor registry.

This is the highest business-risk plan because it explains real-money movement.
The next step must be an autonomous finance/replay registry WP, not a generic
logging or settings WP.

## Current-State Matrix

| Area | Mines | BOXE | HI-LO | Verdict |
| --- | --- | --- | --- | --- |
| Player account summary | Present | Present | Present | Partial: hardcoded branches, no registry. |
| Player replay | Present | Present | Present | Partial: unknown game can fall back incorrectly. |
| Admin finance detail | Partial | Present | Present | Partial: too little ledger metadata/settlement detail. |
| Admin replay frontend | Missing | Present | Present | Gap: backend Mines admin replay exists but UI does not register it. |
| Backend admin replay | Present | Present | Present | Partial: endpoint identity differs by game. |
| Ledger metadata | Partial | Partial | Partial | Gap: missing stable `settlement_kind`, `platform_round_id`, `replay_ref`. |
| Access/table session link | Present real | Present real | Present real | Partial: demo/real explanation not uniform. |
| Auto settlement | Present | Present | Present | Partial: hardcoded per game; refund semantics not explicit. |
| Retention policy | Not found | Not found | Not found | Gap: pagination exists, retention policy does not. |

## Findings

| # | Finding | Current state | Gap | Risk | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Replay fallback is unsafe | Admin finance supports replay for BOXE/HI-LO and falls back to BOXE for non-HI-LO. Player account branches and falls back to Mines. | Contract requires registry and no implicit fallback. | High: new or dirty `game_code` can open the wrong replay. | `frontend/app/ui/admin-finance-panel.tsx:540`, `frontend/app/ui/admin-finance-panel.tsx:614`, `frontend/app/ui/player-account-page.tsx:716`, `frontend/app/ui/player-account-page.tsx:1636` |
| 2 | Mines admin replay is not wired in finance UI | Backend exposes Mines admin replay, but admin finance imports/types only BOXE and HI-LO replay viewers. | Mines must be registered in admin finance. | High: Surface finance/replay is inconsistent across games. | `backend/app/api/routes/mines.py:801`, `backend/app/modules/games/mines/service.py:630`, `frontend/app/ui/admin-finance-panel.tsx:7`, `frontend/app/ui/admin-finance-panel.tsx:76` |
| 3 | Ledger metadata is incomplete | Start metadata includes game/title/site/wallet; settlement metadata is much thinner. Ledger detail does not expose metadata JSON. | Plan requires route from ledger to round/session/replay/settlement reason. | High: audit chain is not self-explanatory. | `backend/app/modules/platform/rounds/service.py:146`, `backend/app/modules/platform/rounds/service.py:399`, `backend/app/modules/ledger/service.py:59`, `backend/app/modules/ledger/service.py:142` |
| 4 | Game-specific metadata is squeezed into Mines-shaped fields | BOXE and HI-LO pass non-Mines meanings through generic `grid_size`/`mine_count` style fields. | Descriptor should expose game-specific config semantically. | Medium: finance explanation inherits wrong conceptual names. | `backend/app/modules/games/boxe/platform_client.py:85`, `backend/app/modules/games/hi_lo/platform_client.py:80` |
| 5 | Demo vs real is not uniform | Mines and HI-LO expose demo state more clearly; BOXE schema lacks persisted wallet/demo source and player account forces `cash`. | Plan requires demo/real separation in descriptor/reporting. | Medium-high: history/reporting can confuse demo and real explanation. | `backend/app/modules/games/mines/service.py:733`, `backend/app/modules/games/hi_lo/service.py:190`, `backend/migrations/sql/0039__boxe_session_tables.sql:11`, `frontend/app/ui/player-account-page.tsx:1587` |
| 6 | Settlement taxonomy is not explicit in data | Auto-settlement is game-branch logic. Refund/no-progress can be represented as win/cashout style completion. | Plan requires `manual_cashout`, `auto_cashout`, `refund_no_progress`, `admin_void`, etc. | High: financial explanation can be technically true but semantically unclear. | `backend/app/modules/platform/access_sessions/service.py:586`, `backend/app/modules/platform/access_sessions/service.py:679`, `backend/app/modules/platform/access_sessions/service.py:753`, `backend/app/modules/platform/access_sessions/service.py:850` |
| 7 | Admin finance detail is too thin | Detail exposes transaction id, round id, amounts and enrichment string, but not full ledger entries, metadata, replay ref, structured settlement or anomaly flags. | Plan requires drilldown chain, not just summary rows. | High for support/audit. | `backend/app/modules/admin/service.py:918` |

## CTO Corrections To Carry Forward

- Finance/replay registry is required before the next game.
- Unknown game must mean "replay unavailable", never fallback to Mines/BOXE.
- Metadata enrichment is forward-only; do not rewrite old ledger rows casually.
- Retention policy is not pagination.
- Settlement semantics must be structured, not inferred from status strings.

## Approved Next WP

`WP-FINANCE-REPLAY-REGISTRY-MVP`

Scope:

- descriptor registry for Mines, BOXE and HI-LO;
- remove fallback replay behavior;
- wire Mines admin replay into admin finance;
- forward-only metadata completeness brief;
- retention MVP documented;
- contract test preventing a fourth hardcoded branch;
- no automatic reconciliation/repair.

## Stop Before Code

Stop if implementation needs decisions on:

- BOXE demo persistence and wallet/demo source;
- canonical field for `settlement_kind`;
- whether `admin_void` is Mines-only or a platform game capability;
- replay retention duration with legal/product implications;
- rewriting historical ledger metadata.

