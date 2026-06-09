Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Error Code Registry - Current-State CTO Review

Reviewed plan: `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`

This review is per-plan only. It is not a cross-plan review and it does not
authorize implementation.

## CTO Verdict

Status: not green, but it is the right first foundation.

CasinoKing has a partial error envelope and a frontend `ApiRequestError`, but
there is no stable `CK.*` registry, no `support_id`, no request id, no central
`AppError`, no normalized `HTTPException` handling and no consistent player UI
display of error codes.

The plan remains approved as the first implementation foundation after this
audit, but the migration must be incremental.

## Findings

| # | Finding | Current state | Gap | Risk | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Backend envelope is partial | `error_response()` emits `success`, `error.code`, `error.message` and optional `details`. | Target envelope needs support id, retryability and registry-backed code semantics. | High: errors are readable but not operationally traceable. | `backend/app/api/responses.py:11` |
| 2 | No request/support id | App setup has no request id middleware and response errors have no support id. | MVP requires `support_id = request_id`. | High: support cannot link UI error to backend logs. | `backend/app/main.py:31`, `backend/app/api/responses.py:18` |
| 3 | `HTTPException` breaks the envelope | Some dependencies put an envelope inside `detail`; CMS v2 returns plain detail strings. | Target requires central handler normalizing `HTTPException`. | Medium-high: frontend loses actual error semantics. | `backend/app/api/dependencies.py:163`, `backend/app/api/routes/cms_v2.py:20` |
| 4 | Frontend collapses `detail` to validation | `api.ts` maps any payload with `detail` to `VALIDATION_ERROR`. | It must preserve `detail.error.code` when present. | Medium-high: `FORBIDDEN` or CMS 404 becomes misleading. | `frontend/app/lib/api.ts:59`, `frontend/app/lib/api.ts:101` |
| 5 | Legacy codes are widespread | Route code uses short codes such as `UNAUTHORIZED`, `FORBIDDEN`, `INSUFFICIENT_BALANCE`, `GAME_STATE_CONFLICT`, `IDEMPOTENCY_CONFLICT`. | New errors should be `CK.*`; old codes need compatibility. | Medium: migration can break tests and classifiers if done in one pass. | `backend/app/api/dependencies.py:16`, `backend/app/api/routes/admin.py:846`, `backend/app/api/routes/mines.py:115`, `backend/app/api/routes/hi_lo.py:308` |
| 6 | Game services have local mini error classes | BOXE/HI-LO carry status/code/message locally. | They should map to registry-backed `AppError` or adapters. | Medium: game-specific codes drift independently. | `backend/app/modules/games/boxe/service.py:80`, `backend/app/modules/games/hi_lo/service.py:71` |
| 7 | `ApiRequestError` lacks support fields | It stores only `code` and `status`. | Needs `supportId`, `details`, `retryable`. | Medium: UI cannot render compact diagnostic line. | `frontend/app/lib/api.ts:14` |
| 8 | Game error overlay hides code | `GameActionError` renders title/message only. | Player-facing errors must show compact code/support id line. | Medium: product sees a friendly message but support sees no diagnostic id. | `frontend/app/ui/game-runtime/game-action-error.tsx:5`, `frontend/app/ui/game-runtime/game-action-error.tsx:44` |
| 9 | Copy adapter discards codes | `buildGameErrorMessage()` classifies and replaces backend details with copy, but returns only a string. | Adapter should preserve code/support id separately from localized message. | Medium: better UX currently costs observability. | `frontend/app/ui/game-runtime/game-error-copy-adapter.ts:21` |
| 10 | Admin UI usually shows fallback + message | `readErrorMessage()` concatenates fallback and backend message without code/support id. | Admin/support surfaces need details view. | Medium: admin errors remain difficult to triage. | `frontend/app/lib/api.ts:134`, `frontend/app/ui/casinoking-console.tsx:1854` |

## Legacy Codes Observed

Examples found during audit:

`VALIDATION_ERROR`, `RESOURCE_NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`,
`CONFLICT`, `INSUFFICIENT_BALANCE`, `IDEMPOTENCY_CONFLICT`,
`IDEMPOTENCY_KEY_REQUIRED`, `GAME_STATE_CONFLICT`,
`SESSION_VOIDED_BY_OPERATOR`, `GAME_LAUNCH_TOKEN_REQUIRED`,
`GAME_LAUNCH_TOKEN_INVALID`, `TABLE_LIMIT_EXCEEDED`,
`TABLE_SESSION_EXPIRED`, `BONUS_WALLET_EMPTY`, `ROUND_ALREADY_CLOSED`,
`ACTION_NOT_ALLOWED`, `CASHOUT_NOT_ALLOWED`, `ROUND_NOT_FOUND`,
`SESSION_NOT_FOUND`, `ROUND_ALREADY_ACTIVE`, `TITLE_NOT_PUBLISHED`,
`LAUNCH_REJECTED_MASTER`, `CONFIG_MISSING`, `BAD_CONFIG`, `INVALID_ROW`,
`INVALID_POSITION`, `INVALID_WALLET_SOURCE`, `INVALID_BET`,
`RATE_LIMITED`, `TITLE_ARCHIVE_BLOCKED`.

## CTO Corrections To Carry Forward

- Keep old-code compatibility during migration.
- Do not migrate every route in one pass.
- `HTTPException` handling is part of the MVP, not a later polish.
- UI must show code/support id compactly, not as a dominant scary block.
- Backend technical detail must not become player copy.

## Approved Next WP

`WP-ERROR-REQUEST-FOUNDATION-MVP`

Scope:

- typed backend registry;
- `AppError`;
- request id middleware;
- `support_id = request_id` in error envelope;
- handlers for `AppError`, validation, `HTTPException` and unexpected errors;
- frontend `ApiRequestError` with `supportId`, `details`, `retryable`;
- `GameActionError` compact code/support line;
- migrate auth/session/game launch and wallet/table balance first;
- use HI-LO action errors as the first game proof after platform path passes.

## Stop Before Code

Stop if implementation proposes:

- full route migration in one wave;
- DB-backed editable error registry;
- hiding codes from players;
- removing short-code compatibility immediately;
- exposing stack traces, SQL errors or raw backend details in player UI.

