Status: ACTIVE
Last meaningful update: 2026-05-26

# Site V3 - Admin Navigation Restructure Approach

## 0. Executive Verdict

The current Site V3 admin builder is technically functional, but the UX model is
wrong for a human CMS operator.

It compresses page selection, page identity, module type menu, page composition,
module instance editing, validation, preview and version history into one dense
workbench. That made sense as a WP3 technical MVP, but it is not the right CMS
shape for Michele's product workflow.

Decision: keep the existing Site V3 backend, module descriptors, draft/publish
flow and public renderer; refactor only the admin Site V3 navigation into a
menu-driven CMS with one clear surface at a time.

## 1. Current-State Audit

| Area | Current file/lines | Finding | Verdict |
| --- | --- | --- | --- |
| Admin entry point | `frontend/app/admin/site-v3/page.tsx:1` | Route mounts the existing admin console with `adminSiteV3Route`. | Keep. |
| Site V3 mount | `frontend/app/ui/casinoking-console.tsx:3493` | Console mounts `<SiteV3AdminBuilder accessToken={accessToken} />`. | Keep. |
| Page list | `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx:520` | Page list exists, but is a left column beside all editor surfaces. | Refactor into `Pages` screen. |
| Command/status | `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx:566` | Save/validate/publish/archive works from the compressed editor header. | Keep logic; move to page-level header. |
| Workbench compression | `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx:666` | `SiteV3CMSWorkbench` renders module menu + page canvas + module detail in a three-column card. | Replace. |
| Module taxonomy | `frontend/app/ui/site-v3-admin/site-v3-admin-descriptors.ts:246` | Module categories already exist: structure, hero, catalog, promo, text/legal. | Reuse as CMS menu taxonomy. |
| Module instance editor | `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx:844` | Instance detail is trapped in a side panel. | Move to full detail screen. |
| CSS layout | `frontend/app/globals.css:2317` | `.site-v3-workbench-grid` enforces three compressed columns. | Deprecate for new navigation. |

## 2. Target CMS Information Architecture

```text
Site V3
|- Site overview
|- Pages
|  |- Page list
|  |- Page detail
|  |  |- Page identity
|  |  |- Page composition
|  |  |  |- Module instance detail
|  |  |- Validation
|  |  |- Version history
|- Modules
   |- Global structure
   |  |- Global header
   |  |- Global footer
   |- Hero and banners
   |  |- Hero banner
   |- Game catalog
   |  |- Game grid
   |  |- Featured game
   |- Promos and editorial
   |  |- Promo band
   |- Text and legal
      |- Rich text safe
```

Key distinction:

- **Module type**: manifest/descriptor such as `game_grid`.
- **Module instance**: a specific `game_grid` mounted inside Homepage at a
  given position with specific config.

The current UI mixes those concepts. The new UI makes them explicit.

## 3. UI Behavior

### 3.1 Main CMS Menu

Add a persistent CMS navigation panel inside `/admin/site-v3`.

Primary items:

- Overview
- Pages
- Modules
- Validation
- Versions
- Open public Site V3

This menu is not the public site header. It is an admin CMS navigation surface.

### 3.2 Pages

The Pages screen shows only page management:

- locale/status filters;
- page list;
- page status;
- actions to open detail;
- empty/loading/error states.

Clicking a page loads the page and opens Page detail.

### 3.3 Page Detail

The Page detail screen shows:

- page status and version summary;
- command actions: load saved draft, save draft, validate, publish live,
  archive;
- dirty-state and validation-state;
- page identity fields.

It does not show the module type catalog in the same card.

### 3.4 Page Composition

The composition screen shows the mounted modules top-to-bottom:

- module order;
- module label/category;
- preview headline;
- move up/down;
- remove;
- edit instance action.

Adding a module sends the operator to the Modules section, where types are
grouped by category.

### 3.5 Modules

The Modules screen is a library of module types, grouped by category.

Clicking a category opens a category page.
Clicking a module type opens a module type detail page.

The detail page explains:

- what the module does;
- where it can be used;
- config fields;
- validation constraints;
- current use count in the loaded page;
- action to add the module to the current page.

### 3.6 Module Instance Detail

Clicking an already-mounted module opens a full-width detail screen:

- module identity;
- page position;
- slot/role;
- all config fields;
- asset picker/game picker where relevant.

No side-panel editing for the main operator path.

## 4. Implementation Plan

### Commit 1 - docs(site-v3): plan admin navigation restructure

- Add this approach doc.

### Commit 2 - refactor(site-v3): split admin builder into cms navigation screens

- Add a `SiteV3AdminView` state model.
- Replace the compressed `SiteV3CMSWorkbench` render path with dedicated
  screens.
- Keep existing API calls, save/validate/publish/archive logic and dirty-state.
- Keep module descriptor model unchanged.
- Do not change backend routes or public renderer.

### Commit 3 - style(site-v3): add cms navigation and full-detail admin layout

- Add CSS for:
  - CMS shell;
  - sidebar menu;
  - full-page cards;
  - module category cards;
  - module type detail;
  - module instance detail;
  - responsive/mobile admin behavior.
- Deprecate three-column workbench visual usage.

### Commit 4 - docs(site-v3): update manual and roadmap after cms navigation

- Update `docs/BACKOFFICE_MANUAL.md`.
- Update `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`.
- Update `docs/ACTIVE_OPEN_LOOPS.md`.

## 5. Out Of Scope

- No backend schema/API changes.
- No public renderer redesign on `:3001`.
- No Site V1 player/admin changes outside the Site V3 admin route.
- No new module types beyond the 7 MVP modules.
- No upload pipeline changes.
- No WP6 `frontend-v2/` cleanup.

## 6. Gate

Functional gates:

- `/admin/site-v3` loads with the new CMS menu.
- Pages screen lists current pages.
- Page detail can edit page title/code and marks dirty state.
- Save draft remains enabled after every editable change.
- Page composition can add, reorder, remove and open module instance detail.
- Modules screen groups the 7 MVP module types by category.
- Module type detail can add a module to the loaded page.
- Validation and version history remain reachable.

Regression gates:

- `npm run build` in `frontend/` passes.
- `http://localhost:3000/admin/site-v3` responds after Docker frontend rebuild.
- `http://localhost:3001` still responds.
- V1 public player routes and V1 admin shell are not changed outside Site V3
  entry wiring.

Documentation gates:

- Backoffice manual documents the new navigation.
- Roadmap logs WP5 navigation restructure.
- Active open loops reflect that Site V3 admin is no longer a compressed
  workbench.

## 7. Capability Matrix

| Capability | DB | Backend | API | Admin UI | Public UI | CSS | Test | Docs | Status | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CMS navigation | unchanged | unchanged | unchanged | new menu-driven screens | n/a | new | browser/manual | this doc/manual | planned | Replaces compact workbench. |
| Page list/detail | unchanged | unchanged | existing | split list/detail | n/a | new | browser/manual | manual | planned | No behavior change to draft data. |
| Page composition | unchanged | unchanged | existing | full composition screen | n/a | new | browser/manual | manual | planned | Existing module payload preserved. |
| Module type library | n/a | descriptor exists | n/a | category/type/detail screens | n/a | new | browser/manual | manual | planned | Uses existing 7 MVP descriptors. |
| Module instance editing | unchanged | unchanged | existing | full-width detail screen | n/a | new | browser/manual | manual | planned | Reuses current field components. |
| Draft/publish lifecycle | unchanged | unchanged | existing | command bar preserved | public unchanged | minor | build/browser | roadmap | planned | No published-only contract change. |
