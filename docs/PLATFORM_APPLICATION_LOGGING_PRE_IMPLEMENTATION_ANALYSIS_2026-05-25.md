Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Application Logging - Pre-Implementation Analysis

## Verdict

Status: not green.

This is now analyzed enough to implement, but it must not be the first coding
slice. Logging depends on request id, support id, redaction and stable error
codes. Without those foundations, "structured logging" would only make current
uncorrelated errors prettier.

Recommended implementation order:

1. `WP-ERROR-REQUEST-FOUNDATION-MVP`
2. `WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP`
3. logging status rows in read-only Platform Settings
4. production log sink / retention after MVP behavior is stable

## Scope Of This Analysis

This analysis closes the pre-development audit for application logging. No
additional discovery should be required before writing the first implementation
prompt, unless the CTO changes the target architecture.

Read before implementation:

- `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md`
- `docs/PLATFORM_APPLICATION_LOGGING_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_APPLICATION_LOGGING_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md`
- this document

## Current Code Evidence

| Area | Current state | Evidence | Risk |
| --- | --- | --- | --- |
| App setup | FastAPI app installs CORS, router and static mounts only. No request context middleware. | `backend/app/main.py:31`, `backend/app/main.py:39`, `backend/app/main.py:46` | No request can be correlated across response, support, backend logs. |
| Background job logging | Access-session sweeper logs one free-text exception. | `backend/app/main.py:63`, `backend/app/main.py:68` | Timeout/settlement failures touch money but are not searchable by stable event name. |
| Logger usage | Only isolated Python logging exists. | `backend/app/main.py:5`, `backend/app/main.py:16`, `backend/app/modules/games/boxe/state_machine.py:5`, `backend/app/modules/games/boxe/state_machine.py:201` | Logging pattern is local and easy to duplicate inconsistently. |
| Error envelope | `error_response()` has code/message/details only. | `backend/app/api/responses.py:11`, `backend/app/api/responses.py:18` | Cannot attach support id or request id to failures. |
| Global handlers | No central handlers visible in `create_app()`. | `backend/app/main.py:31` to `backend/app/main.py:60` | Validation/HTTP/unexpected exceptions can drift in shape. |
| Raw HTTP errors | New CMS v2 route raises plain strings. | `backend/app/api/routes/cms_v2.py:20`, `backend/app/api/routes/cms_v2.py:26`, `backend/app/api/routes/cms_v2.py:60` | Raw details can reach clients and logs before normalization. |
| Sensitive config | Secrets and seeds live in settings. | `backend/app/core/config.py:21`, `backend/app/core/config.py:31`, `backend/app/core/config.py:35` | Any broad logging before redaction risks leaking secrets. |
| Uvicorn/Docker logs | Docker launches backend without explicit JSON/access log policy. | `infra/docker/docker-compose.yml:9` | Runtime logs are not yet production-structured. |
| CMS v2 lab console | Lab frontend can log raw caught errors. | `frontend-v2/app/page.tsx:85` | Browser-side raw errors can leak context if copied into future telemetry. |
| Admin token query | Admin shell passes token to CMS v2 lab via query string. | `frontend/app/ui/admin-shell-panel.tsx:81` | URL/query logging must be treated as sensitive. |
| Access logs | Existing access log module is login/audit-ish DB logging, not app logging. | `backend/app/modules/platform/access_logs.py:4`, `backend/app/modules/platform/access_logs.py:23` | Do not mistake it for request correlation; failures can be silent. |
| Local token storage | Game runtime tokens live in localStorage. | `frontend/app/ui/game-runtime/game-storage.ts:23` | Frontend telemetry must never dump storage contents. |
| Reset token | Auth can return reset token in non-production. | `backend/app/modules/auth/service.py:426` | Redaction must include reset-token style fields. |
| Frontend console | Frontend uses console mostly in scripts/tests, not a telemetry/logging layer. | `frontend/scripts/lint-mines-i18n.js:147`, `frontend/scripts/clean-next.js:48` | Browser telemetry is not ready and should remain out of MVP. |

## What Is Already Useful

- Python `logging` is already imported in the backend, so adopting a helper does
  not require a new runtime dependency.
- The main app creation point is centralized enough for middleware and exception
  handler registration.
- The access-session timeout loop is a perfect first structured-log proof
  because it is platform-owned and operationally important.
- Admin audit fingerprints already exist for admin mutations, but they are not
  application logs and must not be confused with request logging.

