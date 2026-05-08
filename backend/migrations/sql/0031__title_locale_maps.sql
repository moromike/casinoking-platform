-- CasinoKing Title locale maps
--
-- Versioned player-facing copy per Title. Mines publishes exactly one locale
-- per Title/config at runtime: no player-side language selector and no
-- locale query parameter. This is Title-level, not platform-wide i18n, and
-- does not touch payout/RNG/wallet/ledger.

CREATE TABLE IF NOT EXISTS title_locale_maps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code) ON DELETE CASCADE,
    version integer NOT NULL,
    status varchar(16) NOT NULL,
    is_current boolean NOT NULL DEFAULT false,
    default_locale_code varchar(16) NOT NULL,
    fallback_locale_code varchar(16) NOT NULL DEFAULT 'it',
    locales_json jsonb NOT NULL,
    completeness_json jsonb NOT NULL,
    content_hash_sha256 varchar(64) NOT NULL,
    created_by_admin_user_id uuid NULL REFERENCES users(id),
    published_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NULL,
    CONSTRAINT title_locale_maps_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT title_locale_maps_version_positive_check
        CHECK (version > 0),
    CONSTRAINT title_locale_maps_default_locale_not_blank_check
        CHECK (char_length(trim(default_locale_code)) > 0),
    CONSTRAINT title_locale_maps_fallback_locale_not_blank_check
        CHECK (char_length(trim(fallback_locale_code)) > 0),
    CONSTRAINT title_locale_maps_single_published_locale_check
        CHECK (default_locale_code = fallback_locale_code),
    CONSTRAINT title_locale_maps_locales_object_check
        CHECK (jsonb_typeof(locales_json) = 'object'),
    CONSTRAINT title_locale_maps_default_locale_payload_check
        CHECK (
            locales_json ? default_locale_code
        ),
    CONSTRAINT title_locale_maps_completeness_object_check
        CHECK (jsonb_typeof(completeness_json) = 'object'),
    CONSTRAINT title_locale_maps_content_hash_sha256_check
        CHECK (content_hash_sha256 ~ '^[a-f0-9]{64}$'),
    UNIQUE (title_code, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS title_locale_maps_one_draft_per_title
    ON title_locale_maps (title_code)
    WHERE status = 'draft';

CREATE UNIQUE INDEX IF NOT EXISTS title_locale_maps_one_current_published_per_title
    ON title_locale_maps (title_code)
    WHERE status = 'published' AND is_current = true;

CREATE INDEX IF NOT EXISTS idx_title_locale_maps_title_status
    ON title_locale_maps (title_code, status, version DESC);
