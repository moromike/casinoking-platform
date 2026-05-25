Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Error / Request Foundation MVP Brief

## Purpose

This brief narrows the error-code registry plan into the first implementable
work package.

The goal is not to solve all observability, logging, finance audit, settings,
or backoffice error-matrix problems at once. The goal is to create the platform
foundation that every later slice can safely inherit:

- a request identifier on every API request;
- a support id visible to the user when an error blocks them;
- a typed backend error registry for the first platform codes;
- central error handlers that stop leaking raw backend strings;
- frontend parsing that preserves code, support id, retryability, and details;
- game-runtime error UI that can show a useful but non-technical failure.

This is still a planning brief. Do not start code until CTO/product explicitly
approves this slice or narrows it further.

## Required Inputs

Read in this order before implementation:

1. `docs/README.md`
2. `docs/SOURCE_OF_TRUTH.md`
3. `docs/TASK_EXECUTION_GUARDRAILS.md`
4. `docs/AI_CRITICAL_JUDGMENT_RULES.md`
5. `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`
6. `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md`
7. `docs/PLATFORM_ERROR_CODE_REGISTRY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
8. `docs/PLATFORM_APPLICATION_LOGGING_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`

The logging current-state review is required only for request-id/log-correlation
constraints. It does not authorize the full logging WP.

## Current Evidence

The current codebase has pieces of an error pattern but no platform-level
contract.

| Area | Evidence | Problem |
| --- | --- | --- |
| Backend envelope | `backend/app/api/responses.py:11` | `error_response()` returns code/message/details but no support id, request id, retryability, severity, or registry metadata. |
| Backend route wiring | `backend/app/api/router.py:24` | Routes are grouped through one API router, so central handlers/middleware can be added without per-game wiring. |
| Backend auth/dependencies | `backend/app/api/dependencies.py:14`, `backend/app/api/dependencies.py:36`, `backend/app/api/dependencies.py:163` | Several auth/session failures are still ad hoc `HTTPException` paths or legacy code paths. |
| Backend raw exceptions | `backend/app/api/routes/cms_v2.py:20`, `backend/app/api/routes/cms_v2.py:60` | Newer routes still raise `HTTPException(detail=...)` with strings; this confirms the pattern will repeat without a foundation. |
| Frontend API error | `frontend/app/lib/api.ts:14`, `frontend/app/lib/api.ts:61`, `frontend/app/lib/api.ts:103`, `frontend/app/lib/api.ts:134` | `ApiRequestError` captures status/code/message but not support id, retryable, or structured details. |
| Game error dialog | `frontend/app/ui/game-runtime/game-action-error.tsx:5`, `frontend/app/ui/game-runtime/game-action-error.tsx:25` | The shared game dialog exists but cannot yet display a support id or standardized code. |
| Error copy adapter | `frontend/app/ui/game-runtime/game-error-copy-adapter.ts:21`, `frontend/app/ui/game-runtime/game-error-copy-adapter.ts:65` | Copy mapping exists but is local and partial; it must accept platform codes and legacy codes during migration. |
| Tests | `tests/contract/test_api_contract.py:13`, `tests/contract/test_demo_token_contract.py:52`, `tests/integration/test_boxe_api.py:72` | Tests assert legacy codes directly. A big-bang code rename would create high churn and false failures. |

## MVP Scope

### In Scope

1. Request id foundation:
   - accept inbound `X-Request-ID` if present and valid enough for logs;
   - generate one if absent;
   - return it as `X-Request-ID`;
   - expose it to error handlers as `request_id`.

2. Support id:
   - MVP support id equals request id;
   - every blocking API error response includes `support_id`;
   - user-facing dialogs may show compact copy such as `Codice: CK.AUTH.SESSION_EXPIRED` and `Supporto: <id>`.

3. Backend typed registry:
   - introduce a typed registry of platform error definitions;
   - include stable code, HTTP status, default message key/copy, retryable flag, log level, and safe details policy;
   - keep the registry in code for MVP, not database/backoffice.

4. Backend `AppError`:
   - add one domain exception class for intentional application failures;
   - route it through a central handler;
   - do not leak raw exception messages to players.

5. Central handlers:
   - `AppError`;
   - validation errors;
   - `HTTPException`;
   - unexpected exceptions.

6. Frontend API parsing:
   - extend `ApiRequestError` with `supportId`, `details`, `retryable`, and `requestId`;
   - extend shared API error types so TypeScript models support/request/retryable fields;
   - parse current legacy envelopes and new platform envelopes;
   - preserve `detail.error` when FastAPI/HTTPException wraps an existing error envelope.

7. Game runtime UI:
   - extend `GameActionError` to display code/support id in a compact way;
   - add equivalent compact diagnostic display to Mines custom error/recovery surfaces;
   - keep Mines/BOXE/HI-LO visual patterns stable;
   - no raw backend strings in player-facing game dialogs.

8. First migrated backend domains:
   - auth/session/token expiry;
   - game launch token missing/invalid;
   - wallet/table-balance insufficient funds;
   - idempotency conflict/key required if already surfaced by touched flows.

9. HI-LO proof:
   - after the platform path is stable, route HI-LO session-expired/unstable-connection failures through the new path;
   - do not use HI-LO as a one-off local fix.

### Out Of Scope

- Full migration of every backend route.
- Full logging implementation.
- Finance audit trail registry.
- Replay retention policy.
- Backoffice editable error matrix.
- Installation settings write UI.
- Database-backed error registry.
- Rewriting all legacy tests in one step.
- Removing legacy error-code compatibility from frontend adapters.
- New visual design for game error dialogs.

## CTO Correction To Existing Plan

The current error registry plan mentions validation handling, but the namespace
list is not explicit enough for validation codes. The MVP should add:

- `CK.VALIDATION.INVALID_REQUEST`
- optional future namespace `CK.VALIDATION.*`

This is a platform domain, not a game domain. Validation failures must not be
folded into `CK.SYSTEM.*` because they are client/request problems and need
different retry/copy semantics.

## Proposed Backend Shape

Prefer small modules under `backend/app/api/` because the first foundation is
an API transport contract, not yet a domain/business registry.

| Module | Responsibility |
| --- | --- |
| `backend/app/api/request_context.py` | Request-id generation, validation, context access helper. |
| `backend/app/api/errors.py` | `ErrorCode`, `ErrorDefinition`, registry, `AppError`, handler helpers. |
| `backend/app/api/responses.py` | Preserve current envelope helper, extend with `support_id`, `request_id`, `retryable`, optional safe `details`. |
| `backend/app/main.py` | Install middleware and exception handlers in app creation. |

If implementation discovers an existing better home, use it, but keep the
foundation in API/platform code, not inside any game module.

## Initial Error Code Set

Use a deliberately small registry. Add only codes that are exercised by tests
or by the first migrated paths.

| Code | HTTP | Retryable | Notes |
| --- | ---: | --- | --- |
| `CK.AUTH.UNAUTHORIZED` | 401 | yes | Generic unauthenticated request. |
| `CK.AUTH.INVALID_TOKEN` | 401 | yes | Invalid bearer/demo/launch token where token refresh may help. |
| `CK.AUTH.SESSION_EXPIRED` | 401 | yes | Expired cached session/token. |
| `CK.AUTH.FORBIDDEN` | 403 | no | Authenticated but not allowed. |
| `CK.VALIDATION.INVALID_REQUEST` | 422 | no | FastAPI/Pydantic validation. |
| `CK.WALLET.INSUFFICIENT_BALANCE` | 402 or 409 | no | Use existing HTTP semantics if already contracted by tests. |
| `CK.LEDGER.IDEMPOTENCY_KEY_REQUIRED` | 400 | no | Only if touched in the slice. |
| `CK.LEDGER.IDEMPOTENCY_CONFLICT` | 409 | no | Only if touched in the slice. |
| `CK.GAME.LAUNCH_TOKEN_REQUIRED` | 401 | yes | Missing launch token for protected game launch. |
| `CK.GAME.LAUNCH_TOKEN_INVALID` | 401 | yes | Invalid/expired launch token. |
| `CK.GAME.ROUND_CLOSED` | 409 | no | Only if a touched game action needs it. |
| `CK.SYSTEM.SERVICE_UNAVAILABLE` | 503 | yes | Temporary dependency/backend outage. |
| `CK.SYSTEM.INTERNAL_ERROR` | 500 | yes | Unexpected exception, generic user copy only. |

Do not invent broad final taxonomy in this WP. Add a code only when a concrete
path needs it.

## Envelope Contract

Target error envelope:

```json
{
  "success": false,
  "error": {
    "code": "CK.AUTH.SESSION_EXPIRED",
    "message": "Sessione scaduta, ricarica.",
    "support_id": "req_...",
    "request_id": "req_...",
    "retryable": true,
    "details": {}
  }
}
```

Compatibility requirement:

- existing legacy shape must remain parseable;
- migrated endpoints may emit `CK.*` codes;
- non-migrated endpoints may still emit legacy short codes during the transition;
- frontend copy adapters must understand both.

## HTTPException Handler Rules

The `HTTPException` handler must avoid double-wrapping.

1. If `exc.detail` already looks like `{"success": false, "error": {...}}`,
   normalize it by adding missing `support_id` and `request_id`, not by nesting
   another `error`.
2. If `exc.detail` is a string, map by status code to a safe platform code and
   user-facing message.
3. If `exc.detail` is a dict but not an error envelope, treat only whitelisted
   fields as safe details.
4. Never echo arbitrary backend exception text to player-facing responses.

## Frontend Contract

`frontend/app/lib/api.ts` should become the single transport parser for new and
legacy envelopes.

`ApiRequestError` should expose:

- `status`;
- `code`;
- `message`;
- `supportId`;
- `requestId`;
- `retryable`;
- `details`;
- raw response only if already present today and safe for tests.

`GameErrorCopyAdapter` should map:

- new platform codes;
- current legacy codes;
- unknown code fallback to safe user copy.

MVP UI rule:

- user sees a friendly message;
- code/support id are visible enough for support;
- details stay out of the UI unless explicitly product-approved.

## Migration Strategy

Do not do a big-bang migration.

### Step A - Request Id And Envelope Compatibility

- Add middleware/header propagation.
- Extend `error_response()` with optional support/request fields.
- Add tests that do not require all routes to use `CK.*` yet.

### Step B - Registry And Central Handlers

- Add typed registry and `AppError`.
- Install handlers.
- Verify validation, HTTPException, and unexpected exception behavior.

### Step C - Frontend Parsing And Game Dialog

- Extend `ApiRequestError`.
- Extend `GameActionError`.
- Keep existing visual look stable.
- Add adapter tests for legacy and `CK.*`.

### Step D1 - First Domain Migration: Auth / Session / Launch

- Migrate auth/session/game-launch paths first.
- Prove `CK.AUTH.*` and `CK.GAME.LAUNCH_*`.
- Update tests for those paths only.
- Keep wallet/table-balance/idempotency untouched in this sub-slice.
- Keep legacy tests for untouched paths.

### Step D2 - First Domain Migration: Wallet / Idempotency

- Migrate insufficient balance and idempotency only after D1 is green.
- Do not change HTTP status semantics silently.
- Decide explicitly whether insufficient balance/table limit remains `422` for
  compatibility or moves to `402`/`409`.

### Step E - UI Diagnostic Parity

- Shared `GameActionError` gets compact diagnostic line.
- Mines custom error/recovery UI gets equivalent compact diagnostic line.
- Existing visual patterns remain stable.

### Step F - HI-LO Proof

- Route the observed session-expired/unstable-action dialog through the shared
  path.
- Confirm retry/return-to-site behavior remains product-safe.

## Test And Gate Plan

Minimum automated gates:

- backend request id generated when absent;
- backend request id preserved when valid `X-Request-ID` is supplied;
- error response includes `support_id` and `request_id`;
- validation error maps to `CK.VALIDATION.INVALID_REQUEST`;
- `AppError` maps to registry metadata;
- `HTTPException(detail=existing_error_envelope)` is normalized, not nested;
- `HTTPException(detail="raw string")` does not leak raw technical text;
- unexpected exception maps to `CK.SYSTEM.INTERNAL_ERROR`;
- `ApiRequestError` parses new envelope fields;
- `ApiRequestError` still parses legacy envelopes;
- `GameActionError` renders code/support id without visual breakage;
- Mines custom error/recovery surfaces render code/support id without visual drift;
- migrated auth/session/launch/wallet paths return expected `CK.*` code;
- non-migrated legacy routes still pass their current tests.

Manual gates:

- one player-facing game error screenshot before/after;
- verify message is understandable and contains support id;
- verify no backend raw string is visible;
- verify Mines, BOXE, and HI-LO still render their existing game error dialog
  style.

Standard gates:

- backend focused tests for touched routes;
- frontend build;
- relevant smoke tests for HI-LO and at least one existing game path;
- static frontend boundary test if the usual timeout recurs.

## File Ownership

Expected files:

- `backend/app/api/responses.py`
- `backend/app/api/request_context.py` (new)
- `backend/app/api/errors.py` (new)
- `backend/app/main.py`
- selected backend dependencies/routes for first migrated paths
- `frontend/app/lib/api.ts`
- `frontend/app/lib/types.ts`
- `frontend/app/lib/helpers.ts`
- `frontend/app/ui/game-runtime/game-action-error.tsx`
- `frontend/app/ui/game-runtime/game-error-copy-adapter.ts`
- Mines custom error/recovery UI if needed for diagnostic parity
- focused contract/integration tests

Avoid:

- game math;
- wallet ledger business rules except error wrapping;
- replay logic;
- backoffice settings UI;
- unrelated copy/visual redesign.

## Stop And Ask

Stop before coding further if:

- a migrated path requires changing settlement, wallet, or table-session
  semantics;
- support id must differ from request id for product/legal reasons;
- more than two backend domains become necessary to touch;
- central handlers break legacy test expectations outside the chosen slice;
- player UI needs a new visual pattern rather than a small shared extension;
- a route currently returns sensitive details and no safe mapping is obvious;
- legacy code compatibility would need to be removed.

## Effort Estimate

| Slice | Estimate |
| --- | ---: |
| Request-id middleware and envelope compatibility | 2-4 prompts |
| Registry, `AppError`, and central handlers | 4-6 prompts |
| Frontend parser and game dialog extension | 2-4 prompts |
| First domain migration and tests | 3-5 prompts |
| HI-LO proof and manual evidence | 1-2 prompts |

Expected total: 12-21 prompts depending on how many legacy tests need careful
compatibility updates.

## CTO Recommendation

Approve this as the next implementation slice only if the team accepts the
incremental migration rule:

1. first add request/support id safely;
2. then add registry/handlers;
3. then migrate a few high-value paths;
4. keep legacy parsing alive until route migration is deliberately completed.

This is the smallest useful foundation that reduces the user-facing error bug
without starting the full logging/settings/finance platform program.
