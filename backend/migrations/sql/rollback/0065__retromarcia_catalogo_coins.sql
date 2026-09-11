-- 0065 rollback — retromarcia del catalogo Coins (PASSO 3-bis, 3bA).
--
-- PROCEDURA MANUALE (il migratore carica solo migrations/sql/*.sql, non
-- questa directory). Eseguire con psql a backend SPENTO:
--
--   psql "$CASINOKING_TEST_DATABASE_URL" \
--        -f backend/migrations/sql/rollback/0065__retromarcia_catalogo_coins.sql
--
-- Poi rimuovere la riga dalla tabella schema_migrations:
--
--   psql "$CASINOKING_TEST_DATABASE_URL" -c \
--        "DELETE FROM schema_migrations WHERE migration_name = '0065__catalogo_coins.sql'"
--
-- E riavviare il backend con il codice precedente (senza coins in
-- game_codes.py e senza la rotta di introspezione).
--
-- GUARDIA: se esistono gia' partite (platform_rounds) legate a coins o al
-- fornitore m-and-m-games, il rollback ABORTISCE: cancellare il catalogo
-- sotto a partite contabili lascerebbe il ledger senza il suo referente.

BEGIN;

DO $$
DECLARE
    v_partite integer;
BEGIN
    SELECT count(*) INTO v_partite
    FROM platform_rounds
    WHERE game_code = 'coins' OR provider_code = 'm-and-m-games';
    IF v_partite <> 0 THEN
        RAISE EXCEPTION
            'Rollback 0065 impossibile: % partite legate a coins/m-and-m-games',
            v_partite;
    END IF;
END $$;

DELETE FROM site_titles
WHERE title_code IN ('coins', 'coins001');

DELETE FROM title_configs
WHERE title_code IN ('coins', 'coins001');

DELETE FROM game_titles
WHERE title_code IN ('coins', 'coins001');

DELETE FROM game_engines
WHERE engine_code = 'coins';

DELETE FROM game_providers
WHERE provider_code = 'm-and-m-games';

COMMIT;
