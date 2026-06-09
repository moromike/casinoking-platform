Status: ACTIVE
Last meaningful update: 2026-05-22

# BOXE Wave 7 - Backoffice Full Closure Plan

## Purpose

Wave 7 closes the real Surface 10 Backoffice gap after the full-layer audit
found the previous green status was wrong.

This is the live control document for the work. Keep it updated while the work
advances so Michele, CTO Claude and Codex can resume from the same map without
reconstructing context from chat.

## Source Documents

Read these before implementation:

1. `docs/README.md`
2. `docs/SOURCE_OF_TRUTH.md`
3. `docs/TASK_EXECUTION_GUARDRAILS.md`
4. `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`
5. `docs/games/boxe/BACKOFFICE_FULL_LAYER_AUDIT_STEP1_2026-05-22.md`
6. `docs/games/boxe/BACKOFFICE_FULL_LAYER_AUDIT_STEP2_VERIFIER_2026-05-22.md`
7. `docs/games/boxe/BACKOFFICE_AUDIT_ROOT_CAUSE_2026-05-22.md`

## CTO Decision

Proceed with Wave 7 as the next major work.

Surface 10 Backoffice is **red** until BOXE reaches Mines-level admin
management parity at all relevant layers, especially the parent engine page
`/admin/games/boxe`.

Michele's 2026-05-22 feedback supersedes the older "advanced skin deferred"
comfort: BOXE Theme is visibly poorer than Mines Theme and must be brought to
parity unless a new explicit product exception is written. No silent exception.

## Non-Negotiable Rules

- Mines is the reference. Do not regress Mines visually or functionally.
- BOXE inherits shared platform/admin patterns unless the difference is
  documented as game-specific in product docs.
- "Container shared" is not enough. Parity means container + content + fields +
  workflow + visual behavior.
- No scrollbar-based game/player solution belongs in this Wave. That issue is
  tracked separately by gameplay/no-scrollbar rules.
- Every green claim needs screenshot or focused test evidence.

## Current Truth

| Area | Current status | Reason |
| --- | --- | --- |
| Surface 10 Backoffice overall | green-major | Parent admin engine page, title detail tabs, theme depth, locale/rules workflow and admin access are now aligned with Mines. |
| `/admin/games/mines` | reference | Rich master/variant engine management. |
| `/admin/games/boxe` | green-major | Uses the same master/variant management view as Mines, with create variant, filters, inline save, preview and archive actions. |
| BOXE title detail tabs | green-major | Overview/copy/rules/config/assets/sounds/theme/diagnostics are present and visually captured side-by-side. |
| BOXE Theme | green-major | Advanced skin/title presentation payload fixed; BOXE runtime now consumes uploaded safe/mine symbols. |
| BOXE locale/copy/rules admin | green-major | Backend now persists default locale, 7 rules sections and full copy extras; runtime uses published locale. |
| Save draft workflow | green-major | Focused draft/live separation tests pass for Mines and BOXE title editor flow. |

## Workstreams

### WP7-A - Admin Engine Page Parity

Priority: P0

Expected effort: 14-22 prompts
Main files:

- `frontend/app/ui/games/games-overview.tsx`
- `frontend/app/ui/games/game-category-view.tsx`
- `frontend/app/ui/games/game-master-card.tsx`
- `frontend/app/ui/games/game-variant-list.tsx`
- `frontend/app/ui/games/game-status-badges.tsx`
- `frontend/app/ui/casinoking-console.tsx`

Goal:

Generalize the Mines-only engine management page so BOXE consumes the same
conceptual interface.

Required capabilities:

- master/variant grouping
- master card
- Editable Titles section
- title code + display name create form
- Create variant button
- Test toggle on create
- Active / Inactive / Archived / All filters
- Test only filter
- inline display name editing
- per-row Save
- per-row Preview
- per-row Archive / Restore
- status badges
- publication badges for hidden/visible, demo on/off, real on/off
- Open detail action

Gate:

- `/admin/games/mines` and `/admin/games/boxe` side-by-side screenshots.
- BOXE can create a variant from the engine page.
- BOXE can edit display name inline and save.
- BOXE exposes Preview and Archive/Restore.
- Mines screenshots show zero visual/functional drift.

