Status: COMPLETED
Last meaningful update: 2026-05-22

# BOXE Backoffice Full Layer Audit - Step 2 Verifier

Verifier rule: this pass starts from the filesystem and route/component inventory, then checks whether Step 1 covered the resulting surfaces. It intentionally expands scope beyond sub-editor tabs.

## A. Independent File Inventory

### Admin Routes

| File | Role | Mines equivalent | BOXE equivalent | Verifier finding |
| --- | --- | --- | --- | --- |
| `frontend/app/admin/page.tsx` | Admin root shell. | Same shell. | Same shell. | Shared route; not game-specific. |
| `frontend/app/admin/games/page.tsx` | Games root route. | Mines appears in generic hub. | BOXE appears in generic hub. | Root hub is not the problem. |
| `frontend/app/admin/games/[engine]/page.tsx` | Engine route. | Mines engine page. | BOXE engine page. | Same wrapper, divergent inner rendering. |
| `frontend/app/admin/games/[engine]/titles/[title_code]/page.tsx` | Title detail route. | Mines editor detail. | BOXE editor detail. | Detail mount exists for both. |

### Admin Console and Games Layer

| File | Role | Mines status | BOXE status | Verifier finding |
| --- | --- | --- | --- | --- |
| `frontend/app/ui/casinoking-console.tsx` | Owns admin route state, catalog actions, title detail shell. | Has Mines-specific duplicate handler at `:1366`; title detail actions are generic at `:1452`, `:1553`, `:1601`, `:1644`. | BOXE uses generic title detail actions, but engine page does not expose most of them. | Mixed: title detail mostly generic, engine page still Mines-shaped. |
| `frontend/app/ui/platform-catalog-panel.tsx` | Loads catalog and passes handlers to `GamesOverview`. | Passes duplicate/title handlers to Mines category. | Same props available, but `GamesOverview` does not use them for BOXE. | Step 1 OK. |
| `frontend/app/ui/games/games-overview.tsx` | Games hub and engine overview. | Special-cases Mines with `GameCategoryView`. | Non-Mines goes to `Other engines`. | Core red gap. |
| `frontend/app/ui/games/game-category-view.tsx` | Rich engine category management. | Used only for Mines; copy says "Create Mines variant". | Not used for BOXE. | Core red gap and genericization target. |
| `frontend/app/ui/games/game-variant-list.tsx` | Variant table/actions. | Used by Mines. | Not used by BOXE. | BOXE misses inline Save/Preview/Archive/Restore on engine page. |
| `frontend/app/ui/games/game-status-badges.tsx` | Status and publication badges. | Full badges in Mines variant list. | Partial status badges in BOXE flat row. | Publication badge parity missing on BOXE engine page. |
| `frontend/app/ui/games/game-master-card.tsx` | Master title summary. | Used by Mines. | Not used by BOXE. | Master/variant grouping gap. |

### Title Editor Shared Layer

| File | Role | Mines status | BOXE status | Verifier finding |
| --- | --- | --- | --- | --- |
| `frontend/app/ui/title-editor/title-editor-shell.tsx` | Locks master, mounts variant editor and diagnostics. | Works. | Works, diagnostics absent. | Step 1 OK. |
| `frontend/app/ui/title-editor/engine-editor-registry.ts` | Dynamic editor/diagnostics registry. | Editor and diagnostics registered. | Editor registered, diagnostics missing. | Step 1 OK, diagnostics gap. |
| `frontend/app/ui/title-editor/title-editor-command-bar.tsx` | Load draft/load live/save/publish bar. | Consumed. | Consumed. | Step 1 OK. |
| `frontend/app/ui/title-editor/tabs/title-editor-status-banner.tsx` | Title status banner. | Consumed. | Consumed. | Step 1 OK. |
| `frontend/app/ui/title-editor/tabs/title-editor-tab-frame.tsx` | Tab frame. | Consumed. | Consumed. | Step 1 OK. |
| `frontend/app/ui/title-editor/tabs/title-editor-overview-tab.tsx` | Shared overview presentation. | Used indirectly by Mines overview component. | Used by BOXE overview component. | Conceptual parity, not identical descriptors. |
| `frontend/app/ui/title-editor/tabs/title-editor-config-tab.tsx` | Config choice-field primitive. | Mines grid/mines. | BOXE rows/difficulty. | Correct game-specific divergence. |
| `frontend/app/ui/title-editor/tabs/title-editor-validation-display.tsx` | Validation panel. | Consumed by BOXE; Mines has mixed/local validation. | Consumed. | Not fully symmetric. |
| `frontend/app/ui/title-editor/title-sound-assets-editor.tsx` | Shared sound asset editor. | Consumed via Mines wrapper. | Consumed directly. | Parity green. |

