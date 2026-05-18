-- CasinoKing - BOXE admin config draft/live state.
--
-- Scope:
-- - persist BOXE operator-owned rows/difficulty settings
-- - persist BOXE copy/rules draft and published payload
-- - no platform, wallet, ledger, Mines, or runtime math schema changes

BEGIN;

CREATE TABLE IF NOT EXISTS boxe_admin_config (
    title_code varchar(64) PRIMARY KEY REFERENCES game_titles(title_code) ON DELETE CASCADE,
    rows_enabled_json jsonb NOT NULL,
    default_rows integer NOT NULL,
    difficulty_enabled_json jsonb NOT NULL,
    default_difficulty varchar(16) NOT NULL,
    draft_payload_json jsonb NOT NULL,
    published_payload_json jsonb NOT NULL,
    draft_updated_by_admin_user_id uuid NULL REFERENCES users(id),
    published_updated_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    draft_updated_at timestamptz NULL,
    published_at timestamptz NULL,
    CONSTRAINT boxe_admin_config_rows_enabled_json_array_check
        CHECK (jsonb_typeof(rows_enabled_json) = 'array'),
    CONSTRAINT boxe_admin_config_default_rows_check
        CHECK (default_rows IN (4, 5, 6, 7, 8)),
    CONSTRAINT boxe_admin_config_difficulty_enabled_json_array_check
        CHECK (jsonb_typeof(difficulty_enabled_json) = 'array'),
    CONSTRAINT boxe_admin_config_default_difficulty_check
        CHECK (default_difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT boxe_admin_config_draft_payload_json_object_check
        CHECK (jsonb_typeof(draft_payload_json) = 'object'),
    CONSTRAINT boxe_admin_config_published_payload_json_object_check
        CHECK (jsonb_typeof(published_payload_json) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_boxe_admin_config_published_at
    ON boxe_admin_config (published_at DESC)
    WHERE published_at IS NOT NULL;

COMMIT;
