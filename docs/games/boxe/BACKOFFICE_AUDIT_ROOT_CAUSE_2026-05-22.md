Status: COMPLETED
Last meaningful update: 2026-05-22

# BOXE Backoffice Audit Root Cause - 2026-05-22

This document explains why Wave 5 declared Surface 10 Backoffice green while Michele later found obvious admin-layer gaps by opening `/admin/games`.

## 1. Which Wave 5 Audit Points Did Not Cover Admin Engine Page

The Wave 5 audit prompt had 15 minimum points. They were useful, but they centered on the title-detail editor and its sub-tabs. They did not force the auditor to open the parent engine-management page.

| # | Wave 5 audit point | Did it cover `/admin/games/<engine>`? | What it missed |
| --- | --- | --- | --- |
| 1 | Command/status/tab frame | No | Only Title Editor chrome, not engine catalog management. |
| 2 | Overview tab | No | Only `/admin/games/<engine>/titles/<title_code>` detail content. |
| 3 | Copy i18n keys | No | Manifest content, not title list/variant operations. |
| 4 | Rules HTML | No | Rules editor content, not engine page actions. |
| 5 | Config tab | No | Game config schema, not master/variant grouping. |
| 6 | Demo/Real labels | No | Runtime/player labels and legacy-label cleanup, not lobby publication badges in engine page. |
| 7 | Lobby card asset | No | Title asset editor, not engine page lobby publication controls/badges. |
| 8 | Board/symbol assets | No | Board asset editor, not parent admin page. |
| 9 | Sound assets | No | Sound tab only. |
| 10 | Theme tokens | No | Theme editor base tokens, not engine page. |
| 11 | Advanced skin / skin assets | Partially | Covered theme depth, but not whether Surface 10 can still be called full green with a documented BOXE exception. |
| 12 | Validation display + validators | No | Validation panel only, not catalog/title actions. |
| 13 | Workflow draft/save/publish | Partially | Covered detail editor workflow; did not require browser-level save-draft proof or parent engine actions. |
| 14 | Error/success messages localized | No | Local status copy, not engine page actions. |
| 15 | Admin login + access patterns | Weakly | Could have found `admin-management.tsx` valid areas, but did not require `/admin/games/boxe` functional parity. |

The missing category was "admin engine page layer": master/variant grouping, editable titles, create variant, filters, test toggle, row actions and publication badges.

## 2. Why Verifier Step 2 Did Not Expand Scope

The verifier followed the prompt shape instead of the product surface.

Specific misses:

