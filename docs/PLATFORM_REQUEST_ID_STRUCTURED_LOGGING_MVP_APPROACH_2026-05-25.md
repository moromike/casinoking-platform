Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Request-ID And Structured Logging MVP - Implemented Approach

## Scope

WP2 implements the backend application logging MVP approved in
`docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md`.

Implemented:

- stdout JSON line-delimited structured logs;
- request-bound correlation through WP1 `request_id`;
- background-job correlation through explicit `job_id`;
- redaction policy v2 with exact sensitive key list plus key-pattern matcher;
- string/depth/payload clamps;
- central exception handler events;
- access-session timeout sweeper events, including critical auto-settlement
  failure labeling.

Not implemented:

- DB-backed application logs;
- request/response body logging;
- frontend telemetry;
- pager, Slack, email or other alerting sink for `critical`;
- log retention job or production log sink.

## `log_event` Signature

Final MVP signature:

```python
log_event(
    level: str,
    event_name: str,
    details: Mapping[str, Any] | None = None,
    *,
    job_id: str | None = None,
) -> None
```

Behavior:

- emits one compact JSON object per stdout line;
- accepts levels `debug`, `info`, `warning`, `error`, `critical`;
- reads `request_id` automatically from WP1 request context;
- if `job_id` is provided, the record is job-bound and does not include
  `request_id`;
- if neither request context nor `job_id` exists, emits
  `log.missing_request_id` and records `request_id: "-"`;
- non-JSON-serializable values fall back to `str()` and emit
  `log.serialization_fallback`;
- redaction/logging errors are swallowed so business code does not fail because
  logging failed.

## Redaction Policy V2

Exact key list:

- `authorization`
- `token`
- `jwt`
- `secret`
- `password`
- `pwd`
- `server_seed`
- `private_key`
- `database_url`
- `redis_url`
- `reset_token`
- `access_token`
- `launch_token`

Case-insensitive key patterns:

- suffix: `_token`, `_secret`, `_password`, `_pwd`, `_key`, `_seed`,
  `_credential`, `_authorization`;
- substring: `secret`, `password`, `token`, `seed`, `credential`,
  `authorization`, `bearer`, `authheader`;
- compact camelCase suffix matching for common keys such as `bearerToken`,
  `authHeader` and `apiKey`.

Clamp policy:

- max string length: 256 chars, with `...[truncated]` semantic suffix
  implemented as `\u2026[truncated]`;
- max nested depth: 3;
- max serialized payload: 8KB. If exceeded, details are dropped and
  `log.payload_truncated` is emitted.

## Event Policy

MVP event names are append-only. Existing fields should not be removed or
renamed; additive fields are allowed.

`critical` is only a label in this MVP. It does not trigger paging, alerting or
operator notification automatically. A future `WP-CRITICAL-EVENT-ALERTING`
must connect critical events to an alerting sink.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Structured stdout JSON logging | N/A | Complete | N/A | N/A | N/A | N/A | Complete | Complete | Complete | One JSON object per stdout line. |
| Redaction and clamp policy | N/A | Complete | N/A | N/A | N/A | N/A | Complete | Complete | Complete | Exact keys, patterns, string/depth/payload clamps. |
| Request-bound log correlation | N/A | Complete | Error envelope unchanged from WP1 | N/A | Existing support flow | N/A | Complete | Complete | Complete | Uses WP1 `request_id`. |
| Job-bound sweeper logging | N/A | Complete | N/A | N/A | N/A | N/A | Complete | Complete | Complete | Uses generated `job_id`; no request context assumption. |
| Central exception handler events | N/A | Complete | Existing WP1 error response | N/A | Existing support id display | N/A | Complete | Complete | Complete | No raw exception message in structured details. |
| Alerting/retention/production sink | Not changed | Not implemented | N/A | N/A | N/A | N/A | N/A | Documented | Out of scope | Requires post-MVP WP. |

## Support Workflow

Player-facing and admin-facing error payloads keep WP1 `support_id`. Support can
search backend stdout JSON logs by the same request id when the event is
request-bound. Background timeout failures are searched by `job_id` and stable
event name.

## Verification

Focused gate used for implementation:

```powershell
$env:PYTHONPATH='backend'; python -m pytest tests/contract/test_structured_logging_mvp.py tests/contract/test_error_request_foundation.py
```

Coverage added:

- redaction variants including `bearerToken`, `authHeader`, `api_key`,
  `server_seed`;
- string, depth and payload truncation;
- request id and job id correlation;
- JSON line parseability;
- non-serializable fallback;
- central validation/HTTP/unhandled exception events;
- timeout auto-settlement failure critical job event.
