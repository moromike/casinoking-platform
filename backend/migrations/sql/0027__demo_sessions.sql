BEGIN;

CREATE TABLE demo_play_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    anonymous_id uuid NOT NULL,
    user_id uuid NULL REFERENCES users(id),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    balance_chips numeric(18, 6) NOT NULL,
    starting_balance_chips numeric(18, 6) NOT NULL DEFAULT 100,
    opened_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    status varchar(16) NOT NULL DEFAULT 'active',
    CONSTRAINT demo_play_sessions_status_check
        CHECK (status IN ('active', 'exhausted', 'closed')),
    CONSTRAINT demo_play_sessions_balance_check
        CHECK (balance_chips >= 0),
    CONSTRAINT demo_play_sessions_identity_check
        CHECK (
            (anonymous_id IS NOT NULL AND user_id IS NULL)
            OR (user_id IS NOT NULL)
        )
);

CREATE INDEX idx_demo_play_sessions_anon_title_status
    ON demo_play_sessions (anonymous_id, title_code, status);

CREATE TABLE demo_round_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    demo_play_session_id uuid NOT NULL REFERENCES demo_play_sessions(id),
    kind varchar(16) NOT NULL,
    amount numeric(18, 6) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    payload_json jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT demo_round_events_kind_check
        CHECK (kind IN ('bet', 'win', 'cashout', 'reveal_safe', 'mine_hit')),
    CONSTRAINT demo_round_events_amount_check
        CHECK (amount >= 0)
);

CREATE UNIQUE INDEX idx_demo_round_events_idempotency
    ON demo_round_events (demo_play_session_id, idempotency_key);

CREATE TABLE demo_mines_game_rounds (
    id uuid PRIMARY KEY,
    demo_play_session_id uuid NOT NULL REFERENCES demo_play_sessions(id),
    anonymous_id uuid NOT NULL,
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    site_code text NOT NULL REFERENCES sites(site_code),
    grid_size integer NOT NULL,
    mine_count integer NOT NULL,
    bet_amount numeric(18, 6) NOT NULL,
    status varchar(32) NOT NULL,
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
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    CONSTRAINT demo_mines_game_rounds_status_check
        CHECK (status IN ('active', 'won', 'lost', 'cancelled')),
    CONSTRAINT demo_mines_game_rounds_grid_size_check
        CHECK (grid_size IN (9, 16, 25, 36, 49)),
    CONSTRAINT demo_mines_game_rounds_mine_count_check
        CHECK (mine_count > 0 AND mine_count < grid_size),
    CONSTRAINT demo_mines_game_rounds_bet_amount_check
        CHECK (bet_amount > 0),
    CONSTRAINT demo_mines_game_rounds_safe_reveals_count_check
        CHECK (safe_reveals_count >= 0),
    CONSTRAINT demo_mines_game_rounds_safe_reveals_upper_bound_check
        CHECK (safe_reveals_count <= (grid_size - mine_count))
);

CREATE UNIQUE INDEX idx_demo_mines_game_rounds_anon_idempotency
    ON demo_mines_game_rounds (anonymous_id, idempotency_key);

CREATE INDEX idx_demo_mines_game_rounds_anon_created
    ON demo_mines_game_rounds (anonymous_id, created_at DESC);

COMMIT;
