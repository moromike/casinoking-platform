Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Observability / Errors / Settings - CTO Review

Review date: 2026-05-24

Scope note: this document is a cross-plan orchestration review. It does not
replace the dedicated CTO review attached to each individual plan.

Reviewed plans:

- `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md`
  - Dedicated review:
    `docs/PLATFORM_APPLICATION_LOGGING_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_PLAN_2026-05-24.md`
  - Dedicated review:
    `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`
  - Dedicated review:
    `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md`
  - Dedicated review:
    `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md`

## 1. Executive Verdict

Verdict: direction approved, implementation not approved as one big WP.

The four plans correctly identify the core platform issue:

- ledger is not application logging;
- financial audit is not generic debug logging;
- user-facing errors need stable codes;
- global installation settings must not become a dangerous live-control panel.

However, the plans are too broad to implement directly. They must be converted
into a staged platform program with strict dependency order, data classification,
and minimal first slices.

CTO decision:

1. Approve the architectural split into four domains.
2. Require a short pre-implementation audit before any code.
3. Require the first implementation slice to be error/request foundation, not
   backoffice settings.
4. Block editable platform settings until read-only inventory and error matrix
   exist.
5. Block any financial correction path that writes outside the ledger.

## 2. Cross-Plan Review

### 2.1 What Is Strong

The plans make the most important separation correctly:

| Concern | Correct owner |
| --- | --- |
| Money movement | Ledger |
| Why money moved | Financial audit / replay / metadata |
| Admin config mutation | `admin_audit_log` |
| Runtime diagnosis | Application logs |
| User error display | Error code registry + i18n copy |
| Global visibility/control | Platform Settings backoffice |

This separation is critical. If CasinoKing mixes these domains, the system will
become hard to debug and dangerous to operate.

### 2.2 Main Weakness

The plans are individually coherent, but they understate cross-dependencies.
In particular:

- logging depends on request context and error codes;
- error code registry depends on API envelope normalization;
- platform settings depends on both error registry and observability inventory;
- financial audit depends on replay/finance registry and ledger metadata;
- reconciliation depends on traceability, not on generic logs.

Therefore implementation must be sequenced. Parallel work is possible only after
the foundation is in place.

### 2.3 Non-Negotiable Rules

These rules apply to all four plans:

1. Ledger remains the accounting source of truth.
2. Application logs never become the accounting source of truth.
3. Every visible error must have a stable error code.
4. Backend technical detail must not be rendered directly to players.
5. Secrets and unrevealed server seeds must never appear in logs or settings UI.
6. Platform Settings MVP is read-only except explicitly approved low-risk
   operational values.
7. No setting that changes financial outcome, RTP, wallet behavior or
   settlement behavior is editable without CTO/product/legal approval.
8. Retention is a product/legal decision, not a convenient hardcoded limit.

## 3. Review By Plan

## 3.1 Application Logging Plan

Verdict: approved as architecture, not yet approved for full implementation.

### Strengths

- Correctly separates logs from ledger and audit.
- Correctly pushes toward structured JSON logging.
- Correctly requires request/correlation id.
- Correctly blocks sensitive payloads.
- Correctly avoids "log everything" thinking.

### Gaps To Fix Before Code

1. Request context must be implemented before logger helpers are useful.
2. The plan should explicitly define whether `support_id` equals `request_id`.
   CTO recommendation: for MVP, support id is the backend request id exposed in
   the error response.
3. Need a redaction policy before logging details objects.
4. Need a minimal event-name registry; otherwise event names drift like copy did.
5. Need explicit behavior for unexpected exceptions:
   - log stack internally;
   - return generic error code;
   - show support id;
   - never expose stack trace.
6. Need to decide if frontend browser errors are in scope. CTO decision: not in
   MVP. Start backend/API first.

### CTO Narrowed MVP

Allowed first slice:

- FastAPI request id middleware;
- `X-Request-ID` response header;
- structured log helper;
- unexpected exception handler logs `CK.SYSTEM.INTERNAL_ERROR`;
- timeout sweeper converted to structured log event;
- tests for request id and no secret fields.

Not in first slice:

- external log collector;
- OpenTelemetry;
- frontend telemetry;
- high-volume gameplay action logging;
- DB-backed application logs.

### Risk Rating

Medium. Low product risk, medium platform risk because bad logging can leak
secrets or create noise.

## 3.2 Financial Audit Traceability Plan

Verdict: approved conceptually, high priority, must be split.

### Strengths

