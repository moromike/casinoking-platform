# APPROVED WITH CHANGES

## Review Scope

Independent peer review of [`docs/TECHNICAL_CLEANUP_PLAN_01.md`](docs/TECHNICAL_CLEANUP_PLAN_01.md:1), with focus on database cleanup, CSS modularization, and helper renaming.

## Overall Assessment

The cleanup direction is reasonable, but the plan is not safe to execute exactly as written. The highest-risk gaps are in the database section: the proposed drop is premature, the migration-backfill fix in [`apply_migrations.py`](backend/app/tools/apply_migrations.py:14) is not robust enough for legacy-schema edge cases, and one SQL join recommendation is incorrect for the current target schema.

---

## 1. Database Cleanup Review

### Status

Conditionally acceptable only after corrections. Not safe as currently specified.

### Findings

1. **Dropping [`game_sessions`](backend/migrations/sql/0005__game_sessions_foundations.sql:20) is not yet safe because direct references still exist outside the three code changes listed in the plan.**

   The plan correctly updates [`fairness.py`](backend/app/modules/games/mines/fairness.py:66), [`service.py`](backend/app/modules/games/mines/service.py:881), and [`platform/rounds/service.py`](backend/app/modules/platform/rounds/service.py:9), but it misses remaining direct reads from [`game_sessions`](backend/migrations/sql/0005__game_sessions_foundations.sql:20) in tests and fixtures, including:

   - [`tests/conftest.py`](tests/conftest.py:305)
   - [`tests/integration/test_financial_and_mines_flows.py`](tests/integration/test_financial_and_mines_flows.py:612)
   - [`tests/integration/test_financial_and_mines_flows.py`](tests/integration/test_financial_and_mines_flows.py:701)
   - [`tests/integration/test_mines_fairness_seeded.py`](tests/integration/test_mines_fairness_seeded.py:54)
   - [`tests/concurrency/test_mines_concurrency.py`](tests/concurrency/test_mines_concurrency.py:40)
   - [`tests/concurrency/test_mines_concurrency.py`](tests/concurrency/test_mines_concurrency.py:98)
   - [`tests/concurrency/test_mines_concurrency.py`](tests/concurrency/test_mines_concurrency.py:302)
   - [`tests/concurrency/test_mines_concurrency.py`](tests/concurrency/test_mines_concurrency.py:395)
   - [`tests/concurrency/test_mines_concurrency.py`](tests/concurrency/test_mines_concurrency.py:502)

   This matters because [`docs/NEXT_STEPS_2026_03_31.md`](docs/NEXT_STEPS_2026_03_31.md:38) explicitly says to drop the table only after verifying that no code uses it directly.

2. **The proposed join for fairness verification is wrong for the target schema.**

   The plan says to join [`mines_game_rounds`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:49) to [`platform_rounds`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:14) using `mgr.id = pr.id` in [`docs/TECHNICAL_CLEANUP_PLAN_01.md`](docs/TECHNICAL_CLEANUP_PLAN_01.md:35). That works only because migration [`0013__migrate_game_sessions_data.sql`](backend/migrations/sql/0013__migrate_game_sessions_data.sql:31) currently copies the same UUID into both columns.

   The schema contract is actually `mgr.platform_round_id -> pr.id`, as shown in [`0012__schema_split_platform_rounds.sql`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:51) and already used elsewhere in [`backend/app/modules/games/mines/service.py`](backend/app/modules/games/mines/service.py:176). The review recommendation is:

   - use `JOIN platform_rounds pr ON pr.id = mgr.platform_round_id`
   - do **not** encode the current 1:1 UUID coincidence as the long-term join rule

