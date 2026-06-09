-- DIV-02 Parte-B: unificazione demo Mines
-- Rimuove le FK su users per permettere round demo anonimi (pattern BOXE).

BEGIN;

ALTER TABLE mines_game_rounds
    DROP CONSTRAINT IF EXISTS mines_game_rounds_user_id_fkey;

ALTER TABLE mines_idempotency_keys
    DROP CONSTRAINT IF EXISTS mines_idempotency_keys_player_id_fkey;

COMMIT;
