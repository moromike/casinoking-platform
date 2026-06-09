-- CasinoKing - HI-LO catalog seed.
--
-- Scope:
-- - register HI-LO engine and canonical master/first variant
-- - assign both Titles to CasinoKing site in hidden, non-launchable state
-- - seed generic title_configs rows required by shared title/theme surfaces
-- - no wallet, ledger, platform_rounds, math, RNG, fairness, or gameplay changes

BEGIN;

INSERT INTO game_engines (
    engine_code,
    display_name,
    runtime_module,
    status
)
VALUES (
    'hi_lo',
    'HI-LO',
    'app.modules.games.hi_lo',
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
    ('hi_lo', 'hi_lo', 'HI-LO Master', 'active', true, NULL),
    ('hilo001', 'hi_lo', 'HI-LO 001', 'active', false, 'hi_lo')
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
        'hi_lo',
        920,
        'active',
        'hidden',
        false,
        false,
        'HI-LO Master',
        'Reference master Title for HI-LO.',
        false
    ),
    (
        'casinoking',
        'hilo001',
        921,
        'active',
        'hidden',
        false,
        false,
        'HI-LO',
        'Predict the next card, climb the multiplier, and collect before the streak breaks.',
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
    ('hi_lo', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW()),
    ('hilo001', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
ON CONFLICT (title_code)
DO NOTHING;

COMMIT;
