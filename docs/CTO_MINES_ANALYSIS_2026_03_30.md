# CasinoKing — CTO / Principal Engineer Analysis: MINES

**Date:** 2026-03-30
**Scope:** Deep analysis of the Mines game product within the CasinoKing platform
**Method:** Full documentation review + complete source code audit

---

## 1. Executive Summary

The CasinoKing project has **solid backend foundations** and a **well-documented architectural vision**, but is currently in a transitional state between a monolithic implementation and the target separated-product architecture. The Mines game — the first and only game product — works end-to-end with server-authoritative gameplay, provably fair RNG, double-entry ledger accounting, and idempotent financial operations.

**The good news:** The mathematical core, financial model, fairness system, and API contract are production-grade in quality. The backend boundary separation (platform vs. game) has already begun with [`round_gateway.py`](backend/app/modules/games/mines/round_gateway.py) and [`platform/rounds/service.py`](backend/app/modules/platform/rounds/service.py).

**The bad news:** The frontend is the project's weakest point. [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) is a 5,329-line monolith containing the entire platform UI (lobby, auth, account, admin backoffice, and legacy Mines views). [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx) at ~1,148 lines still mixes desktop, mobile, and embedded concerns in a single file. The CSS at 3,732 lines contains extensive `display: none !important` overrides to hide legacy elements — a clear sign of accumulated visual debt.

**Bottom line:** This project is recoverable without a rewrite. The backend needs incremental boundary refinement; the frontend needs disciplined decomposition. The biggest risk is not technical debt — it is regression from large, cross-cutting frontend patches.

---

## 2. What Is Already Solid

### 2.1 Mines Mathematical Core

The payout runtime is loaded from the official canonical file and cached correctly:

- [`runtime.py`](backend/app/modules/games/mines/runtime.py:46) — `get_payout_table()` uses `@lru_cache(maxsize=1)`, loads from `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json`, parses with `Decimal` precision. This is exactly right.
- [`runtime.py:31`](backend/app/modules/games/mines/runtime.py:31) — `get_multiplier()` does a clean table lookup by `grid_size`, `mine_count`, `safe_reveals_count`.
- [`runtime.py:41`](backend/app/modules/games/mines/runtime.py:41) — `supports_configuration()` validates against the canonical table.

### 2.2 Fairness & Randomness

The fairness system is well-implemented and auditable:

- [`randomness.py`](backend/app/modules/games/mines/randomness.py) — Deterministic board generation using SHA-256 hashing of `{fairness_version, grid_size, mine_count, nonce, server_seed}`. The algorithm is reproducible and verifiable.
- [`fairness.py:22`](backend/app/modules/games/mines/fairness.py:22) — `create_fairness_artifacts()` correctly generates mine positions, RNG material, and board hash within the same transaction.
- [`fairness.py:66`](backend/app/modules/games/mines/fairness.py:66) — `verify_session_fairness_for_admin()` provides full re-computation and comparison of stored vs. computed hashes.
- [`fairness.py:142`](backend/app/modules/games/mines/fairness.py:142) — Seed rotation with idempotency, proper `FOR UPDATE` locking, and retirement tracking.

### 2.3 Financial Model (Double-Entry Ledger)

The financial core follows the documented model faithfully:

- [`platform/rounds/service.py:42`](backend/app/modules/platform/rounds/service.py:42) — `open_mines_round()` performs balance check with `FOR UPDATE`, creates `ledger_transactions` + `ledger_entries` (debit player, credit house), and updates `wallet_accounts.balance_snapshot` — all in one transaction.
- [`platform/rounds/service.py:265`](backend/app/modules/platform/rounds/service.py:265) — `settle_mines_round_win()` handles the reverse flow with idempotency check via `get_existing_round_win_by_key()`.
- [`platform/rounds/service.py:204`](backend/app/modules/platform/rounds/service.py:204) — `settle_mines_round_loss()` validates that no win transaction already exists before confirming loss.

