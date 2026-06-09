Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Installation Settings Backoffice - CTO Review

Reviewed plan: `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md`

## Verdict

Read-only MVP approved after error/request foundation. Editable settings are not
approved.

The plan is useful because CasinoKing needs a place to see platform state,
error matrix, observability posture and game registry health. The danger is
turning that place into a control panel that changes money, security, settlement
or infrastructure casually.

## CTO Approval

Approved:

- Platform Settings as read-only backoffice area;
- superadmin-only MVP;
- Error Matrix read-only;
- Game Registry Health read-only;
- Environment diagnostics masked/read-only;
- Observability status read-only;
- Finance/retention display read-only.

Not approved:

- editing log level live;
- editing session timeout;
- editing finance retention;
- editing settlement behavior;
- editing error semantics;
- exposing secrets/env values unmasked;
- building draft/publish before first editable setting is approved.

## Required Corrections Applied To Plan

The plan was corrected to add:

- superadmin-only RBAC;
- read-only first restriction;
- source-of-truth inventory table;
- environment masking/restart rules;
- read-only treatment for observability, error matrix, finance retention and
  session recovery;
- UI rule that read-only values must not look editable;
- narrowed MVP and explicit exclusions.

## Residual Risks

1. Operators may assume visible values are editable.
2. A global settings panel can bypass game-specific safety if not constrained.
3. Showing too much environment detail can leak infrastructure information.
4. Editable settings without rollout semantics can create production drift.

## Required First WP

`WP-PLATFORM-SETTINGS-READONLY-INVENTORY`

Prerequisites:

- error registry MVP;
- request/support id foundation;
- game registry descriptors at least stubbed.

Scope:

- inventory all candidate settings;
- classify hidden/masked/read-only/editable;
- create read-only admin shell;
- render Error Matrix and Game Registry Health read-only;
- no edits.