- Correctly states that financial "logs" are not application logs.
- Correctly keeps ledger as primary source.
- Correctly identifies replay as financial explanation, not only player UX.
- Correctly calls out registry need for account/admin finance.
- Correctly separates retention classes.

### Gaps To Fix Before Code

1. Needs an explicit current-state matrix:
   - Mines;
   - BOXE;
   - HI-LO;
   - player account;
   - admin finance;
   - replay endpoints;
   - ledger metadata completeness.
2. Needs exact settlement taxonomy:
   - manual cashout;
   - auto cashout;
   - refund;
   - void;
   - loss;
   - expired;
   - quarantined.
3. Needs an explicit "demo vs real" split. Demo may have demo wallet/event
   storage; real must route through platform ledger.
4. Needs migration strategy for existing ledger metadata. Do not rewrite old
   ledger rows casually.
5. Needs anomaly severity:
   - informative;
   - warning;
   - financial risk;
   - quarantine required.
6. Reconciliation should not auto-fix by default. It reports first, then any
   correction path must be designed separately.

### CTO Narrowed MVP

Allowed first finance slice:

- game finance/replay registry;
- remove implicit fallback in admin/player finance;
- expose Mines/BOXE/HI-LO replay descriptors consistently;
- document retention MVP;
- read-only admin finance explanation improvement.

Not in first slice:

- automatic ledger repair;
- physical deletion/anonymization policy;
- new quarantine table unless audit proves it is needed immediately;
- changing existing settlement math or wallet semantics.

### Risk Rating

High. This touches real-money explanation and supportability. It must be done,
but with careful gates.

## 3.3 Error Code Registry Plan

Verdict: strongest plan and best first foundation.

### Strengths

- Correctly defines stable non-translated codes.
- Correctly separates code from localized message.
- Correctly targets AppError -> envelope -> frontend error object.
- Correctly requires visible code in UI.
- Correctly recommends read-only error matrix first.

### Gaps To Fix Before Code

1. Need decide code namespace exactly.
   CTO decision: use `CK.<DOMAIN>.<ERROR_NAME>` for platform errors and
   `CK.<GAME>.<ERROR_NAME>` for game-specific errors.
2. Need compatibility with current frontend `ApiRequestError`.
3. Need compatibility with FastAPI validation errors, which currently may use
   framework-shaped details.
4. Need migration rule for existing short codes such as `INSUFFICIENT_BALANCE`.
   CTO decision: keep backward compatibility in frontend classifier during
   migration, but new backend envelope should emit `CK.*`.
5. Need ensure the UI code is not shown in a visually ugly way. It must be
   visible but not dominate the player message.
6. Need an error registry source of truth:
   - MVP: typed backend module plus generated/read-only frontend/admin view;
   - future: DB only if there is a real product need.

### CTO Narrowed MVP

First implementation should include:

- backend error registry file;
- `AppError`;
- request id/support id in error envelope;
- exception handlers for AppError, validation error and unexpected exception;
- frontend `ApiRequestError` extended with `supportId` and `details`;
- `GameActionError` renders code/support id;
- one or two migrated domains only, not all routes at once.

Recommended first migrated domains:

1. auth/session/runtime errors used by game launch;
2. wallet/insufficient balance/table gate;
3. HI-LO action errors as proof of pattern.

### Risk Rating

Medium-low if incremental. High if attempted as global route migration in one
pass.

## 3.4 Installation Settings Backoffice Plan

Verdict: useful, but must be read-only first. Editable settings are not approved
yet.

### Strengths

- Correctly warns against an omnipotent dangerous panel.
- Correctly separates visible, configurable and blocked values.
- Correctly includes Error Matrix and Game Registry Health.
- Correctly requires audit for changes.
- Correctly points to draft/publish for critical settings.

### Gaps To Fix Before Code

1. Needs RBAC definition: who can view vs edit platform settings.
2. Needs "source of truth" for every field before UI exists.
3. Needs explicit safe/unsafe setting inventory.
4. Needs environment restrictions:
   - local/staging may expose more diagnostics;
   - production must hide/mask aggressively.
5. Needs "restart required" semantics. Some env settings cannot be changed live.
6. Needs audit action kinds for platform settings changes.
7. Needs UI proof that read-only values do not look editable.

### CTO Narrowed MVP

Approved first slice only if read-only:

- Platform Settings shell;
- Overview;
- Error Matrix read-only from registry;
- Game Registry Health read-only;
- Observability status read-only;
- Finance retention policy display read-only;
- no edits except maybe harmless UI preferences after separate approval.

