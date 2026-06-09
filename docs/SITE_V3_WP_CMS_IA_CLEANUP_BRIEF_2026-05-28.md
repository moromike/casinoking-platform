Status: ACTIVE
Last meaningful update: 2026-05-28

# Site V3 - CMS IA Cleanup Brief (Punto 0)

This brief turns the audit `docs/SITE_V3_CMS_INFORMATION_ARCHITECTURE_AUDIT_2026-05-28.md`
into an executable, scoped plan. It is the CTO contract for the work. Read the
audit for the full diagnosis; this brief locks scope, decisions and gates.

The goal is Michele's "punto 0 decente": few things, done well. Clean what
exists, remove duplication and fake features. Add no new capability.

## 0. Locked Decisions (Michele, 2026-05-28)

1. **Builder split: light + contextual.** While cleaning the IA, extract the
   existing screen functions out of the 2683-line `site-v3-admin-builder.tsx`
   into per-screen files. Bounded to the areas touched; low risk; no leftover
   monolith debt. One WP, visual-parity gate.
2. **Theme tokens (public site CSS): separate WP after the IA cleanup.** WP-A
   (this brief, IA cleanup) ships and gets a walkthrough first. WP-B (theme
   token extraction) is a separate focused WP, defined in section 5 below, not
   executed in WP-A.
3. **Everything in audit section 8 is frozen.** No page-tree/navigation model,
   no asset workflow, no WP6 `frontend-v2/` removal in this WP.

## 1. CTO Vocabulary Decision

Keep a **single** vocabulary: `module` (the type) and `module instance`
(the mounted block). Do **not** introduce a second word ("block", "section").

Reason: the code, the data model (`SiteV3AdminModule`, `module_code`), the
descriptors and the 2026-05-26 approach doc already use `module` consistently.
Introducing "block" only in the UI would create a UI-vs-code split, i.e. a new
version of the exact confusion we are removing. The cheap, clean win is to
purge the *synonyms* ("template") and the ambiguous *verb* ("Add module"),
not to coin a new noun.

The only word to delete is **"template"** (it implies a reusable editorial
preset feature that does not exist).

## 2. Verified Current State

The audit's 10 findings were checked against the code. They are accurate. The
relevant facts for execution:

- The 2026-05-26 navigation restructure was already implemented. The menu-driven
  screens exist as functions inside one file (`SiteV3AdminNav` at line 871,
  `SiteV3CompositionScreen` at 1331, `SiteV3ModuleLibraryScreen` at 1468,
  `SiteV3ModuleInstanceScreen` at 1747, etc.).
- The confusion was re-introduced *on top* of that restructure by two later
  quick fixes:
  - a `Mounted modules` instance list inside the left nav, under Pages
    (`site-v3-admin-builder.tsx:934-950`);
  - a standalone "Add module" wizard screen using "template" wording
    (`SiteV3NewModuleWizardScreen`, `site-v3-admin-builder.tsx:1515-1628`),
    reached from a nav entry `Add module` (`:974-977`).
- **Composition is already in good shape.** Rows already show position index,
  label, category/code/slot, the real instance headline (`previewHeadline`),
  readiness pill, and Up/Down/Duplicate/Remove (`:1417-1459`). Two hero banners
  are already distinguishable by their headline. The audit's "strengthen rows"
  step is therefore mostly satisfied; only a minor copy tweak remains.
- **There are two add-module paths** (a concrete "pagina doppia"): the inline
  picker inside Composition (`:1346-1411`) and the standalone wizard
  (`:1515-1628`). The inline-in-Composition path is the correct model.
- A fake hierarchy note `Parent page / Root / Homepage` is hardcoded in
  Composition (`:1412-1416`).

## 3. WP-A Scope — `WP-SITE-V3-CMS-IA-CLEANUP`

Surgical and contained. No backend, no API, no public renderer behavior change.

### A1. Remove `Mounted modules` from the left nav
- Delete the `Mounted modules` subnav block (`site-v3-admin-builder.tsx:934-950`).
- Keep under Pages only: `All pages`, `Settings`, `Composition`, `Validation`,
  `Versions`.
- Mounted instances are reachable only from inside Composition (click a row).

### A2. Remove the redundant Add-module wizard (kills "template" and a duplicate page)
- Delete `SiteV3NewModuleWizardScreen` (`:1515-1628`) and its nav entry
  `Add module` (`:974-977`), and the `moduleWizard` view kind from
  `SiteV3AdminView`.
- Adding a module remains possible from exactly two legitimate places:
  - the inline picker inside Composition (`Add module to page`);
  - the `Mount on current page` action on a Module type detail screen.
- This removes the only occurrence of "template" wording and one duplicate page.

### A3. Remove the fake hierarchy note
- Delete the `Parent page / Root / Homepage` note (`:1412-1416`), or replace it
  with a neutral current-page identity line: `Current page: {title} / {page_code}`.
- Do not imply parent-child hierarchy until the backend models it.

### A4. Minor copy alignment (single vocabulary)
- Composition add button/heading: `Add module` -> `Add module to page`
  (`:1367`, `:1373`). The inline help text is already correct.
- Ensure no surface uses `template` or `block` as a noun for a module/instance.
- Module instance detail title should read as editing one mounted instance, not
  the global type (verify `SiteV3ModuleInstanceScreen` copy, `:1747+`).