### 2.4 Idempotency

Idempotency is handled correctly across all financially sensitive operations:

- Namespaced idempotency keys: `mines:start:{user_id}:{key}`, `mines:cashout:{user_id}:{key}`
- Unique constraint detection via [`is_mines_round_open_idempotency_violation()`](backend/app/modules/platform/rounds/service.py:34) and [`is_mines_round_settlement_idempotency_violation()`](backend/app/modules/platform/rounds/service.py:38)
- Request fingerprinting in [`service.py:749`](backend/app/modules/games/mines/service.py:749) to detect payload mismatches on idempotent retries

### 2.5 Game Launch Token

The platform-to-game handoff token is implemented:

- [`game_launch/service.py:23`](backend/app/modules/platform/game_launch/service.py:23) — `issue_game_launch_token()` creates a JWT with `iss`, `aud`, `sub`, `platform_session_id`, `play_session_id`, `game_play_session_id`, `nonce`, and expiry.
- [`game_launch/service.py:61`](backend/app/modules/platform/game_launch/service.py:61) — `validate_game_launch_token()` verifies signature, audience, issuer, and token kind.
- The frontend [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx:1009) correctly uses `ensureGameLaunchToken()` to obtain and cache the token.

### 2.6 Round Gateway (Transitional Boundary)

- [`round_gateway.py`](backend/app/modules/games/mines/round_gateway.py) is a clean adapter that translates between Mines-domain exceptions and platform-domain exceptions. It delegates all financial operations to [`platform/rounds/service.py`](backend/app/modules/platform/rounds/service.py).
- This is the correct first step toward the seamless wallet model described in Document 31.

### 2.7 Board Component

- [`mines-board.tsx`](frontend/app/ui/mines-board.tsx) is a well-isolated, reusable component with clean props interface, no internal state, and proper accessibility labels. It supports custom board assets via data URLs.

### 2.8 Backoffice Config

- [`backoffice_config.py`](backend/app/modules/games/mines/backoffice_config.py) implements a proper draft/publish workflow with HTML sanitization, configuration validation against the runtime, and board asset support. The validation logic is thorough (grid size subset checks, mine count limits, default mine count membership).

### 2.9 Test Coverage

The test suite is comprehensive:
- Contract tests for API responses
- Concurrency tests for mines, fairness rotation, and admin operations
- Integration tests for financial flows, fairness verification, reconciliation
- Player session history and admin session drilldown tests

---

## 3. What Is Still Transitional / In-Progress

### 3.1 Backend: `service.py` Still Owns Game Session Table

[`service.py`](backend/app/modules/games/mines/service.py) correctly delegates financial operations to `round_gateway`, but still directly writes to `game_sessions` table (lines 94-151, 388-404, 438-458, 471-489, 571-579). In the target architecture, the game session record should be split:
- **Platform** owns the financial round record
- **Game** owns the technical game state

Today they are the same row in `game_sessions`.

### 3.2 Backend: `game_launch_token` Is Stateless Only

The token is a JWT validated by signature only ([`game_launch/service.py:61`](backend/app/modules/platform/game_launch/service.py:61)). Per Document 35, it needs:
- Consumption tracking (single-use or bounded-use)
- Revocation capability
- Persistence of the play session

Currently the token can be reused indefinitely until expiry.

### 3.3 Frontend: `mines-standalone.tsx` Is Too Large

At ~1,148 lines, this file contains:
- Desktop layout (lines 900-923)
- Mobile layout (lines 886-899)
- Embedded view detection (line 256)
- Game launch token management (lines 1009-1060)
- API client (lines 1062-1102)
- Demo mode flow (lines 431-463)
- All game state management (reveal, cashout, session loading)
- Rules modal (lines 925-971)
- Mobile settings sheet (lines 973-1002)
- Balance footer, action buttons, config fields, bet field — all inline

