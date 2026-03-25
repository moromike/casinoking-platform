-- CasinoKing Mines fairness seeded internal evolution
-- Source references:
-- - docs/md/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.md
-- - docs/md/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.md
-- - docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md
--
-- Scope of this migration:
-- - introduce nonce and server_seed_hash persistence on game_sessions
-- - prepare seeded internal fairness with unique nonce tracking
--
-- Explicitly deferred:
-- - external reveal APIs
-- - client_seed and provably-fair verification tooling

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SEQUENCE IF NOT EXISTS game_sessions_nonce_seq AS bigint;

ALTER TABLE game_sessions
    ADD COLUMN nonce bigint NULL,
    ADD COLUMN server_seed_hash varchar(128) NULL;

UPDATE game_sessions
SET nonce = nextval('game_sessions_nonce_seq')
WHERE nonce IS NULL;

UPDATE game_sessions
SET server_seed_hash = encode(digest(rng_material, 'sha256'), 'hex')
WHERE server_seed_hash IS NULL;

ALTER TABLE game_sessions
    ALTER COLUMN nonce SET NOT NULL,
    ALTER COLUMN nonce SET DEFAULT nextval('game_sessions_nonce_seq'),
    ALTER COLUMN server_seed_hash SET NOT NULL;

CREATE UNIQUE INDEX idx_game_sessions_nonce_unique
    ON game_sessions (nonce);

COMMIT;
