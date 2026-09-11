-- 0063 rollback — retromarcia della tabella unica di idempotenza.
--
-- PROCEDURA MANUALE (il migratore carica solo migrations/sql/*.sql, non
-- questa directory).  Eseguire con psql dopo aver spento il backend:
--
--   psql "$CASINOKING_TEST_DATABASE_URL" \
--        -f backend/migrations/sql/rollback/0063__retromarcia_game_idempotency_keys.sql
--
-- Poi rimuovere la riga dalla tabella schema_migrations:
--
--   psql "$CASINOKING_TEST_DATABASE_URL" -c \
--        "DELETE FROM schema_migrations WHERE migration_name = '0063__game_idempotency_keys.sql'"
--
-- E riavviare il backend con il codice precedente (pre-5B).

BEGIN;

-- 1. Rinomina indietro
ALTER TABLE boxe_idempotency_keys_pref4  RENAME TO boxe_idempotency_keys;
ALTER TABLE hi_lo_idempotency_keys_pref4 RENAME TO hi_lo_idempotency_keys;
ALTER TABLE mines_idempotency_keys_pref4 RENAME TO mines_idempotency_keys;

-- 2. Riversa nelle vecchie tabelle le righe scritte DOPO lo switch
--    (quelle con created_at maggiore della piu' vecchia riga della tabella
--    unica, che e' il momento approssimato della migrazione).
--    Le righe originali sono gia' nelle vecchie tabelle (la migrazione
--    forward le aveva copiate, non spostate).
INSERT INTO boxe_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM game_idempotency_keys
WHERE game_code = 'boxe'
  AND id NOT IN (SELECT id FROM boxe_idempotency_keys)
ON CONFLICT DO NOTHING;

INSERT INTO hi_lo_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM game_idempotency_keys
WHERE game_code = 'hi_lo'
  AND id NOT IN (SELECT id FROM hi_lo_idempotency_keys)
ON CONFLICT DO NOTHING;

INSERT INTO mines_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT id, player_id, round_id, operation, idempotency_key,
       request_fingerprint, response_json, created_at, expires_at
FROM game_idempotency_keys
WHERE game_code = 'mines'
  AND id NOT IN (SELECT id FROM mines_idempotency_keys)
ON CONFLICT DO NOTHING;

-- 3. Drop della tabella unica
DROP TABLE IF EXISTS game_idempotency_keys;

COMMIT;