Document 35 recommends splitting into: `MinesStageHeader`, `MinesControlRailDesktop`, `MinesMobileSettingsSheet`, `MinesBalanceFooter`, `MinesActionButtons`, `MinesRulesModal`, `MinesBoard`.

### 3.4 Frontend: `casinoking-console.tsx` Is a 5,329-Line Monolith

This file contains the entire platform: lobby, login, register, account, admin backoffice (finance, players, games), Mines backoffice editor, and legacy Mines game views. It is the single biggest risk to the project because:
- Any change to admin can regress player views
- Any change to Mines backoffice can regress the lobby
- The file is too large for safe incremental patching

### 3.5 Frontend: CSS Uses `display: none !important` Extensively

[`globals.css:2093-2119`](frontend/app/globals.css:2093) contains blocks of `display: none` and `display: none !important` to hide legacy elements from the clean Mines product shell. This is a transitional workaround, not a target state.

### 3.6 Frontend: Duplicated API Client

Both [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx:317) and [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx:136) define their own `ApiRequestError` class and `apiRequest()` function. These should be extracted to a shared module.

### 3.7 Frontend: Duplicated Type Definitions

`SessionSnapshot`, `MinesRuntimeConfig`, `FairnessCurrentConfig`, and other types are defined independently in both files with slight variations.

---

## 4. Problem Classification

### 4.1 Architecture

| # | File(s) | Severity | Description |
|---|---------|----------|-------------|
| A1 | [`service.py`](backend/app/modules/games/mines/service.py) | **High** | Game service still writes directly to `game_sessions` table, mixing game-technical and platform-financial lifecycle in one row. Target: split into game-round state and platform-round record. |
| A2 | [`game_launch/service.py`](backend/app/modules/platform/game_launch/service.py) | **Medium** | Launch token is stateless JWT with no consumption tracking or revocation. Acceptable for MVP but not for production. |
| A3 | [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) | **Critical** | 5,329-line monolith containing all platform UI. Every patch is high-risk. Must be decomposed before any further feature work. |
| A4 | [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx) | **High** | 1,148 lines mixing desktop, mobile, embedded, demo mode, API client, and all game state. Needs component extraction per Document 35. |

### 4.2 Boundary

| # | File(s) | Severity | Description |
|---|---------|----------|-------------|
| B1 | [`service.py`](backend/app/modules/games/mines/service.py) | **High** | `start_session()` creates the `game_sessions` row including `wallet_account_id`, `start_ledger_transaction_id`, `wallet_balance_after_start` — these are platform concerns leaked into the game service. |
| B2 | [`mines.py`](backend/app/api/routes/mines.py:208) | **Medium** | Launch token issuance endpoint lives under `/games/mines/` but is a platform operation. Should eventually move to a platform route. |
| B3 | [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) | **High** | Mines backoffice editor lives inside the platform admin shell. The backoffice should be a separate Mines-domain component. |
| B4 | [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx) + [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) | **Medium** | Both files import from [`casinoking-console.helpers.ts`](frontend/app/ui/casinoking-console.helpers.ts), creating a dependency from the game product back to the platform shell helpers. |

### 4.3 Technical Debt

| # | File(s) | Severity | Description |
|---|---------|----------|-------------|
| D1 | [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx:136), [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx:317) | **Medium** | Duplicated `ApiRequestError` class and `apiRequest()` function. Should be extracted to shared module. |
| D2 | [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx:44), [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx:90) | **Medium** | Duplicated type definitions (`MinesRuntimeConfig`, `SessionSnapshot`, etc.) with slight variations. |
| D3 | [`globals.css:2093-2119`](frontend/app/globals.css:2093) | **Medium** | Extensive `display: none !important` blocks to hide legacy elements. Indicates incomplete separation. |
| D4 | [`backoffice_config.py:247`](backend/app/modules/games/mines/backoffice_config.py:247) | **Low** | `is_published_configuration_supported()` calls `get_public_backoffice_config()` which hits the database on every `start_session()`. Should be cached or checked less frequently. |
| D5 | [`fairness.py:237`](backend/app/modules/games/mines/fairness.py:237) | **Low** | `_get_or_create_active_seed()` uses f-string for SQL `FOR UPDATE` clause. While safe in this context (boolean-controlled), it is a pattern to avoid. |
| D6 | [`service.py:362`](backend/app/modules/games/mines/service.py:362) | **Low** | `reveal_cell()` opens a `db_connection()` context manager but the `return` on line 491 happens outside the `with` block for the safe-reveal-continue case. The connection is already committed by context manager exit, but the code structure is confusing. |

