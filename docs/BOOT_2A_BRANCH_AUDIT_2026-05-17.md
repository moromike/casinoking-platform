Status: ACTIVE
Last meaningful update: 2026-05-17

# BOOT-2A Branch Audit - 2026-05-17

## Premessa

Audit branch: `audit/boot-2a-branch-reconciliation`

Requested branch: `feature/boot-2a-4b-gameplay-rest`

Requested branch HEAD: `d96d10b feat: complete BOOT-2A.4b gameplay extraction`

Current comparison main HEAD: `010026d merge: design session recovery engine`

Important finding: the requested branch ref no longer exists locally or on
`origin`. The commit `d96d10b` still exists and is already contained in current
`main`. Reflog shows it was merged into `main` on 2026-05-15 by merge commit
`0a54714 merge: BOOT-2A.4b gameplay extraction`.

Current merge-base between `main` and `d96d10b`: `d96d10b`.

Reconstructed original branch base from reflog: `49c1727 merge: BOOT-2A.4a
Mines gameplay board`.

Therefore, there is no currently available branch-only work to merge from
`feature/boot-2a-4b-gameplay-rest`. The meaningful audit range for the historical
BOOT-2A.4b work is `49c1727..d96d10b`.

## Commit On Historical Branch Not In Its Reconstructed Base

| SHA | Date | Subject |
| --- | --- | --- |
| `d96d10b` | 2026-05-15 | feat: complete BOOT-2A.4b gameplay extraction |

Commits on requested branch not on current `main`: none. `d96d10b` is already an
ancestor of `main`.

## Files Changed In Historical BOOT-2A.4b Range

Range: `49c1727..d96d10b`

### Backend

No backend files changed.

### Frontend

| File | Added | Removed | Notes |
| --- | ---: | ---: | --- |
| `frontend/app/ui/game-runtime/game-boot-log.ts` | 0 | 16 | Removed development `bootLog` helper. |
| `frontend/app/ui/mines/mines-gameplay.tsx` | 549 | 42 | Extracted gameplay surface from `MinesStandalone`. |
| `frontend/app/ui/mines/mines-standalone.tsx` | 91 | 574 | Reduced wrapper/orchestration file and delegated board/gameplay UI. |
| `frontend/app/ui/mines/types.ts` | 24 | 0 | Added local Mines types for gameplay boundary. |

### Tests

| File | Added | Removed | Notes |
| --- | ---: | ---: | --- |
| `tests/fixtures/boot-2a/bootlog-baseline.json` | 0 | 13 | Removed boot log baseline fixture. |
| `tests/integration/test_mines_embed_browser_smoke.py` | 223 | 206 | Removed boot log baseline test and adjusted boot/browser smoke coverage. |

### Docs

No docs files changed in `d96d10b`.

## Capability Matrix

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status sul branch | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mines gameplay component boundary | n/a | n/a | n/a | n/a | REFACTORED | n/a | UPDATED | n/a | REFACTORED | `MinesGameplay` becomes the extracted player surface; `MinesStandalone` keeps orchestration. |
| Mines standalone wrapper/orchestration | n/a | n/a | n/a | n/a | REFACTORED | n/a | UPDATED | n/a | REFACTORED | Large reduction in `mines-standalone.tsx`; API/session/token orchestration remains wrapper-side. |
| Local Mines type boundary | n/a | n/a | n/a | n/a | TOUCHED_ONLY | n/a | n/a | n/a | TOUCHED_ONLY | `frontend/app/ui/mines/types.ts` adds local types used by the gameplay boundary. |
| BOOT-2A development boot log | n/a | n/a | n/a | n/a | TOUCHED_ONLY | n/a | REMOVED | n/a | REFACTORED | Removes `game-boot-log.ts`, baseline fixture, and boot log baseline test. |
| Browser boot smoke coverage | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | n/a | EXTENDED | Smoke file adjusted after boot log removal and gameplay extraction. |

No wallet, ledger, RNG, payout, fairness, or math files are touched by the
historical range.

## BOOT-2A.6 Verification

The four components cited in CTO memory are not present in `d96d10b`.

| Component | Present in `d96d10b`? | Present in current `main`? | Location / Notes |
| --- | --- | --- | --- |
| `GameBootDecisionFlow` | No | Yes | `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx`, added by `4803317 feat(runtime): extract boot decision flow`. |
| `GameProviderIntroGate` | No | Yes | Same file, added by `4803317`. |
| `GameHowToPlayGate` | No | Yes | Same file, added by `4803317`. |
| `GameTableBalanceGate` | No | Yes | Same file, added by `4803317`. |

Conclusion: `d96d10b` is BOOT-2A.4b gameplay extraction, not BOOT-2A.6 platform
decision-flow extraction. BOOT-2A.6 is already on current `main` through
`4803317` and merge commit `42cbdc4 merge: boot 2a6 platform shell`.

## Test Status On Historical Commit

Tests were executed from a detached worktree at `d96d10b` so the audit branch was
not modified.

| Command | Result | Notes |
| --- | --- | --- |
| `python -m pytest tests/unit tests/contract -q` | TIMEOUT after 20 minutes | No useful assertion output before timeout. |
| `python -m pytest tests/contract -q` | TIMEOUT after 5 minutes | Contract-only also did not complete. |
| `python -m pytest tests/unit -q` | TIMEOUT after 5 minutes | Unit-only also did not complete. |
| `python -m pytest tests/integration/test_mines_embed_browser_smoke.py -k "test_boot_" -q` | TIMEOUT after 20 minutes | Docker was rebuilt to `d96d10b` first; no code was changed. |

After the historical boot-smoke attempt, Docker was rebuilt back to current
`main` so localhost does not remain on the detached historical commit.

