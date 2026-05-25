Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Pre-Implementation Analysis Packet

## Purpose

This is the handoff packet for the four platform themes Michele asked to finish
before development:

1. application logging;
2. error registry / request-support foundation;
3. financial traceability / replay / reporting;
4. platform settings / installation settings.

All four are analyzed enough for CTO review. No further discovery pass should
be needed before writing implementation prompts, unless the CTO changes scope
or rejects one of the architectural decisions below.

## Packet Documents

| Theme | Status | Document |
| --- | --- | --- |
| Logging | Not green; ready after error/request foundation | `docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` |
| Error Registry | Not green; first implementation foundation | `docs/PLATFORM_ERROR_REGISTRY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` |
| Error/Request MVP Brief | Ready for CTO approval/correction | `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md` |
| Finance Traceability | Not green; high business risk | `docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` |
| Platform Settings | Not green; read-only inventory only | `docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` |

## CTO Verdict Summary

| Theme | True status | Why |
| --- | --- | --- |
| Logging | Red / blocked | No request id, support id, structured helper, redaction or event registry. |
| Error Registry | Red but first to implement | Existing envelope exists, but no `CK.*`, no `AppError`, no support id, no central handlers. |
| Finance Traceability | Red / high risk | Replay/finance hardcoded, fallback behavior unsafe, ledger metadata incomplete. |
| Platform Settings | Red / read-only only | Source-of-truth inventory and masking do not exist; editable settings would be dangerous. |

## Recommended Implementation Order

### 1. WP-ERROR-REQUEST-FOUNDATION-MVP

Reason: everything else depends on request id, support id and stable error
shape.

Must include:

- request id middleware;
- `support_id = request_id`;
- typed `CK.*` registry MVP;
- `AppError`;
- central handlers;
- frontend parser;
- compact diagnostic line in shared game UI and Mines custom surfaces;
- migration split D1 auth/session/launch, D2 wallet/idempotency.

### 2. WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP

Reason: after request/support id exists, logs become correlable.

Must include:

- structured logger helper;
- redaction helper;
- event registry MVP;
- timeout sweeper conversion;
- no request/response body logging;
- no frontend telemetry.

### 3. WP-FINANCE-REPLAY-REGISTRY-RETENTION

Reason: prevents wrong replay/finance behavior for current and future games.

Must include:

- game finance/replay descriptor registry;
- remove fallback to Mines/BOXE;
- wire Mines admin replay;
- forward metadata contract;
- retention policy MVP as documentation/read-only status;
- no ledger rewrite, no auto-repair.

### 4. WP-PLATFORM-SETTINGS-READONLY-INVENTORY

Reason: after the foundations exist, settings can display status safely.

Must include:

- descriptor contract per setting row;
- masking/visibility;
- superadmin-only read model;
- no editable settings;
- Error Matrix only after Error Registry lands.

## Cross-Theme Dependencies

| Dependency | Blocks |
| --- | --- |
| Request id | support id, logging correlation, error display, log search |
| Error registry | Error Matrix, safe UI copy, structured error logs |
| Redaction | logging details, settings display, audit payload display |
| Finance/replay registry | future games, account history, admin finance, replay retention |
| Settings source inventory | Platform Settings UI, any future editable controls |

## Non-Negotiable Constraints

- No application logs in DB for MVP.
- No request/response body logging.
- No raw secrets, server seeds, JWTs, reset tokens or query tokens in logs/UI.
- No editable Platform Settings in MVP.
- No Error Matrix before error registry.
- No finance/replay fallback to another game.
- No ledger rewrite or historical metadata mutation.
- No financial auto-repair.
- No route-wide `CK.*` migration big bang.

## Stop-Before-Code Decisions

The following are the only open decisions that can block coding:

| Decision | Recommended default |
| --- | --- |
| Player shows error code? | Yes, compact line. |
| `support_id` separate from `request_id`? | No, same value in MVP. |
| Insufficient balance HTTP status? | Keep current status during MVP unless CTO explicitly changes it. |
| Error Matrix editable? | No. Read-only after registry. |
| Platform Settings editable? | No. Read-only inventory first. |
| Retention duration? | Document placeholder now; legal/product decision before deletion jobs. |
| `settlement_kind` location? | Start in forward-only ledger metadata; decide later if platform_rounds column is needed. |
| Admin void as platform capability? | No, not until every game defines semantics. |

## Final Readiness Statement

Analysis is complete enough to proceed to CTO review.

If CTO approves the recommended defaults, the next coding prompt should be:

`WP-ERROR-REQUEST-FOUNDATION-MVP`

If CTO rejects a default, only the affected document needs revision. The repo
does not need another broad analysis pass for these four themes.