### WP7-B - Theme Advanced Skin And Title Presentation Parity

Priority: P0/P1

Expected effort: 8-16 prompts
Main files:

- `frontend/app/ui/mines/mines-theme-editor.tsx` as reference only
- `frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx`
- `frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx`
- `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`
- `frontend/app/ui/boxe/boxe-gameplay.tsx`
- `frontend/app/ui/boxe/boxe.css`
- backend platform theme/asset services only if existing shared payload is not enough

Goal:

BOXE Theme must no longer be a token-only subset where Mines has advanced skin.
Bring BOXE to the same conceptual capability level, adapted only where BOXE is
game-specific.

Required capabilities to verify/implement:

- advanced skin section
- skin asset slots
- title presentation text/image
- title logo/image rendering where applicable
- game area background
- board/gameplay background or equivalent BOXE board skin hook
- saved draft theme includes skin payload, not just tokens
- publish theme includes skin payload

Gate:

- Theme tab side-by-side Mines vs BOXE.
- BOXE advanced skin fields visible.
- BOXE can save draft and publish token + skin payload.
- Runtime BOXE reflects supported title/background changes.
- Mines zero diff.

### WP7-C - Locale, Copy, Rules And Language Admin Unification

Priority: P1

Expected effort: 6-10 prompts
Main files:

- `frontend/app/ui/mines/mines-i18n-admin-editor.tsx` as reference only
- `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`
- `frontend/app/ui/boxe/boxe-i18n/*`
- shared `frontend/app/ui/title-editor/` tabs if needed

Goal:

Unify the admin interaction model for languages/copy/rules. The content remains
BOXE-specific, but the admin experience should not feel like a different system.

Required checks:

- locale selector behavior
- published locale panel or equivalent
- coverage counts
- rules section editing
- validation display
- save/publish messaging

Gate:

- Copy/rules admin side-by-side Mines vs BOXE.
- Same conceptual controls and diagnostics.
- BOXE-specific wording remains correct.
- Mines zero diff.

### WP7-D - Save Draft Workflow Investigation And Fix

Priority: P1

Expected effort: 2-5 prompts
Main files:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `backend/app/modules/games/mines/backoffice_config.py`
- BOXE equivalent files for comparison if needed

Goal:

Reproduce Michele's report that Mines Save draft does not work and only live
publish is effective. Fix only after reproduction.

Required checks:

- Save draft must write draft only.
- Save draft must not change live runtime.
- Publish must change live runtime.
- Same invariant should hold for BOXE.

Gate:

- Focused admin test or browser/API evidence proving draft/live separation.
- Mines player runtime still renders live until publish.
- BOXE workflow not regressed.

### WP7-E - Diagnostics, Admin Access And Adjacent Admin Surfaces

Priority: P2

Expected effort: 4-8 prompts
Main files:

- `frontend/app/ui/title-editor/engine-editor-registry.ts`
- `frontend/app/ui/admin-management.tsx`
- `frontend/app/ui/games/*`
- relevant backend admin permission/config files if needed

Goal:

Close smaller admin-layer gaps from the full audit.

Required checks:

- BOXE diagnostics registration or explicit documented exception
- admin area naming: `mines` vs game/admin access semantics
- adjacent asset/library paths do not hide BOXE-only gaps

Gate:

- Admin navigation/access behaves consistently for Mines and BOXE.
- Any remaining exception is explicitly documented and not counted as full green.

## Execution Order

1. WP7-A Admin Engine Page Parity.
2. WP7-B Theme Advanced Skin And Title Presentation Parity.
3. WP7-C Locale/Copy/Rules Admin Unification.
4. WP7-D Save Draft Workflow Investigation And Fix.
5. WP7-E Diagnostics/Admin Access cleanup.
6. Final Surface 10 closure gate.

Rationale: the engine page is the visible red blocker. Theme is the second
visible product gap. Locale/rules and draft workflow are important, but easier
to validate after the parent admin page is aligned.

## Suggested Branching

Default branch:

- `feature/wave7-backoffice-full-closure`

If the work becomes too large, split into:

- `feature/wave7-bo-engine-page-parity`
- `feature/wave7-bo-theme-skin-parity`
- `feature/wave7-bo-locale-workflow-parity`
- `feature/wave7-bo-save-draft-fix`

