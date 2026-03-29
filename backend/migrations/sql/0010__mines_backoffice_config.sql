-- CasinoKing Mines backoffice configuration
-- Source references:
-- - docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md
-- - docs/md/CasinoKing_Documento_08_v2_Game_Tuning_Numerico.md
-- - docs/md/CasinoKing_Documento_21_Vincoli_Priorita_Gioco_Mines.md
--
-- Scope of this migration:
-- - persist editorial and publication config for Mines
-- - keep runtime math official and separate from backoffice publication choices
-- - support HTML rules content, published grid/mine choices and UI labels

BEGIN;

CREATE TABLE mines_backoffice_config (
    game_code text PRIMARY KEY,
    rules_sections_json jsonb NOT NULL,
    published_grid_sizes_json jsonb NOT NULL,
    published_mine_counts_json jsonb NOT NULL,
    default_mine_counts_json jsonb NOT NULL,
    ui_labels_json jsonb NOT NULL,
    updated_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT mines_backoffice_config_game_code_check
        CHECK (game_code = 'mines'),
    CONSTRAINT mines_backoffice_config_rules_sections_json_object_check
        CHECK (jsonb_typeof(rules_sections_json) = 'object'),
    CONSTRAINT mines_backoffice_config_published_grid_sizes_json_array_check
        CHECK (jsonb_typeof(published_grid_sizes_json) = 'array'),
    CONSTRAINT mines_backoffice_config_published_mine_counts_json_object_check
        CHECK (jsonb_typeof(published_mine_counts_json) = 'object'),
    CONSTRAINT mines_backoffice_config_default_mine_counts_json_object_check
        CHECK (jsonb_typeof(default_mine_counts_json) = 'object'),
    CONSTRAINT mines_backoffice_config_ui_labels_json_object_check
        CHECK (jsonb_typeof(ui_labels_json) = 'object')
);

COMMIT;
