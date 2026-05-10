-- CMS-2D - Site-owned banner assets.
--
-- Scope:
-- - introduce a minimal site media surface for homepage banners
-- - keep media site-owned instead of reusing title_assets
-- - do not create a generic media library, folders, tagging or image editor
-- - keep wallet, ledger, gameplay and Mines runtime untouched

BEGIN;

CREATE TABLE site_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    asset_kind varchar(32) NOT NULL,
    file_path text NOT NULL,
    public_url text NOT NULL,
    mime varchar(64) NOT NULL,
    byte_size integer NOT NULL,
    checksum_sha256 varchar(64) NOT NULL,
    uploaded_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    status varchar(16) NOT NULL,
    CONSTRAINT site_assets_status_check
        CHECK (status IN ('active', 'deleted')),
    CONSTRAINT site_assets_kind_check
        CHECK (asset_kind IN ('homepage_banner')),
    CONSTRAINT site_assets_file_path_not_blank_check
        CHECK (length(btrim(file_path)) > 0),
    CONSTRAINT site_assets_public_url_not_blank_check
        CHECK (length(btrim(public_url)) > 0),
    CONSTRAINT site_assets_mime_not_blank_check
        CHECK (length(btrim(mime)) > 0),
    CONSTRAINT site_assets_byte_size_positive_check
        CHECK (byte_size > 0),
    CONSTRAINT site_assets_checksum_sha256_length_check
        CHECK (length(checksum_sha256) = 64),
    CONSTRAINT site_assets_checksum_sha256_hex_check
        CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE UNIQUE INDEX site_assets_checksum_per_site_kind_idx
    ON site_assets (site_code, asset_kind, checksum_sha256);

CREATE INDEX idx_site_assets_site_kind_status
    ON site_assets (site_code, asset_kind, status, created_at DESC);

ALTER TABLE site_home_slots
    DROP CONSTRAINT IF EXISTS site_home_slots_media_asset_id_fkey;

-- CMS-2A had a provisional title_assets reference before site-owned media existed.
-- Since the UI could not upload/select banner media yet, clear any incompatible
-- manual references before enforcing the site_assets boundary.
UPDATE site_home_slots
SET media_asset_id = NULL
WHERE media_asset_id IS NOT NULL;

ALTER TABLE site_home_slots
    ADD CONSTRAINT site_home_slots_media_asset_id_fkey
    FOREIGN KEY (media_asset_id) REFERENCES site_assets(id);

COMMIT;