3. **The [`apply_migrations.py`](backend/app/tools/apply_migrations.py:14) fix is directionally correct but not robust enough against legacy edge cases.**

   The current issue is real: when no rows exist in [`schema_migrations`](backend/app/tools/apply_migrations.py:11), the script detects a “legacy initialized schema” and backfills **all** known migrations via [`_record_existing_migrations()`](backend/app/tools/apply_migrations.py:120), then skips execution of every SQL file because [`applied_names`](backend/app/tools/apply_migrations.py:22) is replaced with the full migration list at [`apply_migrations.py`](backend/app/tools/apply_migrations.py:24).

   However, the planned correction is still incomplete:

   - Simply removing `"game_sessions"` from [`required_tables`](backend/app/tools/apply_migrations.py:78) weakens legacy detection.
   - A pre-split database could be misclassified and incorrectly skip migrations [`0012__schema_split_platform_rounds.sql`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:1) and [`0013__migrate_game_sessions_data.sql`](backend/migrations/sql/0013__migrate_game_sessions_data.sql:1).
   - A post-split database with missing [`schema_migrations`](backend/app/tools/apply_migrations.py:11) could also be misclassified and re-enter the wrong backfill path.

   The safer approach is to make legacy detection **version-aware** and fail closed:

   - detect the exact known schema shape you want to backfill
   - backfill only the precise migration range that matches that shape
   - if the schema shape is ambiguous or partially migrated, abort instead of guessing

   In practice, the detection should distinguish at least:

   - pre-split legacy baseline
   - post-split / post-data-migration baseline
   - fresh empty database
   - partially migrated or inconsistent database

4. **The plan omits required test changes for the migration bootstrap logic.**

   Existing unit tests in [`tests/unit/test_apply_migrations.py`](tests/unit/test_apply_migrations.py:65) and [`tests/unit/test_apply_migrations.py`](tests/unit/test_apply_migrations.py:87) encode the old behavior and old legacy-table set. They must be updated to cover:

   - cutoff behavior at migration `0013`
   - behavior when [`game_sessions`](backend/migrations/sql/0005__game_sessions_foundations.sql:20) is absent
   - behavior for ambiguous/partial legacy schemas

5. **There is a type mismatch worth acknowledging around the nonce sequence.**

   The sequence created in [`0007__mines_fairness_seed_internal.sql`](backend/migrations/sql/0007__mines_fairness_seed_internal.sql:19) is `bigint`, while [`mines_game_rounds.nonce`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:61) is `integer`. Renaming the sequence is fine, but the cleanup plan should at least note that the legacy type mismatch remains and may deserve follow-up normalization.

### Database Review Verdict

The database section should be treated as **approved only after the plan is amended** to:

- update all remaining direct [`game_sessions`](backend/migrations/sql/0005__game_sessions_foundations.sql:20) consumers, including tests
- correct the fairness join to `mgr.platform_round_id = pr.id`
- make legacy-schema detection in [`apply_migrations.py`](backend/app/tools/apply_migrations.py:14) version-aware or fail-closed
- extend migration unit tests accordingly

---

## 2. CSS Modularization Review

### Status

Conceptually valid, but the risk is understated and the extraction rule is too naive.

### Findings

1. **Importing a global Mines stylesheet in [`layout.tsx`](frontend/app/layout.tsx:1) is valid in Next.js, but the plan overstates cascade safety.**

   Importing [`./ui/mines/mines.css`](frontend/app/ui/mines/mines.css) after [`./globals.css`](frontend/app/layout.tsx:2) will preserve global scope, but it does **not** guarantee identical cascade behavior. Any moved rule now lands after all remaining rules in [`globals.css`](frontend/app/globals.css:1), so equal-specificity conflicts can resolve differently.

2. **The proposed prefix-based extraction misses Mines-related selectors that do not start with the listed prefixes.**

   Examples:

   - [`.page-shell.mines-page-shell-mobile`](frontend/app/globals.css:2152)
   - [`.page-shell.mines-page-shell-embedded`](frontend/app/globals.css:2192)

   These are Mines-specific selectors, but they would be skipped by a rule that only moves selectors prefixed with `.mines-`, `.board-`, `.payout-ladder-`, and `.legend-`.

