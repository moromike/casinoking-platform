Status: ACTIVE
Last meaningful update: 2026-05-25

# WP-ERROR-REQUEST-FOUNDATION-MVP - Approach

## CTO Decision

Proceed. This WP is a compatibility-first platform foundation, not a global
route migration.

Accepted CTO review corrections:

- request id validation: `[A-Za-z0-9_-]`, length 8-64;
- `support_id = request_id` in MVP;
- central handlers must normalize existing error envelopes and never double-wrap;
- frontend `detail` parsing must preserve nested error envelopes;
- insufficient balance keeps the current HTTP status during MVP;
- player diagnostics are compact support aids, not headline copy.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Request id middleware | n/a | NEW | `X-Request-ID` header | n/a | n/a | n/a | NEW | UPDATE | planned | Inbound valid id preserved; invalid id replaced. |
| AppError + registry | n/a | NEW | Extended envelope | n/a | n/a | n/a | NEW | UPDATE | planned | Code-backed registry only. |
| Central handlers | n/a | NEW | Normalize HTTPException / validation / unexpected | n/a | n/a | n/a | NEW | UPDATE | planned | No double wrapping. |
| Frontend parser | n/a | n/a | Parse support/request/retryable/details | n/a | UPDATE | n/a | NEW | UPDATE | planned | Legacy envelopes still parse. |
| Game diagnostic line | n/a | n/a | n/a | n/a | UPDATE | UPDATE | NEW | UPDATE | planned | Shared `GameActionError` + Mines custom dialog. |
| Auth/session compatibility | n/a | UPDATE | support id on auth errors | n/a | UPDATE | n/a | EXISTING | UPDATE | planned | No mass code rename in MVP. |
| Wallet/idempotency compatibility | n/a | UPDATE | support id, status unchanged | n/a | UPDATE | n/a | EXISTING | UPDATE | planned | `CK.WALLET.*` registry exists; status not changed. |

## HTTPException Test Scenarios

| # | Input | Expected |
| --- | --- | --- |
| 1 | `detail={"success": false, "error": {"code": "X.LEGACY"}}` | Keep `X.LEGACY`, add `support_id`, `request_id`, `retryable`; do not nest. |
| 2 | `detail="raw string"` | Safe mapped platform code/message; raw text not echoed. |
| 3 | `detail={"field_x": "value"}` | Safe code/message; details limited to whitelist. |
| 4 | `detail={"success": false, "error": {...}, "extra": "leak"}` | Ignore top-level `extra`; keep only normalized error object. |

## Frontend Parser Regression

`api.ts` must parse these cases without collapsing real codes to
`VALIDATION_ERROR`:

- direct `{success:false,error:{...}}`;
- nested `{detail:{success:false,error:{...}}}`;
- raw FastAPI validation detail;
- legacy envelope without support fields.

## Visual Baseline Plan

The diagnostic line uses one shared class:

- `game-error-diagnostic-line`

Closure evidence:

- shared `GameActionError` renders code/support id under the friendly message;
- Mines custom dialog renders the same compact line under its message;
- BOXE/HI-LO inherit via `GameActionError`;
- no new layout pattern is introduced.

If Playwright visual capture is unavailable during this implementation turn,
the automated contract must at least verify the component/class is present and
Mines consumes it. Product visual walkthrough on `localhost:3000` remains the
final human gate.

## Insufficient Balance Status

MVP keeps current HTTP status. The registry contains
`CK.WALLET.INSUFFICIENT_BALANCE`, but this WP does not silently move existing
422-style table/game flows to 402 or 409. A future
`WP-WALLET-ERROR-STATUS-MIGRATION` may change status after product approval.

## Stop Conditions

Stop only if:

- a route migration requires ledger/table-session semantic changes;
- Mines diagnostic requires a new visual pattern instead of a compact line;
- compatibility with legacy error envelopes would require deleting old codes.
