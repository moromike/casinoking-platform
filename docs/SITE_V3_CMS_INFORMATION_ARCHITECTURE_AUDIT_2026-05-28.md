# Site V3 CMS - Information Architecture Audit

Date: 2026-05-28  
Status: audit / plan only  
Scope: `/admin/site-v3` CMS builder, public Site V3 preview context, current module/page navigation model  
No code changes in this document.

## 1. Why This Audit Exists

Michele requested this audit after testing the Site V3 CMS on
`localhost:3000/admin/site-v3` and finding the navigation still confusing.
The concrete trigger was the left CMS menu showing entries such as `Hero banner`
under `Pages -> Mounted modules`, while `Hero banner` also exists under the
`Modules` library. To a human operator this reads as duplicated or misplaced
content: "why are hero banners under Pages and not under Modules?"

This is not only a visual polish issue. It is an information architecture issue.
The current CMS exposes three different concepts with labels that are too
similar:

- module type: the reusable definition, such as `hero_banner`;
- mounted module instance: one specific `hero_banner` block inside a specific
  page composition;
- page composition: the ordered list of mounted module instances for a page.

The implementation is technically explainable, but the UX does not make those
concepts clear enough. The result is a CMS that is partly functional but still
feels disorderly.

This document is meant to be self-contained so Michele can share it with the CTO
without needing the chat history.

## 2. Current Step Context

Site V3 is the new public site and CMS track, intentionally parallel to the
existing V1 site. The locked boundary is:

- the existing V1 site and game runtime remain on `localhost:3000`;
- the Site V3 admin builder lives inside the existing admin shell at
  `/admin/site-v3` on `localhost:3000`;
- the Site V3 public renderer lives in `frontend-v3/` on `localhost:3001`;
- `frontend-v2/` is a lab artifact to be removed in WP6.

The current Site V3 work is in WP5 Visual/Product QA. WP2 backend, WP3 admin
builder, WP4 public renderer and draft preview live have been implemented. The
current issue is that WP5 is not yet product-clean: the admin CMS navigation is
still too close to the internal implementation model.

Relevant baseline documents:

