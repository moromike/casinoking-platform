-- CMS-V2-3 - Persistence for CMS v2 / Module Composer Lab.
--
-- Scope:
-- - introduce drafts and versions for modular pages
-- - separate CMS v2 schema from legacy site_home_slots

BEGIN;

CREATE TABLE cms_v2_pages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    page_code varchar(64) NOT NULL,
    title varchar(160) NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'draft', -- draft, published, archived
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT cms_v2_pages_page_code_not_blank_check
        CHECK (length(btrim(page_code)) > 0),
    CONSTRAINT cms_v2_pages_page_code_format_check
        CHECK (page_code ~ '^[a-z0-9][a-z0-9_-]{1,63}$'),
    CONSTRAINT cms_v2_pages_status_check
        CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE UNIQUE INDEX idx_cms_v2_pages_site_code_page_code 
    ON cms_v2_pages (site_code, page_code);

CREATE TABLE cms_v2_modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id uuid NOT NULL REFERENCES cms_v2_pages(id) ON DELETE CASCADE,
    slot_key varchar(64) NOT NULL,
    module_code varchar(64) NOT NULL,
    config jsonb NOT NULL DEFAULT '{}',
    sort_order integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT cms_v2_modules_slot_key_not_blank_check
        CHECK (length(btrim(slot_key)) > 0),
    CONSTRAINT cms_v2_modules_module_code_not_blank_check
        CHECK (length(btrim(module_code)) > 0),
    CONSTRAINT cms_v2_modules_sort_order_check
        CHECK (sort_order >= 0)
);

CREATE INDEX idx_cms_v2_modules_page_id ON cms_v2_modules (page_id);
CREATE INDEX idx_cms_v2_modules_slot_key ON cms_v2_modules (page_id, slot_key);

COMMIT;