Do not merge a sub-branch as green without its screenshots/tests.

## Evidence Required

Minimum screenshot set:

1. `/admin/games/mines` vs `/admin/games/boxe`
2. Mines variant list vs BOXE variant list
3. Create variant flow Mines vs BOXE
4. Inline display-name edit/save Mines vs BOXE
5. Theme tab Mines vs BOXE
6. Advanced skin section Mines vs BOXE
7. Assets/skin assets Mines vs BOXE
8. Copy/rules locale admin Mines vs BOXE
9. Draft save before/after live runtime check
10. Publish before/after live runtime check

Minimum automated gates:

- frontend build PASS
- lint/i18n PASS if available
- Mines smoke PASS
- BOXE smoke PASS
- focused admin engine page tests PASS
- focused draft/live separation test PASS if WP7-D changes code
- static game-runtime boundary PASS if touched

## Progress Tracker

| Workstream | Status | Commit(s) | Evidence | Notes |
| --- | --- | --- | --- | --- |
| WP7-A Admin Engine Page Parity | green-major | `5bb5002` | `artifacts/wave7_backoffice_visual_2026-05-22/engine_page_side_by_side.png`; build PASS; focused duplicate/create tests PASS; static parity guard PASS. | `/admin/games/boxe` uses generic `GameCategoryView`; backend duplicate/create supports BOXE master titles. |
| WP7-B Theme Advanced Skin And Title Presentation | green-major | `5bb5002`, `df98da2` | `artifacts/wave7_backoffice_visual_2026-05-22/detail_theme_side_by_side.png`; theme contract PASS; BOXE asset/theme test PASS. | BOXE theme sends nested `tokens.skin`; runtime title uses `game.title` copy; runtime board consumes uploaded `symbol_safe` / `symbol_mine` assets with static fallback. |
| WP7-C Locale/Copy/Rules Admin Unification | green-major | `dde1733`, `2d5c912` | `detail_overview_side_by_side.png`, `detail_copy_side_by_side.png`, `detail_rules_side_by_side.png`; BOXE admin config PASS; BOXE title-editor browser smoke PASS. | Overview exposes Mines-style runtime language and in-game title controls; backend persists `default_locale`, all 7 rules sections and extra copy keys; runtime uses published locale; Copy editor no longer duplicates `game.title`. |
| WP7-D Save Draft Workflow | green-major | `2d5c912` | `test_mines_backoffice_config.py::test_admin_can_save_mines_backoffice_draft_and_publish_it_explicitly` PASS; BOXE title-editor browser smoke PASS. | No Mines code bug reproduced. Draft/live separation is covered by focused integration/browser gates. |
| WP7-E Diagnostics/Admin Access | green-major | `d73ba60` | `detail_overview_side_by_side.png`; focused RBAC PASS; static title-editor contract PASS; BOXE title-editor browser smoke PASS. | `games` is now canonical admin area with legacy `mines` alias; BOXE diagnostics panel registered with explicit read-only v1 fairness exception. |
| Final Surface 10 closure | green-major | `5bb5002`, `dde1733`, `2d5c912`, `df98da2`, `d73ba60` | 8 side-by-side screenshots captured; build/contract/smoke gates PASS. | Remaining items are documented follow-ups, not blockers for the previously red admin layer gaps. |

## Wave 7 Evidence Captured

Visual evidence:

- `artifacts/wave7_backoffice_visual_2026-05-22/engine_page_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_overview_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_copy_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_rules_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_config_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_assets_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_sounds_side_by_side.png`
- `artifacts/wave7_backoffice_visual_2026-05-22/detail_theme_side_by_side.png`

Automated gates rerun on 2026-05-22:

