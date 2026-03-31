-- CasinoKing Phase 4: Schema Split — platform_rounds + mines_game_rounds
-- Source references:
-- - docs/MINES_EXECUTION_PLAN.md (Phase 4, P4-WP1)
-- - docs/md/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.md
-- - docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md
--
-- Scope of this migration:
-- - create platform_rounds table (platform-owned financial round data)
-- - create mines_game_rounds table (game-owned Mines-specific data)
-- - these tables will receive data from game_sessions in migration 0013

BEGIN;

CREATE TABLE platform_rounds (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    game_code varchar(32) NOT NULL,
    wallet_account_id uuid NOT NULL REFERENCES wallet_accounts(id),
    wallet_type varchar(32) NOT NULL,
    bet_amount numeric(18, 6) NOT NULL,
    status varchar(32) NOT NULL,
    payout_amount numeric(18, 6) NOT NULL DEFAULT 0,
    start_ledger_transaction_id uuid NOT NULL UNIQUE REFERENCES ledger_transactions(id),
    settlement_ledger_transaction_id uuid NULL REFERENCES ledger_transactions(id),
    wallet_balance_after_start numeric(18, 6) NOT NULL,
    idempotency_key varchar(128) NULL,
    request_fingerprint varchar(128) NULL,
    closed_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT platform_rounds_status_check
        CHECK (status IN ('created', 'active', 'won', 'lost', 'cancelled')),
    CONSTRAINT platform_rounds_bet_amount_check
        CHECK (bet_amount > 0),
    CONSTRAINT platform_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active') AND closed_at IS NULL)
            OR (status IN ('won', 'lost', 'cancelled') AND closed_at IS NOT NULL)
        ),
    CONSTRAINT platform_rounds_user_idempotency_key_key
        UNIQUE (user_id, idempotency_key)
);

CREATE INDEX idx_platform_rounds_user_id_created_at
    ON platform_rounds (user_id, created_at DESC);

CREATE INDEX idx_platform_rounds_user_id_status
    ON platform_rounds (user_id, status);

CREATE TABLE mines_game_rounds (
    id uuid PRIMARY KEY,
    platform_round_id uuid NOT NULL UNIQUE REFERENCES platform_rounds(id),
    user_id uuid NOT NULL REFERENCES users(id),
    grid_size integer NOT NULL,
    mine_count integer NOT NULL,
    safe_reveals_count integer NOT NULL DEFAULT 0,
    revealed_cells_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    mine_positions_json jsonb NOT NULL,
    multiplier_current numeric(18, 4) NOT NULL DEFAULT 1.0000,
    payout_current numeric(18, 6) NOT NULL,
    fairness_version varchar(32) NOT NULL,
    nonce integer NOT NULL DEFAULT 0,
    server_seed_hash varchar(128) NOT NULL DEFAULT '',
    rng_material text NOT NULL,
    board_hash varchar(128) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    CONSTRAINT mines_game_rounds_grid_size_check
        CHECK (grid_size IN (9, 16, 25, 36, 49)),
    CONSTRAINT mines_game_rounds_mine_count_check
        CHECK (mine_count > 0 AND mine_count < grid_size),
    CONSTRAINT mines_game_rounds_safe_reveals_count_check
        CHECK (safe_reveals_count >= 0),
    CONSTRAINT mines_game_rounds_safe_reveals_upper_bound_check
        CHECK (safe_reveals_count <= (grid_size - mine_count))
);

CREATE INDEX idx_mines_game_rounds_user_id_created_at
    ON mines_game_rounds (user_id, created_at DESC);

CREATE INDEX idx_mines_game_rounds_platform_round_id
    ON mines_game_rounds (platform_round_id);

COMMIT;