### 4.4 UX / Presentation

| # | File(s) | Severity | Description |
|---|---------|----------|-------------|
| U1 | [`mines-standalone.tsx:209-214`](frontend/app/ui/mines-standalone.tsx:209) | **High** | Win message "Hai vinto. X CHIP. Premi di nuovo Bet per la prossima mano." appears as `stageSubtitle` inside the stage header, pushing the MINES wordmark and payout preview chips down. This causes layout shift on win/loss. The message should be in a fixed-height notification area, not inline in the heading flow. |
| U2 | [`mines-standalone.tsx:833-845`](frontend/app/ui/mines-standalone.tsx:833) | **Medium** | Multiplier preview chips (e.g., 0.9531x, 0.982x) are rendered in a flex row that can wrap and overlap on narrow viewports. The `mines-payout-preview` container needs constrained width or truncation. |
| U3 | [`mines-standalone.tsx:756-779`](frontend/app/ui/mines-standalone.tsx:756) | **Medium** | Bet amount field shows the numeric value above the input (as a label "Bet amount" + the value in the input). On mobile, the bet amount display can appear redundant or confusing when combined with the balance footer. |
| U4 | [`globals.css:2339-2341`](frontend/app/globals.css:2339) | **Low** | Mobile layout hides `mines-stage-subtitle` via CSS (`display: none`), but the mobile layout JSX in [`mines-standalone.tsx:886`](frontend/app/ui/mines-standalone.tsx:886) still renders it. The subtitle is shown on mobile via a different CSS rule at line 2423 (`display: block`), creating a confusing override chain. |
| U5 | [`mines-standalone.tsx:209-214`](frontend/app/ui/mines-standalone.tsx:209) | **Medium** | Win/loss messages are hardcoded in Italian ("Hai vinto", "Hai perso :("). The backoffice has `ui_labels` for demo/real modes but win/loss messages are not configurable. |

---

## 5. Top 3 Risks

### Risk 1: Frontend Regression Cascade

**What:** Any non-trivial change to [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) or [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx) risks breaking unrelated views (admin, lobby, account, game).

**Why it matters:** These files are the primary delivery surface for the product. A regression in the game UI during an admin fix — or vice versa — erodes confidence and slows iteration.

**Trigger:** Any patch that touches layout, state management, or CSS class names in either file.

**Mitigation:**
1. Extract `mines-standalone.tsx` into 5-7 smaller components per Document 35 recommendations
2. Extract shared types and API client from both files into `frontend/app/lib/`
3. Do NOT add new features to `casinoking-console.tsx` — only extract from it
4. Add visual regression tests (screenshot comparison) for the Mines game frame

### Risk 2: Game-Platform Boundary Erosion

**What:** The `game_sessions` table is a single row serving both game-technical state (mine positions, revealed cells, board hash) and platform-financial state (wallet_account_id, ledger_transaction_id, wallet_balance_after_start). Any schema change risks breaking both domains.

**Why it matters:** The target architecture (Document 30, 31) requires clean separation. The longer the shared table persists, the harder the migration becomes.

**Trigger:** Adding new game features (e.g., auto-play, multi-round) or new financial features (e.g., bonus wagering requirements) that need schema changes.

