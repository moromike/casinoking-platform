-- CasinoKing - HI-LO game-specific round, action, and idempotency tables.
--
-- Scope:
-- - persist HI-LO-owned round lifecycle for H2 backend API/state
-- - allow optional links to platform real-money rounds, access sessions and table sessions
-- - no Mines, BOXE, frontend, wallet schema or platform ledger schema changes

BEGIN;

CREATE TABLE IF NOT EXISTS hi_lo_rounds (
    id uuid PRIMARY KEY,
    platform_round_id uuid NULL UNIQUE REFERENCES platform_rounds(id),
    player_id uuid NOT NULL REFERENCES users(id),
    access_session_id uuid NULL REFERENCES game_access_sessions(id),
    table_session_id uuid NULL REFERENCES game_table_sessions(id),
    demo_session_id uuid NULL REFERENCES demo_play_sessions(id),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    site_code varchar(64) NOT NULL DEFAULT 'casinoking',
    status varchar(32) NOT NULL,
    wallet_source varchar(16) NOT NULL,
    bet_amount numeric(18, 6) NOT NULL,
    current_card_rank integer NOT NULL,
    current_card_suit varchar(16) NOT NULL,
    current_draw_index integer NOT NULL DEFAULT 0,
    correct_predictions_count integer NOT NULL DEFAULT 0,
    active_skip_count integer NOT NULL DEFAULT 0,
    cumulative_success_probability numeric(24, 18) NOT NULL DEFAULT 1,
    multiplier_current numeric(18, 4) NOT NULL DEFAULT 1.0000,
    payout_current numeric(18, 6) NOT NULL DEFAULT 0,
    final_payout_amount numeric(18, 6) NULL,
    outcome varchar(32) NULL,
    fairness_version varchar(32) NOT NULL,
    server_seed text NOT NULL,
    server_seed_hash varchar(128) NOT NULL,
    client_seed varchar(255) NOT NULL,
    round_nonce integer NOT NULL,
    start_idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    terminal_reason varchar(64) NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    CONSTRAINT hi_lo_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'cashout_pending',
            'completed_cashout',
            'failed_prediction',
            'expired',
            'quarantined'
        )),
    CONSTRAINT hi_lo_rounds_wallet_source_check
        CHECK (wallet_source IN ('demo', 'cash', 'bonus')),
    CONSTRAINT hi_lo_rounds_bet_amount_check
        CHECK (bet_amount > 0),
    CONSTRAINT hi_lo_rounds_current_card_rank_check
        CHECK (current_card_rank BETWEEN 1 AND 13),
    CONSTRAINT hi_lo_rounds_current_card_suit_check
        CHECK (current_card_suit IN ('clubs', 'spades', 'hearts', 'diamonds')),
    CONSTRAINT hi_lo_rounds_current_draw_index_check
        CHECK (current_draw_index >= 0),
    CONSTRAINT hi_lo_rounds_correct_predictions_count_check
        CHECK (correct_predictions_count >= 0),
    CONSTRAINT hi_lo_rounds_active_skip_count_check
        CHECK (active_skip_count >= 0),
    CONSTRAINT hi_lo_rounds_cumulative_success_probability_check
        CHECK (cumulative_success_probability > 0 AND cumulative_success_probability <= 1),
    CONSTRAINT hi_lo_rounds_multiplier_current_check
        CHECK (multiplier_current >= 1.0000),
    CONSTRAINT hi_lo_rounds_payout_current_check
        CHECK (payout_current >= 0),
    CONSTRAINT hi_lo_rounds_final_payout_amount_check
        CHECK (final_payout_amount IS NULL OR final_payout_amount >= 0),
    CONSTRAINT hi_lo_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'failed_prediction', 'expired', 'quarantined') AND closed_at IS NOT NULL)
        ),
    CONSTRAINT hi_lo_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'loss', 'expired', 'quarantined')
        )
);

CREATE INDEX IF NOT EXISTS idx_hi_lo_rounds_player_created
    ON hi_lo_rounds (player_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_hi_lo_rounds_status
    ON hi_lo_rounds (status);

CREATE INDEX IF NOT EXISTS idx_hi_lo_rounds_platform_round_id
    ON hi_lo_rounds (platform_round_id)
    WHERE platform_round_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_hi_lo_rounds_one_open_per_player_title
    ON hi_lo_rounds (player_id, title_code)
    WHERE status IN ('created', 'active', 'cashout_pending');

CREATE TABLE IF NOT EXISTS hi_lo_actions (
    id uuid PRIMARY KEY,
    round_id uuid NOT NULL REFERENCES hi_lo_rounds(id) ON DELETE CASCADE,
    action_index integer NOT NULL,
    action_type varchar(32) NOT NULL,
    prediction_action varchar(16) NULL,
    success boolean NULL,
    probability numeric(24, 18) NULL,
    multiplier_after numeric(18, 4) NOT NULL,
    payout_after numeric(18, 6) NOT NULL,
    previous_card_json jsonb NULL,
    drawn_card_json jsonb NOT NULL,
    draw_index integer NOT NULL,
    draw_purpose varchar(64) NOT NULL,
    rng_material text NOT NULL,
    response_json jsonb NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT hi_lo_actions_action_index_check
        CHECK (action_index >= 0),
    CONSTRAINT hi_lo_actions_action_type_check
        CHECK (action_type IN ('start', 'active_skip', 'prediction', 'cashout')),
    CONSTRAINT hi_lo_actions_prediction_action_check
        CHECK (
            prediction_action IS NULL
            OR prediction_action IN ('black', 'red', 'down', 'up')
        ),
    CONSTRAINT hi_lo_actions_probability_check
        CHECK (probability IS NULL OR (probability > 0 AND probability <= 1)),
    CONSTRAINT hi_lo_actions_multiplier_after_check
        CHECK (multiplier_after >= 1.0000),
    CONSTRAINT hi_lo_actions_payout_after_check
        CHECK (payout_after >= 0),
    CONSTRAINT hi_lo_actions_draw_index_check
        CHECK (draw_index >= 0),
    CONSTRAINT hi_lo_actions_round_action_index_key
        UNIQUE (round_id, action_index),
    CONSTRAINT hi_lo_actions_round_idempotency_key
        UNIQUE (round_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_hi_lo_actions_round_created
    ON hi_lo_actions (round_id, created_at);

CREATE TABLE IF NOT EXISTS hi_lo_idempotency_keys (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL REFERENCES users(id),
    round_id uuid NULL REFERENCES hi_lo_rounds(id) ON DELETE CASCADE,
    operation varchar(32) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NULL,
    CONSTRAINT hi_lo_idempotency_keys_operation_check
        CHECK (operation IN ('start_round', 'active_skip', 'predict', 'cashout')),
    CONSTRAINT hi_lo_idempotency_keys_player_operation_key
        UNIQUE (player_id, operation, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_hi_lo_idempotency_keys_round
    ON hi_lo_idempotency_keys (round_id)
    WHERE round_id IS NOT NULL;

COMMIT;
