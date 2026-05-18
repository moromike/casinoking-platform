-- CasinoKing - BOXE game-specific session, round, pick, and idempotency tables.
--
-- Scope:
-- - create BOXE-owned state tables for WP-BOXE-2B
-- - allow optional references to existing platform/session rows
-- - no wallet, ledger, platform_rounds, game_access_sessions, game_table_sessions,
--   Mines, API, or frontend schema changes

BEGIN;

CREATE TABLE IF NOT EXISTS boxe_sessions (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL,
    access_session_id uuid NULL REFERENCES game_access_sessions(id),
    table_session_id uuid NULL REFERENCES game_table_sessions(id),
    title_code varchar(64) NOT NULL,
    site_code varchar(64) NULL,
    status varchar(32) NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    CONSTRAINT boxe_sessions_status_check
        CHECK (status IN ('active', 'closed', 'expired', 'quarantined')),
    CONSTRAINT boxe_sessions_closed_at_consistency_check
        CHECK (
            (status = 'active' AND closed_at IS NULL)
            OR (status IN ('closed', 'expired', 'quarantined') AND closed_at IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_boxe_sessions_player_created
    ON boxe_sessions (player_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_boxe_sessions_status
    ON boxe_sessions (status);

CREATE INDEX IF NOT EXISTS idx_boxe_sessions_access_session_id
    ON boxe_sessions (access_session_id)
    WHERE access_session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_boxe_sessions_table_session_id
    ON boxe_sessions (table_session_id)
    WHERE table_session_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS boxe_rounds (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES boxe_sessions(id) ON DELETE CASCADE,
    platform_round_id uuid NULL UNIQUE REFERENCES platform_rounds(id),
    player_id uuid NOT NULL,
    title_code varchar(64) NOT NULL,
    site_code varchar(64) NULL,
    status varchar(32) NOT NULL,
    rows_count integer NOT NULL,
    difficulty varchar(16) NOT NULL,
    current_step integer NOT NULL DEFAULT 0,
    safe_picks_count integer NOT NULL DEFAULT 0,
    bet_amount numeric(18, 6) NOT NULL,
    multiplier_current numeric(18, 4) NOT NULL DEFAULT 1.0000,
    payout_current numeric(18, 6) NOT NULL DEFAULT 0,
    final_payout_amount numeric(18, 6) NULL,
    outcome varchar(32) NULL,
    config_snapshot_json jsonb NOT NULL,
    multiplier_table_json jsonb NOT NULL,
    fairness_version varchar(32) NOT NULL,
    server_seed text NOT NULL,
    server_seed_hash varchar(128) NOT NULL,
    client_seed varchar(255) NOT NULL,
    nonce integer NOT NULL,
    round_path_hash varchar(128) NULL,
    start_idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    terminal_reason varchar(64) NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    expires_at timestamptz NULL,
    CONSTRAINT boxe_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'row_revealed',
            'cashout_pending',
            'completed_cashout',
            'completed_top_row',
            'failed_mine',
            'expired',
            'quarantined'
        )),
    CONSTRAINT boxe_rounds_rows_count_check
        CHECK (rows_count IN (4, 5, 6, 7, 8)),
    CONSTRAINT boxe_rounds_difficulty_check
        CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT boxe_rounds_current_step_check
        CHECK (current_step >= 0 AND current_step <= rows_count),
    CONSTRAINT boxe_rounds_safe_picks_count_check
        CHECK (safe_picks_count >= 0 AND safe_picks_count <= rows_count),
    CONSTRAINT boxe_rounds_bet_amount_check
        CHECK (bet_amount > 0),
    CONSTRAINT boxe_rounds_multiplier_current_check
        CHECK (multiplier_current >= 1.0000),
    CONSTRAINT boxe_rounds_payout_current_check
        CHECK (payout_current >= 0),
    CONSTRAINT boxe_rounds_final_payout_amount_check
        CHECK (final_payout_amount IS NULL OR final_payout_amount >= 0),
    CONSTRAINT boxe_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'row_revealed', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'completed_top_row', 'failed_mine', 'expired', 'quarantined') AND closed_at IS NOT NULL)
        ),
    CONSTRAINT boxe_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'top_row', 'loss', 'expired', 'quarantined')
        ),
    CONSTRAINT boxe_rounds_session_start_idempotency_key
        UNIQUE (session_id, start_idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_boxe_rounds_session_created
    ON boxe_rounds (session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_boxe_rounds_player_created
    ON boxe_rounds (player_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_boxe_rounds_status
    ON boxe_rounds (status);

CREATE INDEX IF NOT EXISTS idx_boxe_rounds_platform_round_id
    ON boxe_rounds (platform_round_id)
    WHERE platform_round_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_boxe_rounds_one_open_per_session
    ON boxe_rounds (session_id)
    WHERE status IN ('created', 'active', 'row_revealed', 'cashout_pending');

CREATE TABLE IF NOT EXISTS boxe_picks (
    id uuid PRIMARY KEY,
    round_id uuid NOT NULL REFERENCES boxe_rounds(id) ON DELETE CASCADE,
    step integer NOT NULL,
    row_index integer NOT NULL,
    selected_box_index integer NOT NULL,
    safe boolean NOT NULL,
    multiplier_after numeric(18, 4) NOT NULL,
    payout_after numeric(18, 6) NOT NULL,
    rng_material varchar(128) NOT NULL,
    success_probability numeric(18, 12) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT boxe_picks_step_check
        CHECK (step >= 1),
    CONSTRAINT boxe_picks_row_index_check
        CHECK (row_index >= 0),
    CONSTRAINT boxe_picks_selected_box_index_check
        CHECK (selected_box_index >= 0),
    CONSTRAINT boxe_picks_multiplier_after_check
        CHECK (multiplier_after >= 1.0000),
    CONSTRAINT boxe_picks_payout_after_check
        CHECK (payout_after >= 0),
    CONSTRAINT boxe_picks_success_probability_check
        CHECK (success_probability >= 0 AND success_probability <= 1),
    CONSTRAINT boxe_picks_round_step_key
        UNIQUE (round_id, step),
    CONSTRAINT boxe_picks_round_idempotency_key
        UNIQUE (round_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_boxe_picks_round_created
    ON boxe_picks (round_id, created_at);

CREATE TABLE IF NOT EXISTS boxe_idempotency_keys (
    id uuid PRIMARY KEY,
    session_id uuid NULL REFERENCES boxe_sessions(id) ON DELETE CASCADE,
    round_id uuid NULL REFERENCES boxe_rounds(id) ON DELETE CASCADE,
    operation varchar(32) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NULL,
    CONSTRAINT boxe_idempotency_keys_operation_check
        CHECK (operation IN ('start_round', 'reveal_pick', 'cashout', 'recovery_auto_cashout', 'admin_quarantine')),
    CONSTRAINT boxe_idempotency_keys_owner_check
        CHECK (session_id IS NOT NULL OR round_id IS NOT NULL),
    CONSTRAINT boxe_idempotency_keys_round_operation_key
        UNIQUE (round_id, operation, idempotency_key),
    CONSTRAINT boxe_idempotency_keys_session_operation_key
        UNIQUE (session_id, operation, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_boxe_idempotency_keys_round
    ON boxe_idempotency_keys (round_id)
    WHERE round_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_boxe_idempotency_keys_session
    ON boxe_idempotency_keys (session_id)
    WHERE session_id IS NOT NULL;

COMMIT;