**Mitigation:**
1. Keep `round_gateway.py` as the only bridge between game and platform
2. Plan a migration to split `game_sessions` into `platform_rounds` + `mines_game_rounds`
3. Do not add new platform-financial columns to `game_sessions`

### Risk 3: Launch Token Security Gap

**What:** The `game_launch_token` is a stateless JWT that can be reused until expiry. There is no server-side session tracking, no consumption counter, and no revocation mechanism.

**Why it matters:** In a production environment, a leaked or intercepted token could be used to start multiple game sessions or access another player's game state (though ownership checks exist at the API level).

**Trigger:** Moving to production, multi-device support, or third-party game integration.

**Mitigation:**
1. For MVP: acceptable as-is with short TTL (current `game_launch_token_ttl_minutes` setting)
2. For production: add a `game_launch_sessions` table to track token consumption
3. Add a `consumed_at` timestamp and reject tokens that have already been consumed

---

## 6. Roadmap Proposal

### Phase 1: Frontend Stabilization — "Stop the Bleeding"

**Goal:** Make the Mines game frontend safe to iterate on without risking regressions.

**Tasks:**
1. Extract shared types to `frontend/app/lib/types.ts`
2. Extract shared API client to `frontend/app/lib/api.ts`
3. Extract `MinesRulesModal` from `mines-standalone.tsx`
4. Extract `MinesBalanceFooter` from `mines-standalone.tsx`
5. Extract `MinesActionButtons` from `mines-standalone.tsx`
6. Extract `MinesMobileSettingsSheet` from `mines-standalone.tsx`
7. Extract `MinesStageHeader` from `mines-standalone.tsx`
8. Fix win/loss message layout shift (U1) — use a fixed-height notification slot
9. Fix hardcoded Italian strings (U5) — use `ui_labels` from backoffice config

**Dependencies:** None — this is pure refactoring.
**Complexity:** M

### Phase 2: Backend Boundary Hardening — "Draw the Line"

**Goal:** Complete the platform↔game boundary so that Mines backend only owns game logic.

**Tasks:**
1. Move `game_sessions` INSERT from [`service.py:94`](backend/app/modules/games/mines/service.py:94) into a dedicated game-round creation function that receives `platform_round_id` from the gateway
2. Remove `wallet_account_id`, `start_ledger_transaction_id`, `wallet_balance_after_start` from the game service's direct knowledge — pass them through the gateway response only
3. Add `platform_round_id` column to `game_sessions` (or create a mapping table)
4. Move launch token endpoints from `/games/mines/` to `/platform/` routes
5. Add consumption tracking to `game_launch_token` (optional for MVP)

**Dependencies:** Phase 1 should be started first to reduce frontend risk during backend changes.
**Complexity:** L

### Phase 3: Frontend Product Separation — "Two Products"

**Goal:** Mines frontend and platform frontend are independently deployable within the monorepo.

**Tasks:**
1. Create `frontend/app/ui/mines/` directory with extracted components
2. Remove all Mines-specific code from `casinoking-console.tsx`
3. Move Mines backoffice editor into a dedicated `frontend/app/ui/mines-backoffice/` module
4. Remove `display: none !important` CSS overrides — they should no longer be needed
5. Ensure `/mines` route works standalone without any dependency on `casinoking-console.tsx`

**Dependencies:** Phase 1 completed.
**Complexity:** M

### Phase 4: Schema Split & Contract Formalization — "Clean Architecture"

**Goal:** `game_sessions` is split into platform-owned and game-owned tables. The internal Python adapter becomes a formal API contract.

**Tasks:**
1. Create `platform_rounds` table for financial lifecycle
2. Create `mines_game_rounds` table for game-technical state
3. Migrate existing `game_sessions` data
4. Update `round_gateway.py` to work with the new schema
5. Formalize the gateway as a versioned internal API contract (per Document 34)
6. Add integration tests for the split schema

**Dependencies:** Phase 2 completed.
**Complexity:** L

