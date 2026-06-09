Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Application Logging - Current-State CTO Review

Reviewed plan: `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md`

This review is per-plan only. It is not a cross-plan review and it does not
authorize implementation.

## CTO Verdict

Status: not green.

CasinoKing has minimal Python logging, but it does not yet have platform
application logging. There is no request/support id foundation, no structured
logger helper, no redaction policy, no event-name registry and no global
exception/validation handler.

The plan remains correct, but the first implementation must stay narrow:

`WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP`

Do not start a broad observability program, frontend telemetry, log collector,
or DB-backed application logs.

## Findings

| # | Finding | Current state | Gap | Risk | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | No request id middleware | `create_app()` registers CORS, router and static mounts only. | Plan requires `X-Request-ID`, backend context and propagation to error responses. | High: support cannot correlate browser error, API response and backend log. | `backend/app/main.py:31`, `backend/app/main.py:39` |
| 2 | Error envelope has no support id | `error_response()` emits code/message/details only. | MVP requires `support_id = request_id`. | High: player/admin cannot quote a diagnostic id. | `backend/app/api/responses.py:11` |
| 3 | No global exception handlers | No `RequestValidationError`, `HTTPException` or unexpected exception handler is registered in app creation. | Plan requires structured `system.unhandled_exception` and generic client response. | High: 500/422 shapes can drift and leak framework details. | `backend/app/main.py:31`, `backend/app/api/router.py:24` |
| 4 | Route-level exception mapping is fragmented | BOXE/HI-LO map some service exceptions locally and re-raise unknown exceptions. | Global handler must catch unknowns and log stable event/code. | Medium-high: real-money gameplay failures become hard to reconstruct. | `backend/app/api/routes/hi_lo.py:304`, `backend/app/api/routes/boxe.py:276` |
| 5 | `HTTPException` paths bypass the envelope | Some dependencies place an envelope inside `detail`; CMS v2 emits plain detail strings. | Error/logging foundation needs one normalized shape. | Medium: frontend cannot reliably extract code/support id. | `backend/app/api/dependencies.py:163`, `backend/app/api/routes/cms_v2.py:20` |
| 6 | Logging is free-text | `logger.exception("Access-session timeout sweep failed")` and one BOXE warning exist, but no structured fields are guaranteed. | Plan requires JSON-compatible fields, `event_name`, context and redaction. | High once production support starts relying on logs. | `backend/app/main.py:68`, `backend/app/modules/games/boxe/state_machine.py:201` |
| 7 | Timeout sweeper has no stable event name | The loop catches exceptions and logs only a text message. | Plan requires events like `access_session.timeout_sweep_failed`. | High: timeout/settlement failures touch money but are not traceable enough. | `backend/app/main.py:63`, `backend/app/modules/platform/access_sessions/service.py:282` |
| 8 | Event registry is absent | Event names can be invented inline. | Plan requires a minimal typed event-name registry. | Medium: queryability and alerting drift over time. | `backend/app/modules/games/boxe/state_machine.py:201` |
| 9 | Redaction helper is absent | Secrets and seed-related settings exist, but there is no centralized log sanitization. | Plan requires recursive redaction and truncation before details are logged. | High if logging expands before redaction. | `backend/app/core/config.py:21`, `backend/app/api/responses.py:16` |
| 10 | Observability settings are not modeled | Config has app/env/db/auth/assets only; no log mode, sink, redaction version or structured logging flag. | Plan needs a minimal operational posture, even if read-only. | Medium: future implementations may choose inconsistent defaults. | `backend/app/core/config.py:12`, `infra/docker/docker-compose.yml:9` |

## CTO Corrections To Carry Forward

- Request/support id is the first dependency. Logging without it is noise.
- Redaction must land before logging arbitrary details.
- Event names must be registered, not invented inside service code.
- The access-session timeout sweeper is the first system job to convert.
- Frontend telemetry remains out of MVP.
- DB-backed application logs remain out of MVP.

## Approved Next WP

`WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP`

Scope:

- request id middleware;
- `X-Request-ID` response header;
- support id available to error envelope through the error foundation;
- structured logger helper;
- redaction helper;
- event-name registry MVP;
- unexpected exception handler;
- timeout sweeper structured event;
- tests for request id and redaction.

## Stop Before Code

Stop if implementation proposes:

- logging request/response bodies;
- DB-backed application logs;
- frontend telemetry;
- logging secrets, tokens or unrevealed server seeds;
- logging high-volume gameplay events before the foundation is stable.

