-- CasinoKing Mines game session foundations
-- Source references:
-- - docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md
-- - docs/md/CasinoKing_Documento_07_v2_Mines_Matematica_Congelata.md
-- - docs/md/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.md
-- - docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md
--
-- Scope of this migration:
-- - create the base game_sessions table for Mines
-- - preserve ownership, idempotency, fairness metadata and link to the
--   start ledger transaction
--
-- Explicitly deferred:
-- - reveal/cashout specific indexes and constraints
-- - admin/game audit extensions
-- - future seed-hash / nonce advanced fairness fields

BEGIN;

CREATE TABLE game_sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    game_code varchar(32) NOT NULL,
    wallet_account_id uuid NOT NULL REFERENCES wallet_accounts(id),
    wallet_type varchar(32) NOT NULL,
    start_ledger_transaction_id uuid NOT NULL UNIQUE REFERENCES ledger_transactions(id),
    idempotency_key varchar(128) NULL,
    request_fingerprint varchar(128) NULL,
    grid_size integer NOT NULL,
    mine_count integer NOT NULL,
    bet_amount numeric(18, 6) NOT NULL,
    status varchar(32) NOT NULL,
    safe_reveals_count integer NOT NULL DEFAULT 0,
    revealed_cells_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    mine_positions_json jsonb NOT NULL,
    multiplier_current numeric(18, 4) NOT NULL DEFAULT 1.0000,
    payout_current numeric(18, 6) NOT NULL,
    wallet_balance_after_start numeric(18, 6) NOT NULL,
    fairness_version varchar(32) NOT NULL,
    rng_material text NOT NULL,
    board_hash varchar(128) NOT NULL,
    closed_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT game_sessions_game_code_check
        CHECK (game_code = 'mines'),
    CONSTRAINT game_sessions_status_check
        CHECK (status IN ('created', 'active', 'won', 'lost', 'cancelled')),
    CONSTRAINT game_sessions_bet_amount_check
        CHECK (bet_amount > 0),
    CONSTRAINT game_sessions_grid_size_check
        CHECK (grid_size IN (9, 16, 25, 36, 49)),
    CONSTRAINT game_sessions_mine_count_check
        CHECK (mine_count > 0 AND mine_count < grid_size),
    CONSTRAINT game_sessions_safe_reveals_count_check
        CHECK (safe_reveals_count >= 0),
    CONSTRAINT game_sessions_user_idempotency_key_key
        UNIQUE (user_id, idempotency_key)
);

CREATE INDEX idx_game_sessions_user_id_created_at
    ON game_sessions (user_id, created_at DESC);

CREATE INDEX idx_game_sessions_user_id_status
    ON game_sessions (user_id, status);

COMMIT;