- `docs/SITE_V3_SCOPE_AND_ARCHITECTURE_PLAN_2026-05-25.md`
- `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`
- `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`
- `docs/SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md`
- `docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md`
- `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
- `docs/ACTIVE_OPEN_LOOPS.md`

## 3. Correct Conceptual Model

### 3.1 Module Type

A module type is a reusable definition in the module library.

Examples:

- `global_header`
- `hero_banner`
- `game_grid`
- `featured_game`
- `promo_band`
- `rich_text_safe`
- `global_footer`

Code reference: `frontend/app/ui/site-v3-admin/site-v3-admin-descriptors.ts`
defines these descriptors and categories.

Correct UX location:

- `Modules -> Module library`
- `Modules -> Categories`
- `Modules -> Module type detail`

A module type is not "on the page" yet.

### 3.2 Mounted Module Instance

A mounted module instance is one concrete occurrence of a module type inside a
page.

Example:

- Homepage has one `hero_banner` at position 3.
- Homepage has another `hero_banner` at position 4.

Both are instances of the same type. They can have different headline, image,
CTA, placement area and order.

Code reference: `SiteV3AdminModule` contains `module_code`, `slot_key`,
`sort_order` and `config_json`.

Correct UX location:

- `Pages -> selected page -> Composition`
- then click a row to open the instance detail.

### 3.3 Page Composition

Page Composition is the ordered list of mounted module instances for the selected
page.

It answers:

- what blocks are on this page?
- in what order?
- are they ready?
- which one do I edit?

Correct UX location:

- `Pages -> selected page -> Composition`

### 3.4 Module Library

Module Library is the catalog of available module types.

It answers:

- what kinds of blocks can I add?
- what category do they belong to?
- what fields will the type expose?

Correct UX location:

- `Modules -> Module library`
- `Modules -> category`
- `Modules -> module type detail`

## 4. What Is Wrong Right Now

| # | Area | Current State | Why It Is Wrong | Correct Direction |
|---|---|---|---|---|
| 1 | Left menu under Pages | The menu shows `Mounted modules` and lists `Global header`, `Game grid`, `Hero banner`, `Hero banner`, `Global footer`. | These are page instances, but they use the same names as module types. A human reads them as duplicated module library entries under the wrong parent. | Remove mounted instances from the left nav, or relabel as `Page blocks` with clearer instance labels. Preferred: remove from nav and keep them only inside Composition. |
| 2 | Hero banner duplication | Two `Hero banner` rows appear because the page has two mounted hero instances. | This is technically valid but UX-poor: the CMS does not explain that they are two page blocks, not two type definitions. | Show duplicates only in Composition with position and headline, e.g. `#3 Hero banner - CasinoKing`. |
| 3 | Pages vs Modules | `Pages` contains both page-level screens and instance shortcuts. | It breaks the hierarchy documented in the navigation approach: module instance detail should sit behind Composition, not as a sibling in the side nav. | `Pages` should contain `All pages`, `Settings`, `Composition`, `Validation`, `Versions`. |
| 4 | Add module wording | `Add module` appears in several places. | It sounds like creating a new module type. In reality it mounts an instance of an existing type into the current page. | Use `Add block to page` in Composition and `Mount on page` from module library/type detail. |
| 5 | Template wording | The wizard says "template". | The current platform has module types, not reusable editorial templates. "Template" suggests a capability that does not exist yet. | Use `Module type`. Save "template" for future page/module presets if implemented. |
| 6 | Global header/footer wording | `Global header` and `Global footer` are mounted as per-page modules. | "Global" implies site-wide settings, but the data model treats them as page composition blocks. | Either rename to `Header` / `Footer` for MVP, or move true globals to Site Settings in a later WP. |
| 7 | Page hierarchy note | Composition displays `Root / Homepage` hardcoded. | The backend does not yet model real parent page hierarchy. The UI implies a feature that is not implemented. | Remove the fake hierarchy note or make it reflect only the current page identity. |
| 8 | Game Grid wording | Some labels still mix "game icon modules", "catalog", and "library". | A Game Grid is one module instance; the selected games are titles, not modules. | Use `Selected game titles` and `Available title library`. |
| 9 | Preview live expectation | Preview reads saved draft, not unsaved local state. | The label can make users expect every local edit to appear instantly before Save draft. | Keep preview but make copy explicit: save draft updates preview. |
| 10 | Builder file shape | A lot of routing, screens, field rendering and workflows live in one large file. | This made it easy to add quick fixes but harder to reason about UX boundaries. | Split into screen/components before adding page tree, nav builder, SEO and asset workflows. |

## 5. Why The Work Became Confusing

### 5.1 Too Much Was Implemented Iteratively From Feedback

The CMS started as a functional MVP and then got multiple product corrections:

- make it more like a real CMS;
- split menu and submenus;
- add preview live;
- add module wizard;
- make add-module stay in Composition;
- expose mounted modules for direct access;
- make Game Grid more human.

Each individual fix was reasonable locally, but the total effect introduced a
mixed IA: the CMS now has both a clean concept (`Composition`) and a shortcut
that undermines that concept (`Mounted modules` in the side nav).

### 5.2 I Optimized For Access Speed, Not Conceptual Cleanliness

The mounted modules were added to the side menu to solve a real usability issue:
Michele could not easily reach `Game Grid` from the left menu. The fix made
access faster but introduced conceptual duplication.

Better solution:

- keep the left menu clean;
- make Composition easier and clearer;
- inside Composition, each block row should be obviously clickable and editable;
- optionally add a compact "jump to block" control inside Composition, not in
  the global left navigation.

### 5.3 The Terms Were Not Strict Enough

The UI uses:

- module;
- module type;
- mounted module;
- template;
- block;
- slot;
- placement area.

This is too much vocabulary. A human CMS should use a small language:

