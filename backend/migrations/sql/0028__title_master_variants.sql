-- Title master/variant metadata.
--
-- Scope:
-- - mark canonical engine Titles that must stay immutable from admin UI
-- - track which master a variant was derived from
-- - seed the current Mines Title as the Mines master

BEGIN;

ALTER TABLE game_titles
    ADD COLUMN IF NOT EXISTS is_master boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS source_title_code varchar(64) NULL REFERENCES game_titles(title_code);

CREATE INDEX IF NOT EXISTS idx_game_titles_source_title_code
    ON game_titles (source_title_code);

UPDATE game_titles
SET is_master = true,
    source_title_code = NULL,
    updated_at = NOW()
WHERE title_code = 'mines_classic';

UPDATE game_titles
SET source_title_code = 'mines_classic',
    updated_at = NOW()
WHERE engine_code = 'mines'
  AND title_code <> 'mines_classic'
  AND source_title_code IS NULL;

COMMIT;
