BEGIN;

DROP VIEW IF EXISTS game_sessions_compat;
DROP TABLE IF EXISTS game_sessions;
ALTER SEQUENCE IF EXISTS game_sessions_nonce_seq RENAME TO mines_fairness_nonce_seq;

COMMIT;
