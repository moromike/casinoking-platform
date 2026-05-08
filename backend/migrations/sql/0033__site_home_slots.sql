-- CMS-2A - Homepage/banner slots for Site CMS.
--
-- Scope:
-- - introduce a platform-owned editorial surface for homepage/lobby banners
-- - validate launchable Title targets in the backend service, not in SQL
-- - keep this slice outside wallet, ledger, gameplay, RNG and launch flows

BEGIN;

CREATE TABLE site_home_slots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    slot_key varchar(64) NOT NULL,
    title varchar(160) NOT NULL,
    subtitle text NULL,
    cta_label varchar(80) NULL,
    cta_target_type varchar(16) NOT NULL DEFAULT 'none',
    cta_target_ref varchar(64) NULL REFERENCES game_titles(title_code),
    media_asset_id uuid NULL REFERENCES title_assets(id),
    sort_order integer NOT NULL DEFAULT 0,
    status varchar(16) NOT NULL DEFAULT 'draft',
    starts_at timestamptz NULL,
    ends_at timestamptz NULL,
    created_by uuid NULL REFERENCES users(id),
    updated_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT site_home_slots_slot_key_not_blank_check
        CHECK (length(btrim(slot_key)) > 0),
    CONSTRAINT site_home_slots_slot_key_format_check
        CHECK (slot_key ~ '^[a-z0-9][a-z0-9_-]{1,63}$'),
    CONSTRAINT site_home_slots_title_not_blank_check
        CHECK (length(btrim(title)) > 0),
    CONSTRAINT site_home_slots_subtitle_length_check
        CHECK (subtitle IS NULL OR length(subtitle) <= 500),
    CONSTRAINT site_home_slots_cta_label_length_check
        CHECK (cta_label IS NULL OR length(cta_label) <= 80),
    CONSTRAINT site_home_slots_cta_target_type_check
        CHECK (cta_target_type IN ('none', 'title_demo', 'title_real')),
    CONSTRAINT site_home_slots_cta_target_ref_check
        CHECK (
            (cta_target_type = 'none' AND cta_target_ref IS NULL)
            OR (cta_target_type IN ('title_demo', 'title_real') AND cta_target_ref IS NOT NULL)
        ),
    CONSTRAINT site_home_slots_sort_order_check
        CHECK (sort_order >= 0),
    CONSTRAINT site_home_slots_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_home_slots_schedule_check
        CHECK (starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at)
);

CREATE UNIQUE INDEX site_home_slots_site_slot_key_idx
    ON site_home_slots (site_code, slot_key);

CREATE INDEX idx_site_home_slots_public
    ON site_home_slots (site_code, status, sort_order, starts_at, ends_at);

CREATE INDEX idx_site_home_slots_media_asset
    ON site_home_slots (media_asset_id)
    WHERE media_asset_id IS NOT NULL;

CREATE INDEX idx_site_home_slots_target_ref
    ON site_home_slots (cta_target_ref)
    WHERE cta_target_ref IS NOT NULL;

COMMIT;