### Mines Admin/Runtime Files

| File | What it does | BOXE equivalent | Verifier finding |
| --- | --- | --- | --- |
| `frontend/app/ui/mines/mines-engine-editor.tsx` | Engine editor adapter to Mines backoffice. | `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx` | Present for both. |
| `frontend/app/ui/mines/mines-engine-diagnostics.tsx` | Mines diagnostics. | None. | Gap. |
| `frontend/app/ui/mines/mines-backoffice-editor.tsx` | Orchestrates Mines title detail tabs, draft/publish, assets, theme. | `boxe-engine-editor.tsx` | Present but field-level differences remain. |
| `frontend/app/ui/mines/mines-config-overview.tsx` | Mines overview diagnostics. | `boxe-config-overview.tsx` | BOXE has an equivalent intent. |
| `frontend/app/ui/mines/mines-i18n-admin-editor.tsx` | Copy/rules locale admin plus published locale coverage. | BOXE copy/rules blocks inside `boxe-engine-editor.tsx`. | Present but not same component/model. |
| `frontend/app/ui/mines/mines-grid-config-editor.tsx` | Grid/mines config editor. | BOXE rows/difficulty `TitleEditorConfigTab`. | Correctly game-specific. |
| `frontend/app/ui/mines/mines-board-assets-editor.tsx` | Safe/mine board symbols. | `boxe-assets-editor.tsx` | Present with BOXE labels. |
| `frontend/app/ui/mines/mines-sound-assets-editor.tsx` | Sound editor wrapper. | `TitleSoundAssetsEditor` in BOXE. | Present. |
| `frontend/app/ui/mines/mines-theme-editor.tsx` | Theme tokens, presets, advanced skin, skin assets. | `boxe-theme-editor.tsx` | BOXE only token/preset subset; documented exception, not full green. |
| `frontend/app/ui/mines/use-mines-sounds.ts` | Runtime sound resolver. | `frontend/app/ui/boxe/use-boxe-audio.ts` | Present. |
| `frontend/app/ui/mines/mines-gameplay.tsx` | Runtime applies theme skin/logo/background/cell texture. | BOXE runtime has no equivalent advanced skin consumption found. | Documented exception, product revalidation needed. |

### BOXE Backoffice Files

| File | Role | Verifier finding |
| --- | --- | --- |
| `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx` | BOXE title detail editor. | Good for sub-tabs; does not solve parent engine page. Theme saves tokens only. |
| `frontend/app/ui/boxe-backoffice/boxe-config-overview.tsx` | BOXE overview diagnostics. | Present; game-specific rows/difficulty/fairness summaries. |
| `frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx` | Lobby card and board symbols. | Present; no advanced skin assets. |
| `frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx` | Base theme tokens/presets. | Present; advanced skin intentionally absent per current docs. |

### Adjacent Admin Files

| File | Role | Verifier finding |
| --- | --- | --- |
| `frontend/app/ui/site/site-lobby-publication-panel.tsx` | Site-wide lobby publication management. | Shared and can manage BOXE titles, but not a substitute for `/admin/games/boxe` engine-page parity. |
| `frontend/app/ui/site/site-lobby-title-row.tsx` | Row-level lobby visibility, demo, real, featured, lobby copy. | Shared and stronger than engine-page publication badges. |
| `frontend/app/ui/admin-finance-panel.tsx` | Finance reports and BOXE replay rendering. | Contains BOXE-specific replay import; platform extraction may be future debt. |
| `frontend/app/ui/audit/admin-audit-log.tsx` | Admin audit log. | Shared. |
| `frontend/app/ui/admin-management.tsx` | Admin user/area management. | Valid areas are `finance`, `end_user`, `mines`; BOXE is absent or hidden behind misnamed `mines`. |
| `frontend/app/ui/player-admin-panel.tsx` | Player management. | Not game-specific. |
| `frontend/app/ui/admin-shell-panel.tsx` | Admin nav shell. | Shared. |

