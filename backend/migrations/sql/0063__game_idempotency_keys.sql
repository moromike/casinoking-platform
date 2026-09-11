-- 0063 — PASSO 5B (F-4): una sola tabella di idempotenza per i tre giochi.
--
-- Unifica boxe_idempotency_keys, hi_lo_idempotency_keys, mines_idempotency_keys
-- in game_idempotency_keys.  Le vecchie tabelle sono rinominate *_pref4 (non
-- droppate): rollback manuale in migrations/sql/rollback/0063__*.sql.
--
-- RICHIEDE stop/restart del backend locale: i lock presi dal DDL sono
-- incompatibili col codice vecchio che scrive ancora sulle tre tabelle.
--
-- ATOMICITA': un solo BEGIN/COMMIT.  La quadratura solleva RAISE EXCEPTION
-- se i conteggi non coincidono, facendo annullare l'intera transazione.
-- Il registro del migratore (schema_migrations) e' aggiornato DOPO questo
-- file, in una transazione separata del runner: schema e registrazione
-- non sono atomici.

BEGIN;

-- 1. Tabella unica
CREATE TABLE game_idempotency_keys (
    id                  uuid PRIMARY KEY,
    game_code           varchar(16) NOT NULL,
    player_id           uuid NOT NULL,
    round_id            uuid NULL,
    operation           varchar(32) NOT NULL,
    idempotency_key     varchar(128) NOT NULL,
    request_fingerprint varchar(128) NOT NULL,
    response_json       jsonb NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NULL,

    CONSTRAINT game_idempotency_keys_game_check
        CHECK (game_code IN ('boxe', 'hi_lo', 'mines')),

    CONSTRAINT game_idempotency_keys_game_operation_check
        CHECK (
            (game_code = 'boxe'  AND operation IN ('start_round', 'reveal_pick', 'cashout', 'recovery_auto_cashout', 'admin_quarantine'))
         OR (game_code = 'hi_lo' AND operation IN ('start_round', 'active_skip', 'predict', 'cashout'))
         OR (game_code = 'mines' AND operation IN ('start_round', 'reveal', 'cashout'))
        ),

    CONSTRAINT game_idempotency_keys_player_operation_key
        UNIQUE (game_code, player_id, operation, idempotency_key)
);

CREATE INDEX idx_game_idempotency_keys_round
    ON game_idempotency_keys (game_code, round_id) WHERE round_id IS NOT NULL;

-- 2. Copia dei dati dalle tre tabelle
INSERT INTO game_idempotency_keys
    (id, game_code, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, 'boxe', player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM boxe_idempotency_keys;

INSERT INTO game_idempotency_keys
    (id, game_code, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, 'hi_lo', player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM hi_lo_idempotency_keys;

INSERT INTO game_idempotency_keys
    (id, game_code, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, 'mines', player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM mines_idempotency_keys;

-- 3. Quadratura per id, EXCEPT simmetrico: nessuna riga persa, nessuna
--    riga inventata (il solo conteggio non basterebbe)
DO $$
DECLARE
    v_diff  integer;
BEGIN
    SELECT count(*) INTO v_diff FROM (
        (
            SELECT id FROM game_idempotency_keys
            EXCEPT
            SELECT id FROM (
                SELECT id FROM boxe_idempotency_keys
                UNION ALL
                SELECT id FROM hi_lo_idempotency_keys
                UNION ALL
                SELECT id FROM mines_idempotency_keys
            ) vecchie
        )
        UNION ALL
        (
            SELECT id FROM (
                SELECT id FROM boxe_idempotency_keys
                UNION ALL
                SELECT id FROM hi_lo_idempotency_keys
                UNION ALL
                SELECT id FROM mines_idempotency_keys
            ) vecchie
            EXCEPT
            SELECT id FROM game_idempotency_keys
        )
    ) differenze;
    IF v_diff <> 0 THEN
        RAISE EXCEPTION
            'Quadratura idempotenza fallita: % id difformi fra tabella unica e vecchie tabelle',
            v_diff;
    END IF;
END $$;

-- 4. Rinomina delle vecchie tabelle in *_pref4 (non DROP)
ALTER TABLE boxe_idempotency_keys  RENAME TO boxe_idempotency_keys_pref4;
ALTER TABLE hi_lo_idempotency_keys RENAME TO hi_lo_idempotency_keys_pref4;
ALTER TABLE mines_idempotency_keys RENAME TO mines_idempotency_keys_pref4;

COMMIT;
