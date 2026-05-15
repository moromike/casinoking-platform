-- CasinoKing - Game title logical archive and test flag.
-- Additive only: no hard delete, no cascade, no financial table changes.

BEGIN;

ALTER TABLE game_titles
    ADD COLUMN IF NOT EXISTS archived_at timestamptz NULL,
    ADD COLUMN IF NOT EXISTS archived_by_admin_user_id uuid NULL REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS archive_reason text NULL,
    ADD COLUMN IF NOT EXISTS is_test boolean NOT NULL DEFAULT false;

ALTER TABLE game_titles
    DROP CONSTRAINT IF EXISTS game_titles_master_not_test_check,
    ADD CONSTRAINT game_titles_master_not_test_check
        CHECK (is_master = false OR is_test = false);

CREATE INDEX IF NOT EXISTS idx_game_titles_active_status_test
    ON game_titles (status, is_test, engine_code, display_name)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_game_titles_archived_at
    ON game_titles (archived_at)
    WHERE archived_at IS NOT NULL;

COMMIT;