Not approved:

- editing log level live in production;
- editing session timeout;
- editing finance retention;
- editing settlement behavior;
- editing error semantics.

### Risk Rating

Medium as read-only. High if editable.

## 4. Required Execution Order

Recommended order:

| Step | WP | Why |
| --- | --- | --- |
| 0 | Current-state audit | Avoid repeating BOXE false-green pattern |
| 1 | Error/request foundation | Enables every other plan |
| 2 | Application logging MVP | Uses request id and error code |
| 3 | Finance/replay traceability registry | Highest business value after foundation |
| 4 | Platform Settings read-only | Consumes registry/log/error inventory |
| 5 | Reconciliation report MVP | Needs finance traceability first |
| 6 | Editable platform settings | Only after safe inventory + RBAC |

Parallelization:

- Step 0 can audit all domains in parallel.
- Step 1 must be mostly serial.
- Step 2 and Step 3 can partially parallelize after Step 1.
- Step 4 should wait for Step 1 and at least descriptors from Step 3.

## 5. Pre-Implementation Audit Required

Before code, create:

`docs/PLATFORM_OBSERVABILITY_ERROR_SETTINGS_CURRENT_STATE_AUDIT_2026-05-24.md`

Minimum audit rows:

1. all backend `HTTPException` usages;
2. all `error_response(...)` usages and current codes;
3. frontend `ApiRequestError` consumers;
4. all `GameActionError` consumers;
5. all current logging calls;
6. admin audit action kinds;
7. admin financial actions;
8. ledger transaction metadata shapes for Mines/BOXE/HI-LO;
9. replay endpoint/viewer coverage for Mines/BOXE/HI-LO;
10. hardcoded finance/replay branches;
11. settings/env values that might appear in Platform Settings;
12. secrets that must never appear in UI/logs.

This audit is mandatory because the risk is not coding difficulty. The risk is
missing a surface, as happened with BOXE backoffice and HI-LO finance/replay.

## 6. Data Classification Requirement

Before structured logging or settings UI, define field classes:

| Class | Examples | Treatment |
| --- | --- | --- |
| Public | game code, title code | Can be shown/logged |
| Internal id | round id, request id | Can be shown to admin/support |
| Financial reference | ledger tx id, amount | Log by reference, show with care |
| PII | email, user profile fields | Minimize, mask if possible |
| Secret | JWT, DB password, server seed unrevealed | Never log/show |
| Fairness reveal | revealed server seed after terminal | Replay/audit only |

No implementation should proceed without this classification.

## 7. Product / CTO Questions

Questions that need explicit answer before implementation:

1. Should player-facing error dialogs always show full `CK.*` code, or show it
   in a compact "Details" line?
   CTO recommendation: show compact line by default.
2. Who can access Platform Settings?
   CTO recommendation: superadmin only for MVP.
3. Should Platform Settings be visible in local only first?
   CTO recommendation: implement generic RBAC but validate locally first.
4. What is the MVP retention for replay payload?
   CTO recommendation: document policy now, do not auto-delete yet.
5. Should application logs include user id for player requests?
   CTO recommendation: yes when authenticated, but never email/token.

## 8. Revised Effort Estimate

The original plan estimates are individually plausible but optimistic when
combined.

| Program slice | Estimated prompts |
| --- | ---: |
| Current-state audit | 4-7 |
| Error/request foundation MVP | 10-16 |
| Application logging MVP | 6-10 |
| Finance/replay traceability registry MVP | 17-29 |
| Platform Settings read-only MVP | 14-24 |
| Reconciliation report MVP | 8-14 |
| Editable low-risk settings | 10-18 |

Recommended near-term scope:

```text
Audit + Error/request foundation + Application logging MVP
```

Estimated near-term total: 20-33 prompts.

Do not combine all four plans into one mega-wave.

## 9. Final CTO Decision

Approved:

- architecture split;
- stable error code registry concept;
- request/support id foundation;
- structured JSON logging direction;
- finance/replay traceability registry direction;
- read-only Platform Settings direction.

Not approved yet:

- editable Platform Settings;
- DB-backed application logs;
- broad route migration in one pass;
- auto-repair reconciliation;
- changing financial retention without product/legal decision;
- exposing any secret or unrevealed fairness seed in settings/logs.

Next action:

Create the current-state audit doc, then implement the Error/request foundation
MVP if no blocking issue appears.
