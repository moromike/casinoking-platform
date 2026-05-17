Status: COMPLETED
Last meaningful update: 2026-05-17

# Recovery Capability Reconciliation - 2026-05-16

## Status

- Type: audit report.
- Branch: `audit/recovery-capability-reconciliation`.
- Baseline main: `42cbdc4 merge: boot 2a6 platform shell`.
- Reference checkpoint: `checkpoint/local-worktree-2026-05-14`.
- Scope: audit and report only.
- No code fixes are included in this work package.

## Executive Summary

Michele's concern is valid: the previous recovery based on file and hunk diffs
did not prove that every user-facing capability was restored end to end.

The concrete symptom is the `game_card` lobby asset capability. On current
`main`, the backend asset registry still accepts `game_card`, and the migration
and asset-registry tests exist. However, the operator cannot manage the card in
the Title detail, `/games/library` does not return the card asset, and the
player lobby does not render it.

Root cause: the recovery was classified by files/hunks instead of by complete
capability chains.

From this audit, the confirmed high-impact partial regression is:

- `game_card` lobby asset upload/delete/preview + `/games/library` payload +
  player lobby render.

The second partial regression candidate is:

- Theme editor load gate / compact empty state. The editor shows default
  editable controls even when the theme state is not loaded.

The rest of the audited areas are either complete on `main`, intentionally
skipped product work, obsolete/replaced by BOOT-2A, or require CTO product
decision.

## Method

The audit used the direct comparison:

```powershell
git diff main..checkpoint/local-worktree-2026-05-14
```

This matters. `main...checkpoint/local-worktree-2026-05-14` compares the
checkpoint against the merge-base and produces many false positives after the
recovery and BOOT-2A merges.

Each capability was checked as a chain:

```text
DB / migration
Backend service
API payload
Admin UI
Player UI or runtime UI
CSS/layout
Tests
Docs
```

Statuses:

- `COMPLETE_ON_MAIN`: capability exists end to end on current `main`.
- `INTENTIONALLY_SKIPPED`: not implemented by decision or still plan-only.
- `PARTIAL_REGRESSION`: capability is present only in fragments and is not
  usable end to end.
- `OBSOLETE_REPLACED`: checkpoint implementation was replaced by a newer
  approved architecture.
