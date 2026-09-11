-- 0065 — PASSO 3-bis (3bA): Coins entra nel catalogo.
--
-- Coins e' il gioco esterno di M&M Games: la piattaforma gli emette il
-- gettone di lancio e lui muove denaro SOLO attraverso il confine seamless
-- (reserve/commit/rollback su ledger). Registrandolo sotto il fornitore
-- `m-and-m-games` il confine puo' verificare che chi chiama e' il proprietario
-- del gioco (game_engines.provider_code, vedi seamless/router.py).
--
-- Segue lo stampo della 0042 (hi_lo) e della 0056 (manichino): sui conflitti
-- si riafferma l'identita' (motore, titolo, parametri di vetrina) ma NON gli
-- stati di fornitore/motore/titolo, perche' una sospensione e' una decisione
-- operativa che una migrazione non deve annullare.
--
-- Rollback MANUALE: migrations/sql/rollback/0065__retromarcia_catalogo_coins.sql.

BEGIN;

INSERT INTO game_providers (provider_code, display_name, status)
VALUES ('m-and-m-games', 'M&M Games', 'active')
ON CONFLICT (provider_code) DO UPDATE
SET display_name = EXCLUDED.display_name;

-- Il runtime_module non punta a un modulo della piattaforma: Coins gira fuori
-- (servizio M&M) e la piattaforma lo raggiunge solo via seamless. La stringa
-- lo dichiara, perche' la colonna e' NOT NULL e un modulo inesistente
-- spaccato fra i moduli interni sarebbe un'ambigua promessa.
INSERT INTO game_engines (engine_code, display_name, runtime_module, status, provider_code)
VALUES (
    'coins',
    'Coins',
    'external:m-and-m-games/coins',
    'active',
    'm-and-m-games'
)
ON CONFLICT (engine_code) DO UPDATE
SET display_name = EXCLUDED.display_name,
    runtime_module = EXCLUDED.runtime_module,
    provider_code = EXCLUDED.provider_code
WHERE game_engines.engine_code = 'coins';

INSERT INTO game_titles (
    title_code,
    engine_code,
    display_name,
    status,
    is_master,
    source_title_code
)
VALUES
    ('coins', 'coins', 'Coins Master', 'active', true, NULL),
    ('coins001', 'coins', 'Coins', 'active', false, 'coins')
ON CONFLICT (title_code) DO UPDATE
SET engine_code = EXCLUDED.engine_code,
    display_name = EXCLUDED.display_name,
    is_master = EXCLUDED.is_master,
    source_title_code = EXCLUDED.source_title_code,
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
    ('coins', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW()),
    ('coins001', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
ON CONFLICT (title_code) DO NOTHING;

-- La variante deve essere lanciabile in modalita' reale: e' la precondizione
-- perche' la piattaforma possa emettere il gettone che M&M introspetta.
-- Il demo resta spento: il gioco esterno non ha una modalita' demo servita
-- dalla piattaforma.
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
        'coins',
        960,
        'active',
        'hidden',
        false,
        false,
        'Coins Master',
        'Reference master Title for Coins.',
        false
    ),
    (
        'casinoking',
        'coins001',
        961,
        'active',
        'visible',
        false,
        true,
        'Coins',
        'Coins by M&M Games.',
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
