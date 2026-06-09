Status: ACTIVE
Last meaningful update: 2026-05-30

# Site V3 - Backoffice CTO Usability Review

## 0. Scope

This review checks whether the Site V3 admin/backoffice shape still respects
the CMS IA audit and the product expectation for module creation, registration
management and admin usability.

It is a CTO/product review, not a redesign implementation.

## 1. Verdict

The current Site V3 backoffice is conceptually coherent for the first slice:

- navigation separates `Site`, `Pages` and `Modules`;
- mounted page modules live in `Pages -> Composition`, not in the left nav;
- Module Studio exists and creates data-driven custom module definitions;
- registration is a managed system page through `system_registration_form`;
- draft/save/validate/publish rules are explicit;
- public rendering uses published snapshots and custom definition snapshots.

It is not production-finished UX. The main remaining risk is operator
ergonomics, not architecture.

Recovery update 2026-05-30: two findings from this review were fixed in the
same work session:

- `system_registration_form` is now blocked outside the `register` system page
  by backend validation and hidden/disabled from normal mounting on other pages;
- `/admin/site-v3` now shows a clear no-access state for admins without
  superadmin or `games` area, instead of rendering a confusing shell that fails
  API calls.

## 2. Findings

### P1 - Module Studio Is Safe But Still Expert-Oriented

Evidence:

- `frontend-v3/app/ui/site-v3-admin/screens/site-v3-module-studio-screen.tsx`
  exposes safe field types and approved renderer templates;
- backend validates `custom_` code namespace and field schema;
- tests cover create/publish/archive, reserved/unsafe codes, mount/preview and
  publish snapshots.

Assessment:

- safety boundary is good;
- the workflow still assumes the operator understands renderer template,
  category, field schema and defaults;
- this is acceptable for Michele/operator-with-support, but not yet a polished
  no-training CMS wizard.

Recommended next WP:

- add guided steps, clearer empty states and template-specific field grouping;
- do not add arbitrary React/JS/HTML.

### P1 - Registration Is CMS-Owned, KYC Is Not Yet Real Backend Workflow

Evidence:

- `System pages -> Registration` opens/creates page `register`;
- descriptor `system_registration_form` controls copy, field visibility,
  document-step gate and post-register path;
- public `/register` consumes the published page snapshot or falls back to the
  built-in default form;
- docs explicitly say backend document storage/consent is future work.

Assessment:

- registration CMS ownership is good;
- no hidden second registration product remains;
- the document-step option is UX-only until a dedicated KYC/document WP exists.

Recommended next WP:

- identity/KYC work package with document persistence, consent audit,
  backoffice review states and player profile editing.

### Closed - System Registration Module Scope

Evidence after recovery:

- backend validation returns `SITEV3.VALIDATION.SYSTEM_MODULE_PAGE` when
  `system_registration_form` is mounted on a page other than `register`;
- Composition filters the system registration module out of the add picker for
  non-register pages;
- Module type detail disables `Mount on current page` outside `register`.

Assessment:

- the system module no longer behaves like ordinary marketing content;
- the CMS IA now matches the manual's "system pages are not ordinary marketing
  pages" rule.

### Closed - Standalone Site V3 Admin Permission UX

Evidence after recovery:

- `/admin/site-v3` checks `is_superadmin` or normalized `games`/legacy `mines`
  area before rendering the builder;
- unauthorized admins see a clear no-access message plus Backoffice/Sign out
  actions;
- backend endpoint RBAC remains the source of security enforcement.

Assessment:

- no backend security change was needed;
- the confusing empty/failing admin shell is removed.

### P2 - Admin IA Matches The 2026-05-28 Audit

Evidence:

- left nav has `Pages -> Settings / Composition / Validation / Versions`;
- mounted module instances are not listed as left-nav children;
- `Composition` is the only visible ordered mounted-module list;
- module categories are under `Modules`, separate from instances.

Assessment:

