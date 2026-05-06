-- Lightweight site lobby publication for game Titles.
--
-- Scope:
-- - keep technical Site/Title publication separate from player lobby visibility
-- - allow admin to expose variants in demo/real without making masters editable

BEGIN;

ALTER TABLE site_titles
    ADD COLUMN IF NOT EXISTS lobby_visibility varchar(16) NOT NULL DEFAULT 'hidden',
    ADD COLUMN IF NOT EXISTS demo_enabled boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS real_enabled boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS lobby_display_name varchar(160) NULL,
    ADD COLUMN IF NOT EXISTS lobby_description text NULL,
    ADD COLUMN IF NOT EXISTS featured boolean NOT NULL DEFAULT false,
    ADD CONSTRAINT site_titles_lobby_visibility_check
        CHECK (lobby_visibility IN ('hidden', 'visible'));

UPDATE site_titles
SET lobby_visibility = 'hidden',
    demo_enabled = false,
    real_enabled = false,
    updated_at = NOW()
WHERE title_code IN (
    SELECT title_code
    FROM game_titles
    WHERE is_master = true
);

COMMIT;