## B. Step 1 Verification

| Point | Step 1 status | Verifier verdict | Notes |
| --- | --- | --- | --- |
| Admin route wrappers | Covered | OK STEP1 | Route wrappers are shared; inner rendering divergence is correctly located. |
| `GamesOverview` hardcoded Mines path | Covered | OK STEP1 | This is the main red gap. |
| `GameCategoryView` rich engine page | Covered | OK STEP1 | Step 1 included create variant, filters and variant list. |
| `GameVariantList` inline actions | Covered | OK STEP1 | Step 1 included Save/Preview/Archive/Restore. |
| Publication badges on engine page | Covered | OK STEP1 | Step 1 distinguished adjacent Site Lobby from missing engine-page badges. |
| Title detail route and shell | Covered | OK STEP1 | Accurate. |
| Engine diagnostics | Covered | OK STEP1 | Missing BOXE diagnostics is a valid gap. |
| Sub-editor tab existence | Covered | OK STEP1 | Accurate enough. |
| Copy/rules field parity | Covered | OK STEP1 | Step 1 called out conceptual vs shared differences. |
| Config game-specific divergence | Covered | OK STEP1 | Correctly cited BOXE SPEC rows/difficulty. |
| Sound assets | Covered | OK STEP1 | Green. |
| Theme tokens and presets | Covered | OK STEP1 | Accurate. |
| Advanced skin | Covered | WEAK STEP1, ridiagnostico: | Step 1 correctly cited SPEC exception, but this is product-conflict-sensitive because Michele flagged it. It must be tracked as "documented exception requiring revalidation", not green. |
| Runtime board/background skin | Covered | WEAK STEP1, ridiagnostico: | Step 1 found no BOXE runtime equivalent. Because SPEC defers advanced skin, this is not implementation red by itself, but closure docs must not hide it. |
| Save draft/publish | Covered | WEAK STEP1, ridiagnostico: | Step 1 was code-only and could not reproduce Michele's reported bug. Needs E2E follow-up. |
| Adjacent Site Lobby | Covered | OK STEP1 | Correctly says Site Lobby does not close engine-page gap. |
| Admin access areas | Covered | OK STEP1 | `mines` area naming is a new scope-expansion finding. |

## C. Scope Expansion: Additional Points Beyond Step 1