3. **Some Mines selectors are mixed into shared grouped rules, so extraction is not a pure copy-paste operation.**

   Examples:

   - [`.auth-forms, .account-grid, .wallet-grid, .mines-grid, ...`](frontend/app/globals.css:713)
   - [`@media (max-width: 1080px) { .dashboard-grid, .hero-grid, .mines-grid, ... }`](frontend/app/globals.css:1989)

   If `.mines-grid` is pulled out of these groups, the declarations must be rewritten carefully. That changes source order and can alter the cascade.

4. **The safest extraction unit is a complete Mines-specific block, not a prefix grep.**

   This is especially important for:

   - grouped selectors
   - compound selectors
   - media-query overrides
   - stateful descendants such as [`frontend/app/globals.css`](frontend/app/globals.css:1344), [`frontend/app/globals.css`](frontend/app/globals.css:2075), and [`frontend/app/globals.css`](frontend/app/globals.css:3215)

### CSS Review Verdict

The CSS plan is **acceptable with one correction**: do not describe the extraction as cascade-neutral by default. The implementation should explicitly preserve order-sensitive Mines blocks and include compound selectors such as [`.page-shell.mines-page-shell-mobile`](frontend/app/globals.css:2152). A manual review of grouped selectors and media queries is mandatory.

---

## 3. Helper Renaming Review

### Status

Mostly correct for code imports, but incomplete for repository-wide references.

### Findings

1. **The identified runtime import sites are correct.**

   The plan correctly covers current code imports in:

   - [`frontend/app/ui/casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx:17)
   - [`frontend/app/ui/mines/mines-backoffice-editor.tsx`](frontend/app/ui/mines/mines-backoffice-editor.tsx:15)
   - [`frontend/app/ui/mines/mines-balance-footer.tsx`](frontend/app/ui/mines/mines-balance-footer.tsx:8)
   - [`frontend/app/ui/mines/mines-standalone.tsx`](frontend/app/ui/mines/mines-standalone.tsx:18)
   - [`frontend/app/lib/api.ts`](frontend/app/lib/api.ts:13)

2. **The documentation/comment update list is incomplete.**

   The plan mentions [`frontend/app/lib/types.ts`](frontend/app/lib/types.ts:1), which is correct, but there are additional repository references to the old filename, for example:

   - [`docs/PROJECT_STATUS_2026_03_30.md`](docs/PROJECT_STATUS_2026_03_30.md:46)
   - [`docs/MINES_EXECUTION_PLAN.md`](docs/MINES_EXECUTION_PLAN.md:573)

   These do not block the build, but a “complete” rename plan should either update them or explicitly scope them out.

3. **The rename should be verified with search, not only with the pre-listed files.**

   For this kind of move, the authoritative check is a repository-wide search for the old helper path after the rename, followed by a frontend build. The plan already includes [`npm run build`](frontend/package.json), which is good, but the search step should be stated explicitly.

### Helper Rename Review Verdict

The rename strategy is **functionally close to complete for runtime code**, but not fully complete for repository-wide references and verification discipline.

---

## Required Corrections Before Implementation

1. Amend the database plan so that the drop only happens after all direct [`game_sessions`](backend/migrations/sql/0005__game_sessions_foundations.sql:20) consumers are removed, including tests.
2. Fix the fairness query guidance to join on [`mgr.platform_round_id`](backend/migrations/sql/0012__schema_split_platform_rounds.sql:51), not `mgr.id`.
3. Replace the [`apply_migrations.py`](backend/app/tools/apply_migrations.py:14) proposal with a version-aware or fail-closed legacy-schema detection strategy.
4. Expand the CSS step to include compound/selective Mines rules such as [`.page-shell.mines-page-shell-mobile`](frontend/app/globals.css:2152) and grouped selectors involving [`.mines-grid`](frontend/app/globals.css:716).
5. Expand the helper rename checklist to include repo-wide search cleanup and any intentionally in-scope docs/comments.

## Final Status

**APPROVED WITH CHANGES** — the cleanup direction is sound, but the plan needs the corrections above before Code Mode should execute it.
