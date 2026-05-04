-- CasinoKing Phase 4 - Title asset registry
-- Source references:
-- - docs/ASSET_REGISTRY_PLAN.md
-- - docs/TITLE_CONFIG_PLAN.md
-- - docs/md/CasinoKing_Documento_37_Catalogo_Engine_Title_Site.md
-- - docs/md/CasinoKing_Documento_38_Configurazione_Per_Title.md
--
-- Scope of this migration:
-- - introduce a platform-owned asset registry for Title assets
-- - keep one active asset per title_code + asset_kind
-- - allow checksum-based idempotency and versioned static URLs
--
-- Out of scope:
-- - moving existing data-URL payloads from mines_title_configs to files
-- - removing legacy board_assets JSON/data-URL support
-- - changes to gameplay, payout runtime, RNG, fairness, wallet or ledger

BEGIN;

CREATE TABLE title_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    asset_kind varchar(32) NOT NULL,
    file_path text NOT NULL,
    public_url text NOT NULL,
    mime varchar(64) NOT NULL,
    byte_size integer NOT NULL,
    checksum_sha256 varchar(64) NOT NULL,
    uploaded_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    status varchar(16) NOT NULL,
    CONSTRAINT title_assets_status_check
        CHECK (status IN ('active', 'deleted')),
    CONSTRAINT title_assets_kind_check
        CHECK (asset_kind IN (
            'logo',
            'background',
            'symbol_safe',
            'symbol_mine',
            'audio_win',
            'audio_lose',
            'audio_click',
            'font'
        )),
    CONSTRAINT title_assets_file_path_not_blank_check
        CHECK (length(btrim(file_path)) > 0),
    CONSTRAINT title_assets_public_url_not_blank_check
        CHECK (length(btrim(public_url)) > 0),
    CONSTRAINT title_assets_mime_not_blank_check
        CHECK (length(btrim(mime)) > 0),
    CONSTRAINT title_assets_byte_size_positive_check
        CHECK (byte_size > 0),
    CONSTRAINT title_assets_checksum_sha256_length_check
        CHECK (length(checksum_sha256) = 64),
    CONSTRAINT title_assets_checksum_sha256_hex_check
        CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE UNIQUE INDEX title_assets_one_active_kind_per_title_idx
    ON title_assets (title_code, asset_kind)
    WHERE status = 'active';

CREATE UNIQUE INDEX title_assets_checksum_per_title_kind_idx
    ON title_assets (title_code, asset_kind, checksum_sha256);

CREATE INDEX idx_title_assets_title_code
    ON title_assets (title_code);

COMMIT;