| # | Added point | Evidence | Final verdict | Why it matters |
| --- | --- | --- | --- | --- |
| X1 | `GameCategoryView` copy is Mines-specific, not just data-specific. | `frontend/app/ui/games/game-category-view.tsx:140` aria-label says "Create Mines variant"; placeholder examples at `:154` and `:168` are Mines-specific. | diverso - debt | A generic engine category page must parameterize copy/placeholders. |
| X2 | Duplicate title handler is explicitly named `handleDuplicateMinesTitle`. | `frontend/app/ui/casinoking-console.tsx:1366`. | diverso - debt | Even if backend endpoint is generic, the frontend ownership/copy remained Mines-shaped. |
| X3 | Detail runtime config load special-cases Mines. | `frontend/app/ui/casinoking-console.tsx:541-572`. | diverso - debt | Works for BOXE, but shared admin route still has Mines-specific state branches. |
| X4 | Admin management areas are not game-agnostic. | `frontend/app/ui/admin-management.tsx:32` valid areas are `finance`, `end_user`, `mines`. | diverso - gap | BOXE admin permissions are ambiguous. |
| X5 | Finance admin imports BOXE replay directly. | `frontend/app/ui/admin-finance-panel.tsx:7`, replay endpoint at `frontend/app/ui/admin-finance-panel.tsx:490-491`. | diverso - debt | Replay parity landed, but the finance panel is not registry-based. |
| X6 | Theme backend is already platform-capable for skin. | `backend/app/modules/platform/catalog/theme_service.py:41-60`, `backend/app/modules/platform/catalog/theme_service.py:114-115`, `backend/app/modules/platform/catalog/theme_service.py:429-439`. | diverso - specifico BOXE | This proves the missing BOXE advanced skin is a product-scope exception, not backend impossibility. |
| X7 | Asset registry already supports skin asset kinds. | `backend/app/modules/platform/asset_registry/service.py:43-45` and `:69-71`. | diverso - specifico BOXE | Same as X6; exception must be explicit. |
| X8 | Mines tab id `tema` differs from visible label `Theme`. | `frontend/app/ui/mines/mines-backoffice-editor.tsx:1431-1434`. | diverso - debt | Minor, but a verifier should catch internal drift when using tab ids for tests. |
| X9 | BOXE theme type keeps `skin?: unknown` while UI ignores it. | `frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx:5-6`. | diverso - debt | The type hints at platform skin support but BOXE editor does not expose it. |
| X10 | Prior requested audit docs absent from this branch. | `rg --files docs/games/boxe` found no `BACKOFFICE_AUDIT_STEP1_2026-05-21.md` or `STEP2`. | diverso - debt | Process evidence was not available where this audit had to run. |
| X11 | Surface 10 in Playbook is too coarse. | `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:277` names "Backoffice editor" as overview/config/copy/rules/assets/theme/sounds. | diverso - debt | It omits parent admin engine page and adjacent admin access layers. |
| X12 | Prior Wave 5 addendum over-narrowed visual specularity. | `docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md:213-224` says shared admin surfaces and advanced skin out of scope. | diverso - debt | Accurate local statement, but closure turned it into broad green. |

## D. Final Consolidated Verdict

| Area | Final verdict | Blocking gaps |
| --- | --- | --- |
| Layer 1 engine page | red | BOXE lacks generic `GameCategoryView` path, create variant, filters, inline title editing, Save/Preview/Archive/Restore, publication badges. |
| Layer 2 title detail | partial | Detail editor exists; diagnostics missing. |
| Layer 3 tab existence | green-major | Tabs exist; theme id/shape debt remains. |
| Layer 4 field depth | partial | Copy/rules/config/sound/assets mostly present; theme advanced skin is a documented BOXE exception, not full parity. |
| Layer 5 draft/save/publish | partial | Code paths exist, but Michele reports Mines draft bug; E2E proof missing. |
| Layer 6 adjacent admin | partial | Site Lobby shared; admin access areas and finance replay extraction debt remain. |

Surface 10 true status: **red**.

The red verdict is caused by Layer 1. Even if the title detail page were acceptable, the parent engine management page is visibly and functionally non-parity for BOXE.

## E. Recommended Fix Scope

| WP | Priority | Description | Effort |
| --- | --- | --- | --- |
| WP-ADMIN-ENGINE-PAGE-PARITY | P0 | Replace Mines-only `GameCategoryView` usage with a generic engine category page consumed by Mines and BOXE. Include variant creation, filters, inline display-name edit, Save/Preview/Archive/Restore, status/publication badges. | 14-22 prompts |
| WP-TITLE-DIAGNOSTICS-PARITY | P1 | Add BOXE diagnostics or a generic diagnostics adapter. | 4-7 prompts |
| WP-ADMIN-DRAFT-PUBLISH-E2E | P1 | Reproduce and fix save draft/live publish separation. | 6-10 prompts |
| WP-THEME-ADVANCED-SKIN-DECISION | P1 | Product decision: keep BOXE exception or inherit advanced skin. If inherit, implement UI/assets/runtime. | 8-16 prompts |
| WP-ADMIN-ACCESS-GAME-AGNOSTICITY | P2 | Replace `mines` admin area naming with game-admin/per-engine access. | 4-7 prompts |

Total estimate: **36-62 prompts**.

## F. Surface 10 Status for 12-Surface Check

Surface 10 Backoffice: **red**.

Closure criterion for moving to green: `/admin/games/boxe` must show a rich engine page equivalent to Mines or an explicit product decision must remove that requirement. Current evidence shows no such product exception.
