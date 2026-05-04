# Title configuration split - Piano operativo Fase 3

## Stato

Cantiere implementato e verificato localmente.

Questo documento definisce il piano operativo della Fase 3 della roadmap "Suite giochi single-player skinnabili". La Fase 3 sposta la configurazione di backoffice da `mines_backoffice_config(PK='mines')` a un modello per-Title diviso fra una tabella generica `title_configs` e una tabella engine-specific `mines_title_configs`.

La Fase 1 e' completata e documentata in `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md`.
La Fase 2 e' completata e documentata in `docs/TITLE_CODE_PROPAGATION_PLAN.md`.

## Mappa documenti del cantiere

| Documento | Tipo | Ruolo in questa attivita' | Quando leggerlo |
| --- | --- | --- | --- |
| `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md` | Roadmap completa v3 esterna | Definisce la Fase 3 come spostamento configurazione sotto Title con strategia di transizione PostgreSQL realistica. | Prima di modificare scope o ordine delle fasi. |
| `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md` | Piano operativo Fase 1 | Stato completato del catalogo. La Fase 3 usa `game_titles.title_code='mines_classic'` come chiave delle nuove tabelle. | Prima di referenziare title/engine. |
| `docs/TITLE_CODE_PROPAGATION_PLAN.md` | Piano operativo Fase 2 | Stato completato della propagation. La Fase 3 NON cambia round/sessioni: lavora solo sul backoffice. | Per capire cosa NON va toccato. |
| `docs/TITLE_CONFIG_PLAN.md` | Piano operativo Fase 3 | Questo documento. Definisce schema split, file, test e strategia di transizione `mines_backoffice_config`. | Durante implementazione e verifica della Fase 3. |
| `docs/SOURCE_OF_TRUTH.md` | Fonte ufficiale progetto | Va aggiornata con riferimento a questo piano operativo. | Sempre prima di lavorare sul progetto. |
| `docs/README.md` | Indice documentale | Va aggiornato per indicizzare questo piano sotto Platform/Game split. | Per orientamento documentale. |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | Atlas Mines | Sezione `MINES_BACKOFFICE_00600/00610` da riallineare al modello per-Title. | Prima di toccare backoffice config Mines. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Checklist obbligatoria | Impone scope minimo, niente feature non richieste. | Inizio e fine task. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Regole manutenzione docs | Dice quali docs aggiornare se cambiano schema, atlas o flussi backoffice. | Prima di chiudere il task. |

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md`
- `docs/TITLE_CODE_PROPAGATION_PLAN.md`
- roadmap v3 esterna: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- `backend/migrations/sql/0010__mines_backoffice_config.sql`
- `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql`
- `backend/app/modules/games/mines/backoffice_config.py` (estratto: firme funzioni e costanti chiave)
- ricerca mirata su `backend/app/api/routes/admin.py` per gli endpoint `/admin/games/mines/backoffice-config*`
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `tests/integration/test_mines_backoffice_config.py`
- `tests/integration/test_title_configs_split.py`
- `docs/ARCHITECTURE_ATLAS_MINES.md`

File individuati ma non letti integralmente:

- documenti canonici Word Mines

Motivo: i Word canonici sono rimandati al consolidamento documentale separato registrato in fondo a questo piano; per F3 sono stati letti i documenti operativi e i file direttamente toccati.

## Avanzamento implementazione

| Area | Stato | File principali |
| --- | --- | --- |
| Migration 0025 | Completata e applicata localmente | `backend/migrations/sql/0025__title_configs_split.sql` |
| Config generica per Title | Completata | `backend/app/modules/platform/catalog/title_config_service.py` |
| Config Mines per Title | Completata | `backend/app/modules/games/mines/backoffice_config.py` |
| Endpoint admin title-aware | Completati | `backend/app/api/routes/admin.py` |
| Alias endpoint legacy Mines | Completati | `backend/app/api/routes/admin.py` |
| Fixture test backoffice | Completata | `tests/conftest.py` |
| Editor backoffice frontend | Completato senza nuova route Next | `frontend/app/ui/mines/mines-backoffice-editor.tsx` |
| Test F3 | Completati | `tests/integration/test_title_configs_split.py`, `tests/integration/test_mines_backoffice_config.py` |
| Documentazione | Completata per docs operativi e atlas | `docs/SOURCE_OF_TRUTH.md`, `docs/README.md`, `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/TITLE_CONFIG_PLAN.md` |

## Verifiche eseguite

| Verifica | Esito |
| --- | --- |
| `schema_migrations` contiene `0025__title_configs_split.sql` | OK |
| `python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py` | OK, 9 passed |
| `python -m pytest tests/integration/test_financial_and_mines_flows.py tests/integration/test_title_code_propagation.py tests/integration/test_platform_catalog_bootstrap.py tests/unit/test_apply_migrations.py` | OK, 35 passed |
| `npx tsc --noEmit` in `frontend/` | OK |

Nota ambiente test: i comandi pytest locali sono stati lanciati con `DATABASE_URL=postgresql://casinoking:casinoking@localhost:55432/casinoking`, perche' da host Windows il nome Docker interno `postgres` non risolve.

