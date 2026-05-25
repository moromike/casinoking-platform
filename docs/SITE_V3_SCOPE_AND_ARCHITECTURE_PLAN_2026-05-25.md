Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - Scope And Architecture Plan

## 0. Executive Verdict

Site V3 should be treated as a new parallel site/CMS product, not as a patch on
the current Site V1 and not as a continuation of the Gemini `frontend-v2` lab.

The product intent is:

- keep the current Site V1 alive and stable;
- build a second site/CMS line with its own boundaries;
- reuse platform services only through explicit contracts;
- avoid contaminating V1 runtime, V1 publication flows, current game launch,
  wallet, ledger and game admin surfaces;
- use the Gemini lab only as material to audit, not as the architecture.

Recommendation: rename the workstream from **CMS v2** to **Site V3**.

## 1. Why Not Continue V2 As-Is

The current `frontend-v2/` artifact is a lab, not a production-ready second
frontend:

| Area | Current state | Verdict |
| --- | --- | --- |
| App boundary | `frontend-v2` hosts a Module Composer builder. | Wrong boundary: the builder belongs to admin, not the public player site. |
| Port meaning | Port `3001` is occupied by the builder. | Wrong meaning: `3001` should be the public Site V3 player surface. |
| Backoffice entry | Admin opens an external lab window. | Temporary only; final builder should live inside admin `:3000`. |
| Build artifacts | `.next` and `node_modules` exist inside the untracked artifact. | Never commit as-is. |
| Product scope | It implements module editing before defining the site product. | Too component-first. |
| Security/handoff | Previous lab flow had admin token handoff risk, now mitigated by removing token query. | Final V3 needs a real secure handoff or internal admin route. |

Conclusion: do not build further on `frontend-v2` blindly. Audit it and salvage
only the pieces that survive the Site V3 contract.

## 2. Coexistence Rule: V1 Must Not Be Broken

Site V1 remains the current operational site:

- lobby and game library;
- launch cashier / game launch;
- Site/Lobby publication for games;
- homepage slots and banner media currently used by the player frontend;
- account/login/register/player shell.

Site V3 must coexist with V1 until explicitly promoted. No V3 change may break
V1 launch, lobby, real-money gate, account, registration or game runtime.

## 3. Port And App Boundary

Recommended local meaning:

| Port | Owner | Purpose |
| --- | --- | --- |
| `3000` | Current `frontend/` | Operational player/admin app, including Site V1 and backoffice. |
| `3000/admin/site-v3` or equivalent | Current `frontend/` | Site V3 builder/admin surface when implementation starts. |
| `3001` | Future `frontend-v3` or cleaned `frontend-v2` app | Public Site V3 player renderer only. |
| `8000` | Backend API | CMS/Site V3 persistence and public/admin API. |

Yes: **Site V3 can and should point to port `3001`** for the public player
renderer. The builder should not live there in the final architecture.

Temporary admin label: `Site v3 (Lab)` may still open `http://localhost:3001`
while the lab is being audited. This is a label of caution, not a production
approval.

## 4. What To Salvage From The Gemini Lab

| Artifact | Salvage level | Reason |
| --- | --- | --- |
| `frontend-v2/app/lib/modules/registry.ts` | Maybe salvage | Good seed for a typed module manifest, but too small and lab-oriented. |
| `ModulePicker` | Maybe salvage | Useful interaction idea; needs admin design system and validation. |
| `ModuleEditor` | Maybe salvage | Useful dynamic schema idea; needs field-level help, validation, assets and i18n. |
| `ComposerPreview` | Maybe salvage | Useful concept; needs draft/live preview semantics and stable admin styling. |
| `ModuleRenderer` | Reference only | Current renderers are placeholders; public Site V3 needs polished, responsive modules. |
| `frontend-v2/app/page.tsx` | Do not salvage as architecture | It mixes app shell, auth handoff, builder state and save/publish logic. |
| `.next`, `node_modules` | Delete/ignore | Build artifacts and dependencies are not product source. |

## 5. Site V3 Product Scope To Decide

Before implementation, define whether Site V3 includes:

| Area | Default recommendation |
| --- | --- |
| Homepage | Yes, modular. |
| Game lobby/library | Yes, consuming the same published game catalog, not duplicating game data. |
| Game detail pages | Probably yes, but Phase 2 after homepage/lobby. |
| Header/footer/global layout | Yes, managed through Site V3 layout modules. |
| Editorial banners/promos | Yes, module-based. |
| Static pages | Maybe: Terms, responsible gaming, FAQ as V3 content pages. |
| Login/account/cashier | No in MVP; link/route to existing V1 account/auth unless product explicitly wants a new shell. |
| Game runtime pages | No; game runtime remains owned by game standalone routes/shells. |
| SEO metadata | Yes, at least per page. |
| Multilingual site content | Decide. Current games use IT/EN/DE/ES; site may need same set or staged rollout. |

