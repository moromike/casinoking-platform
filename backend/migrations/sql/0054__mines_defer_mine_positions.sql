-- CasinoKing - SIC-08: defer mine positions materialization to round close.
--
-- Scope:
-- - mine_positions_json and rng_material are a deterministic function of
--   (server_seed, nonce, grid_size, mine_count, fairness_version)
--   (see app/modules/games/mines/randomness.py generate_board).
-- - writing them while the round is OPEN exposes the outcome in cleartext
--   to anyone who can read the database.
-- - they are now recomputed on the fly during the round and persisted only
--   when the round reaches a terminal status (won/lost/cancelled), so the
--   fairness verification of closed rounds keeps working unchanged.
--
-- This migration only relaxes the NOT NULL constraints so OPEN rounds can
-- store NULL in both columns.

BEGIN;

ALTER TABLE mines_game_rounds
    ALTER COLUMN mine_positions_json DROP NOT NULL;

ALTER TABLE mines_game_rounds
    ALTER COLUMN rng_material DROP NOT NULL;

COMMIT;
