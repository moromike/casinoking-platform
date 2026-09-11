-- 0064 rollback — ricrea vuote le tabelle legacy congelate dal 0063.
--
-- PROCEDURA MANUALE: dopo questo file eseguire il rollback 0063, che
-- riversa game_idempotency_keys nelle tre tabelle qui ricreate.
-- Lo schema e' quello effettivo delle tabelle rinominate da 0063: migrazioni
-- 0043, 0048, 0049, 0050, 0052 e le modifiche applicate prima di 0063.

BEGIN;

CREATE TABLE IF NOT EXISTS boxe_idempotency_keys_pref4 (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL,
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
    ON boxe_idempotency_keys_pref4 (round_id)
    WHERE round_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS hi_lo_idempotency_keys_pref4 (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL,
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
    ON hi_lo_idempotency_keys_pref4 (round_id)
    WHERE round_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS mines_idempotency_keys_pref4 (
    id uuid PRIMARY KEY,
    player_id uuid NOT NULL,
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
    ON mines_idempotency_keys_pref4 (round_id)
    WHERE round_id IS NOT NULL;

COMMIT;
