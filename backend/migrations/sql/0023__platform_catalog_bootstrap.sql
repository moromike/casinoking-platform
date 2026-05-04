-- Platform catalog bootstrap: Engine / Title / Site.
--
-- Scope:
-- - create the minimum catalog tables needed by the game suite roadmap
-- - seed the current Mines runtime as engine `mines`
-- - seed the current published game identity as title `mines_classic`
-- - seed the current local/public site identity as `casinoking`
--
-- Deliberately out of scope for this phase:
-- - no API/router
-- - no admin UI
-- - no title_code/site_code propagation to round/session tables
-- - no gameplay, wallet, ledger, RNG, fairness or payout changes

BEGIN;

CREATE TABLE game_engines (
    engine_code varchar(32) PRIMARY KEY,
    display_name varchar(120) NOT NULL,
    runtime_module varchar(160) NOT NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT game_engines_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE game_titles (
    title_code varchar(64) PRIMARY KEY,
    engine_code varchar(32) NOT NULL REFERENCES game_engines(engine_code),
    display_name varchar(160) NOT NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT game_titles_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE sites (
    site_code varchar(32) PRIMARY KEY,
    display_name varchar(160) NOT NULL,
    base_url text NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT sites_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE site_titles (
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    position integer NOT NULL DEFAULT 0,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    PRIMARY KEY (site_code, title_code),
    CONSTRAINT site_titles_status_check
        CHECK (status IN ('active', 'inactive')),
    CONSTRAINT site_titles_position_check
        CHECK (position >= 0)
);

CREATE INDEX idx_game_titles_engine_code
    ON game_titles (engine_code);

CREATE INDEX idx_site_titles_title_code
    ON site_titles (title_code);

INSERT INTO game_engines (
    engine_code,
    display_name,
    runtime_module,
    status
)
VALUES (
    'mines',
    'Mines',
    'app.modules.games.mines',
    'active'
)
ON CONFLICT (engine_code) DO NOTHING;

INSERT INTO game_titles (
    title_code,
    engine_code,
    display_name,
    status
)
VALUES (
    'mines_classic',
    'mines',
    'Mines Classic',
    'active'
)
ON CONFLICT (title_code) DO NOTHING;

INSERT INTO sites (
    site_code,
    display_name,
    base_url,
    status
)
VALUES (
    'casinoking',
    'CasinoKing',
    NULL,
    'active'
)
ON CONFLICT (site_code) DO NOTHING;

INSERT INTO site_titles (
    site_code,
    title_code,
    position,
    status
)
VALUES (
    'casinoking',
    'mines_classic',
    0,
    'active'
)
ON CONFLICT (site_code, title_code) DO NOTHING;

COMMIT;
