-- Site V3 - Persistence for modular public site.
--
-- Scope:
-- - introduce Site V3 pages with locale-aware identity
-- - introduce immutable page versions for draft/published history
-- - introduce draft modules attached to pages
-- - keep cms_v2_* dormant and untouched
--
-- Rollback plan:
--   BEGIN;
--   DROP TABLE IF EXISTS site_v3_modules;
--   DROP TABLE IF EXISTS site_v3_page_versions;
--   DROP TABLE IF EXISTS site_v3_pages;
--   COMMIT;
--
-- After published Site V3 content exists, rollback is data-destructive and
-- requires exporting snapshots plus CTO approval.

BEGIN;

CREATE TABLE site_v3_pages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    page_code varchar(64) NOT NULL,
    locale varchar(8) NOT NULL DEFAULT 'it',
    title varchar(160) NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'draft',
    draft_version integer NOT NULL DEFAULT 0,
    published_version integer NULL,
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    archived_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    archived_at timestamptz NULL,
    CONSTRAINT site_v3_pages_page_code_not_blank_check
        CHECK (length(btrim(page_code)) > 0),
    CONSTRAINT site_v3_pages_page_code_format_check
        CHECK (page_code ~ '^[a-z0-9][a-z0-9_-]{1,63}$'),
    CONSTRAINT site_v3_pages_locale_check
        CHECK (locale IN ('it', 'en', 'de', 'es')),
    CONSTRAINT site_v3_pages_title_not_blank_check
        CHECK (length(btrim(title)) > 0),
    CONSTRAINT site_v3_pages_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_v3_pages_draft_version_check
        CHECK (draft_version >= 0),
    CONSTRAINT site_v3_pages_published_version_check
        CHECK (published_version IS NULL OR published_version > 0),
    CONSTRAINT site_v3_pages_archive_consistency_check
        CHECK (
            (status = 'archived' AND archived_at IS NOT NULL)
            OR (status <> 'archived')
        )
);

CREATE UNIQUE INDEX idx_site_v3_pages_site_page_locale
    ON site_v3_pages (site_code, page_code, locale);

CREATE INDEX idx_site_v3_pages_site_status_updated
    ON site_v3_pages (site_code, status, updated_at DESC);

CREATE INDEX idx_site_v3_pages_site_locale_status
    ON site_v3_pages (site_code, locale, status);

CREATE TABLE site_v3_page_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id uuid NOT NULL REFERENCES site_v3_pages(id) ON DELETE CASCADE,
    version integer NOT NULL,
    status varchar(16) NOT NULL,
    snapshot_json jsonb NOT NULL,
    validation_json jsonb NOT NULL DEFAULT '{"status":"unknown","issues":[]}'::jsonb,
    created_by uuid NOT NULL REFERENCES users(id),
    published_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NULL,
    CONSTRAINT site_v3_page_versions_version_check
        CHECK (version > 0),
    CONSTRAINT site_v3_page_versions_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_v3_page_versions_snapshot_object_check
        CHECK (jsonb_typeof(snapshot_json) = 'object'),
    CONSTRAINT site_v3_page_versions_validation_object_check
        CHECK (jsonb_typeof(validation_json) = 'object'),
    CONSTRAINT site_v3_page_versions_publish_consistency_check
        CHECK (
            (status = 'published' AND published_at IS NOT NULL AND published_by IS NOT NULL)
            OR (status <> 'published')
        )
);

CREATE UNIQUE INDEX idx_site_v3_page_versions_page_version
    ON site_v3_page_versions (page_id, version);

CREATE INDEX idx_site_v3_page_versions_page_status_version
    ON site_v3_page_versions (page_id, status, version DESC);

CREATE INDEX idx_site_v3_page_versions_published_at
    ON site_v3_page_versions (published_at DESC)
    WHERE status = 'published';

CREATE TABLE site_v3_modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id uuid NOT NULL REFERENCES site_v3_pages(id) ON DELETE CASCADE,
    module_code varchar(64) NOT NULL,
    schema_version integer NOT NULL DEFAULT 1,
    slot_key varchar(64) NOT NULL DEFAULT 'main',
    sort_order integer NOT NULL DEFAULT 0,
    config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT site_v3_modules_module_code_not_blank_check
        CHECK (length(btrim(module_code)) > 0),
    CONSTRAINT site_v3_modules_module_code_format_check
        CHECK (module_code ~ '^[a-z0-9][a-z0-9_]{1,63}$'),
    CONSTRAINT site_v3_modules_schema_version_check
        CHECK (schema_version > 0),
    CONSTRAINT site_v3_modules_slot_key_not_blank_check
        CHECK (length(btrim(slot_key)) > 0),
    CONSTRAINT site_v3_modules_slot_key_format_check
        CHECK (slot_key ~ '^[a-z0-9][a-z0-9_-]{0,63}$'),
    CONSTRAINT site_v3_modules_sort_order_check
        CHECK (sort_order >= 0),
    CONSTRAINT site_v3_modules_config_object_check
        CHECK (jsonb_typeof(config_json) = 'object')
);

CREATE UNIQUE INDEX idx_site_v3_modules_page_slot_sort_order
    ON site_v3_modules (page_id, slot_key, sort_order);

CREATE INDEX idx_site_v3_modules_page_slot
    ON site_v3_modules (page_id, slot_key, sort_order ASC);

CREATE INDEX idx_site_v3_modules_module_code
    ON site_v3_modules (module_code, schema_version);

COMMIT;