## Gaps To Close

| Gap | Required fix | Dependency |
| --- | --- | --- |
| No request id | Add middleware: accept/generate `X-Request-ID`, put in response header, expose via context. | Error/request foundation |
| No support id | In MVP `support_id = request_id`. Add to backend error envelope and frontend error object. | Error/request foundation |
| No redaction | Add recursive sanitizer for keys like token/secret/password/authorization/jwt/server_seed. | Before any details logging |
| No event registry | Add typed event names for a small MVP set. | Logging MVP |
| No structured logger helper | Add helper that attaches request context and applies redaction. | Logging MVP |
| No global exception logging | Central unexpected exception handler logs stable event and returns generic envelope. | Error/request foundation |
| No logging settings view | Read-only Platform Settings can show log posture later. | Settings read-only inventory |
| No retention policy | Document application-log retention separately from ledger/replay. | CTO/legal/product decision |

## Event Registry MVP

Start with a deliberately tiny event list:

| Event | Level | When | Required fields |
| --- | --- | --- | --- |
| `system.unhandled_exception` | error | Any unhandled backend exception | request_id, error_code |
| `system.validation_error` | warning | Request validation failure | request_id, error_code, path |
| `system.http_exception_normalized` | warning | Raw HTTPException normalized | request_id, status_code, error_code |
| `access_session.timeout_sweep_failed` | error | Sweeper loop failure | job_name, error_code |
| `access_session.auto_settlement_failed` | critical | Timeout close cannot settle a real-money round | access_session_id, game_code, title_code |
| `ledger.idempotency_conflict` | warning | Financial idempotency conflict | idempotency_key_hash, game_code |

Do not add high-volume gameplay telemetry in this WP.

## Redaction Policy MVP

The logger helper must redact recursively before serialization.

Always redact keys containing:

- `authorization`
- `token`
- `jwt`
- `secret`
- `password`
- `server_seed`
- `private_key`
- `database_url`
- `redis_url`
- `reset_token`
- `access_token`
- `launch_token`

Truncate long strings and nested payloads. Log ids and hashes, not raw secrets.

Also treat full URLs and query strings as sensitive until a safe URL sanitizer
exists. The current CMS v2 lab bridge can put an admin token in a query string,
so request logging must never dump `url` blindly.

## Implementation Slices

### Slice L1 - Request Context Dependency

Owned by `WP-ERROR-REQUEST-FOUNDATION-MVP`.

- middleware;
- `X-Request-ID`;
- request context helper;
- support id in error envelope.

### Slice L2 - Logger Helper And Redaction

- `backend/app/core/logging.py` or `backend/app/api/logging.py`;
- `log_event(event_name, level, details, ...)`;
- typed event names;
- redaction tests.

### Slice L3 - Exception/Job Integration

- unexpected exception handler logs `system.unhandled_exception`;
- validation handler logs `system.validation_error`;
- timeout sweeper logs `access_session.timeout_sweep_failed`;
- no request/response body logging.

### Slice L4 - Read-Only Visibility

Later, Platform Settings can show:

- structured logging enabled;
- redaction policy version;
- request id mode;
- retention policy text;
- sink type.

## Stop-and-Ask

Stop before code if:

- anyone wants DB-backed application logs in this MVP;
- anyone wants request/response body logging;
- support id must differ from request id immediately;
- logs must contain unrevealed server seed or tokens;
- log retention has legal implications not decided yet.

## Test Gates

Automated:

- request id generated when absent;
- valid incoming `X-Request-ID` returned;
- error envelope includes `support_id`;
- redaction removes token/secret/password/server_seed keys;
- unexpected exception logs stable event name;
- timeout sweeper uses structured event helper;
- no frontend boundary imports from game modules.

Manual:

- trigger one backend error and verify UI code/support id;
- verify backend log can be searched by request id;
- verify no token or seed appears in log output.

## CTO Development Recommendation

Do not start with logging alone. Approve it as the second implementation slice
after error/request foundation. The first logging commit should be small:
request context already present, logger helper, redaction helper and timeout
sweeper event.

## Analysis Completeness

Closed for pre-development:

- current backend logging locations;
- missing request/support id;
- raw HTTPException paths;
- redaction risks;
- event registry MVP;
- first implementation sequence;
- tests/gates.

No further discovery is expected before writing the implementation prompt,
unless the CTO changes the scope to production log sink or DB-backed logs.
