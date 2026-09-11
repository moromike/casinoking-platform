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
--
-- CONFLITTO LOGICO (giro 3): se la stessa (player_id, operation,
-- idempotency_key) esiste sia nella tabella congelata *_pref4 sia nella
-- tabella unica, vince la riga VIVA della tabella unica: la riga congelata
-- viene sostituita in tutti i campi, id compreso.  Copre il caso "chiave
-- pre-0063 cancellata con il round e poi riusata": la risposta nuova
-- sostituisce quella vecchia, che altrimenti riprodurrebbe un round morto.
--
-- POLITICA ORFANI (dichiarata): le righe della tabella unica il cui round_id
-- non esiste piu' nella tabella round del gioco NON sono riversate — non
-- potrebbero: le vecchie tabelle hanno FK round_id -> round.  Sono contate e
-- segnalate con RAISE WARNING.  La loro perdita e' sicura: il round non
-- esiste, quindi la risposta memorizzata non sarebbe rigiocabile.

BEGIN;

-- 1. Rinomina indietro
ALTER TABLE boxe_idempotency_keys_pref4  RENAME TO boxe_idempotency_keys;
ALTER TABLE hi_lo_idempotency_keys_pref4 RENAME TO hi_lo_idempotency_keys;
ALTER TABLE mines_idempotency_keys_pref4 RENAME TO mines_idempotency_keys;

-- 2. Per ogni riga VIVA della tabella unica, elimina dalla vecchia tabella
--    la riga congelata corrispondente (stesso id OPPURE stessa chiave
--    logica): al passo 4 la riga viva ne prende il posto.
DELETE FROM boxe_idempotency_keys b
USING game_idempotency_keys g
WHERE g.game_code = 'boxe'
  AND (g.id = b.id
       OR (g.player_id = b.player_id
           AND g.operation = b.operation
           AND g.idempotency_key = b.idempotency_key));

DELETE FROM hi_lo_idempotency_keys h
USING game_idempotency_keys g
WHERE g.game_code = 'hi_lo'
  AND (g.id = h.id
       OR (g.player_id = h.player_id
           AND g.operation = h.operation
           AND g.idempotency_key = h.idempotency_key));

DELETE FROM mines_idempotency_keys m
USING game_idempotency_keys g
WHERE g.game_code = 'mines'
  AND (g.id = m.id
       OR (g.player_id = m.player_id
           AND g.operation = m.operation
           AND g.idempotency_key = m.idempotency_key));

-- 3. Orfani: contati e segnalati, NON riversati (politica in testa al file)
DO $$
DECLARE
    v_orfani integer;
BEGIN
    SELECT count(*) INTO v_orfani
    FROM game_idempotency_keys g
    WHERE g.round_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM boxe_rounds br
          WHERE g.game_code = 'boxe' AND br.id = g.round_id
      )
      AND NOT EXISTS (
          SELECT 1 FROM hi_lo_rounds hr
          WHERE g.game_code = 'hi_lo' AND hr.id = g.round_id
      )
      AND NOT EXISTS (
          SELECT 1 FROM mines_game_rounds mr
          WHERE g.game_code = 'mines' AND mr.id = g.round_id
      );
    IF v_orfani > 0 THEN
        RAISE WARNING 'rollback 0063: % righe orfane (round inesistente) NON riversate',
            v_orfani;
    END IF;
END $$;

-- 4. Riversa nelle vecchie tabelle le righe VIVE della tabella unica
--    (esclusi gli orfani, vedi politica in testa)
INSERT INTO boxe_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT g.id, g.player_id, g.round_id, g.operation, g.idempotency_key,
       g.request_fingerprint, g.response_json, g.created_at, g.expires_at
FROM game_idempotency_keys g
WHERE g.game_code = 'boxe'
  AND (g.round_id IS NULL
       OR EXISTS (SELECT 1 FROM boxe_rounds br WHERE br.id = g.round_id));

INSERT INTO hi_lo_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT g.id, g.player_id, g.round_id, g.operation, g.idempotency_key,
       g.request_fingerprint, g.response_json, g.created_at, g.expires_at
FROM game_idempotency_keys g
WHERE g.game_code = 'hi_lo'
  AND (g.round_id IS NULL
       OR EXISTS (SELECT 1 FROM hi_lo_rounds hr WHERE hr.id = g.round_id));

INSERT INTO mines_idempotency_keys
    (id, player_id, round_id, operation, idempotency_key,
     request_fingerprint, response_json, created_at, expires_at)
SELECT g.id, g.player_id, g.round_id, g.operation, g.idempotency_key,
       g.request_fingerprint, g.response_json, g.created_at, g.expires_at
FROM game_idempotency_keys g
WHERE g.game_code = 'mines'
  AND (g.round_id IS NULL
       OR EXISTS (SELECT 1 FROM mines_game_rounds mr WHERE mr.id = g.round_id));

-- 5. Drop della tabella unica
DROP TABLE IF EXISTS game_idempotency_keys;

COMMIT;
