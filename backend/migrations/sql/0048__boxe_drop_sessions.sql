-- CasinoKing - Drop BOXE bespoke session table; align BOXE to HI-LO/Mines pattern (session_id == round_id).
--
-- Scope:
-- - remove boxe_sessions (one-round wrapper, no longer needed)
-- - move access_session_id / table_session_id directly to boxe_rounds
-- - align boxe_idempotency_keys to HI-LO pattern (player_id, no session_id)
-- - rebuild idempotency constraint: UNIQUE (player_id, operation, idempotency_key)

BEGIN;

-- 1. Remove session_id artifacts from boxe_rounds
ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_session_start_idempotency_key;

DROP INDEX IF EXISTS idx_boxe_rounds_session_created;
DROP INDEX IF EXISTS idx_boxe_rounds_one_open_per_session;

ALTER TABLE boxe_rounds
    DROP COLUMN IF EXISTS session_id;

-- 2. Add access/table session refs directly to boxe_rounds (HI-LO pattern)
ALTER TABLE boxe_rounds
    ADD COLUMN IF NOT EXISTS access_session_id uuid NULL REFERENCES game_access_sessions(id);

ALTER TABLE boxe_rounds
    ADD COLUMN IF NOT EXISTS table_session_id uuid NULL REFERENCES game_table_sessions(id);

-- 3. Rebuild boxe_idempotency_keys without session_id, with player_id
DROP TABLE IF EXISTS boxe_idempotency_keys;

CREATE TABLE boxe_idempotency_keys (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL REFERENCES users(id),
    round_id uuid NULL REFERENCES boxe_rounds(id) ON DELETE CASCADE,
    operation varchar(32) NOT NULL,
    idempotency_key varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NULL,
    CONSTRAINT boxe_idempotency_keys_operation_check
        CHECK (operation IN ('start_round', 'reveal_pick', 'cashout', 'recovery_auto_cashout', 'admin_quarantine')),
    CONSTRAINT boxe_idempotency_keys_player_operation_key
        UNIQUE (player_id, operation, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_boxe_idempotency_keys_round
    ON boxe_idempotency_keys (round_id)
    WHERE round_id IS NOT NULL;

-- 4. Drop bespoke session table and its indexes
DROP TABLE IF EXISTS boxe_sessions CASCADE;

COMMIT;
