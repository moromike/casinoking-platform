# Technical Cleanup Plan 01

## Executive Summary
This document serves as the architectural blueprint for executing the "Technical Cleanup" steps defined in `docs/NEXT_STEPS_2026_03_31.md`. The goal is to perform a safe removal of the legacy `game_sessions` table, incrementally modularize the oversized `globals.css`, and reorganize frontend helper utilities to improve codebase health. 

This plan strictly adheres to the guardrails defined in `docs/TASK_EXECUTION_GUARDRAILS.md` and maintains the systemic integrity established by `docs/SOURCE_OF_TRUTH.md`. No new functionality is introduced.

---

## 1. Database Cleanup: Dropping `game_sessions`

### Rationale
The `game_sessions` table data was split into `platform_rounds` and `mines_game_rounds` during migrations 0012/0013. A compatibility view (`game_sessions_compat`) was created to ease the transition. We will now drop both the compatibility view and the underlying table, cleaning up residual dependencies in the backend.

### Execution Steps
1. **Create SQL Migration (`backend/migrations/sql/0014__drop_game_sessions.sql`)**:
   ```sql
   -- CasinoKing Phase 4: Drop legacy game_sessions
   -- Scope of this migration:
   -- - Drop the game_sessions_compat view
   -- - Drop the legacy game_sessions table
   -- - Rename the fairness nonce sequence to detach it from the dropped table's name

   DROP VIEW IF EXISTS game_sessions_compat;
   DROP TABLE IF EXISTS game_sessions;
   ALTER SEQUENCE IF EXISTS game_sessions_nonce_seq RENAME TO mines_fairness_nonce_seq;
   ```

2. **Fix Legacy Migration Check (`backend/app/tools/apply_migrations.py`)**:
   - The `_looks_like_legacy_initialized_schema` function currently registers *all* available `.sql` files as applied if it detects a legacy DB.
   - **Action**: Update `_record_existing_migrations` or the calling logic so that it only marks migrations up to `0013__migrate_game_sessions_data.sql` as applied. This guarantees `0014__drop_game_sessions.sql` (and future migrations) actually run on legacy databases instead of being silently skipped.
   - **Action**: Remove `"game_sessions"` from the `required_tables` set in `_looks_like_legacy_initialized_schema()`, as it will no longer exist in newly initialized schemas. Note: We must ensure this function still correctly identifies legacy vs fresh databases without relying on `game_sessions` if possible, or gracefully handle schema detection.

3. **Update Python Code References**:
   - `backend/app/modules/games/mines/fairness.py`: Update `verify_session_fairness_for_admin` to query `mines_game_rounds mgr` JOIN `platform_rounds pr` ON `mgr.id = pr.id` instead of the legacy `game_sessions` table.
   - `backend/app/modules/games/mines/service.py`: Update `_get_next_fairness_nonce` to execute `SELECT nextval('mines_fairness_nonce_seq') AS nonce` instead of the old sequence name.
   - `backend/app/modules/platform/rounds/service.py`: Remove `"game_sessions_user_idempotency_key_key"` from the `MINES_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS` frozen set.

### Risks & Verification
- **Risks**: Modifying `apply_migrations.py` could break bootstrapping for fresh environments or legacy environments.
- **Testing Steps**: 
  - Run all backend integration tests (`pytest`).
  - Perform a fresh local bootstrap (`docker compose up --build backend`) to ensure `0014` applies cleanly and `schema_migrations` registers correctly.

---

## 2. CSS Modularization: `globals.css`

### Rationale
`frontend/app/globals.css` has grown to ~3,800 lines. The safest incremental approach without disrupting global scoping or rewriting to CSS modules is to split the file by domain context, retaining standard CSS imports at the global layout level.

### Execution Steps
1. **Create Dedicated Mines CSS File**:
   - Create `frontend/app/ui/mines/mines.css`.
2. **Extract Styles**:
   - Move all selectors prefixed with `.mines-`, `.board-`, `.payout-ladder-`, and `.legend-` out of `frontend/app/globals.css` and into `mines.css`.
3. **Import in Layout**:
   - In `frontend/app/layout.tsx`, add `import "./ui/mines/mines.css";` immediately after `import "./globals.css";`.

### Risks & Verification
- **Risks**: Minimal. As long as `mines.css` is imported directly in `layout.tsx`, the specificity and global scope of the classes remain identical to when they were in `globals.css`.
- **Testing Steps**: 
  - Visually inspect the CasinoKing console and the Mines embedded browser interface (`npm run dev`) to confirm that grid layouts, interactive board elements, and payout ladders look correct.
  - Run frontend smoke tests.

---

## 3. Helper Componentization: `helpers.ts`

### Rationale
`helpers.ts` contains shared domain formatting functions (e.g., currency, IDs) but is located in the UI folder and named after a specific component, which misrepresents its global utility.

### Execution Steps
1. **Rename File**: 
   - Move `frontend/app/lib/helpers.ts` into the neutral shared utility location.
2. **Update Imports Across Frontend Codebase**:
   - `frontend/app/ui/casinoking-console.tsx`: Update relative import to `../lib/helpers`.
   - `frontend/app/ui/mines/mines-backoffice-editor.tsx`: Update relative import to `../../lib/helpers`.
   - `frontend/app/ui/mines/mines-balance-footer.tsx`: Update relative import to `../../lib/helpers`.
   - `frontend/app/ui/mines/mines-standalone.tsx`: Update relative import to `../../lib/helpers`.
   - `frontend/app/lib/api.ts`: Update alias import from `@/app/lib/helpers`.
3. **Update Documentation References**:
   - `frontend/app/lib/types.ts`: Update the JSDoc/comment referring to `helpers.ts`.

### Risks & Verification
- **Risks**: Missing an import path resulting in Next.js build failures.
- **Testing Steps**:
  - Run `npm run build` in the frontend directory to ensure the TypeScript compiler correctly resolves all updated import paths.

---

## Final Checklist Before Implementation (Guardrails)
- [x] Does this touch the financial ledger logic? **No.**
- [x] Does this change Mines math or payout data? **No.**
- [x] Does this change API contract schemas? **No.**
- [x] Are the CSS extractions pure and incremental? **Yes.**

The blueprint is finalized. Ready for Code Mode execution.
