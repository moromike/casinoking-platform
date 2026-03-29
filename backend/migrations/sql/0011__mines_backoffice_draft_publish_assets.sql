-- CasinoKing Mines backoffice draft/publish split and board assets
-- Source references:
-- - docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md
-- - docs/md/CasinoKing_Documento_09_v2_Game_Engine_Testing.md
-- - docs/md/CasinoKing_Documento_21_Vincoli_Priorita_Gioco_Mines.md
--
-- Scope of this migration:
-- - separate editorial draft from published live config
-- - add persisted board asset slots for diamond and mine
-- - preserve the official runtime as the mathematical source of truth

BEGIN;

ALTER TABLE mines_backoffice_config
    ADD COLUMN IF NOT EXISTS published_board_assets_json jsonb NOT NULL DEFAULT '{"safe_icon_data_url": null, "mine_icon_data_url": null}'::jsonb,
    ADD COLUMN IF NOT EXISTS draft_rules_sections_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS draft_grid_sizes_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS draft_mine_counts_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS draft_default_mine_counts_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS draft_ui_labels_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS draft_board_assets_json jsonb NULL,
    ADD COLUMN IF NOT EXISTS published_at timestamptz NULL,
    ADD COLUMN IF NOT EXISTS draft_updated_by_admin_user_id uuid NULL REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS draft_updated_at timestamptz NULL;

UPDATE mines_backoffice_config
SET published_board_assets_json = '{"safe_icon_data_url": null, "mine_icon_data_url": null}'::jsonb
WHERE published_board_assets_json IS NULL;

ALTER TABLE mines_backoffice_config
    ADD CONSTRAINT mines_backoffice_config_published_board_assets_json_object_check
        CHECK (jsonb_typeof(published_board_assets_json) = 'object');

COMMIT;