## Decisioni vincolanti

- `game_code` resta legacy/engine code. Le nuove tabelle usano `title_code` come PK.
- Il modello pubblicazione resta a livello di Title: una sola riga di config draft e una sola riga di config published per Title, atomicamente promossa con `publish`.
- La pubblicazione tocca contemporaneamente la parte generica e la parte engine-specific in singola transazione.
- Nessuna modifica a payout runtime, RTP, RNG/fairness, ledger/wallet.
- Nessuna creazione UI di nuovi Title in F3: la creazione di Title aggiuntivi avviene da SQL manuale per i test; l'editor wizard arriva in Fase 7.
- Non vengono ancora popolati `bet_limits_json`, `demo_labels_json`, `theme_tokens_json`: sono placeholder NULL pronti per le fasi successive (F5, F6, F7). F3 li crea ma non li valida ne' li espone in editor.
- Endpoint legacy `/admin/games/mines/backoffice-config*` continuano a funzionare puntando a `title_code='mines_classic'` per retrocompatibilita'.

## Scope Fase 3

Incluso:

- migration `backend/migrations/sql/0025__title_configs_split.sql`:
  - `RENAME mines_backoffice_config -> mines_backoffice_config_legacy`
  - `CREATE TABLE title_configs`
  - `CREATE TABLE mines_title_configs`
  - `INSERT INTO ... SELECT FROM mines_backoffice_config_legacy WHERE game_code='mines'` con `title_code='mines_classic'`
  - `CREATE VIEW mines_backoffice_config` (read-only) per readers non ancora migrati
- nuovo modulo `backend/app/modules/platform/catalog/title_config_service.py` (parte generica: ui_labels, rules, draft/publish meta)
- refactor `backend/app/modules/games/mines/backoffice_config.py` parametrizzato su `title_code` e che legge/scrive sulle nuove tabelle
- helper `resolve_title_config(title_code)` che compone le due tabelle e ritorna oggetto unico
- nuovi endpoint admin `/admin/games/titles/{title_code}/config{,/publish}`
- mantenimento endpoint legacy `/admin/games/mines/backoffice-config{,/publish}` come alias verso `mines_classic`
- frontend admin: `mines-backoffice-editor.tsx` parametrizzato su `title_code` (default `mines_classic`); nessuna nuova route Next se non strettamente necessaria, in linea con la scelta fatta in Fase 2
- aggiornamento test backend e frontend
- aggiornamento atlas Mines per i blocchi `MINES_BACKOFFICE_00600` e `MINES_BACKOFFICE_00610`
- aggiornamento `docs/SOURCE_OF_TRUTH.md` con riferimento a questo piano

Escluso:

- DROP `mines_backoffice_config_legacy`: si fa in step finale solo dopo tests verdi e settling, eventualmente con migration successiva dedicata (vedi sezione cleanup).
- editor wizard creazione Title (Fase 7)
- skin editor / theme tab (Fase 5)
- asset registry filesystem (Fase 4)
- demo mode (Fase 6)
- riscrittura UI editor: solo parametrizzazione su `title_code`, niente nuovi controlli o tab
- modifiche a payout runtime, RTP, RNG, fairness
- modifiche a wallet/ledger
- creazione di Title aggiuntivi da UI

