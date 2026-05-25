Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Error Code Registry - CTO Review

Reviewed plan: `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`

## Verdict

Approved as the first implementation foundation after current-state audit.

This is the strongest and most actionable plan. It should land before broad
logging, Platform Settings, and finance reconciliation, because all of those
need stable request/support/error identity.

## CTO Approval

Approved:

- stable `CK.*` codes;
- visible player error code;
- support id in envelope;
- backend `AppError`;
- central exception handlers;
- frontend `ApiRequestError` extension;
- read-only Error Matrix later.

Not approved:

- full route migration in one pass;
- editable DB error semantics;
- hiding codes from players;
- rendering backend detail as player copy;
- removing compatibility with existing short codes immediately.

## Required Corrections Applied To Plan

The plan was corrected to add:

- exact namespace taxonomy;
- old-code compatibility rule;
- `support_id = request_id` MVP;
- display rules for player/admin UI;
- backend typed registry as source of truth;
- `AppError` required fields;
- validation handling;
- first domains to migrate.

## Residual Risks

1. Partial migration may create two styles temporarily.
2. If UI makes codes ugly, product may push to hide them.
3. If old code compatibility is removed too early, games break.
4. If every route is touched at once, regression risk is high.

## Required First WP

`WP-ERROR-REQUEST-FOUNDATION-MVP`

Scope:

- current-state error audit;
- backend registry;
- `AppError`;
- request/support id;
- handlers;
- frontend `ApiRequestError`;
- `GameActionError` code display;
- migrate auth/session and wallet/table-balance first.

HI-LO action errors are the recommended game proof after the platform path
passes.
