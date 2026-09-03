BEGIN;

-- 1. Il titolo giocabile, clonato dal master, come boxe001 e hilo001.
INSERT INTO game_titles (title_code, engine_code, display_name, status, is_master, source_title_code, is_test)
SELECT 'mines001', engine_code, 'Mines', status, false, 'mines_classic', false
  FROM game_titles WHERE title_code = 'mines_classic'
ON CONFLICT (title_code) DO NOTHING;

-- 2. La configurazione comune (regole, etichette), copiata dal master.
INSERT INTO title_configs (title_code, rules_sections_json, ui_labels_json, bet_limits_json,
                           demo_labels_json, theme_tokens_json, published_at, created_at, updated_at)
SELECT 'mines001', rules_sections_json, ui_labels_json, bet_limits_json,
       demo_labels_json, theme_tokens_json, NOW(), NOW(), NOW()
  FROM title_configs WHERE title_code = 'mines_classic'
ON CONFLICT (title_code) DO NOTHING;

-- 3. La configurazione specifica di Mines (griglie, numero di mine).
INSERT INTO mines_title_configs (title_code, published_grid_sizes_json, published_mine_counts_json,
                                 default_mine_counts_json, published_board_assets_json,
                                 draft_grid_sizes_json, draft_mine_counts_json,
                                 draft_default_mine_counts_json, draft_board_assets_json,
                                 created_at, updated_at)
SELECT 'mines001', published_grid_sizes_json, published_mine_counts_json,
       default_mine_counts_json, published_board_assets_json,
       draft_grid_sizes_json, draft_mine_counts_json,
       draft_default_mine_counts_json, draft_board_assets_json, NOW(), NOW()
  FROM mines_title_configs WHERE title_code = 'mines_classic'
ON CONFLICT (title_code) DO NOTHING;

-- 4. In vetrina, con demo e denaro attivi, subito dopo BOXE e HI-LO.
INSERT INTO site_titles (site_code, title_code, position, status, lobby_visibility,
                         demo_enabled, real_enabled, lobby_display_name, featured,
                         created_at, updated_at)
VALUES ('casinoking', 'mines001', 941, 'active', 'visible', true, true, 'Mines', false, NOW(), NOW())
ON CONFLICT (site_code, title_code) DO UPDATE
   SET lobby_visibility = 'visible', demo_enabled = true, real_enabled = true,
       position = 941, updated_at = NOW();

-- 5. Via dalla vetrina tutti i titoli di prova. Non si cancellano: si nascondono.
UPDATE site_titles
   SET lobby_visibility = 'hidden', updated_at = NOW()
 WHERE site_code = 'casinoking'
   AND (title_code LIKE 'mines_flow_%' OR title_code LIKE 'mines_auth_%'
     OR title_code LIKE 'mines_bo_cfg_%' OR title_code LIKE 'mines_latest_%'
     OR title_code LIKE '%_test%');

COMMIT;

-- 6. Via dalla vetrina qualunque altro residuo di test: restano solo i tre giochi veri.
UPDATE site_titles SET lobby_visibility='hidden', updated_at=NOW()
 WHERE site_code='casinoking' AND lobby_visibility='visible'
   AND title_code NOT IN ('boxe001','hilo001','mines001');