- the previous conceptual bug is closed;
- wording still uses "Add module to page" rather than "Add block to page",
  but supporting copy clarifies "module type" and "mounted at the end".

Recommended next WP:

- optional copy polish from "Add module" to "Add block" if product wants less
  technical language.

### P2 - Preview Live Behavior Is Correctly Guarded

Evidence:

- action bar states that saving draft updates Preview live;
- publish is disabled while dirty or invalid;
- preview panel uses saved draft preview token;
- tests cover draft preview, security and publish-only public rendering.

Assessment:

- workflow is safe;
- operator must still learn "save draft before trusting preview".

Recommended next WP:

- browser QA with Michele on real edits, not code changes.

### P2 - Admin Login Separation Is Correct

Evidence:

- backoffice login says there is no player registration/promo/lobby/game flow;
- admin storage keys are separate from player storage keys;
- local bootstrap rules say use technical admin for automation.

Assessment:

- separation is acceptable;
- CSS was repaired in the current recovery work.

Recommended next WP:

- no architecture change; keep local admin bootstrap documented.

### P3 - Multilingual Admin Workflow Is Partial By Design

Evidence:

- Site V3 can author public content fields per module/config where supported;
- game runtime copy has per-title/locale systems;
- backoffice administrative UI labels are English.

Assessment:

- current multilingual support is content/runtime-oriented, not full admin UI
  localization;
- acceptable for MVP, but must be explicit.

Recommended next WP:

- if needed, open a platform i18n-admin WP. Do not hide it inside Module
  Studio or registration.

## 3. Product QA Covered

Recovery update 2026-05-30: the first product QA pass was covered by browser
and integration smoke on the local edge:

- `tests/integration/test_site_v3_admin_builder_browser.py` covers builder
  draft, validate and publish smoke;
- `tests/integration/test_site_v3_public_renderer_browser.py` covers published
  public pages and custom renderer templates including `image_banner` and
  `game_grid`;
- `tests/integration/test_frontend_smoke.py` and
  `tests/contract/test_site_v3_public_renderer_contract.py` cover `/register`
  ownership and CMS system-module wiring;
- `tests/integration/test_site_v3_backend.py` covers validation and publish
  gates, including the `system_registration_form` page restriction;
- `tests/contract/test_site_v3_admin_builder_contract.py` covers dirty-state
  guard, validation-before-publish and Module Studio boundaries.

Remaining QA is manual operator acceptance, not a known code blocker:

- Michele/operator walkthrough of real copy edits in Module Studio;
- optional wording polish if "module type" remains too technical;
- mobile admin readability beyond the current browser smoke matrix.

## 4. Backoffice Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IA cleanup | none | none | none | implemented | none | existing | contract | IA audit/manual | Green | Instances stay in Composition. |
| Module Studio safety | module definitions/version tables | validation APIs | custom definition payload | implemented | public templates | existing | contract/integration/browser | custom module plan/manual | Green first slice | Expert-oriented UX remains; unsafe custom HTML/URL validation covered. |
| Registration CMS ownership | existing Site V3 pages/modules | Site V3 page APIs + `/auth/register` unchanged | `system_registration_form` config | implemented | `/register` consumes published snapshot | existing | contract/integration | retirement/manual | Green first slice | System module blocked outside `register`; KYC/doc backend future WP. |
| Preview/publish workflow | published snapshots | preview token/publish service | validation JSON | implemented | published-only renderer | existing | contract/integration | manual | Green | Save draft before preview remains operator rule. |
| Admin login separation | none | admin auth APIs | admin token | implemented | none | repaired | API smoke + contract | manual | Green | `/admin/site-v3` has no-access UX for admins without Site V3 area. |
| Admin multilingual UI | none | none | none | English only | content can be localized | none | partial | manual | Accepted MVP | Separate future WP if required. |

## 5. Required Next Step

Run Michele/operator acceptance on the real local edge and decide whether to
open a small operator-UX polish WP for Module Studio wording/steps. Do not
reopen the IA cleanup unless a new screenshot shows mounted instances back in
the left nav.