### A5. Light split of the builder file (contextual to the cleanup)
Split along the existing function seams. Pragmatic target (adjust names as
sensible, keep it mechanical — move function + its imports, no logic rewrite):

```
frontend/app/ui/site-v3-admin/
  site-v3-admin-builder.tsx          # SiteV3AdminBuilder: state, handlers, view routing only
  site-v3-admin-types.ts             # exists
  site-v3-admin-descriptors.ts       # exists
  site-v3-admin-api.ts               # exists
  site-v3-draft-preview-panel.tsx    # exists
  site-v3-admin-helpers.ts           # pure helpers (:2383-2675): serialize/sort/format/nav-items
  screens/
    site-v3-admin-nav.tsx            # SiteV3AdminNav + CmsNavButton
    site-v3-overview-screen.tsx
    site-v3-site-settings-screen.tsx
    site-v3-pages-screen.tsx
    site-v3-page-detail-screen.tsx   # + SiteV3PageActionBar
    site-v3-composition-screen.tsx
    site-v3-module-library-screen.tsx# + category + type detail screens
    site-v3-module-instance-screen.tsx
    site-v3-validation-panel.tsx
    site-v3-version-history.tsx
    site-v3-draft-preview.tsx        # SiteV3DraftPreview + PreviewModule
  fields/
    module-field.tsx                 # ModuleField + field sub-editors (:1905+)
```

Rules for the split:
- No behavior change. The orchestrator keeps all state and handlers and passes
  props down exactly as today.
- Shared types/helpers move to `site-v3-admin-types.ts` / `site-v3-admin-helpers.ts`.
- `npm run build` in `frontend/` must pass with no new warnings.
- This is a refactor commit, kept separate from the IA-removal commit in git
  history so a regression can be bisected.

### A6. Contract test
Update `tests/contract/test_site_v3_admin_builder_contract.py`:
- assert the side nav does NOT render mounted-instance labels under Pages;
- assert no rendered admin copy contains the word `template`;
- assert there is no standalone "Add module" wizard route/view;
- assert Composition still renders rows with position + instance headline.

### A7. Docs
- `docs/BACKOFFICE_MANUAL.md`: the human workflow — select/create page; add
  module to page; edit module; save draft; refresh preview; publish.
- `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`: log WP-A; record the
  hard IA rule (library = module types; Composition = mounted instances; the
  left nav never lists mounted instances).
- `docs/ACTIVE_OPEN_LOOPS.md`: reflect WP-A done and WP-B (theme tokens) open.

## 4. WP-A Gate (hard)

Functional:
- `/admin/site-v3` left nav has no mounted-instance list under Pages.
- No `template` wording anywhere in the admin UI.
- Exactly one add-module entry point flow (Composition inline) plus the Module
  type detail `Mount on current page` action; no separate wizard page.
- Composition lists all mounted modules with position + headline + edit; add a
  Hero banner and stay in Composition; the new row appears at the bottom.
- Save draft, refresh, preview updates.

Regression:
- `npm run build` in `frontend/` passes.
- `http://localhost:3000/admin/site-v3` loads after frontend rebuild.
- `http://localhost:3001` (public V3) unchanged.
- No backend/API/public-renderer/V1 changes.

Product:
- Michele walkthrough on `:3000` before green. Internal green is not enough.

## 5. WP-B Scope (DEFINED, NOT EXECUTED IN WP-A) — `WP-SITE-V3-THEME-TOKENS`

Goal: give Michele one place to restyle the whole public site (background,
colours, fonts) so a later "rivedi il sito" request (by him or by an AI) edits a
single token block instead of hunting through 766 lines.

Current state: `frontend-v3/app/globals.css` has only 3 layout tokens
(`--site-v3-content-width`, `--site-v3-module-gap`, `--site-v3-page-gutter`).
All colours, the body gradient, text colours, borders, radii and the font stack
are hardcoded and scattered (e.g. `#0c1224`, `#f7f5ee`, the body gradient,
rgba borders). There is no theme layer.

Scope when WP-B runs:
- Add a single design-token block (top of `globals.css` `:root`, or a
  `theme.css` imported first) with named variables: `--bg`, `--bg-gradient`,
  `--surface`, `--surface-raised`, `--text`, `--text-muted`, `--accent`,
  `--accent-contrast`, `--border`, `--border-strong`, `--radius-sm/md/lg`,
  `--font-sans`, plus the existing layout tokens.
- Replace the hardcoded values across `globals.css` with `var(--token)`.
- **Zero visual change**: identical computed values; the gate is side-by-side
  screenshot parity on `:3001` before/after.
- HTML needs no change: the public shell (`site-v3-public-page.tsx`,
  `layout.tsx`) and per-module components are already cleanly separated.
- Document the token list (short comment block + a manual note) as the single
  restyle lever.

WP-B brief/prompt will be produced after WP-A passes its walkthrough.

## 6. Out Of Scope (frozen)

- Real page/navigation tree, slugs, internal link resolver, SEO fields.
- Asset upload/picker rework; V1 banner fallback removal.
- WP6 `frontend-v2/` removal.
- Any backend schema/API change.
- New module types beyond the 7 MVP descriptors.
- Vocabulary rename to "block"/"section" (rejected, see section 1).

## 7. Supersedes / Relationship

This brief supersedes the drift points of
`docs/SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md`: the mounted
list in the nav and the standalone add wizard introduced after that doc are
removed here. The target IA of that doc otherwise stands.
