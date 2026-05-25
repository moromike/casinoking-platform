Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Error Registry - Pre-Implementation Analysis

## Verdict

Status: not green, but this is the first platform foundation to implement.

The system has a partial error envelope and game-facing error dialogs, but it
does not have a platform error contract. The highest-value next step is still:

`WP-ERROR-REQUEST-FOUNDATION-MVP`

The brief `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md`
is valid as the implementation starting point, with one correction already
included: add explicit `CK.VALIDATION.*` namespace.

## Scope Of This Analysis

This analysis closes pre-development discovery for the error registry and
request/support-id foundation. It does not authorize a full route migration.

Read before implementation:

- `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`
- `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_ERROR_CODE_REGISTRY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md`
- this document

## Current Code Evidence

| Area | Current state | Evidence | Risk |
| --- | --- | --- | --- |
| Backend envelope | Helper emits `success=false`, `error.code`, `error.message`, optional `details`. | `backend/app/api/responses.py:11`, `backend/app/api/responses.py:18` | No support id, retryability, request id, registry metadata. |
| Auth dependency | Auth errors return local legacy codes and raw-ish messages. | `backend/app/api/dependencies.py:13`, `backend/app/api/dependencies.py:35`, `backend/app/api/dependencies.py:65` | Session/token failures cannot be traced or consistently copied. |
| Admin area guard | Some forbidden errors are raised as `HTTPException` with envelope nested in `detail`. | `backend/app/api/dependencies.py:163`, `backend/app/api/dependencies.py:178` | Frontend parser currently collapses `detail` to validation. |
| CMS v2 | New route raises plain string `HTTPException`. | `backend/app/api/routes/cms_v2.py:20`, `backend/app/api/routes/cms_v2.py:26`, `backend/app/api/routes/cms_v2.py:60` | Confirms future drift will continue without central handlers. |
| Game route mappings | BOXE and HI-LO have route-local `_map_exception()` functions. | `backend/app/api/routes/boxe.py:276`, `backend/app/api/routes/hi_lo.py:304` | Game error semantics drift independently. |
| Local game codes | BOXE/HI-LO services raise local API error classes with short codes. | `backend/app/modules/games/boxe/service.py:61`, `backend/app/modules/games/hi_lo/service.py:71` | No `CK.BOXE.*` / `CK.HILO.*` registry contract. |
| Frontend API parser | `ApiRequestError` stores only message/code/status. | `frontend/app/lib/api.ts:14`, `frontend/app/lib/api.ts:18` | UI cannot show support id or retryable state. |
| Frontend type shape | API error types do not model support/request/retryable fields. | `frontend/app/lib/types.ts:25`, `frontend/app/lib/types.ts:32` | Runtime parser and TS contract can drift. |
| Frontend helpers | Validation/detail helper can turn raw detail strings into user messages. | `frontend/app/lib/helpers.ts:187`, `frontend/app/lib/helpers.ts:212` | Safe-copy policy must cover helper behavior, not only `api.ts`. |
| Frontend `detail` handling | Any payload with `detail` becomes `VALIDATION_ERROR`. | `frontend/app/lib/api.ts:59`, `frontend/app/lib/api.ts:101` | Nested error envelopes lose their real code. |
| Game error UI | Dialog renders title/message/actions only. | `frontend/app/ui/game-runtime/game-action-error.tsx:5`, `frontend/app/ui/game-runtime/game-action-error.tsx:44` | Player sees message but support has no code/id. |
| Copy adapter | Classifies legacy codes and returns only localized string. | `frontend/app/ui/game-runtime/game-error-copy-adapter.ts:21`, `frontend/app/ui/game-runtime/game-error-copy-adapter.ts:55` | Better UX discards operational diagnostics. |
| Mines UI | Mines has custom error/recovery behavior and does not simply consume `GameActionError`. | `frontend/app/ui/mines/mines-standalone.tsx:1371`, `frontend/app/ui/mines/mines-standalone.tsx:1813` | A BOXE/HI-LO-only diagnostic line would leave the reference game behind. |
| Test surface | Many tests assert legacy short codes. | `tests/integration/test_boxe_api.py:72`, `tests/integration/test_financial_and_mines_flows.py:1121`, `tests/contract/test_api_contract.py:70` | Big-bang rename would create noisy failures. |

## Core Problem

The current pattern mixes three responsibilities:

1. domain semantics (`round closed`, `insufficient balance`, `invalid token`);
2. transport shape (`HTTPException`, JSON envelope, FastAPI validation);
3. user copy (`Sessione scaduta`, `Connessione instabile`, etc.).

The implementation must separate them:

```text
Exception / domain failure
  -> AppError(code, status, safe details)
  -> API envelope with support_id/request_id
  -> ApiRequestError preserving fields
  -> localized UI copy + visible diagnostic line
```

## MVP Backend Registry

Start with these codes only:

