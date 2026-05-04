-- Fase 2: propagate commercial Title/Site identity alongside legacy engine game_code.
-- game_code remains engine-scoped. title_code/site_code are persisted for audit,
-- reporting and dispute reconstruction.

ALTER TABLE platform_rounds
    ADD COLUMN title_code text,
    ADD COLUMN site_code text;

ALTER TABLE game_access_sessions
    ADD COLUMN title_code text,
    ADD COLUMN site_code text;

ALTER TABLE game_table_sessions
    ADD COLUMN title_code text,
    ADD COLUMN site_code text;

ALTER TABLE mines_game_rounds
    ADD COLUMN title_code text,
    ADD COLUMN site_code text;

UPDATE platform_rounds
SET
    title_code = COALESCE(title_code, 'mines_classic'),
    site_code = COALESCE(site_code, 'casinoking');

UPDATE game_access_sessions
SET
    title_code = COALESCE(title_code, 'mines_classic'),
    site_code = COALESCE(site_code, 'casinoking');

UPDATE game_table_sessions
SET
    title_code = COALESCE(title_code, 'mines_classic'),
    site_code = COALESCE(site_code, 'casinoking');

UPDATE mines_game_rounds mgr
SET
    title_code = COALESCE(mgr.title_code, pr.title_code, 'mines_classic'),
    site_code = COALESCE(mgr.site_code, pr.site_code, 'casinoking')
FROM platform_rounds pr
WHERE mgr.platform_round_id = pr.id;

UPDATE mines_game_rounds
SET
    title_code = COALESCE(title_code, 'mines_classic'),
    site_code = COALESCE(site_code, 'casinoking');

ALTER TABLE platform_rounds
    ALTER COLUMN title_code SET NOT NULL,
    ALTER COLUMN site_code SET NOT NULL,
    ADD CONSTRAINT platform_rounds_title_code_fk
        FOREIGN KEY (title_code) REFERENCES game_titles(title_code),
    ADD CONSTRAINT platform_rounds_site_code_fk
        FOREIGN KEY (site_code) REFERENCES sites(site_code);

ALTER TABLE game_access_sessions
    ALTER COLUMN title_code SET NOT NULL,
    ALTER COLUMN site_code SET NOT NULL,
    ADD CONSTRAINT game_access_sessions_title_code_fk
        FOREIGN KEY (title_code) REFERENCES game_titles(title_code),
    ADD CONSTRAINT game_access_sessions_site_code_fk
        FOREIGN KEY (site_code) REFERENCES sites(site_code);

ALTER TABLE game_table_sessions
    ALTER COLUMN title_code SET NOT NULL,
    ALTER COLUMN site_code SET NOT NULL,
    ADD CONSTRAINT game_table_sessions_title_code_fk
        FOREIGN KEY (title_code) REFERENCES game_titles(title_code),
    ADD CONSTRAINT game_table_sessions_site_code_fk
        FOREIGN KEY (site_code) REFERENCES sites(site_code);

ALTER TABLE mines_game_rounds
    ALTER COLUMN title_code SET NOT NULL,
    ALTER COLUMN site_code SET NOT NULL,
    ADD CONSTRAINT mines_game_rounds_title_code_fk
        FOREIGN KEY (title_code) REFERENCES game_titles(title_code),
    ADD CONSTRAINT mines_game_rounds_site_code_fk
        FOREIGN KEY (site_code) REFERENCES sites(site_code);

CREATE INDEX idx_platform_rounds_title_site_created
    ON platform_rounds (title_code, site_code, created_at DESC);

CREATE INDEX idx_platform_rounds_site_created
    ON platform_rounds (site_code, created_at DESC);

CREATE INDEX idx_game_access_sessions_title_site_status
    ON game_access_sessions (title_code, site_code, status);

CREATE INDEX idx_game_table_sessions_title_site_status
    ON game_table_sessions (title_code, site_code, status);

CREATE INDEX idx_mines_game_rounds_title_site_created
    ON mines_game_rounds (title_code, site_code, created_at DESC);