## 6. Architecture Proposal

### 6.1 Admin Builder

Lives in the existing admin app on `:3000`.

Responsibilities:

- page list;
- draft editor;
- module picker;
- module config editor;
- preview draft;
- save draft;
- publish live;
- validation issues;
- audit trail;
- asset selection/upload through platform asset APIs;
- role-gated access.

It should consume current admin shell/navigation and not open a separate
authentication universe.

### 6.2 Public Site Renderer

Lives on `:3001`.

Responsibilities:

- read published Site V3 pages through public APIs;
- render modules in player-quality UI;
- never expose draft/admin controls;
- gracefully fallback if a page/module is unavailable;
- link to current game launch routes and account/auth flows;
- support responsive/mobile rendering from day one.

### 6.3 Backend Site V3 API

Current `cms_v2_pages` / `cms_v2_modules` can be a seed, but must be audited
before reuse.

Needed concepts:

- page identity: `site_code`, `page_code`, locale if enabled;
- draft vs published snapshot;
- module order and slot;
- module schema/version;
- validation result;
- publication metadata;
- rollback/versioning decision;
- public read endpoint separate from admin read/write;
- audit log on save/publish/delete.

## 7. Non-Negotiable Constraints

- Do not break Site V1.
- Do not use query-string admin tokens.
- Do not commit `.next` or `node_modules`.
- Do not treat placeholders as product modules.
- Do not mark Site V3 green without a Product Owner walkthrough on
  `localhost:3000` and `localhost:3001`.
- Do not make the builder the public site.
- Do not duplicate game catalog truth; Site V3 consumes the platform catalog.
- Do not let module config become arbitrary unsafe HTML/JS without sanitization
  and explicit product/security review.

## 8. Recommended Work Packages

### WP-SITEV3-AUDIT-RESCUE

Doc-only.

Outputs:

- audit `frontend-v2/` source vs build artifacts;
- salvage/throw-away table;
- backend CMS v2 schema/API gap table;
- V1 coexistence matrix;
- proposed rename/migration from CMS v2 to Site V3 terminology.

### WP-SITEV3-CONTRACT

Doc-only.

Outputs:

- product scope;
- module taxonomy;
- page lifecycle;
- draft/live/versioning rules;
- security and auth model;
- visual/design principles.

### WP-SITEV3-BACKEND-MVP

Code.

Outputs:

- hardened admin/public endpoints;
- draft/live separation;
- validation;
- audit;
- tests.

### WP-SITEV3-ADMIN-BUILDER-MVP

Code.

Outputs:

- admin route `Site v3`;
- page list/editor;
- module picker/editor;
- preview;
- save/publish;
- no external lab auth handoff.

### WP-SITEV3-PUBLIC-RENDERER-MVP

Code.

Outputs:

- clean `3001` player Site V3 app;
- public page fetch;
- module renderers;
- game catalog module;
- responsive homepage/lobby.

### WP-SITEV3-PRODUCT-POLISH

Code/design.

Outputs:

- final visual language;
- module richness;
- mobile checks;
- SEO/meta;
- Product Owner walkthrough.

## 9. Open Questions For Michele

These are real product questions before implementation:

1. Is Site V3 initially only homepage/lobby, or does it include full content
   pages too?
2. Should Site V3 use the same four locales as games (`it/en/de/es`) from day
   one?
3. Should login/register/account stay in V1 for MVP?
4. Do we want V3 to visually replace the current player site, or run as a
   previewable alternate site until approved?
5. Which modules are mandatory for MVP: header, hero, game grid, promo band,
   rich text, footer?
6. Is rollback/version history mandatory in MVP or Phase 2?
7. Should the public V3 app be named `frontend-v3` eventually, or reuse a
   cleaned `frontend-v2` folder after deleting lab artifacts?

## 10. CTO Recommendation

Proceed, but do not write production code yet.

First open `WP-SITEV3-AUDIT-RESCUE` and `WP-SITEV3-CONTRACT`. Once those are
approved, implement backend/admin/public renderer in separate WPs.

The Gemini lab is not worthless, but it must be treated as prototype material.
The architecture starts here, not there.