- Page
- Section / Block
- Block type
- Composition
- Library
- Settings

### 5.4 Existing Docs Already Warned About The Problem

`SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md` already defined:

- `Module type`: manifest/descriptor such as `game_grid`;
- `Module instance`: a specific `game_grid` mounted inside Homepage;
- `Composition`: mounted modules top-to-bottom;
- `Modules`: library of module types grouped by category.

The current implementation partially drifted from that model by exposing
mounted module instances as a side-nav list under Pages.

This is a process issue: the IA rule existed, but the latest quick fix optimized
locally instead of preserving the clean hierarchy.

## 6. Recommended Target IA

### 6.1 Left CMS Menu

Recommended structure:

```text
CMS menu
  Site
    Dashboard
    Site settings

  Pages
    All pages
    Selected page
      Settings
      Composition
      Validation
      Versions

  Module library
    Add block to page
    Categories
      Global structure
      Hero and banners
      Game catalog
      Promos and editorial
      Text and legal

  Open public Site V3
```

Important: do not list mounted module instances in this left menu.

### 6.2 Composition Screen

Composition should be the only place that lists the blocks currently mounted in
the page.

Each row should show:

- position number;
- block type label;
- instance headline/title;
- category;
- readiness state;
- edit button;
- move up/down;
- duplicate;
- remove.

Example:

```text
1  Header          CasinoKing navigation          Ready
2  Game grid       Games                          Ready
3  Hero banner     CasinoKing                     Ready
4  Hero banner     Mines promotion                Ready
5  Footer          Play responsibly               Ready
```

This makes duplicates legitimate: two hero banners are just two page blocks.

### 6.3 Module Library

Module Library should not show the page's current instances as primary content.
It should show available block types.

For each type:

- what it does;
- where it can be used;
- fields it exposes;
- button: `Mount on current page`.

### 6.4 Add Block Workflow

From Composition:

1. click `Add block`;
2. choose category;
3. choose block type;
4. click `Mount block`;
5. remain in Composition;
6. show row added at bottom;
7. user can click row if they want to edit settings.

Do not auto-route into detail unless the user explicitly clicks `Edit`.

### 6.5 Module Instance Detail

When editing one mounted block:

- title should be `Edit page block`;
- show `Block type: Hero banner`;
- show `Page position: 3`;
- show fields grouped by human task;
- button back: `Back to Composition`.

It should not feel like the user is editing the module type globally.

## 7. Action Plan To Clean It

### WP-SITE-V3-CMS-IA-CLEANUP

Goal: remove conceptual duplication and make the CMS menu understandable.

Files likely touched:

- `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx`
- `frontend/app/globals.css`
- `tests/contract/test_site_v3_admin_builder_contract.py`
- `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
- `docs/BACKOFFICE_MANUAL.md`

#### Step 1 - Remove Mounted Modules From Left Nav

- Remove `Mounted modules` subnav under `Pages`.
- Keep only `Settings`, `Composition`, `Validation`, `Versions`.
- Contract test: assert mounted module labels are not rendered in side nav.

Expected result: `Hero banner` no longer appears under Pages except inside
Composition.

#### Step 2 - Strengthen Composition Rows

- Make Composition rows clearly represent page blocks.
- Show better instance labels:
  - `#3 Hero banner - CasinoKing`
  - `#4 Hero banner - Mines promotion`
- Add explicit `Edit settings` button.
- Keep move/duplicate/remove actions.

Expected result: if two hero banners exist, the reason is visible.

#### Step 3 - Rename Ambiguous UI Copy

Replace:

- `Add module` -> `Add block`
- `New module` -> do not use
- `Choose template` -> `Choose block type`
- `Mount module` -> `Mount block`
- `Selected game icons` / `game icon modules` -> `Selected game titles`
- `Global header/footer` -> evaluate MVP rename to `Header` / `Footer`

Expected result: the UI language matches what the user is actually doing.

#### Step 4 - Fix Fake Hierarchy Copy