- It treated "Backoffice editor" as equivalent to the Title Editor detail page because Playbook Surface 10 is worded as "Backoffice editor (overview, config, copy, rules, assets, theme, sounds)" at `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:277`.
- It did not start from route inventory (`frontend/app/admin/games/page.tsx`, `[engine]/page.tsx`, `[engine]/titles/[title_code]/page.tsx`) and walk every page.
- It did not inspect `frontend/app/ui/games/games-overview.tsx`, which contains the actual hardcoded Mines branch at `:49-55` and `:138-185`.
- It trusted shared `title-editor/` consumption as evidence of Surface 10, despite Playbook anti-pattern guidance that extracting scaffolding is not proof of shared implementation (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:574-575`).
- It accepted "visual specularity" screenshots inside sub-tabs and did not ask whether `/admin/games/boxe` was visually/functionally specular to `/admin/games/mines`.

The verifier was therefore compliant with a narrow interpretation of the brief, but not with the spirit of Rule 13: Codex should have challenged the scope boundary and expanded to route-level admin pages.

## 3. Fault Allocation

This is not a single-person error; it is a system/process failure.

| Owner | Fault % | Reason |
| --- | ---: | --- |
| CTO Claude brief/scope | 40% | The prior audit prompt listed 15 points focused on sub-editor parity. It did not explicitly name `/admin/games/<engine>` as Layer 1. |
| Codex audit execution/verifier | 45% | Codex should have started from routes and product-visible admin entry points, not only from the prompt checklist. It should have found `GamesOverview` hardcoding Mines. |
| Playbook/framework | 15% | Surface 10 was too coarse and named only overview/config/copy/rules/assets/theme/sounds. It did not split parent engine page, title detail page, sub-tabs, workflow and adjacent admin pages. |

Net: Codex carries the largest share because the verifier's job was to catch scope blind spots. The CTO brief contributed by naming a sub-editor-centered checklist. The Playbook contributed by allowing Surface 10 to remain monolithic.

## 4. What Would Have Caught This Earlier

The miss would have been caught by any of these gates:

1. Route-first audit: list all `frontend/app/admin/*` routes and click/inspect each game-specific path before sub-tabs.
2. Parent-child admin model: separate Surface 10 into:
   - 10A admin games hub
   - 10B admin engine page
   - 10C title detail shell
   - 10D title detail sub-tabs
   - 10E workflow draft/save/publish
   - 10F adjacent admin pages
3. Visual side-by-side evidence for `/admin/games/mines` vs `/admin/games/boxe`, not only title detail tabs.
4. File-map verifier rule: every file in `frontend/app/ui/games/*` must be classified in admin parity audits.
5. "Green means route and content": no surface can be green if the shared container exists but parent route behavior differs.
6. Product-owner smoke path: audit the exact URL Michele will open, not only internal components.

## 5. Applicable Playbook and Memory Feedback Not Applied

Relevant rules existed, but were not applied broadly enough:

- Playbook 6.3 says missing 12-surface rows are blind spots and audits must produce reference/new current/product/verdict/correction (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:249-301`). The problem is Surface 10 itself was too coarse.
- Playbook anti-pattern says "Extracting scaffolding without extracting shared implementations" must be fixed by promoting real surfaces (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:574`).
- Playbook anti-pattern says `GameBootShell` usage is not proof of visual implementation (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:575`). The same principle applies to `TitleEditorShell`.
- The new memory `feedback_audit_scope_breadth_critical` should be treated as a standing rule: audit scope must start from all user-visible routes, not the named component layer only.

## 6. Required Playbook Update

Recommended new Playbook text:

> Surface 10 Backoffice must be audited as multiple admin layers: admin games hub, engine page, title detail page, title editor sub-tabs, draft/save/publish workflow, adjacent admin pages and admin permissions. A title-editor sub-tab audit alone cannot mark Surface 10 green.

Recommended mandatory evidence:

- Side-by-side screenshots for `/admin/games/mines` and `/admin/games/boxe`.
- Side-by-side screenshots for `/admin/games/mines/titles/<variant>` and `/admin/games/boxe/titles/<variant>`.
- File inventory for `frontend/app/admin/*`, `frontend/app/ui/games/*`, `frontend/app/ui/title-editor/*`, reference-game admin files and new-game admin files.
- Explicit classification of product-documented exceptions such as BOXE advanced skin deferred. Exceptions cannot be counted as full green; they are "green with documented exception" or "partial" depending product expectation.

## 7. Consolidated Gap Table

| Priority | Gap | Cause | Fix direction |
| --- | --- | --- | --- |
| P0 | BOXE engine page flat list instead of Mines rich engine management. | `GamesOverview` hardcoded Mines path and non-Mines "Other engines" fallback. | Generic engine category page consumed by Mines and BOXE. |
| P0 | BOXE cannot create variants from engine page. | Duplicate handler/UI named and copy-shaped around Mines. | Generic duplicate-title flow and parameterized copy. |
| P0 | BOXE lacks inline Save/Preview/Archive/Restore in engine page. | `GameVariantList` not used for BOXE. | Reuse `GameVariantList` through generic engine category. |
| P1 | BOXE diagnostics absent. | Registry only registers Mines diagnostics. | Add BOXE or generic diagnostics adapter. |
| P1 | Theme advanced skin status over-closed. | Current docs defer BOXE advanced skin, but closure called Surface 10 full green. | Product revalidation and explicit exception tracking or implementation. |
| P1 | Draft/save/publish bug reported but not E2E verified. | Code audit replaced browser verification. | Admin E2E test for draft/live separation. |
| P2 | Admin permissions still named `mines`. | Area model not game-agnostic. | Rename/split game admin area. |

## 8. Recommended Scope and Estimate

Recommended Wave scope:

- WP-ADMIN-ENGINE-PAGE-PARITY: 14-22 prompts.
- WP-TITLE-DIAGNOSTICS-PARITY: 4-7 prompts.
- WP-ADMIN-DRAFT-PUBLISH-E2E: 6-10 prompts.
- WP-THEME-ADVANCED-SKIN-DECISION/IMPLEMENTATION: 8-16 prompts.
- WP-ADMIN-ACCESS-GAME-AGNOSTICITY: 4-7 prompts.

Total: **36-62 prompts**.

The expected effort range aligns with the original "30-60 prompt" expectation, with the upper end exceeding 60 only if product reverses BOXE's documented advanced-skin deferral and asks for full Mines inheritance now.

## 9. Final Statement

Surface 10 Backoffice should be considered **red** until the BOXE engine page reaches Mines-level parent-layer parity or product explicitly decides that BOXE should not inherit that admin engine-management capability.
