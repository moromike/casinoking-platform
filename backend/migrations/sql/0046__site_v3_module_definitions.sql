-- Site V3 - Custom module definition registry.
--
-- Scope:
-- - persist operator-authored module definitions behind safe renderer templates
-- - keep draft definitions mutable and published versions immutable
-- - do not mount custom modules on public pages in this migration
--
-- Rollback plan:
--   BEGIN;
--   DROP TABLE IF EXISTS site_v3_module_definition_versions;
--   DROP TABLE IF EXISTS site_v3_module_definitions;
--   COMMIT;
--
-- Published custom definitions are part of CMS product state. Rollback after
-- publication requires exporting definitions and CTO approval.

BEGIN;

CREATE TABLE site_v3_module_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    module_code varchar(64) NOT NULL,
    label varchar(120) NOT NULL,
    category varchar(32) NOT NULL,
    renderer_template varchar(64) NOT NULL,
    draft_schema_version integer NOT NULL DEFAULT 1,
    draft_field_schema_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    draft_default_config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(16) NOT NULL DEFAULT 'draft',
    published_version integer NULL,
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    published_by uuid NULL REFERENCES users(id),
    archived_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NULL,
    archived_at timestamptz NULL,
    CONSTRAINT site_v3_module_definitions_module_code_not_blank_check
        CHECK (length(btrim(module_code)) > 0),
    CONSTRAINT site_v3_module_definitions_module_code_format_check
        CHECK (module_code ~ '^custom_[a-z0-9][a-z0-9_]{1,56}$'),
    CONSTRAINT site_v3_module_definitions_label_not_blank_check
        CHECK (length(btrim(label)) > 0),
    CONSTRAINT site_v3_module_definitions_category_check
        CHECK (category IN ('hero', 'catalog', 'promo', 'text_legal')),
    CONSTRAINT site_v3_module_definitions_renderer_template_check
        CHECK (renderer_template IN ('image_banner', 'game_grid', 'editorial_panel', 'rich_text', 'feature_card')),
    CONSTRAINT site_v3_module_definitions_schema_version_check
        CHECK (draft_schema_version > 0),
    CONSTRAINT site_v3_module_definitions_field_schema_array_check
        CHECK (jsonb_typeof(draft_field_schema_json) = 'array'),
    CONSTRAINT site_v3_module_definitions_default_config_object_check
        CHECK (jsonb_typeof(draft_default_config_json) = 'object'),
    CONSTRAINT site_v3_module_definitions_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_v3_module_definitions_published_version_check
        CHECK (published_version IS NULL OR published_version > 0),
    CONSTRAINT site_v3_module_definitions_archive_consistency_check
        CHECK (
            (status = 'archived' AND archived_at IS NOT NULL AND archived_by IS NOT NULL)
            OR (status <> 'archived')
        ),
    CONSTRAINT site_v3_module_definitions_publish_consistency_check
        CHECK (
            (status = 'published' AND published_version IS NOT NULL AND published_at IS NOT NULL AND published_by IS NOT NULL)
            OR (status <> 'published')
        )
);

CREATE UNIQUE INDEX idx_site_v3_module_definitions_site_module
    ON site_v3_module_definitions (site_code, module_code);

CREATE INDEX idx_site_v3_module_definitions_site_status_updated
    ON site_v3_module_definitions (site_code, status, updated_at DESC);

CREATE INDEX idx_site_v3_module_definitions_site_category
    ON site_v3_module_definitions (site_code, category, status);

CREATE TABLE site_v3_module_definition_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id uuid NOT NULL REFERENCES site_v3_module_definitions(id) ON DELETE CASCADE,
    version integer NOT NULL,
    label varchar(120) NOT NULL,
    category varchar(32) NOT NULL,
    renderer_template varchar(64) NOT NULL,
    schema_version integer NOT NULL,
    field_schema_json jsonb NOT NULL,
    default_config_json jsonb NOT NULL,
    created_by uuid NOT NULL REFERENCES users(id),
    published_by uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT site_v3_module_definition_versions_version_check
        CHECK (version > 0),
    CONSTRAINT site_v3_module_definition_versions_category_check
        CHECK (category IN ('hero', 'catalog', 'promo', 'text_legal')),
    CONSTRAINT site_v3_module_definition_versions_renderer_template_check
        CHECK (renderer_template IN ('image_banner', 'game_grid', 'editorial_panel', 'rich_text', 'feature_card')),
    CONSTRAINT site_v3_module_definition_versions_schema_version_check
        CHECK (schema_version > 0),
    CONSTRAINT site_v3_module_definition_versions_field_schema_array_check
        CHECK (jsonb_typeof(field_schema_json) = 'array'),
    CONSTRAINT site_v3_module_definition_versions_default_config_object_check
        CHECK (jsonb_typeof(default_config_json) = 'object')
);

CREATE UNIQUE INDEX idx_site_v3_module_definition_versions_definition_version
    ON site_v3_module_definition_versions (definition_id, version);

CREATE INDEX idx_site_v3_module_definition_versions_published_at
    ON site_v3_module_definition_versions (published_at DESC);

COMMIT;