## Migration prevista

File: `backend/migrations/sql/0025__title_configs_split.sql`

Struttura:

```sql
BEGIN;

-- Step 1: rename legacy table (preserva PK CHECK game_code='mines' come safety net)
ALTER TABLE mines_backoffice_config RENAME TO mines_backoffice_config_legacy;

-- Step 2: nuova tabella generica per Title (parte non engine-specific)
CREATE TABLE title_configs (
    title_code varchar(64) PRIMARY KEY REFERENCES game_titles(title_code),
    -- payload published
    rules_sections_json jsonb NOT NULL,
    ui_labels_json jsonb NOT NULL,
    -- placeholder per fasi future (F5/F6/F7), NULL in F3
    bet_limits_json jsonb NULL,
    demo_labels_json jsonb NULL,
    theme_tokens_json jsonb NULL,
    -- payload draft
    draft_rules_sections_json jsonb NULL,
    draft_ui_labels_json jsonb NULL,
    draft_bet_limits_json jsonb NULL,
    draft_demo_labels_json jsonb NULL,
    draft_theme_tokens_json jsonb NULL,
    -- audit Title-level (uno per Title, vale per published+draft trasversalmente)
    published_at timestamptz NULL,
    updated_by_admin_user_id uuid NULL REFERENCES users(id),
    draft_updated_by_admin_user_id uuid NULL REFERENCES users(id),
    draft_updated_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT title_configs_rules_sections_json_object_check
        CHECK (jsonb_typeof(rules_sections_json) = 'object'),
    CONSTRAINT title_configs_ui_labels_json_object_check
        CHECK (jsonb_typeof(ui_labels_json) = 'object')
);

-- Step 3: nuova tabella engine-specific Mines
CREATE TABLE mines_title_configs (
    title_code varchar(64) PRIMARY KEY REFERENCES game_titles(title_code),
    -- payload published
    published_grid_sizes_json jsonb NOT NULL,
    published_mine_counts_json jsonb NOT NULL,
    default_mine_counts_json jsonb NOT NULL,
    published_board_assets_json jsonb NOT NULL,
    -- payload draft
    draft_grid_sizes_json jsonb NULL,
    draft_mine_counts_json jsonb NULL,
    draft_default_mine_counts_json jsonb NULL,
    draft_board_assets_json jsonb NULL,
    -- timestamps engine-side (gli audit user_id stanno in title_configs)
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

-- Step 4: copia dati esistenti (game_code='mines' -> title_code='mines_classic')
INSERT INTO title_configs (
    title_code,
    rules_sections_json, ui_labels_json,
    draft_rules_sections_json, draft_ui_labels_json,
    published_at, updated_by_admin_user_id,
    draft_updated_by_admin_user_id, draft_updated_at,
    created_at, updated_at
)
SELECT
    'mines_classic',
    rules_sections_json, ui_labels_json,
    draft_rules_sections_json, draft_ui_labels_json,
    published_at, updated_by_admin_user_id,
    draft_updated_by_admin_user_id, draft_updated_at,
    created_at, updated_at
FROM mines_backoffice_config_legacy
WHERE game_code = 'mines';

INSERT INTO mines_title_configs (
    title_code,
    published_grid_sizes_json, published_mine_counts_json,
    default_mine_counts_json, published_board_assets_json,
    draft_grid_sizes_json, draft_mine_counts_json,
    draft_default_mine_counts_json, draft_board_assets_json,
    created_at, updated_at
)
SELECT
    'mines_classic',
    published_grid_sizes_json, published_mine_counts_json,
    default_mine_counts_json, published_board_assets_json,
    draft_grid_sizes_json, draft_mine_counts_json,
    draft_default_mine_counts_json, draft_board_assets_json,
    created_at, updated_at
FROM mines_backoffice_config_legacy
WHERE game_code = 'mines';

-- Step 5: VIEW di compatibilita' read-only per readers non migrati
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
```

Note operative migration:

- La VIEW e' read-only per design: nessuna scrittura sulla VIEW. Tutti i writer devono essere migrati alle tabelle nuove nello stesso commit di codice di questa migration. **Niente trigger `INSTEAD OF` sulla VIEW**: fixture e test che oggi fanno `DELETE`/`INSERT INTO mines_backoffice_config` vanno migrati ai nuovi service o alle tabelle nuove direttamente. Aggiustare con trigger `INSTEAD OF` introdurrebbe una doppia fonte di verita' nascosta che non vogliamo.
- `mines_backoffice_config_legacy` resta presente fino al cleanup finale (vedi sezione cleanup).
- L'INSERT di copia da `mines_backoffice_config_legacy` deve gestire il caso in cui la tabella legacy non contenga la riga `game_code='mines'` (ambienti freschi/test): in ambienti di test il seed iniziale di `mines_backoffice_config` viene creato in altra logica. La migration deve essere robusta a row count = 0; in tal caso le tabelle nuove restano vuote e la prima `update_admin_backoffice_draft` le popolera' con UPSERT con default validi (CTO requirement: criterio test esplicito - vedi sezione test).
- `published_grid_sizes_json` ed equivalenti restano `NOT NULL` nelle tabelle nuove come nello schema legacy. Se l'ambiente ha legacy vuoto, l'INSERT di copia non scrive righe: alla prima scrittura via service la riga viene creata con UPSERT che fornisce default coerenti con `runtime` (grid sizes/mine counts pubblicati di default, board assets vuoti, ui_labels vuoti object, rules_sections object vuoto).

## Strategia di transizione `mines_backoffice_config`

PostgreSQL non permette VIEW e tabella con stesso nome. Il flusso e' quindi:

1. RENAME tabella legacy a `mines_backoffice_config_legacy` (CHECK `game_code='mines'` resta come sicurezza).
2. CREATE nuove tabelle `title_configs` e `mines_title_configs`.
3. Copia dati con `title_code='mines_classic'`.
4. CREATE VIEW `mines_backoffice_config` read-only.
5. **Stesso commit di codice**: tutti i reader/writer del modulo `backoffice_config.py` migrano alle tabelle nuove (no scritture sulla VIEW).
6. **Step finale separato (cleanup)**: dopo che tests sono verdi e nessun reader nascosto usa la VIEW, applicare `0025_finalize_backoffice_split.sql` con `DROP VIEW mines_backoffice_config; DROP TABLE mines_backoffice_config_legacy;`. Questo cleanup puo' restare nello stesso PR di Fase 3 oppure essere differito a un commit successivo dentro la stessa fase, a discrezione.

Razionale: se i reader fossero piu' di uno e migrati gradualmente, la VIEW serve. Nel nostro caso il reader unico e' `backoffice_config.py`, quindi la VIEW e' un guard-rail di sicurezza piu' che una necessita' funzionale.

