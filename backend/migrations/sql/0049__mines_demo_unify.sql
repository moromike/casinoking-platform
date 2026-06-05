-- CasinoKing - Mines demo unification (DIV-02 Opzione B).
--
-- Scope:
-- - drop bespoke demo table demo_mines_game_rounds
-- - add demo_session_id (and supporting nullable columns) to mines_game_rounds
-- - create mines_idempotency_keys (pattern BOXE/HI-LO)
-- - align Mines demo to shared demo_wallet + single round table

BEGIN;

-- 1. Drop bespoke demo round table and its indexes
DROP TABLE IF EXISTS demo_mines_game_rounds CASCADE;

-- 2. Alter mines_game_rounds to host both real and demo rounds
ALTER TABLE mines_game_rounds
    ALTER COLUMN platform_round_id DROP NOT NULL;

ALTER TABLE mines_game_rounds
    ADD COLUMN IF NOT EXISTS demo_session_id uuid NULL REFERENCES demo_play_sessions(id);

ALTER TABLE mines_game_rounds
    ADD COLUMN IF NOT EXISTS title_code varchar(64) NULL;

ALTER TABLE mines_game_rounds
    ADD COLUMN IF NOT EXISTS site_code text NULL;

ALTER TABLE mines_game_rounds
    ADD COLUMN IF NOT EXISTS bet_amount numeric(18, 6) NULL;

ALTER TABLE mines_game_rounds
    ADD COLUMN IF NOT EXISTS status varchar(32) NULL;

-- At least one of platform_round_id or demo_session_id must be present
ALTER TABLE mines_game_rounds
    ADD CONSTRAINT mines_game_rounds_platform_or_demo_check
    CHECK (
        (platform_round_id IS NOT NULL) OR (demo_session_id IS NOT NULL)
    );

-- Demo rounds must have title_code, site_code, bet_amount, status populated
ALTER TABLE mines_game_rounds
    ADD CONSTRAINT mines_game_rounds_demo_fields_check
    CHECK (
        (demo_session_id IS NULL)
        OR (
            demo_session_id IS NOT NULL
            AND title_code IS NOT NULL
            AND site_code IS NOT NULL
            AND bet_amount IS NOT NULL
            AND status IS NOT NULL
        )
    );

CREATE INDEX IF NOT EXISTS idx_mines_game_rounds_demo_session_id
    ON mines_game_rounds (demo_session_id)
    WHERE demo_session_id IS NOT NULL;

-- 3. Create Mines idempotency table (pattern BOXE/HI-LO)
CREATE TABLE IF NOT EXISTS mines_idempotency_keys (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL REFERENCES users(id),
    round_id uuid NULL REFERENCES mines_game_rounds(id) ON DELETE CASCADE,
    operation varchar(32) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NULL,
    CONSTRAINT mines_idempotency_keys_operation_check
        CHECK (operation IN ('start_round', 'reveal', 'cashout')),
    CONSTRAINT mines_idempotency_keys_player_operation_key
        UNIQUE (player_id, operation, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_mines_idempotency_keys_round
    ON mines_idempotency_keys (round_id)
    WHERE round_id IS NOT NULL;

COMMIT;
