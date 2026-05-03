BEGIN;

CREATE TABLE game_table_sessions (
    id uuid PRIMARY KEY,
    access_session_id uuid NULL REFERENCES game_access_sessions(id),
    user_id uuid NOT NULL REFERENCES users(id),
    game_code varchar(32) NOT NULL,
    wallet_account_id uuid NOT NULL REFERENCES wallet_accounts(id),
    wallet_type varchar(32) NOT NULL,
    table_budget_amount numeric(18, 6) NOT NULL,
    loss_limit_amount numeric(18, 6) NOT NULL,
    loss_reserved_amount numeric(18, 6) NOT NULL DEFAULT 0,
    loss_consumed_amount numeric(18, 6) NOT NULL DEFAULT 0,
    status varchar(32) NOT NULL,
    closed_reason varchar(64) NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz NULL,
    CONSTRAINT game_table_sessions_status_check
        CHECK (status IN ('active', 'closed', 'timed_out')),
    CONSTRAINT game_table_sessions_table_budget_amount_check
        CHECK (table_budget_amount > 0),
    CONSTRAINT game_table_sessions_loss_limit_amount_check
        CHECK (loss_limit_amount > 0),
    CONSTRAINT game_table_sessions_loss_reserved_amount_check
        CHECK (loss_reserved_amount >= 0),
    CONSTRAINT game_table_sessions_loss_consumed_amount_check
        CHECK (loss_consumed_amount >= 0),
    CONSTRAINT game_table_sessions_loss_limit_bounds_check
        CHECK (loss_reserved_amount + loss_consumed_amount <= loss_limit_amount),
    CONSTRAINT game_table_sessions_closed_at_consistency_check
        CHECK (
            (status = 'active' AND closed_at IS NULL)
            OR (status IN ('closed', 'timed_out') AND closed_at IS NOT NULL)
        )
);

CREATE INDEX idx_game_table_sessions_user_id_game_code_created_at
    ON game_table_sessions (user_id, game_code, created_at DESC);

CREATE INDEX idx_game_table_sessions_user_id_status
    ON game_table_sessions (user_id, status);

CREATE INDEX idx_game_table_sessions_access_session_id
    ON game_table_sessions (access_session_id)
    WHERE access_session_id IS NOT NULL;

ALTER TABLE platform_rounds
    ADD COLUMN IF NOT EXISTS table_session_id uuid NULL REFERENCES game_table_sessions(id);

CREATE INDEX idx_platform_rounds_table_session_id
    ON platform_rounds (table_session_id)
    WHERE table_session_id IS NOT NULL;

COMMIT;
