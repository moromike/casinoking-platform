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
| `3001` | Future `frontend-v3/` app | Public Site V3 player renderer only. |
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

## 5. Locked Site V3 Product Scope

Decisione lockata 2026-05-25 - Michele approved.

| Area | Scelta lockata |
| --- | --- |
| Homepage | MVP modulare. |
| Game lobby/library | MVP, consumando il catalogo giochi pubblicato senza duplicarlo. |
| Game detail pages | Phase 2 dopo homepage/lobby. |
| Header/footer/global layout | MVP, gestiti tramite moduli Site V3. |
| Editorial banners/promos | MVP, module-based. |
| Static pages | Phase 2: Terms, responsible gaming, FAQ. |
| Login/account/cashier | Restano V1 con link/route nel MVP. |
| Game runtime pages | No; i giochi restano standalone. |
| SEO metadata | MVP minimo per pagina; refinement Phase 2. |
| Multilingual site content | Data model con `locale` da subito; content MVP solo `it`. |

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

Current `cms_v2_pages` / `cms_v2_modules` remain dormant lab artifacts. WP2
must create new Site V3 tables instead of migrating the lab schema in place.

Needed concepts:

- page identity: `site_code`, `page_code`, `locale` from day one;
- draft vs published snapshot;
- module order and slot;
- module schema/version;
- validation result;
- publication metadata;
- published snapshot plus history list in admin;
- revert UI deferred to Phase 2;
- public read endpoint separate from admin read/write;
- reuse `admin_audit_events` with `source=site_v3` for save/publish/delete.

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

## 9. Locked Product Decisions

Decisione lockata 2026-05-25 - Michele approved.

| # | Decisione | Scelta lockata |
| --- | --- | --- |
| 1 | Cleanup e documentazione | Cleanup/lab governance e Site V3 doc procedono in parallelo; WP2 codice parte dopo merge cleanup. |
| 2 | Public app | Creare `frontend-v3/` nuova; `frontend-v2/` resta lab temporaneo e viene cestinato in WP6. |
| 3 | Data model | Creare nuove tabelle `site_v3_pages`, `site_v3_page_versions`, `site_v3_modules`; `cms_v2_*` resta dormiente. |
| 4 | Moduli MVP | Baseline WP2: `global_header`, `hero_banner`, `game_grid`, `featured_game`, `promo_band`, `rich_text_safe`, `global_footer`. Tranche successive aggiungono `game_grid_4x` e `system_registration_form` come built-in Site V3 senza riaprire il data model. |
| 5 | i18n | Data model con `locale` da subito; content MVP solo `it`. |
| 6 | Login/account/cashier | Baseline: V1 con link/route. WP-MIG1 sposta login/register/account in `frontend-v3`; WP-MIG3 rende configurabile la pagina di sistema `register` senza cambiare backend auth/wallet/ledger. |
| 7 | Versioning | Snapshot published + history list in admin; revert UI in Phase 2. |
| 8 | Audit | Riusare `admin_audit_events` con `source=site_v3`; niente tabella audit dedicata. |

## 10. CTO Recommendation

Proceed, but do not write production code yet.

`WP-SITEV3-AUDIT-RESCUE` e `WP-SITEV3-CONTRACT` sono stati completati e le
decisioni sono lockate. Non aprire codice WP2 finche' il CTO non consegna il
brief Parte A con DDL, API exact, payload, error codes e test plan.

The Gemini lab is not worthless, but it must be treated as prototype material.
The architecture starts here, not there.
