# Final Technical Cleanup Roadmap
*Approved by Architect, Code, and Opus 4.6 (Ask) modes.*

This document serves as the exact execution plan for the Technical Cleanup phase, incorporating all required safety corrections from the peer reviews.

## Execution Order

As recommended by the Opus 4.6 validation, development should proceed in order of increasing risk:

### Phase 1: Helper Componentization (Lowest Risk)
**Goal:** Rename the shared helper file to `helpers.ts` and fix all references.

1. **Rename File**: 
   - Move the shared helper implementation to `frontend/app/lib/helpers.ts`.
2. **Update Runtime Imports**:
   - `frontend/app/ui/casinoking-console.tsx`
   - `frontend/app/ui/mines/mines-backoffice-editor.tsx`
   - `frontend/app/ui/mines/mines-balance-footer.tsx`
   - `frontend/app/ui/mines/mines-standalone.tsx`
   - `frontend/app/lib/api.ts`
3. **Repository-wide Cleanup**:
   - Run a global search for the old helper path and update doc blocks/markdown files (e.g., `frontend/app/lib/types.ts`, `docs/PROJECT_STATUS_2026_03_30.md`, `docs/MINES_EXECUTION_PLAN.md`).
4. **Verification**:
   - Run `npm run build` in `frontend/`.

---

### Phase 2: CSS Modularization (Medium Risk)
**Goal:** Extract Mines-specific styles from the 3800-line `globals.css` without breaking the global cascade.

1. **Create Target File**:
   - `frontend/app/ui/mines/mines.css`
2. **Surgical Extraction (Two-Pass Method)**:
   - *Pass 1 (Safe bulk):* Move pure Mines blocks (e.g., `.mines-container`, `.payout-ladder-item`, `.legend-box`).
   - *Pass 2 (Compound/Grouped selectors):* Carefully extract or duplicate logic for compound selectors like `.page-shell.mines-page-shell-mobile` and grouped classes like `.wallet-grid, .mines-grid`. Do NOT use a naive prefix grep.
3. **Integration**:
   - Import in `frontend/app/layout.tsx`: `import "./ui/mines/mines.css";` (below globals.css).
4. **Verification**:
   - Visual regression testing on Desktop, Mobile, and Embedded views.

---

### Phase 3: Database Cleanup (Highest Risk)
**Goal:** Drop the legacy `game_sessions` table safely.

1. **Pre-requisite: Fix Tests**:
   - 11 occurrences in tests still query `game_sessions` directly (e.g., `conftest.py`, `test_financial_and_mines_flows.py`, `test_mines_concurrency.py`). Rewrite these to query `mines_game_rounds` and `platform_rounds`. This is **mandatory** before dropping the table.
2. **Update Backend Logic**:
   - `fairness.py`: Update `verify_session_fairness_for_admin` to join `mines_game_rounds mgr` with `platform_rounds pr` using `mgr.platform_round_id = pr.id` (do NOT use `mgr.id = pr.id`).
   - `service.py`: Update `_get_next_fairness_nonce` to use the new sequence name `mines_fairness_nonce_seq`.
   - `rounds/service.py`: Remove `"game_sessions_user_idempotency_key_key"` from `MINES_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS`.
3. **Fix Legacy Migration Detection**:
   - In `backend/app/tools/apply_migrations.py`, update `_looks_like_legacy_initialized_schema()` to be **version-aware** and fail-closed. It must not rely purely on the absence of `game_sessions` to trigger a backfill, otherwise post-migration drops will break it.
4. **Create SQL Migration (`0014__drop_game_sessions.sql`)**:
   ```sql
   DROP VIEW IF EXISTS game_sessions_compat;
   DROP TABLE IF EXISTS game_sessions;
   ALTER SEQUENCE IF EXISTS game_sessions_nonce_seq RENAME TO mines_fairness_nonce_seq;
   ```
5. **Verification**:
   - Run `pytest tests/` and confirm all backend integration tests pass.
   - Run `docker compose up --build backend` on a fresh schema to ensure `0014` applies cleanly.
