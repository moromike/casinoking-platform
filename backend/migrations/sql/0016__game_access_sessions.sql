BEGIN;

CREATE TABLE game_access_sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    game_code varchar(32) NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    last_activity_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz NULL,
    status varchar(32) NOT NULL,
    CONSTRAINT game_access_sessions_status_check
        CHECK (status IN ('active', 'closed', 'timed_out')),
    CONSTRAINT game_access_sessions_ended_at_consistency_check
        CHECK (
            (status = 'active' AND ended_at IS NULL)
            OR (status IN ('closed', 'timed_out') AND ended_at IS NOT NULL)
        )
);

CREATE INDEX idx_game_access_sessions_user_id_game_code_started_at
    ON game_access_sessions (user_id, game_code, started_at DESC);

CREATE INDEX idx_game_access_sessions_user_id_status
    ON game_access_sessions (user_id, status);

ALTER TABLE platform_rounds
    ADD COLUMN IF NOT EXISTS access_session_id uuid NULL REFERENCES game_access_sessions(id);

CREATE INDEX idx_platform_rounds_access_session_id
    ON platform_rounds (access_session_id)
    WHERE access_session_id IS NOT NULL;

COMMIT;
