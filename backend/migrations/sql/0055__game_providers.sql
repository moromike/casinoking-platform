-- CasinoKing - provider ownership for game engines.
--
-- Every existing engine belongs to the internal CasinoKing provider.  The
-- backfill precedes NOT NULL so a migrated database cannot retain an orphan.

BEGIN;

CREATE TABLE game_providers (
    provider_code varchar(32) PRIMARY KEY,
    display_name varchar(120) NOT NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT game_providers_status_check
        CHECK (status IN ('active', 'suspended'))
);

INSERT INTO game_providers (provider_code, display_name, status)
VALUES ('casinoking', 'CasinoKing', 'active')
ON CONFLICT (provider_code) DO UPDATE
SET display_name = EXCLUDED.display_name,
    status = EXCLUDED.status;

ALTER TABLE game_engines
    ADD COLUMN provider_code varchar(32);

UPDATE game_engines
SET provider_code = 'casinoking'
WHERE provider_code IS NULL;

ALTER TABLE game_engines
    ALTER COLUMN provider_code SET NOT NULL,
    ADD CONSTRAINT game_engines_provider_code_fkey
        FOREIGN KEY (provider_code)
        REFERENCES game_providers(provider_code);

COMMIT;
