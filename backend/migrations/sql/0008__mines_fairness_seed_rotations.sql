-- CasinoKing Mines fairness seed rotations
-- Source references:
-- - docs/md/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.md
-- - docs/md/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.md
-- - docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md
--
-- Scope of this migration:
-- - persist internal fairness seed rotations for Mines
-- - support one active seed per game code with rotation audit trail
--
-- Explicitly deferred:
-- - external reveal flows
-- - separate secret store
-- - client seed and verification tooling

BEGIN;

CREATE TABLE fairness_seed_rotations (
    id uuid PRIMARY KEY,
    game_code varchar(32) NOT NULL,
    fairness_version varchar(32) NOT NULL,
    server_seed text NOT NULL,
    server_seed_hash varchar(128) NOT NULL UNIQUE,
    status varchar(16) NOT NULL,
    rotated_by_admin_user_id uuid NULL REFERENCES users(id),
    idempotency_key varchar(128) NULL UNIQUE,
    activated_at timestamptz NOT NULL,
    retired_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fairness_seed_rotations_game_code_check
        CHECK (game_code = 'mines'),
    CONSTRAINT fairness_seed_rotations_status_check
        CHECK (status IN ('active', 'retired'))
);

CREATE UNIQUE INDEX idx_fairness_seed_rotations_active_game_code
    ON fairness_seed_rotations (game_code)
    WHERE status = 'active';

CREATE INDEX idx_fairness_seed_rotations_created_at
    ON fairness_seed_rotations (created_at DESC);

COMMIT;