Interpretation: the historical commit is not reliably testable with the current
local test environment without further investigation. This audit does not
attempt to fix or adapt those tests.

## Rebase Risk

Because `d96d10b` is already merged into `main`, a literal rebase/merge of the
requested branch is not applicable. If someone attempted to replay or reapply
the historical diff onto current `main`, risk would be high for the files below.

| File | Changed after `d96d10b` on `main`? | Conflict probability | Reason |
| --- | --- | --- | --- |
| `frontend/app/ui/mines/mines-standalone.tsx` | Yes, 5 relevant commits | High | Later changes include BOOT-2A.6 decision flow, MSK V2 skin, viewport/diamond fixes, resume variant title, and cleanup. |
| `frontend/app/ui/mines/mines-gameplay.tsx` | Yes, 4 relevant commits | High | Later changes include MSK V2 skin, replay/rules modal sizing, cell background dominance, and short viewport gate. |
| `tests/integration/test_mines_embed_browser_smoke.py` | Yes, 11 relevant commits | High | Later smoke modernization, mobile gate, resume variant, and real-mode safety tests would be overwritten by old test structure. |
| `frontend/app/ui/mines/types.ts` | No | Low | Historical local type file remains compatible as already merged. |
| `frontend/app/ui/game-runtime/game-boot-log.ts` | No, remains removed | Low | Removal already reflected on current main. |
| `tests/fixtures/boot-2a/bootlog-baseline.json` | No, remains removed | Low | Removal already reflected on current main. |

Overall rebase risk for reapplying the historical diff: High. Overall merge need:
none, because the commit is already in current history.

## Capability Regression Risk

If the historical BOOT-2A.4b files were reapplied wholesale over current `main`,
these STABLE capabilities could regress:

| Main capability | Risk | Why |
| --- | --- | --- |
| `GameBootDecisionFlow` / `GameProviderIntroGate` / `GameHowToPlayGate` / `GameTableBalanceGate` | High | `d96d10b` predates these components; old `MinesStandalone` does not represent the final BOOT-2A.6 boundary. |
| Mines skin advanced V2 | High | Later skin asset/runtime work touched `mines-gameplay.tsx` and `mines-standalone.tsx`. |
| Mines skinned cells + rules/replay modal sizing | High | Later hotfixes changed the same gameplay surface. |
| Mobile landscape-short viewport gate | High | Later `GameShortViewportGate` and tests touched gameplay/test files. |
| Resume session on variant title | High | Later backend/frontend/test changes depend on current runtime/session assumptions. |
| Launch Cashier and player lobby card flow | Medium | Runtime files are not directly touched by `d96d10b`, but old smoke tests would under-cover the restored Launch Cashier flow. |
| Legacy browser smoke tests | High | Current main has 38 green smoke tests; historical tests time out locally and lack the latest selector/access-session modernization. |

## Gap Analysis

Functional BOOT-2A.4b gap: none identified as unmerged. The historical gameplay
extraction commit is already on `main`.

BOOT-2A.6 gap: not in `d96d10b`, but present on current `main` via `4803317` and
`42cbdc4`. The product-owner confusion is therefore explained by mixed memory:
BOOT-2A.4b and BOOT-2A.6 were separate WPs.

Open risk: the historical commit cannot be used as a clean test reference today
because unit, contract, and boot smoke commands time out from the detached
worktree. Current main, however, already has later green smoke history after
SMOKE-1/2/3.

## Recommended Merge Strategy

| Option | Pros | Cons | Recommendation |
| --- | --- | --- | --- |
| A. Rebase clean + single PR | Simple when a branch has unmerged work. | Not applicable: branch ref is gone and `d96d10b` is already on `main`; replaying old diff risks regressions. | Do not use. |
| B. Split in sub-PR by area | Useful when there is live unmerged work across runtime/mines/tests/docs. | No live branch-only work found; would manufacture work from historical commits. | Do not use. |
| C. Cherry-pick selective / no-op for obsolete commits | Safest when the historical branch is already merged and later commits supersede pieces. | Requires discipline not to reapply old files wholesale. | Recommended: no merge from this branch. Treat `d96d10b` as historical and use current `main` BOOT-2A.6 (`4803317/42cbdc4`) as the platform-shell source. |

Recommended path: choose Option C as a no-op merge decision. Do not rebase or
cherry-pick `d96d10b`; it is already in history and later main commits are the
authoritative state.

## Post-Merge Testing Required If CTO Still Reopens BOOT-2A Files

If any BOOT-2A files are touched again despite this audit, run at minimum:

- `npm --prefix frontend run build`
- `python -m pytest tests/contract/test_game_runtime_frontend_boundary.py -q`
- `python -m pytest tests/integration/test_mines_embed_browser_smoke.py -q`
- `python -m pytest tests/integration/test_mines_skin_visual_regression.py -q`
- Targeted resume variant title test from RESUME-FIX-1
- Targeted mobile short viewport gate tests from WP-SMOKE-2
- Targeted real-mode access-session safety tests from WP-SMOKE-3
- Manual player checks: Launch Cashier, lobby game card, rules/replay modal,
  skinned cells, mobile portrait, landscape-short gate.

## Documentation And Memory Updates Needed

- Record that `feature/boot-2a-4b-gameplay-rest` was already merged as
  `0a54714`, with `d96d10b` as the feature commit.
- Record that BOOT-2A.6 platform decision flow is not part of `d96d10b`; it is
  `4803317` / merge `42cbdc4` on current main.
- Keep `docs/CAPABILITY_INVENTORY_2026-05-17.md` as the active capability map;
  it already lists the BOOT-2A.6 Gate components as STABLE on main.
- No update to wallet/ledger/RNG/payout/fairness/math documentation is required
  because the audited range does not touch those areas.

