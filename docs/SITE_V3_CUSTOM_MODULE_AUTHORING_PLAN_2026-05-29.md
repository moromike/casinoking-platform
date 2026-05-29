Status: ACTIVE - WP-CM1A/CM2A/CM2B/CM3/CM4 first slice implemented
Last meaningful update: 2026-05-29

# Site V3 - Custom Module Authoring Plan

## 1. Problem

Site V3 currently supports a fixed module type library:

- `global_header`
- `hero_banner`
- `game_grid`
- `game_grid_4x`
- `featured_game`
- `promo_band`
- `rich_text_safe`
- `global_footer`

The admin can mount, configure, duplicate and reorder module instances, but it
cannot define new module types from the UI.

Michele expectation: the CMS must allow an operator to create a new module,
assign it to a category, define guided fields, and then mount that new module
like any built-in module.

## 2. Principle

Do not let CMS users create arbitrary React, JavaScript or unsafe HTML.

Custom modules should be data-driven definitions rendered by approved renderer
templates. The operator creates the schema and defaults; the platform owns the
actual rendering templates and validation boundary.

## 3. Proposed Model

Add a new "Module Studio" area under Site V3 admin.

Core concepts:

- Module definition: a reusable module type, site-scoped or global.
- Module instance: a mounted usage of a module definition on a page.
- Renderer template: approved visual layout used by one or more definitions.
- Field schema: operator-defined fields constrained to safe types.

Initial renderer templates:

- Image banner: image, optional copy, optional CTA.
- Game grid: title list, heading, density variant.
- Editorial panel: heading, body, CTA.
- Safe rich text block: allowlisted HTML.
- Feature card: one title, image, copy, CTA.

Initial field types:

- text
- textarea
- boolean
- select
- asset picker
- title picker
- title list
- safe HTML
- URL/path

## 4. Data Shape

Candidate tables:

- `site_v3_module_definitions`
  - id
  - site_code
  - module_code
  - label
  - category
  - renderer_template
  - schema_version
  - field_schema_json
  - default_config_json
  - status: draft/published/archived
  - created_by/updated_by/published_by
  - timestamps

- `site_v3_module_definition_versions`
  - immutable snapshots of published definitions.

Existing `site_v3_modules` can keep storing mounted instances. For custom
modules, `module_code` points to the custom definition code; validation resolves
the definition from the custom registry first, then built-ins.

## 5. Admin UX

Wizard flow:

1. Choose category and renderer template.
2. Name the module and generate a code.
3. Add fields from allowed field types.
4. Configure defaults and required flags.
5. Preview with sample data.
6. Validate and publish the module definition.
7. Mount the new module from the normal Module Library.

The Module Library should show built-in and custom module types together, with a
clear badge for custom definitions.

## 6. Runtime Rules

- Published public pages must render from immutable snapshots.
- Publishing a page should snapshot the custom module definition version used by
each mounted custom module.
- A later edit to a custom module definition must not silently mutate already
published page snapshots.
- No custom JavaScript.
- HTML stays allowlisted through the existing sanitizer.
- Asset URLs stay limited to approved `/static/`, `/uploads/` or http(s)
  sources, as already enforced for Site V3.

## 7. Work Packages

### WP-CM1 - Product Contract

Define exact field types, renderer templates, permissions, naming rules and
versioning behavior.

Output:

- final schema decision;
- wizard wireframe;
- validation matrix;
- migration plan.

### WP-CM2 - Backend Definitions

Add persistence, API, validation and publish snapshots for custom module
definitions.

Gate:

- no arbitrary executable code;
- built-in modules continue to validate exactly as today;
- custom definitions are immutable once published.

### WP-CM3 - Admin Module Studio

Add the guided wizard and custom module management screens.

Gate:

- operator can create, preview, publish, archive a custom module definition;
- custom module appears in Module Library;
- custom module can be mounted and configured in Composition.

### WP-CM4 - Public Renderer Templates

Add generic template renderers for custom definitions.

Gate:

- public renderer consumes only published snapshots;
- browser smoke for every template;
- mobile/desktop no-overlap verification.

## 8. Immediate Next Step

WP-CM1A is locked for the first safe slice:

- custom module codes must use the `custom_` namespace;
- custom definitions are site-scoped;
- custom definitions may use only approved renderer templates;
- custom definitions may not define React, JavaScript or unsafe HTML behavior;
- custom definitions can be drafted, validated, published and archived before
  they become mountable in page Composition;
- public rendering remains a separate WP because mounted page snapshots must
  include immutable definition versions.

Approved first-slice renderer templates:

- `image_banner`
- `game_grid`
- `editorial_panel`
- `rich_text`
- `feature_card`

Approved first-slice custom field types:

- `string`
- `html`
- `boolean`
- `asset_ref`
- `title_code`
- `title_code_list`
- `url`

Implemented first-slice checkpoint:

1. Persistent custom definition registry and immutable definition versions.
2. Admin API for list/create/get/update-draft/validate/publish/archive.
3. Module Studio management screen.
4. Published custom definitions appear in Module Library and Composition.
5. Page publish/preview snapshots embed immutable custom definition snapshots.
6. Public renderer consumes custom snapshots through approved templates only.

Remaining later hardening:

- richer Module Studio editing/preview for existing definitions;
- browser QA matrix for every template with real authored content;
- more operator-friendly custom field presets and template examples;
- final product decision on custom module badges/labels in the admin library.

## 9. Implementation Log

### 2026-05-29 - WP-CM1A/CM2A Foundation

**Discovery / Decision**: Custom module authoring is safe only if operators
author data schemas, not executable UI code.
**Why it matters**: It keeps Site V3 extensible without letting CMS content
bypass React ownership, sanitizer boundaries or asset URL validation.
**What we did**: Added `site_v3_module_definitions` and immutable
`site_v3_module_definition_versions`, plus admin APIs and Module Studio for
create, validate, publish and archive.
**Affects**: Module authoring registry, admin Module Studio and
`docs/BACKOFFICE_MANUAL.md`.

### 2026-05-29 - WP-CM2B/CM3/CM4 Mount And Render

**Discovery / Decision**: Mounted custom modules must reference the published
definition version through the module `schema_version`, while public snapshots
embed the full definition snapshot.
**Why it matters**: Later draft edits to a custom definition must not silently
mutate already published public pages or draft preview tokens.
**What we did**: Added dynamic custom manifest resolution for validation,
Composition descriptors for published definitions, draft/publish custom
snapshot embedding and public renderer templates for `image_banner`,
`game_grid`, `editorial_panel`, `rich_text` and `feature_card`.
**Affects**: Site V3 backend validation/publish, admin Module Library and
Composition, `frontend-v3` renderer and Site V3 custom module tests.
