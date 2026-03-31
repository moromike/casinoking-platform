-- CasinoKing Phase 4: Data migration from game_sessions + backward-compat view
-- Source references:
-- - docs/MINES_EXECUTION_PLAN.md (Phase 4, P4-WP2)
--
-- Scope of this migration:
-- - copy platform fields from game_sessions into platform_rounds
-- - copy game fields from game_sessions into mines_game_rounds
-- - create game_sessions_compat view joining both tables
--
-- NOTE: game_sessions table is NOT dropped — kept for safety.
-- The nonce and server_seed_hash columns exist in game_sessions (added by 0007)
-- and are migrated directly.

BEGIN;

-- Migrate platform fields
INSERT INTO platform_rounds (
    id, user_id, game_code, wallet_account_id, wallet_type,
    bet_amount, status, payout_amount, start_ledger_transaction_id,
    wallet_balance_after_start, idempotency_key, request_fingerprint,
    closed_at, created_at
)
SELECT
    id, user_id, game_code, wallet_account_id, wallet_type,
    bet_amount, status, payout_current, start_ledger_transaction_id,
    wallet_balance_after_start, idempotency_key, request_fingerprint,
    closed_at, created_at
FROM game_sessions;

-- Migrate game fields (platform_round_id = id for 1:1 mapping)
INSERT INTO mines_game_rounds (
    id, platform_round_id, user_id,
    grid_size, mine_count, safe_reveals_count, revealed_cells_json,
    mine_positions_json, multiplier_current, payout_current,
    fairness_version, nonce, server_seed_hash, rng_material, board_hash,
    created_at, closed_at
)
SELECT
    id, id, user_id,
    grid_size, mine_count, safe_reveals_count, revealed_cells_json,
    mine_positions_json, multiplier_current, payout_current,
    fairness_version, nonce, server_seed_hash, rng_material, board_hash,
    created_at, closed_at
FROM game_sessions;

-- Backward-compat view
CREATE OR REPLACE VIEW game_sessions_compat AS
SELECT
    pr.id,
    pr.user_id,
    pr.game_code,
    pr.wallet_account_id,
    pr.wallet_type,
    pr.bet_amount,
    pr.status,
    pr.start_ledger_transaction_id,
    pr.wallet_balance_after_start,
    pr.idempotency_key,
    pr.request_fingerprint,
    pr.closed_at,
    pr.created_at,
    mgr.grid_size,
    mgr.mine_count,
    mgr.safe_reveals_count,
    mgr.revealed_cells_json,
    mgr.mine_positions_json,
    mgr.multiplier_current,
    mgr.payout_current,
    mgr.fairness_version,
    mgr.nonce,
    mgr.server_seed_hash,
    mgr.rng_material,
    mgr.board_hash
FROM platform_rounds pr
JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id;

COMMIT;
