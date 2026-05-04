-- CasinoKing Phase 3 - Title configuration split
-- Source references:
-- - docs/TITLE_CONFIG_PLAN.md (operational plan)
-- - C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md (roadmap v3)
--
-- Scope of this migration:
-- - rename existing mines_backoffice_config to mines_backoffice_config_legacy
-- - introduce title_configs (engine-agnostic) and mines_title_configs (engine-specific)
-- - copy mines_backoffice_config legacy data with title_code='mines_classic'
-- - expose a read-only mines_backoffice_config view for hidden readers during transition
--
-- Out of scope:
-- - DROP of mines_backoffice_config_legacy and the compatibility view: deferred to a
--   later cleanup migration once tests have been green for a cycle.
-- - changes to platform_rounds, mines_game_rounds, fairness_seed_rotations, ledger,
--   wallet snapshot, payout runtime or RNG.

BEGIN;

-- Step 1: rename legacy table preserving its data and CHECK (game_code='mines').
ALTER TABLE mines_backoffice_config RENAME TO mines_backoffice_config_legacy;

-- Step 2: generic title configuration (one row per Title).
-- Holds editorial fields shared across engines plus placeholders for future phases:
-- - bet_limits_json (Phase 5+ optional, NULL in Phase 3)
-- - demo_labels_json (Phase 6, NULL in Phase 3)
-- - theme_tokens_json (Phase 5, NULL in Phase 3)
-- Title-level audit fields live here so a single publish transaction across
-- title_configs + <engine>_title_configs shares a coherent provenance.
CREATE TABLE title_configs (
    title_code varchar(64) PRIMARY KEY REFERENCES game_titles(title_code),
    rules_sections_json jsonb NOT NULL,
    ui_labels_json jsonb NOT NULL,
    bet_limits_json jsonb NULL,
    demo_labels_json jsonb NULL,
    theme_tokens_json jsonb NULL,
    draft_rules_sections_json jsonb NULL,
    draft_ui_labels_json jsonb NULL,
    draft_bet_limits_json jsonb NULL,
    draft_demo_labels_json jsonb NULL,
    draft_theme_tokens_json jsonb NULL,
    published_at timestamptz NULL,
    updated_by_admin_user_id uuid NULL REFERENCES users(id),
    draft_updated_by_admin_user_id uuid NULL REFERENCES users(id),
    draft_updated_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT title_configs_rules_sections_object_check
        CHECK (jsonb_typeof(rules_sections_json) = 'object'),
    CONSTRAINT title_configs_ui_labels_object_check
        CHECK (jsonb_typeof(ui_labels_json) = 'object'),
    CONSTRAINT title_configs_bet_limits_object_check
        CHECK (bet_limits_json IS NULL OR jsonb_typeof(bet_limits_json) = 'object'),
    CONSTRAINT title_configs_demo_labels_object_check
        CHECK (demo_labels_json IS NULL OR jsonb_typeof(demo_labels_json) = 'object'),
    CONSTRAINT title_configs_theme_tokens_object_check
        CHECK (theme_tokens_json IS NULL OR jsonb_typeof(theme_tokens_json) = 'object')
);

-- Step 3: Mines engine-specific configuration (one row per Title that uses the
-- mines engine). Audit user_id columns live in title_configs because a publish
-- is a single Title-level operation.
CREATE TABLE mines_title_configs (
    title_code varchar(64) PRIMARY KEY REFERENCES game_titles(title_code),
    published_grid_sizes_json jsonb NOT NULL,
    published_mine_counts_json jsonb NOT NULL,
    default_mine_counts_json jsonb NOT NULL,
    published_board_assets_json jsonb NOT NULL,
    draft_grid_sizes_json jsonb NULL,
    draft_mine_counts_json jsonb NULL,
    draft_default_mine_counts_json jsonb NULL,
    draft_board_assets_json jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT mines_title_configs_published_grid_sizes_array_check
        CHECK (jsonb_typeof(published_grid_sizes_json) = 'array'),
    CONSTRAINT mines_title_configs_published_mine_counts_object_check
        CHECK (jsonb_typeof(published_mine_counts_json) = 'object'),
    CONSTRAINT mines_title_configs_default_mine_counts_object_check
        CHECK (jsonb_typeof(default_mine_counts_json) = 'object'),
    CONSTRAINT mines_title_configs_published_board_assets_object_check
        CHECK (jsonb_typeof(published_board_assets_json) = 'object')
);

-- Step 4: copy legacy data into the new tables. Idempotent on rerun thanks
-- to ON CONFLICT DO NOTHING. If the legacy table is empty (fresh environments)
-- no row is inserted; the service layer will UPSERT defaults on first write.
INSERT INTO title_configs (
    title_code,
    rules_sections_json,
    ui_labels_json,
    draft_rules_sections_json,
    draft_ui_labels_json,
    published_at,
    updated_by_admin_user_id,
    draft_updated_by_admin_user_id,
    draft_updated_at,
    created_at,
    updated_at
)
SELECT
    'mines_classic',
    rules_sections_json,
    ui_labels_json,
    draft_rules_sections_json,
    draft_ui_labels_json,
    published_at,
    updated_by_admin_user_id,
    draft_updated_by_admin_user_id,
    draft_updated_at,
    created_at,
    updated_at
FROM mines_backoffice_config_legacy
WHERE game_code = 'mines'
ON CONFLICT (title_code) DO NOTHING;

INSERT INTO mines_title_configs (
    title_code,
    published_grid_sizes_json,
    published_mine_counts_json,
    default_mine_counts_json,
    published_board_assets_json,
    draft_grid_sizes_json,
    draft_mine_counts_json,
    draft_default_mine_counts_json,
    draft_board_assets_json,
    created_at,
    updated_at
)
SELECT
    'mines_classic',
    published_grid_sizes_json,
    published_mine_counts_json,
    default_mine_counts_json,
    published_board_assets_json,
    draft_grid_sizes_json,
    draft_mine_counts_json,
    draft_default_mine_counts_json,
    draft_board_assets_json,
    created_at,
    updated_at
FROM mines_backoffice_config_legacy
WHERE game_code = 'mines'
ON CONFLICT (title_code) DO NOTHING;

-- Step 5: read-only compatibility view for hidden readers still looking at the
-- old table name. Writers (DELETE/INSERT/UPDATE) on this view are NOT supported
-- and are not allowed: by design, all writers must be migrated to the new
-- tables in the same code commit (no INSTEAD OF triggers, to avoid hidden
-- dual sources of truth).
CREATE VIEW mines_backoffice_config AS
SELECT
    'mines'::text AS game_code,
    tc.rules_sections_json,
    mtc.published_grid_sizes_json,
    mtc.published_mine_counts_json,
    mtc.default_mine_counts_json,
    tc.ui_labels_json,
    mtc.published_board_assets_json,
    tc.draft_rules_sections_json,
    mtc.draft_grid_sizes_json,
    mtc.draft_mine_counts_json,
    mtc.draft_default_mine_counts_json,
    tc.draft_ui_labels_json,
    mtc.draft_board_assets_json,
    tc.published_at,
    tc.updated_by_admin_user_id,
    tc.draft_updated_by_admin_user_id,
    tc.draft_updated_at,
    tc.created_at,
    tc.updated_at
FROM title_configs tc
JOIN mines_title_configs mtc ON mtc.title_code = tc.title_code
WHERE tc.title_code = 'mines_classic';

COMMIT;