- Remove hardcoded `Root / Homepage` from Composition, or replace with:
  `Current page: {title} / {page_code}`.
- Do not imply parent-child hierarchy until backend supports it.

#### Step 5 - Update Documentation And Manual

- Update roadmap WP5 notes to say:
  - block type library and page block composition are separate concepts;
  - mounted block instances must not be duplicated in the global nav;
  - Composition is the source of truth for page block ordering/editing.
- Update `BACKOFFICE_MANUAL.md` with human workflow:
  - create/select page;
  - add block;
  - edit block;
  - save draft;
  - refresh preview;
  - publish.

#### Step 6 - Visual QA

Manual walkthrough required:

1. open `/admin/site-v3`;
2. verify left menu has no mounted block duplicates;
3. open Composition;
4. verify all blocks are visible and editable;
5. add Hero banner;
6. verify still in Composition;
7. save draft;
8. verify preview updates after refresh.

## 8. Broader Follow-Up Work

These are already known or naturally required after IA cleanup.

### WP-SITE-V3-PAGES-NAVIGATION-MODEL

Needed because Site V3 does not yet have a real site/page tree.

Scope:

- parent page / hierarchy model;
- path/slug;
- public V3 internal link resolver;
- navigation builder with submenu support;
- page picker in nav/editor fields;
- minimal SEO fields.

This should be designed before pretending the CMS can manage a full site tree.

### WP-SITE-V3-ASSET-WORKFLOW

Needed because the asset picker still leans on V1 homepage banner assets and
manual URL fallback.

Scope:

- Site V3 asset kinds;
- upload;
- picker;
- dimensions/format constraints;
- preview thumbnails;
- remove V1 fallback as operational crutch where appropriate.

### WP-SITE-V3-BUILDER-SPLIT

Needed before more CMS features are added.

Scope:

- split `site-v3-admin-builder.tsx` into screens/components;
- isolate field editors;
- isolate module library;
- isolate composition;
- isolate preview panel mount logic.

This reduces the risk of more quick UX patches creating new conceptual drift.

### WP6 Cleanup

Already scheduled:

- remove or quarantine `frontend-v2/`;
- ensure `.gitignore` remains correct;
- finalize docs around Site V3 as the active lab.

## 9. Risk Assessment

| Risk | Severity | Why |
|---|---:|---|
| Keeping mounted modules in left nav | High | It keeps creating the exact confusion Michele reported. |
| Adding page tree features inside `global_header.nav_items` | High | It would hide site navigation inside a module config blob. |
| Continuing to grow one builder file | Medium/High | It increases regression risk and makes UX state harder to reason about. |
| Renaming without contract tests | Medium | The same ambiguity can re-enter later. |
| Removing shortcuts too aggressively | Medium | Power users may want direct access; solve later with a clear `Jump to block` inside Composition. |
| Treating WP5 as green without product walkthrough | High | BOXE already showed that internal green is not enough. |

## 10. CTO Recommendation

Do not continue adding more CMS features until the IA cleanup is done.

The immediate next implementation should be:

1. remove mounted module instances from the left menu;
2. make Composition the single source of truth for page blocks;
3. rename copy from module/template vocabulary to block/block type vocabulary;
4. update docs/tests to lock this distinction.

After that, run Michele walkthrough again.

Only after this is clean should we proceed to larger Site V3 work:

- real page/navigation model;
- asset workflow;
- builder component split;
- WP6 cleanup.

## 11. Final Diagnosis

The current problem is not that the backend model is wrong. The backend model is
reasonable for an MVP: pages have ordered modules, and modules have typed config.

The problem is that the admin UI exposes implementation objects in the wrong
place:

- `Modules` should show module types;
- `Composition` should show mounted instances;
- the left nav should not list mounted instances with the same names as module
  types.

That is why `Hero banner` feels misplaced and duplicated.

This can be fixed without rewriting Site V3, but it needs a focused cleanup WP
with a hard rule: no CMS screen may mix module type library and page block
instances unless the UI explicitly explains the relationship.