## Backend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `backend/migrations/sql/0025__title_configs_split.sql` | Nuova migration come da schema sopra. |
| `backend/app/modules/platform/catalog/title_config_service.py` | Nuovo modulo: `get_title_config_generic_published(title_code)`, `get_title_config_generic_draft(title_code)`, `update_title_config_generic_draft(title_code, ...)`, `publish_title_config_generic(title_code, admin_user_id)`. Contiene solo i campi generici: `rules_sections_json`, `ui_labels_json`, audit Title-level. NON tocca i campi engine-specific. |
| `backend/app/modules/games/mines/backoffice_config.py` | Refactor: tutte le funzioni esistenti (`get_public_backoffice_config`, `get_admin_backoffice_config`, `update_admin_backoffice_draft`, `publish_admin_backoffice_config`) ricevono `title_code` come parametro (default `mines_classic` per retrocompatibilita'). Le funzioni leggono/scrivono su `mines_title_configs` per la parte engine-specific e delegano a `title_config_service` per la parte generica. La transazione di publish tocca entrambe le tabelle in un'unica `BEGIN/COMMIT`. La costante `GAME_CODE='mines'` resta come engine identifier per il payload pubblico ma non e' piu' la chiave DB. |
| `backend/app/modules/platform/catalog/resolve_title_config.py` (nuovo helper, oppure metodo nello stesso `title_config_service.py`) | `resolve_title_config(title_code)` che compone `title_configs` + `<engine>_title_configs` (per ora solo `mines`) e ritorna l'oggetto unico atteso dal frontend. Riconosce l'engine via `game_titles.engine_code` per scegliere quale tabella engine-specific leggere. |
| `backend/app/api/routes/admin.py` | Nuovi endpoint:<br>- `GET /admin/games/titles/{title_code}/config`<br>- `PUT /admin/games/titles/{title_code}/config`<br>- `POST /admin/games/titles/{title_code}/config/publish`<br>Endpoint legacy mantenuti come alias che chiamano lo stesso service con `title_code='mines_classic'`:<br>- `GET /admin/games/mines/backoffice-config`<br>- `PUT /admin/games/mines/backoffice-config`<br>- `POST /admin/games/mines/backoffice-config/publish` |
| `backend/app/api/routes/mines.py` | Nessuna modifica al gameplay. Eventuale endpoint pubblico `/games/mines/config` (se esiste) continua a leggere via `get_public_backoffice_config(title_code='mines_classic')`. |

Nota: `MinesBackofficeValidationError` e la logica di validazione esistente (HTML sanitization, validazione griglie/mine, asset MIME/size) restano tutte in `backoffice_config.py` o vengono splittate fra `title_config_service.py` (validazione generica HTML/labels) e `backoffice_config.py` (validazione engine-specific Mines). Decisione di splittaggio della validazione da prendere durante implementazione, mantenendo la regola: **stessa transazione, stesso comportamento osservabile dall'API**.

## Frontend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `frontend/app/ui/mines/mines-backoffice-editor.tsx` | Parametrizzato su `title_code` con default `mines_classic`. Le chiamate API passano da `/admin/games/mines/backoffice-config` a `/admin/games/titles/${titleCode}/config`. Nessun nuovo controllo, nessun nuovo tab, nessuna creazione Title da UI. |
| `frontend/app/ui/casinoking-console.tsx` | Inietta `title_code='mines_classic'` come prop al pannello editor. Niente selettore Title in UI in F3. |
| `frontend/app/lib/api.ts` | Se esistono helper tipizzati per gli endpoint backoffice Mines, vengono affiancati da nuovi helper `titles/${title_code}/config` parametrici. Gli helper legacy restano funzionanti. |

Nota: la roadmap v3 prevedeva una nuova route Next `frontend/app/admin/titles/[title_code]/page.tsx`. In F2 e' stato deciso di integrare il pannello catalog nella shell esistente (`casinoking-console.tsx` + `platform-catalog-panel.tsx`) anziche' creare una route Next dedicata. F3 segue la stessa scelta: nessuna nuova route Next salvo necessita' emersa in implementazione. La shell admin esistente viene estesa per parametrizzare l'editor su `title_code`.

## Compatibilita' legacy

Endpoint legacy mantenuti come alias trasparenti:

- `GET /admin/games/mines/backoffice-config` -> `GET /admin/games/titles/mines_classic/config`
- `PUT /admin/games/mines/backoffice-config` -> `PUT /admin/games/titles/mines_classic/config`
- `POST /admin/games/mines/backoffice-config/publish` -> `POST /admin/games/titles/mines_classic/config/publish`

Comportamento osservabile dal frontend identico finche' l'editor non viene migrato ai nuovi path. Il frontend in F3 viene migrato ai nuovi path, ma gli alias legacy restano per:

- ridurre rischio in caso di rollback parziale
- coprire eventuali tool admin esterni o richiami CLI

Drop degli endpoint legacy non e' previsto in F3. Resta in valutazione per fase futura.

## Test previsti

Aggiornamenti a test esistenti:

- `tests/integration/test_mines_backoffice_config.py`: stesso comportamento osservabile, ma le query interne ora puntano a `title_configs`/`mines_title_configs`. Il test verifica anche che `mines_backoffice_config_legacy` non sia toccata da nuove scritture e che la VIEW `mines_backoffice_config` ritorni gli stessi dati delle nuove tabelle dopo migration.

Nuovi test:

- `tests/integration/test_title_configs_split.py`:
  - migration `0025` applicata: tabelle `title_configs` e `mines_title_configs` esistono, VIEW `mines_backoffice_config` esiste
  - dati di `mines_backoffice_config_legacy` copiati correttamente con `title_code='mines_classic'`
  - `resolve_title_config('mines_classic')` ritorna oggetto identico al legacy `get_admin_backoffice_config()` pre-migration (snapshot test)
  - creazione manuale via SQL di un secondo Title `mines_book_of_ra` con config diversa: `resolve_title_config('mines_book_of_ra')` ritorna la sua config, isolata da `mines_classic`
  - publish atomico: una transazione tocca entrambe le tabelle; un fallimento in mezzo non lascia stato parziale (verificato con error injection o constraint violation forzata)
  - **CTO requirement: ambiente fresco (legacy vuoto)**. Test che parte da `title_configs`/`mines_title_configs` vuote (nessuna riga copiata): la prima `update_admin_backoffice_draft(title_code='mines_classic', ...)` deve produrre righe complete con default validi nelle due tabelle. Le righe risultanti devono soddisfare i CHECK constraint NOT NULL (rules_sections, ui_labels, published_grid_sizes, etc.) e poter essere pubblicate con `publish_admin_backoffice_config` senza errori.
- `tests/contract/test_admin_titles_config_contract.py` (nuovo o aggiunto a contract esistente):
  - `GET/PUT/POST /admin/games/titles/mines_classic/config*` rispondono correttamente
  - alias legacy `/admin/games/mines/backoffice-config*` continua a rispondere e restituisce stessi payload

Test invarianti:

- `tests/integration/test_financial_and_mines_flows.py`: deve restare verde (Mines runtime e wallet non toccati).
- `tests/integration/test_title_code_propagation.py`: deve restare verde (F2 non e' impattata).
- `tests/integration/test_platform_catalog_bootstrap.py`: deve restare verde (F1 non e' impattata).

Comandi di verifica candidati (PowerShell host con DB locale):

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_title_configs_split.py
python -m pytest tests/contract/test_admin_titles_config_contract.py
python -m pytest tests/integration/test_financial_and_mines_flows.py
python -m pytest tests/integration/test_title_code_propagation.py
python -m pytest tests/integration/test_platform_catalog_bootstrap.py
python -m pytest tests/unit/test_apply_migrations.py
cd frontend; npx tsc --noEmit
```

## Sequenza di implementazione proposta

1. Creare `backend/migrations/sql/0025__title_configs_split.sql` come da schema sopra.
2. Applicare la migration in ambiente locale e verificare:
   - tabelle `title_configs` e `mines_title_configs` esistono
   - VIEW `mines_backoffice_config` esiste e ritorna stessi dati del legacy
   - `mines_backoffice_config_legacy` esiste con i dati storici
3. Creare `title_config_service.py` con le funzioni generiche e `resolve_title_config(title_code)`.
4. Refactor `mines/backoffice_config.py` parametrizzato su `title_code`, transazione publish atomica su entrambe le tabelle.
5. Aggiungere endpoint nuovi `/admin/games/titles/{title_code}/config*` in `routes/admin.py`.
6. Mantenere endpoint legacy come alias.
7. Migrare `mines-backoffice-editor.tsx` ai nuovi path.
8. Aggiornare/aggiungere test backend e frontend.
9. Eseguire suite test prevista (lista verifiche sopra).
10. Aggiornare `docs/ARCHITECTURE_ATLAS_MINES.md` blocchi `MINES_BACKOFFICE_00600` e `MINES_BACKOFFICE_00610` per riflettere il modello per-Title.
11. Aggiornare `docs/SOURCE_OF_TRUTH.md` con riferimento a questo piano.
12. Aggiornare `docs/README.md` indice documentale (sezione Platform/Game split).
13. Rileggere `docs/TASK_EXECUTION_GUARDRAILS.md` e `docs/DOCUMENTATION_MAINTENANCE.md`.
14. (Opzionale, in coda al cantiere) Applicare cleanup migration `0025_finalize_backoffice_split.sql` con `DROP VIEW`/`DROP TABLE legacy` solo dopo verifica esplicita che nessun reader usa la VIEW.

## Criteri di accettazione

Fase 3 e' completata solo se:

- migration `0025__title_configs_split.sql` applicata senza errori
- tabelle `title_configs` e `mines_title_configs` esistono con seed `mines_classic` copiato dal legacy
- VIEW `mines_backoffice_config` esiste e riproduce esattamente il payload pre-migration
- `mines_backoffice_config_legacy` esiste con dati storici (non droppata in questa fase)
- modulo `backoffice_config.py` e nuovo `title_config_service.py` leggono/scrivono solo dalle nuove tabelle
- pubblicazione e' atomica fra le due nuove tabelle
- endpoint nuovi `/admin/games/titles/mines_classic/config*` rispondono come ci si aspetta
- endpoint legacy `/admin/games/mines/backoffice-config*` continuano a rispondere identici
- editor frontend funziona senza regressioni visibili: la pagina admin Mines fa le stesse cose di prima
- creazione manuale via SQL di un secondo Title con config diversa e' leggibile via API
- Mines flow reale e wallet/ledger reconciliation restano invariati (smoke test verde)
- documentazione e atlas aggiornati
- nessuna feature fuori scope introdotta

## Rischi noti e mitigazioni

| Rischio | Mitigazione |
| --- | --- |
| VIEW di compatibilita' che ritorna dati diversi dal legacy a causa di NULL in campi draft | Test snapshot pre/post migration su payload canonico mines_classic. |
| Ambienti test con `mines_backoffice_config_legacy` vuota dopo RENAME (nessun seed precedente) | Service layer fa UPSERT alla prima scrittura: `title_configs`/`mines_title_configs` partono vuote ma valide. Test eseguono un primo `update_admin_backoffice_draft` per popolare. |
| Validazione HTML sanitization splittata fra service generico e service mines: doppia validazione o validazione mancante | Tenere la validazione in `backoffice_config.py` come oggi (engine-specific entry point) e farla chiamare prima dell'upsert; il `title_config_service` generico riceve dati gia' validati per la parte generica. Documentato nel modulo. |
| Endpoint legacy alias che rompono se si introduce un Title diverso | Gli alias forzano `title_code='mines_classic'` lato server. Sono di pura retrocompatibilita', non polimorfici. |
| Cleanup `DROP VIEW`/`DROP TABLE legacy` eseguito troppo presto | Cleanup spostato a step 14 separato e opzionale, applicato solo dopo verifica esplicita. |

## Fuori scope esplicito

- DROP `mines_backoffice_config_legacy` e DROP VIEW `mines_backoffice_config`: opzionali in coda al cantiere o differiti.
- Wizard creazione Title in UI (Fase 7).
- Tema/skin editor (Fase 5) e popolamento di `theme_tokens_json`.
- Bet limits configurabili (popolamento di `bet_limits_json`): placeholder presente, popolamento futuro.
- Demo labels (popolamento di `demo_labels_json`): placeholder presente, popolamento in Fase 6.
- Asset registry filesystem (Fase 4): in F3 i `published_board_assets_json` continuano a contenere data-URL come oggi.
- Modifiche a payout, RTP, RNG, fairness, wallet, ledger.
- Riscrittura UI editor: solo parametrizzazione su `title_code`.

## Documentazione attesa a fine F3

- Questo piano operativo esistente e completo.
- `docs/ARCHITECTURE_ATLAS_MINES.md` aggiornato per blocchi `MINES_BACKOFFICE_00600` e `MINES_BACKOFFICE_00610`.
- `docs/SOURCE_OF_TRUTH.md` con riferimento a questo piano.
- `docs/README.md` con questo piano sotto Platform/Game split.

Word canonici: la roadmap v3 prevede che a fine F3 il modello sia stabilizzato e si aggiornino i Word `Documento_31_Catalogo_Engine_Title_Site` e `Documento_32_Configurazione_Per_Title`. Decisione operativa approvata: **rimandare l'aggiornamento Word a un'attivita' separata di consolidamento documentale**, non includerlo nel cantiere F3 per non mischiare codice e Word in un singolo PR.

**Debito documentale registrato**: a fine F3 i Word canonici `Documento_31_Catalogo_Engine_Title_Site.docx` e `Documento_32_Configurazione_Per_Title.docx` non saranno aggiornati. Vanno aggiornati in un'attivita' di consolidamento successiva, prima di iniziare F4 o F5. Questa nota serve a non perdere il debito documentale.
