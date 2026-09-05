-- CasinoKing - provider del manichino di collaudo.
--
-- Perche' esiste questa migrazione:
-- Il manichino e' la cavia che paga vincite a comando attraverso le tubature
-- contabili vere. Deve quindi esistere nel catalogo come primo titolo di un
-- fornitore esterno, senza far sembrare il suo motore proprieta' interna.
-- Spostarlo in un provider distinto permette di sospenderlo senza spegnere
-- Mines, BOXE e HI-LO, che restano sotto il provider interno CasinoKing.
--
-- INVARIANTE DI RILASCIO: questa riga rende visibile un titolo che paga vincite
-- a comando. E' sicura soltanto insieme al codice dello stesso commit, che
-- introduce QUATTRO difese indipendenti: l'interruttore, l'esclusione dei titoli
-- di prova dalla vetrina, il divieto di lanciarli in produzione e il divieto di
-- aprirci sopra una sessione d'accesso. Il backend applica le migrazioni al
-- proprio avvio, quindi codice e migrazione sono un unico artefatto e fra i due
-- non esiste una finestra in cui la riga viva senza le difese.

BEGIN;

INSERT INTO game_providers (provider_code, display_name, status)
VALUES ('ck_collaudo', 'CasinoKing Collaudo', 'active')
ON CONFLICT (provider_code) DO UPDATE
-- Lo stato del fornitore e' una decisione operativa, non un dato di schema:
-- una migrazione non deve annullare una sospensione decisa da qualcuno.
SET display_name = EXCLUDED.display_name;

-- Nei conflitti riaffermiamo l'identita' della cavia (provider, motore, titolo,
-- flag di test/master e parametri di vetrina), ma non gli stati: anche motore e
-- titoli possono essere sospesi da una decisione operativa che la migrazione
-- non deve annullare. Le INSERT restano invece attive per le righe nuove.
INSERT INTO game_engines (engine_code, display_name, runtime_module, status, provider_code)
VALUES (
    'manichino',
    'Manichino',
    'app.modules.games.manichino.service',
    'active',
    'ck_collaudo'
)
ON CONFLICT (engine_code) DO UPDATE
SET display_name = EXCLUDED.display_name,
    runtime_module = EXCLUDED.runtime_module,
    provider_code = EXCLUDED.provider_code
WHERE game_engines.engine_code = 'manichino';

INSERT INTO game_titles (
    title_code,
    engine_code,
    display_name,
    status,
    is_test,
    is_master
)
VALUES (
    'manichino_test',
    'manichino',
    'Manichino di collaudo',
    'active',
    true,
    false
)
ON CONFLICT (title_code) DO UPDATE
SET engine_code = EXCLUDED.engine_code,
    display_name = EXCLUDED.display_name,
    is_test = EXCLUDED.is_test,
    is_master = EXCLUDED.is_master,
    updated_at = NOW()
WHERE game_titles.title_code = 'manichino_test';

INSERT INTO title_configs (
    title_code,
    rules_sections_json,
    ui_labels_json,
    draft_rules_sections_json,
    draft_ui_labels_json,
    created_at,
    updated_at
)
VALUES (
    'manichino_test',
    '{}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (title_code) DO NOTHING;

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
VALUES (
    'casinoking',
    'manichino_test',
    999,
    'active',
    'visible',
    false,
    true,
    'Manichino di collaudo',
    'Titolo di collaudo: non e un gioco.',
    false
)
ON CONFLICT (site_code, title_code) DO UPDATE
SET position = EXCLUDED.position,
    lobby_visibility = EXCLUDED.lobby_visibility,
    demo_enabled = EXCLUDED.demo_enabled,
    real_enabled = EXCLUDED.real_enabled,
    lobby_display_name = EXCLUDED.lobby_display_name,
    lobby_description = EXCLUDED.lobby_description,
    featured = EXCLUDED.featured,
    updated_at = NOW();

COMMIT;