- `NEEDS_CTO_DECISION`: not a safe automatic recovery because it changes product
  behavior or crosses boundaries.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Origine | Stato | Sforzo | Impatto | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game_card` lobby asset upload/delete/preview + render lobby | Partial OK | Partial OK | Missing | Missing | Missing | Missing | Partial | Overclaims | checkpoint + pre-cp observed by Michele | PARTIAL_REGRESSION | M | alto | Backend asset registry and migration exist, but the operator/player capability is broken. See detailed example below. |
| Site/Lobby `Open title assets` bridge | n/a | n/a | n/a | Partial | n/a | OK | No dedicated test | Partial | checkpoint | PARTIAL_REGRESSION | S | medio | The bridge exists, but it points to a Title assets area that no longer exposes `game_card`. This should be fixed together with `game_card`. |
| Theme editor load gate / compact empty state | n/a | n/a | n/a | Partial | n/a | Partial | No dedicated test | Missing | checkpoint / PR-4 intent | PARTIAL_REGRESSION | S | medio | Current UI shows `Theme not loaded` but still renders editable default controls. Risk: operator edits from fallback tokens before real load. |
| Site homepage slots + `homepage_banner` | OK | OK | OK | OK | OK | OK | OK | OK | pre-cp/checkpoint | COMPLETE_ON_MAIN | - | medio | `site_home_slots` and `site_assets.homepage_banner` are present; admin upload/select/delete and player hero render are present. |
| Site/Lobby publication: visible/hidden, demo/real, featured, order, title/description | OK | OK | OK | OK | OK | OK | OK | OK | pre-cp/checkpoint | COMPLETE_ON_MAIN | - | alto | Residual diffs are mostly English copy versus checkpoint Italian copy. |
| Game title archive/restore + Active/Inactive/Archived/All/Test filters | OK | OK | OK | OK | OK | OK | OK | OK | checkpoint | COMPLETE_ON_MAIN | - | alto | Backend/admin/site/lobby/access-session protections align with recovery. |
| Finance drilldown read-only | n/a | OK | OK | OK | n/a | OK | OK | OK | checkpoint `a24912b` | COMPLETE_ON_MAIN | - | alto | Round detail, `platform_round_id`, ledger transaction references and read-only UI exist; no wallet/ledger mutation detected. |
| Local admin bootstrap protection | n/a | OK | n/a | n/a | n/a | n/a | OK | OK | checkpoint | COMPLETE_ON_MAIN | - | medio | `admin@example.com` protected; technical bootstrap uses `codex.agent@example.com`. |
| Admin login invalid credentials visible error | n/a | OK | OK | OK | n/a | OK | OK | n/a | post-checkpoint hotfix | COMPLETE_ON_MAIN | - | alto | Main is ahead of checkpoint; visible invalid-credentials error exists. |
| Board assets safe/mine upload/delete/preview | OK | OK | OK | OK | OK | OK | OK | OK | pre-cp/main | COMPLETE_ON_MAIN | - | alto | `symbol_safe`, `symbol_mine`, Board assets editor and runtime board are present. |
| Runtime sound assets per Title | OK | OK | OK | OK | OK | OK | OK | OK | checkpoint/main | COMPLETE_ON_MAIN | - | medio | Runtime audio kinds, Sounds editor and `useMinesSounds` are present. |
| Theme tokens draft/publish + WCAG gate | OK | OK | OK | OK | OK | OK | OK | OK | checkpoint/main | COMPLETE_ON_MAIN | - | alto | Backend validation, admin save/publish and runtime theme resolution are present. |
| MSK skin assets: `title_logo`, `game_area_background`, `cell_face_down_background` | OK | OK | OK | OK | OK | OK | OK | OK | checkpoint/main | COMPLETE_ON_MAIN | - | medio | Functional chain complete. Effective caps are `title_logo` 150 KB, `game_area_background` 400 KB, `cell_face_down_background` 256 KB. |
| Closed cell background dominance | Theme JSON | OK | OK | OK | OK | OK | Partial | Partial | post-checkpoint hotfix | COMPLETE_ON_MAIN | - | medio | Added after checkpoint and present on main. Not a recovery regression. |
| Copy i18n + published locale + Rules HTML | OK | OK | OK | OK | OK | OK | OK | OK | pre-cp/main | COMPLETE_ON_MAIN | - | alto | Editor, published locale and runtime single-locale chain are present. |
| Grid & mines config draft/publish | OK | OK | OK | OK | OK | OK | OK | OK | pre-cp/main | COMPLETE_ON_MAIN | - | alto | Config chain complete; numeric helper list remains removed as intended. |
| Demo / real labels legacy | OK | OK | OK | OK | OK | n/a | Partial | OK | pre-cp/main | COMPLETE_ON_MAIN | - | medio | Tab and config payload exist. No dedicated end-to-end test, but no capability break found. |
| Admin management / Player admin / Access log | n/a | n/a | n/a | OK | n/a | OK | Not required | n/a | checkpoint + EN copy | COMPLETE_ON_MAIN | - | basso | Residual diffs are English copy versus checkpoint Italian copy. |
| Player lobby direct Demo/Real launch buttons | OK | OK | OK | n/a | OK | OK | OK | OK | main current | COMPLETE_ON_MAIN | - | alto | Current main uses direct Demo/Real buttons. Checkpoint Launch Cashier is separate product work. |
| `wallet_source=real/bonus` hint support for Mines launch | n/a | OK | OK | n/a | Support only | n/a | OK | checkpoint/BOOT-2A | COMPLETE_ON_MAIN | - | medio | Runtime support exists; no current player-lobby caller because Launch Cashier is not on main. |
| Player lobby Launch Cashier modal | n/a | Existing APIs | Partial | n/a | checkpoint only | checkpoint only | checkpoint only | plan/checkpoint | checkpoint/pre-cp | NEEDS_CTO_DECISION | L | alto | Not an automatic recovery. It changes player launch UX, reads wallets and alters click flow. Keep separate from `game_card`. |
| `title_cashier` + `cta_preselect_mode` CTA model | No | No | No | No | No | No | No | plan-only | checkpoint docs | INTENTIONALLY_SKIPPED | L | medio | Plan-only in checkpoint docs. Not a regression. |
| Player lobby badges/category bar | No | No | No | No | No | No | No | plan-only | checkpoint docs | INTENTIONALLY_SKIPPED | M | basso/medio | Plan-only. Not an existing capability recovered incompletely. |
| Site Page Builder | No | No | No | No | No | No | No | plan-only | checkpoint docs | INTENTIONALLY_SKIPPED | L | medio | CMS/Page Builder remains suspended. It must not hide smaller atomically recoverable capabilities like `game_card`. |
| BOOT-2A checkpoint game-runtime files | Replaced | Replaced | Replaced | Replaced | Replaced | Replaced | Replaced | Updated | BOOT-2A.6 | OBSOLETE_REPLACED | - | alto | Current main has the approved `GameBootDecisionFlow` extraction; checkpoint older game-runtime diffs are not recovery targets. |

## Detailed Example: `game_card` Lobby Asset

### Expected Baseline

In `checkpoint/local-worktree-2026-05-14`, `game_card` was a Title-level
asset used by the player lobby card. It was not uploaded from Site/Lobby.
Site/Lobby only linked the operator back to the Title detail.

Expected operator path:

```text
Backoffice -> Games -> Mines -> Open detail -> Lobby card / Assets
```

Expected behavior:

- upload `game_card`;
- preview square card;
- delete/remove card;
- accept PNG/JPEG/WebP;
- reject non-square image;
- reject files above 300 KB;
- `/games/library` returns `game_card_asset`;
- player lobby card renders the uploaded image;
- if missing, player lobby uses the Mines fallback art.

### Current Main

Present on current `main`:

- `backend/app/modules/platform/asset_registry/service.py` supports
  `GAME_CARD_ASSET_KIND`.
- `backend/migrations/sql/0037__title_game_card_asset_kind.sql` and
  `0038__title_skin_asset_kinds.sql` allow `game_card`.
- `tests/integration/test_asset_registry.py` covers square/size validation.
- Docs mention `game_card`.

Missing on current `main`:

- `GameCardAssetEditor` in `frontend/app/ui/mines/mines-backoffice-editor.tsx`.
- Upload/delete handlers for `game_card`.
- Tab label `Lobby card / Assets`.
- `game_card_asset` join/serialization in
  `backend/app/modules/platform/catalog/library_service.py`.
- `game_card_asset` type/render in `frontend/app/ui/player-lobby-page.tsx`.
- CSS for `.game-card-asset-*` and `.player-lobby-card-art.has-game-card`.
- Admin/player smoke coverage for the end-to-end card path.

### Classification

`game_card` is a real `PARTIAL_REGRESSION`, not a generic MSK or Launch Cashier
feature.

Recommended fix WP:

```text
Branch: feature/recovery-game-card-lobby-asset
Scope:
- restore Title detail game_card upload/delete/preview;
- restore /games/library game_card_asset payload;
- restore player lobby image render and CSS;
- add targeted tests/smoke;
- do not restore Launch Cashier;
- do not touch wallet/ledger/RNG/payout/math.
```

## Triage Recommendations

1. **Fix first: `game_card` lobby asset.**
   - Status: confirmed partial regression.
   - Effort: M.
   - Impact: high.
   - Reason: operator-facing capability is broken and docs already claim the
     asset kind exists.

2. **Fix or decide: Theme editor load gate / empty state.**
   - Status: partial regression candidate.
   - Effort: S.
   - Impact: medium.
   - Reason: current editor can show editable fallback state while saying the
     theme is not loaded.

3. **Decide separately: Launch Cashier.**
   - Status: needs CTO product decision.
   - Effort: L.
   - Impact: high.
   - Reason: it changes player launch flow and should not be smuggled into the
     `game_card` fix.

4. **Docs cleanup: `title_logo` size cap.**
   - Status: closed on 2026-05-17.
   - Effort: S.
   - Impact: low/medium.
   - Reason: code uses `title_logo` 150 KB, `game_area_background` 400 KB and
     `cell_face_down_background` 256 KB. The scoped docs were re-audited and no
     remaining incorrect logo cap reference was found.

5. **Keep A2 Backoffice Manual deferred.**
   - The manual branch exists but should not merge until high-priority
     capability regressions are fixed or explicitly documented as pending.

## Process Rule Added

Any future recovery, migration, or cross-cutting refactor must close with a
capability reconciliation matrix. File diffs, line counts and technical tests
are not enough when a feature crosses DB, backend, admin UI, player UI, CSS,
tests and docs.

## Documents Read

Read for this audit:

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/ASSET_REGISTRY_PLAN.md`
- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`

Intentionally not treated as implementation authority:

- archived/superseded plans;
- checkpoint-only broad plans such as Site Page Builder or Launch Cashier,
  except to identify whether a small atomically recoverable capability was
  accidentally hidden inside them.
