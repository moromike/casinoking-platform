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
| Surface 10 Backoffice overall | red | Parent admin engine page is not shared conceptually. |
| `/admin/games/mines` | reference | Rich master/variant engine management. |
| `/admin/games/boxe` | red | Flat "Other engines" list with only Open detail. |
| BOXE title detail tabs | partial/green-major | Many tabs exist, but field depth and workflow gaps remain. |
| BOXE Theme | red/partial | Missing Mines advanced skin/title presentation/skin assets depth. |
| BOXE locale/copy/rules admin | partial | Content improved, but interaction model still diverges. |
| Save draft workflow | red investigation | Michele reported Mines save draft behaves like publish/live. |

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
| WP7-A Admin Engine Page Parity | not started | - | - | First implementation target. |
| WP7-B Theme Advanced Skin And Title Presentation | not started | - | - | Michele explicitly flagged BOXE Theme as poorer than Mines. |
| WP7-C Locale/Copy/Rules Admin Unification | not started | - | - | Content may be mostly ready; interaction model still needs parity check. |
| WP7-D Save Draft Workflow | not started | - | - | Reproduce before fixing. |
| WP7-E Diagnostics/Admin Access | not started | - | - | Smaller closure pass. |
| Final Surface 10 closure | not started | - | - | Cannot be green until all blockers above close or are explicitly excepted. |

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