- `npm --prefix frontend run build`: PASS, including `lint:i18n`.
- `python -m pytest tests/contract/test_game_runtime_frontend_boundary.py tests/contract/test_game_runtime_storage.py tests/contract/test_title_editor_agnostic.py -q`: PASS, 19 tests.
- `python -m pytest tests/integration/test_admin_rbac.py -k "games_admin_can_access_mines_and_boxe_backoffice_config or legacy_mines_area_still_aliases_to_games_access" -q`: PASS, 2 tests with local `DATABASE_URL`.
- `python -m pytest tests/integration/test_boxe_admin_assets.py::test_boxe_assets_upload_preview_delete_and_theme_publish tests/contract/test_title_theme_contract.py::test_admin_title_theme_draft_publish_contract -q`: PASS, 2 tests.
- `python -m pytest tests/integration/test_title_editor_agnostic_frontend.py::test_boxe_title_editor_is_registered_and_saves_publishes_engine_config -q`: PASS.
- `python -m pytest tests/integration/test_mines_backoffice_config.py::test_admin_can_save_mines_backoffice_draft_and_publish_it_explicitly -q`: PASS.
- `python -m pytest tests/integration/test_boxe_smoke.py::test_boxe_demo_safe_sequence_cashout_resets_to_bet tests/integration/test_boxe_smoke.py::test_boxe_info_button_opens_rules_modal_not_how_to_play -q`: PASS, 2 tests.
- `python -m pytest tests/integration/test_mines_embed_browser_smoke.py::test_mines_demo_cashout_reveals_mines_and_plays_collect_sound -q`: PASS.

Residual follow-ups:

- BOXE diagnostics is a documented read-only v1 panel until BOXE gets dedicated seed rotation/session verification endpoints.
- BOXE copy/rules editor is conceptually aligned but not yet extracted into a shared title-editor component.
- BOXE theme asset upload/delete can still mark local theme state unsaved on a failed helper action; this is UX debt, not a parity blocker for the fields/capabilities Michele called out.

## Stop-And-Ask Triggers

- A required Mines capability cannot be generalized without changing backend
  contracts in a risky way.
- Mines visual/functionality changes are needed to make BOXE inherit a pattern.
- Theme advanced skin requires a product decision that changes BOXE runtime art
  direction materially.
- Save draft reproduction shows a platform-wide publish/draft model bug larger
  than Mines/BOXE admin.
- Rebase conflicts touch unrelated gameplay work.

## Replication Memory For Next Game

At Wave 7 closure, create a separate handoff document for CTO Claude:

`docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md`

That document should explain how to replicate the correct path for the next
game:

- start from the 12-surface audit
- split Surface 10 into admin engine page, title detail, tabs, field depth,
  workflow and adjacent admin access
- never mark a surface green for shared container only
- use Mines as the reference for platform/admin capabilities
- require side-by-side screenshots for every admin layer
- keep documented game-specific exceptions separate from true parity

## Live Log

| Date | Update |
| --- | --- |
| 2026-05-22 | Mini-doc created. Wave 7 approved as next major work. Surface 10 remains red until parent engine page, theme depth, locale/workflow parity and draft behavior are closed. |
| 2026-05-22 | Parallel audit found WP7-A/WP7-B were partially implemented but not closable: BOXE create variant still failed in backend and BOXE theme saved `skin` in the wrong payload shape. Both code paths were fixed; screenshot/browser evidence remains pending. External pre-production audit was incorporated into production-readiness docs as separate non-blocking backlog. |
| 2026-05-22 | WP7-C first closure pass: BOXE Overview now has runtime language and in-game title controls matching the Mines published-language model. Browser smoke verifies the controls are visible. |
| 2026-05-22 | WP7-C backend/runtime closure: FastAPI now accepts `default_locale`, BOXE backend preserves all copy keys sent by admin, validates and stores all 7 rule sections with safe HTML, and player runtime follows the published locale instead of browser language. Focused backend/browser gates passed. |
| 2026-05-22 | WP7-E closure pass: backend/frontend admin access uses canonical `games` with legacy `mines` alias; BOXE diagnostics registered as an explicit read-only v1 panel; focused RBAC/static/browser gates passed. WP7-B adjacent asset gap also closed by passing uploaded `symbol_safe`/`symbol_mine` assets into the runtime board. |
| 2026-05-22 | Wave 7 visual evidence captured: 8 admin side-by-side screenshots Mines vs BOXE on `localhost:3000`; build, contract, RBAC focused, asset/theme, title-editor browser, Mines draft/live, BOXE smoke and Mines smoke gates pass. Surface 10 moves from red to green-major with documented follow-ups. |