| Code | HTTP | Retryable | Source paths to migrate first |
| --- | ---: | --- | --- |
| `CK.AUTH.UNAUTHORIZED` | 401 | yes | `backend/app/api/dependencies.py:13` |
| `CK.AUTH.INVALID_TOKEN` | 401 | yes | `backend/app/api/dependencies.py:35` |
| `CK.AUTH.SESSION_EXPIRED` | 401 | yes | cached token / game launch paths |
| `CK.AUTH.FORBIDDEN` | 403 | no | `backend/app/api/dependencies.py:65`, `backend/app/api/dependencies.py:163` |
| `CK.VALIDATION.INVALID_REQUEST` | 422 | no | FastAPI validation, explicit invalid payloads |
| `CK.WALLET.INSUFFICIENT_BALANCE` | 422 or 402 | no | wallet/table balance/game start |
| `CK.LEDGER.IDEMPOTENCY_KEY_REQUIRED` | 422 | no | BOXE/HI-LO/Mines start/action headers |
| `CK.LEDGER.IDEMPOTENCY_CONFLICT` | 409 | no | game/platform idempotency conflicts |
| `CK.GAME.LAUNCH_TOKEN_REQUIRED` | 401 | yes | game launch token dependency |
| `CK.GAME.LAUNCH_TOKEN_INVALID` | 401 | yes | game launch token dependency |
| `CK.GAME.ROUND_CLOSED` | 409 | no | selected game action proof |
| `CK.SYSTEM.INTERNAL_ERROR` | 500 | yes | unexpected exception handler |
| `CK.SYSTEM.SERVICE_UNAVAILABLE` | 503 | yes | infrastructure/downstream outage |

Legacy short codes must remain parseable.

## MVP Backend Modules

Recommended shape:

| Module | Purpose |
| --- | --- |
| `backend/app/api/request_context.py` | request id context and helpers |
| `backend/app/api/errors.py` | registry, `AppError`, definition lookup |
| `backend/app/api/responses.py` | target envelope shape |
| `backend/app/main.py` | middleware and exception handlers |

The registry should stay code-backed in MVP. Do not create an editable DB error
matrix yet.

## Central Handler Requirements

Handlers must cover:

- `AppError`;
- FastAPI/Pydantic validation;
- `HTTPException`;
- unexpected exceptions.

Special rule for `HTTPException`:

- if `detail` already contains an error envelope, normalize it and add
  support/request id;
- if `detail` is a string, map by status to safe platform code;
- never expose raw SQL, stack traces, path names or framework internals.

## Frontend Requirements

`ApiRequestError` must carry:

- `status`;
- `code`;
- `message`;
- `supportId`;
- `requestId`;
- `retryable`;
- `details`.

`GameActionError` must display:

- friendly localized message;
- compact diagnostic line;
- retry/dismiss/return actions as today.

The UI must not become visually scarier. The code/support id is a support aid,
not the headline.

## Migration Plan

### Step E1 - Transport Compatibility

- request id middleware;
- envelope supports support/request id;
- frontend parser accepts both old and new shape;
- no code rename yet except tests for the new fields.

### Step E2 - Registry And Handlers

- code-backed registry;
- `AppError`;
- central handlers;
- validation and unexpected errors covered.

### Step E3 - First Domain Migration D1

Migrate only:

- auth/session;
- game launch;

This step proves `CK.AUTH.*` and `CK.GAME.LAUNCH_*` without touching wallet or
settlement semantics.

### Step E4 - First Domain Migration D2

Migrate only after D1 is green:

- insufficient balance;
- idempotency;
- table limit / table balance if the HTTP status is agreed.

Open point for D2: decide whether insufficient balance/table limit remains 422
for compatibility or moves to 402/409. Do not change HTTP status silently.

### Step E5 - UI Diagnostic Line

- extend shared game error dialog;
- add compatible diagnostic display to Mines custom dialogs/recovery surfaces;
- update copy adapters to return message plus diagnostic data, not string only;
- keep legacy classifiers.

### Step E6 - Game Proof

Use HI-LO action/session errors as proof after the platform path is stable. Do
not do a local HI-LO-only workaround.

### Step E7 - Route-By-Route Backlog

After MVP, each route/domain gets its own migration. Do not sneak full
migration into the foundation WP.

## Stop-and-Ask

Stop before code if:

- product wants to hide codes from players;
- a code's semantic meaning is unclear;
- support id must be separate from request id in MVP;
- a migration touches wallet/ledger semantics instead of just error wrapping;
- tests require changing many unrelated routes;
- someone proposes deleting legacy-code compatibility.
- Mines requires a new visual error pattern instead of a compact diagnostic line
  inside its existing pattern.

## Test Gates

Automated:

- request id generated/preserved;
- `support_id` appears in every backend error response;
- `AppError` returns registered code/status/retryable;
- validation returns `CK.VALIDATION.INVALID_REQUEST`;
- `HTTPException(detail=existing envelope)` is not double-wrapped;
- raw `HTTPException(detail='...')` maps to safe code/copy;
- unexpected exception returns `CK.SYSTEM.INTERNAL_ERROR`;
- frontend parses legacy envelope;
- frontend parses new envelope fields;
- game dialog renders compact code/support id;
- Mines error/recovery UI renders code/support id without visual drift;
- selected migrated routes return `CK.*`;
- untouched routes still pass legacy tests.

Manual:

- trigger one HI-LO session-expired/unstable action error;
- verify friendly message + diagnostic line;
- verify no backend raw detail appears;
- verify Mines/BOXE dialog visual style does not regress.

## CTO Development Recommendation

Proceed with `WP-ERROR-REQUEST-FOUNDATION-MVP` first. It is narrow enough to
start, but it must be implemented as compatibility-first, not a global rename.

## Analysis Completeness

Closed for pre-development:

- envelope gap;
- request/support id gap;
- handler gap;
- frontend parser gap;
- game dialog gap;
- legacy code/test risk;
- MVP code namespace;
- migration order;
- gates and Stop-and-Ask.

No further analysis is required before the implementation prompt unless the CTO
rejects `support_id = request_id` or the product decides player-facing codes
must be hidden.
