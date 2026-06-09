Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Application Logging - CTO Review

Reviewed plan: `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md`

## Verdict

Architecture approved. Full implementation not approved yet.

This plan is directionally correct because it separates application logs from
ledger, admin audit and replay/fairness. The main correction is sequencing:
logging must not start as a standalone cleanup. It must follow request id and
error-code foundation.

## CTO Approval

Approved:

- structured backend logging direction;
- JSON-compatible event fields;
- request/correlation id requirement;
- explicit no-secrets policy;
- separation from ledger and `admin_audit_log`;
- stdout/log-sink direction instead of DB application logs.

Not approved:

- DB-backed application logs;
- frontend telemetry in MVP;
- request/response body logging;
- high-volume gameplay event logging;
- production log collector design inside first slice.

## Required Corrections Applied To Plan

The plan was corrected to add:

- dependency on request/support id and error code registry;
- CTO decision that `support_id = request_id` in MVP;
- redaction policy;
- event-name registry MVP;
- unexpected exception policy;
- explicit frontend telemetry exclusion from MVP;
- narrowed MVP gate.

## Residual Risks

1. Bad logging can leak sensitive data.
2. Too many low-value events can hide real failures.
3. Logging without request/error correlation is expensive noise.
4. Developers may bypass helper and reintroduce free-text logs.

## Required First WP

`WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP`

Scope:

- request id middleware;
- support id response field via error foundation;
- structured logger helper;
- redaction helper;
- event registry MVP;
- timeout sweeper conversion;
- tests.

Do not include finance registry, platform settings or frontend telemetry.