---

## 7. Recovery Assessment

### Is this project recoverable without a full rewrite?

**Yes.** Unequivocally.

### What must be preserved

- **Entire backend financial model** — wallet, ledger, double-entry, idempotency. This is production-grade.
- **Mines mathematical core** — `runtime.py`, `randomness.py`, `fairness.py`. These are correct and well-tested.
- **Round gateway pattern** — `round_gateway.py` + `platform/rounds/service.py`. This is the right direction.
- **Game launch token** — the JWT-based handoff is architecturally correct, just needs hardening.
- **`mines-board.tsx`** — clean, reusable, well-isolated component.
- **Backoffice config** — draft/publish workflow with proper validation.
- **Test suite** — comprehensive coverage of critical paths.

### What must be refactored

- **`mines-standalone.tsx`** — must be decomposed into 5-7 components. The logic is correct; the structure is not.
- **`casinoking-console.tsx`** — must have Mines-specific code extracted. The file itself can remain as the platform shell during transition.
- **`service.py`** — must stop writing platform-financial fields directly. The gateway pattern is already in place; it just needs to be completed.
- **`globals.css`** — the `display: none !important` blocks must be replaced by proper component boundaries.

### What can be deferred

- Physical repository split (platform repo vs. game repo) — the monorepo is fine for now
- WebSocket support — polling/request-response is correct for MVP per AGENTS.md
- Launch token consumption tracking — acceptable as stateless JWT for MVP
- Schema split of `game_sessions` — can wait until Phase 4
- Aggregator as a separate product — can coincide with web platform for now

### Non-negotiable conditions for success

1. **No more features added to `casinoking-console.tsx`** — only extraction
2. **No cross-domain patches** — every change must declare if it belongs to platform, game, or aggregator (per Document 35)
3. **Frontend changes must be small and scoped** — no more 500-line patches touching desktop + mobile + embedded + backoffice
4. **The round gateway must remain the only bridge** between game and platform financial operations
5. **Tests must pass before and after every refactoring step** — the existing test suite is the safety net
6. **Document 35's component split recommendations must be followed** — they are not suggestions, they are the migration plan

---

## Appendix: File Size Summary

| File | Lines | Domain | Health |
|------|-------|--------|--------|
| [`casinoking-console.tsx`](frontend/app/ui/casinoking-console.tsx) | 5,329 | Platform (mixed) | Critical — must decompose |
| [`globals.css`](frontend/app/globals.css) | 3,732 | Shared | High debt — `!important` overrides |
| [`mines-standalone.tsx`](frontend/app/ui/mines-standalone.tsx) | 1,148 | Game | Needs extraction |
| [`service.py`](backend/app/modules/games/mines/service.py) | 811 | Game (mixed) | Boundary violation |
| [`backoffice_config.py`](backend/app/modules/games/mines/backoffice_config.py) | 703 | Game | Solid |
| [`mines.py`](backend/app/api/routes/mines.py) | 455 | API | Clean |
| [`platform/rounds/service.py`](backend/app/modules/platform/rounds/service.py) | 394 | Platform | Solid |
| [`fairness.py`](backend/app/modules/games/mines/fairness.py) | 386 | Game | Solid |
| [`mines-board.tsx`](frontend/app/ui/mines-board.tsx) | 165 | Game | Excellent |
| [`round_gateway.py`](backend/app/modules/games/mines/round_gateway.py) | 132 | Boundary | Good pattern |
| [`game_launch/service.py`](backend/app/modules/platform/game_launch/service.py) | 116 | Platform | Solid, needs hardening |
| [`runtime.py`](backend/app/modules/games/mines/runtime.py) | 71 | Game | Excellent |
| [`randomness.py`](backend/app/modules/games/mines/randomness.py) | 52 | Game | Excellent |
| [`exceptions.py`](backend/app/modules/games/mines/exceptions.py) | 15 | Game | Clean |
