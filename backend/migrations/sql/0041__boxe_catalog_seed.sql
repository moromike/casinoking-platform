-- CasinoKing - BOXE catalog seed.
--
-- Scope:
-- - register BOXE engine and canonical master/first variant
-- - assign both Titles to CasinoKing site so admin Site/Lobby can publish them
-- - seed generic title_configs rows required by the shared theme service
-- - no wallet, ledger, platform_rounds, math, RNG, fairness, or gameplay changes

BEGIN;

INSERT INTO game_engines (
    engine_code,
    display_name,
    runtime_module,
    status
)
VALUES (
    'boxe',
    'BOXE',
    'app.modules.games.boxe',
    'active'
)
ON CONFLICT (engine_code)
DO UPDATE
SET display_name = EXCLUDED.display_name,
    runtime_module = EXCLUDED.runtime_module,
    status = 'active';

INSERT INTO game_titles (
    title_code,
    engine_code,
    display_name,
    status,
    is_master,
    source_title_code
)
VALUES
    ('boxe', 'boxe', 'BOXE Master', 'active', true, NULL),
    ('boxe001', 'boxe', 'BOXE 001', 'active', false, 'boxe')
ON CONFLICT (title_code)
DO UPDATE
SET engine_code = EXCLUDED.engine_code,
    display_name = EXCLUDED.display_name,
    status = 'active',
    is_master = EXCLUDED.is_master,
    source_title_code = EXCLUDED.source_title_code,
    updated_at = NOW();

INSERT INTO site_titles (
    site_code,
    title_code,
    position,
    status,
    lobby_visibility,
    demo_enabled,
    real_enabled,
    lobby_display_name,
    lobby_description,
    featured
)
VALUES
    (
        'casinoking',
        'boxe',
        900,
        'active',
        'hidden',
        false,
        false,
        'BOXE Master',
        'Reference master Title for BOXE.',
        false
    ),
    (
        'casinoking',
        'boxe001',
        901,
        'active',
        'hidden',
        false,
        false,
        'BOXE',
        'Pick safe boxes, climb the pyramid, and collect before a mine.',
        false
    )
ON CONFLICT (site_code, title_code)
DO UPDATE
SET status = 'active',
    position = EXCLUDED.position,
    lobby_visibility = EXCLUDED.lobby_visibility,
    demo_enabled = EXCLUDED.demo_enabled,
    real_enabled = EXCLUDED.real_enabled,
    lobby_display_name = EXCLUDED.lobby_display_name,
    lobby_description = EXCLUDED.lobby_description,
    featured = EXCLUDED.featured,
    updated_at = NOW();

INSERT INTO title_configs (
    title_code,
    rules_sections_json,
    ui_labels_json,
    draft_rules_sections_json,
    draft_ui_labels_json,
    created_at,
    updated_at
)
VALUES
    ('boxe', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW()),
    ('boxe001', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
ON CONFLICT (title_code)
DO NOTHING;

COMMIT;
