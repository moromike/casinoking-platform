-- CasinoKing - Punto zero giocabile.
--
-- Perche' esiste questa migrazione:
-- Le migrazioni 0041 e 0042 creano boxe001 e hilo001, ma NESSUNA crea il titolo
-- giocabile di Mines. E tutte e tre nascono nascoste e senza demo. Lo stato
-- giocabile era stato messo a mano nel database, quindi spariva a ogni
-- ricostruzione: dopo un azzeramento il sito partiva senza giochi utilizzabili,
-- e Mines non era raggiungibile per un visitatore non registrato.
--
-- Da qui in avanti un database appena creato e' gia' giocabile.
--
-- Ambito: solo catalogo e vetrina. Nessuna modifica a portafogli, libro mastro,
-- matematica dei giochi, generatore casuale o correttezza verificabile.

BEGIN;

-- 1. Il titolo giocabile di Mines, con lo stesso schema di boxe001 e hilo001.
INSERT INTO game_titles (title_code, engine_code, display_name, status, is_master, source_title_code)
VALUES ('mines001', 'mines', 'Mines 001', 'active', false, 'mines_classic')
ON CONFLICT (title_code) DO UPDATE
SET engine_code = EXCLUDED.engine_code,
    display_name = EXCLUDED.display_name,
    status = 'active',
    is_master = EXCLUDED.is_master,
    source_title_code = EXCLUDED.source_title_code,
    updated_at = NOW();

INSERT INTO title_configs (title_code, rules_sections_json, ui_labels_json,
                           draft_rules_sections_json, draft_ui_labels_json, created_at, updated_at)
VALUES ('mines001', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
ON CONFLICT (title_code) DO NOTHING;

INSERT INTO site_titles (site_code, title_code, position, status, lobby_visibility,
                         demo_enabled, real_enabled, lobby_display_name, lobby_description, featured)
VALUES ('casinoking', 'mines001', 941, 'active', 'visible', true, true,
        'Mines', 'Scopri le caselle sicure e incassa prima di trovare una mina.', false)
ON CONFLICT (site_code, title_code) DO UPDATE
SET status = 'active',
    position = EXCLUDED.position,
    lobby_visibility = EXCLUDED.lobby_visibility,
    demo_enabled = EXCLUDED.demo_enabled,
    real_enabled = EXCLUDED.real_enabled,
    lobby_display_name = EXCLUDED.lobby_display_name,
    lobby_description = EXCLUDED.lobby_description,
    updated_at = NOW();

-- 2. I tre titoli giocabili diventano visibili, in demo e a denaro.
--    I master restano nascosti: sono modelli, non giochi.
UPDATE site_titles
   SET lobby_visibility = 'visible',
       demo_enabled = true,
       real_enabled = true,
       updated_at = NOW()
 WHERE site_code = 'casinoking'
   AND title_code IN ('boxe001', 'hilo001', 'mines001');

COMMIT;
