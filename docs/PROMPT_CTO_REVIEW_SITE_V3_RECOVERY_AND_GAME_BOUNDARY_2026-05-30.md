Status: READY
Last meaningful update: 2026-05-30

# Prompt - CTO Review Site V3 Recovery And Game Boundary

Use this prompt with the CTO to audit the work after the latest Site V3 audit
and the recovery fixes.

```text
You are reviewing CasinoKing as CTO.

Context:
- First read docs/SITE_V3_CTO_INCIDENT_AND_HANDOFF_REPORT_2026-05-30.md.
  Treat it as the accountability and incident inventory for the work under
  review.
- Start from docs/SITE_V3_CMS_INFORMATION_ARCHITECTURE_AUDIT_2026-05-28.md,
  docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md,
  docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md,
  docs/SITE_V3_CUSTOM_MODULE_AUTHORING_PLAN_2026-05-29.md and
  docs/SITE_V3_GAME_MODULE_EXTERNALIZATION_PLAN_2026-05-30.md,
  docs/SITE_V3_GMP0_COUPLING_INVENTORY_2026-05-30.md and
  docs/SITE_V3_GMP1_GAME_MODULE_INTEGRATION_CONTRACT_2026-05-30.md,
  docs/SITE_V3_GMP2_PREFLIGHT_CHECKLIST_2026-05-30.md,
  docs/SITE_V3_GMP2_BOXE_IN_PROCESS_ADAPTER_2026-05-30.md and
  docs/SITE_V3_BACKOFFICE_CTO_USABILITY_REVIEW_2026-05-30.md.
- V1/V2 must not survive as parallel products. Site V3 is intended to be the
  only frontend application in the local stack.
- Games are logically separate modules. Current placement under
  frontend-v3/app/runtime/{game} is a deployment decision, not a permanent
  product boundary.
- Do not approve changes that touch wallet, ledger, settlement, RNG, fairness,
  payout math or game runtime semantics unless the work package explicitly
  scopes them.

Review tasks:
1. Verify that Site V3 IA still follows the audit rules:
   - Modules means module type library.
   - Composition means mounted module instances.
   - The left navigation must not list mounted instances.
   - System pages, especially register/system_registration_form, are clear.
   - Module Studio creates safe data-driven custom module definitions only.
2. Verify V1/V2 retirement:
   - public root, login, register, account, admin, game shells, static assets
     and runtime iframe routes are V3-owned;
   - there is no second player product hidden behind V1/V2;
   - any residual legacy terminology is documentation-only or explicitly
     quarantined.
3. Verify player shell:
   - header is brand/auth only;
   - login/register/account are compact and usable;
   - authenticated account does not repeat useless detail navigation;
   - account game history and replay are readable on desktop and mobile.
4. Verify backoffice operational reports:
   - Finance keeps the compact, readable report layout that existed before the
     CSS regression;
   - ledger report and financial/bank session report are dense enough for
     operator use;
   - filter controls are grouped in compact rows/grids, not stretched into a
     huge vertical form;
   - action buttons such as Round detail are readable in all states;
   - Player admin, Games, LOG, Administrators, My Space and Platform Settings
     did not inherit unrelated Site V3 CMS styling.
5. Verify game shell without redesigning games:
   - public game shell only hosts the runtime iframe and return contract;
   - no host topbar with Title/Account/Fullscreen/Close is reintroduced;
   - native game UI, close X, audio popover, replay, mobile and multilingual
     behavior remain owned by the game modules.
6. Verify that no game runtime files were modified by recovery work unless a
   dedicated game work package exists. Check git diff for:
   - frontend-v3/app/ui/mines
   - frontend-v3/app/ui/boxe
   - frontend-v3/app/ui/hi-lo
7. Verify custom module authoring:
   - custom_ namespace;
   - approved renderer templates only;
   - safe field schema only;
   - immutable published definition snapshots in page snapshots;
   - no arbitrary JavaScript, React or unsafe HTML from CMS operators.
8. Verify registration:
   - /register is a Site V3 system page;
   - system_registration_form controls copy/optional fields/document-step gate;
   - backend /auth/register semantics are not secretly changed;
   - future KYC/document upload is kept as a separate WP.
9. Verify game portability plan:
   - confirm modular monolith is acceptable now;
   - identify blockers to making Mines/BOXE/HI-LO installable game modules;
   - approve or reject the completed GMP-2 first-slice direction before any
     physical split;
   - decide whether GMP-3 should proceed as host-neutral launch/storage/replay
     descriptor consumption plus mock non-CasinoKing demo launch.
10. Review tests and QA evidence:
   - frontend-v3 lint/build;
   - runtime extraction contract tests;
   - Site V3 admin/module/register contract tests;
   - replay tests for Mines/BOXE/HI-LO;
   - player account replay browser smoke;
   - desktop/mobile game shell smoke;
   - audio popover smoke.

Output required:
- Findings first, severity ordered.
- Explicit approval/rejection of V1/V2 retirement claim.
- Explicit approval/rejection of Module Studio safety.
- Explicit approval/rejection of registration CMS ownership.
- Explicit approval/rejection of game module externalization direction.
- Explicit approval/rejection of the GMP-2 in-process BOXE adapter first slice.
- Explicit approval/rejection of proceeding to GMP-3 before any package/service
  split.
- A short list of required fixes before the next product work package.
- A short list of accepted residual risks.

Do not propose a rewrite unless you can name the exact failing boundary and the
smallest safe migration path.
```
