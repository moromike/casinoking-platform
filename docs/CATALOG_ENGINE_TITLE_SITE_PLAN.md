# Catalogo Engine / Title / Site - Piano operativo Fase 1

## Stato

Cantiere implementato e verificato localmente. Questo documento definisce il piano operativo della Fase 1 della roadmap "Suite giochi single-player skinnabili" e registra lo stato di avanzamento del lavoro.

La Fase 1 e' solo infrastruttura dati: crea il catalogo minimo Engine / Title / Site e il seed per Mines Classic. Non introduce API, UI, launch title-aware, demo mode, asset registry o modifiche al gameplay.

## Stato avanzamento

| Voce | Stato | Evidenza |
| --- | --- | --- |
| Piano operativo Fase 1 | Completato | `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md` |
| Source of Truth aggiornata | Completato | `docs/SOURCE_OF_TRUTH.md` cita la tassonomia Engine / Title / Site e questo piano |
| Indice documentale aggiornato | Completato | `docs/README.md` include questo piano in Platform/Game split |
| Migration catalogo | Completato | `backend/migrations/sql/0023__platform_catalog_bootstrap.sql` |
| Seed catalogo | Completato | `mines`, `mines_classic`, `casinoking`, relazione `(casinoking, mines_classic)` |
| Test DB/migration | Completato | `tests/integration/test_platform_catalog_bootstrap.py` |
| API catalogo | Non iniziato | Fuori scope Fase 1, previsto da Fase 2 |
| Admin catalog UI | Non iniziato | Fuori scope Fase 1, previsto da Fase 2 |
| Gameplay Mines | Non modificato | Nessun file Mines runtime/frontend toccato |
| Wallet/Ledger | Non modificato | Nessun file accounting toccato |

## Verifiche eseguite

| Verifica | Comando | Esito |
| --- | --- | --- |
| Applicazione migration | `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env exec -T backend python -m app.tools.apply_migrations` | Passata: applicata `0023__platform_catalog_bootstrap.sql` |
| Test catalogo DB | `python -m pytest tests/integration/test_platform_catalog_bootstrap.py` | Passata: 2 passed |
| Test migration runner | `python -m pytest tests/unit/test_apply_migrations.py` | Passata: 10 passed |
| Smoke Mines/financial | `$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'; python -m pytest tests/integration/test_financial_and_mines_flows.py` | Passata: 20 passed |

Nota verifica: un primo lancio dello smoke senza override `DATABASE_URL` ha prodotto 3 failure per host DB `postgres` non risolvibile da PowerShell host. Rilanciando con `DATABASE_URL` puntato a `localhost:55432`, la stessa suite e' passata integralmente. Non era una regressione della migration.

## Mappa documenti del cantiere

| Documento | Tipo | Ruolo in questa attivita' | Quando leggerlo |
| --- | --- | --- | --- |
| `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md` | Roadmap completa v3 esterna | Documento di origine della roadmap a 7 fasi: definisce tassonomia Engine / Title / Site, Fase 1-7, demo, asset, theme ed editor riusabile. | Prima di aprire o modificare una fase della roadmap giochi. |
| `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md` | Piano operativo Fase 1 | Questo documento. Traduce la Fase 1 in scope esatto: migration `0023`, seed catalogo, test DB, nessuna API/UI/gameplay. | Durante implementazione e verifica della Fase 1. |
| `docs/SOURCE_OF_TRUTH.md` | Fonte ufficiale di progetto | Registra che la tassonomia Engine / Title / Site e' parte dei principi architetturali attivi e rimanda a questo piano operativo. | Sempre prima di lavorare sul progetto. |
| `docs/README.md` | Indice documentale | Permette alle prossime AI e agli sviluppatori di trovare questo piano sotto Platform/Game split. | Per orientarsi nella documentazione attiva. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Checklist obbligatoria | Impone lettura proporzionata, niente feature non richieste, verifica reale e dichiarazione dei documenti letti. | Inizio e fine di ogni task. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Regole manutenzione docs | Spiega perche' questo piano operativo va indicizzato e quando aggiornare Source of Truth, README, atlas o Word. | Prima di chiudere task che cambiano docs, codice o architettura. |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | Atlas dominio Mines | Riferimento futuro per fasi che toccheranno Mines runtime, platform boundary, skin o backoffice. Non e' necessario integralmente per Fase 1. | Da Fase 2+ o se il catalogo inizia a toccare Mines/API/runtime. |
| `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md` | Atlas platform/frontend | Riferimento futuro per admin catalog, reporting, backoffice Title e frontend. Non e' necessario integralmente per Fase 1. | Da Fase 2+ o se si aggiunge UI/API/reporting. |

Regola pratica: la roadmap v3 spiega **dove stiamo andando**; questo documento spiega **cosa fare adesso**. Se i due documenti sembrano divergere, fermarsi e riallinearli prima di implementare.

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- piano roadmap v3 esterno: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- elenco migration esistenti in `backend/migrations/sql`
- `backend/app/tools/apply_migrations.py`
- struttura test/fixture DB in `tests/conftest.py` individuata tramite ricerca

File individuati ma non letti integralmente per lettura proporzionata:

- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- documenti canonici Word Mines/API/DB

Motivo esclusione: questa fase non cambia gameplay, API, wallet/ledger, backoffice o frontend. Il task e' limitato a piano operativo, migration catalogo e seed DB.

## Decisione architetturale applicabile

La tassonomia giochi e' a tre livelli:

- Engine: codice/regole/RNG/payout di un tipo di gioco, per esempio `mines`.
- Title: gioco pubblicato con identita' commerciale e configurazione propria, per esempio `mines_classic`.
- Site: sito o destinazione di distribuzione, per esempio `casinoking`.

Regola importante: `game_code` resta legacy/engine code dove gia' esiste. `title_code` e `site_code` arriveranno nelle tabelle di round/sessione solo in Fase 2. La Fase 1 non tocca le tabelle esistenti.

## Scope Fase 1

Incluso:

- nuova migration `backend/migrations/sql/0023__platform_catalog_bootstrap.sql`
- tabella `game_engines`
- tabella `game_titles`
- tabella `sites`
- tabella `site_titles`
- seed:
  - engine `mines`
  - title `mines_classic`
  - site `casinoking`
  - relazione active `(casinoking, mines_classic)`
- test pytest DB/migration allineato alle fixture esistenti
- aggiornamento minimo di `docs/SOURCE_OF_TRUTH.md`

Escluso:

- API catalogo
- pagina admin catalogo
- modifiche a launch token
- modifiche a `platform_rounds`, `game_access_sessions`, `game_table_sessions`, `mines_game_rounds`
- modifiche a wallet/ledger
- modifiche a Mines gameplay, RTP, payout runtime, RNG o fairness
- demo mode
- asset registry
- theme system

## Migration prevista

File:

`backend/migrations/sql/0023__platform_catalog_bootstrap.sql`

Schema previsto:

```sql
BEGIN;

CREATE TABLE game_engines (
    engine_code varchar(32) PRIMARY KEY,
    display_name varchar(120) NOT NULL,
    runtime_module varchar(160) NOT NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT game_engines_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE game_titles (
    title_code varchar(64) PRIMARY KEY,
    engine_code varchar(32) NOT NULL REFERENCES game_engines(engine_code),
    display_name varchar(160) NOT NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT game_titles_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE sites (
    site_code varchar(32) PRIMARY KEY,
    display_name varchar(160) NOT NULL,
    base_url text NULL,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT sites_status_check
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE site_titles (
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    position integer NOT NULL DEFAULT 0,
    status varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    PRIMARY KEY (site_code, title_code),
    CONSTRAINT site_titles_status_check
        CHECK (status IN ('active', 'inactive')),
    CONSTRAINT site_titles_position_check
        CHECK (position >= 0)
);

CREATE INDEX idx_game_titles_engine_code
    ON game_titles (engine_code);

CREATE INDEX idx_site_titles_title_code
    ON site_titles (title_code);

INSERT INTO game_engines (
    engine_code,
    display_name,
    runtime_module,
    status
)
VALUES (
    'mines',
    'Mines',
    'app.modules.games.mines',
    'active'
)
ON CONFLICT (engine_code) DO NOTHING;

INSERT INTO game_titles (
    title_code,
    engine_code,
    display_name,
    status
)
VALUES (
    'mines_classic',
    'mines',
    'Mines Classic',
    'active'
)
ON CONFLICT (title_code) DO NOTHING;

INSERT INTO sites (
    site_code,
    display_name,
    base_url,
    status
)
VALUES (
    'casinoking',
    'CasinoKing',
    NULL,
    'active'
)
ON CONFLICT (site_code) DO NOTHING;

INSERT INTO site_titles (
    site_code,
    title_code,
    position,
    status
)
VALUES (
    'casinoking',
    'mines_classic',
    0,
    'active'
)
ON CONFLICT (site_code, title_code) DO NOTHING;

COMMIT;
```

Note operative:

- La migration deve essere idempotente rispetto ai seed tramite `ON CONFLICT DO NOTHING`.
- Non aggiungere FK da tabelle esistenti verso il catalogo in Fase 1.
- Non rinominare `game_code`.
- Non aggiornare `CURRENT_BASELINE_VERSION` in `apply_migrations.py` salvo evidenza dai test che il legacy baseline ne abbia bisogno. La Fase 1 e' una migration ordinaria successiva alla baseline corrente.

## Test previsti

Nuovo test pytest, collocazione da confermare durante implementazione in base alla struttura reale. Candidato:

`tests/integration/test_platform_catalog_bootstrap.py`

Verifiche minime:

- `game_engines` contiene `mines` active con runtime module `app.modules.games.mines`
- `game_titles` contiene `mines_classic` active collegato a `mines`
- `sites` contiene `casinoking` active
- `site_titles` contiene `(casinoking, mines_classic)` active con `position = 0`
- FK engine/title/site funzionano
- il record `0023__platform_catalog_bootstrap.sql` risulta presente in `schema_migrations` dopo applicazione migration

Comandi di verifica candidati:

```powershell
pytest tests/integration/test_platform_catalog_bootstrap.py
pytest tests/unit/test_apply_migrations.py
```

Se il costo e' accettabile, eseguire anche un sottoinsieme smoke Mines per confermare zero impatto runtime:

```powershell
pytest tests/integration/test_financial_and_mines_flows.py
```

## Sequenza di implementazione

1. Creare `backend/migrations/sql/0023__platform_catalog_bootstrap.sql`. Completato.
2. Applicare le migration in ambiente locale con il tool esistente o tramite avvio backend. Completato.
3. Aggiungere il test pytest DB/migration. Completato.
4. Eseguire il test catalogo e `tests/unit/test_apply_migrations.py`. Completato.
5. Aggiornare `docs/SOURCE_OF_TRUTH.md` solo con la riga di tassonomia e riferimento a questo documento. Completato.
6. Rileggere `docs/TASK_EXECUTION_GUARDRAILS.md` e `docs/DOCUMENTATION_MAINTENANCE.md`. Completato a fine task.
7. Dichiarare esplicitamente che API/UI/gameplay non sono stati modificati. Completato.

## Criteri di accettazione

La Fase 1 e' completata solo se:

- la migration `0023__platform_catalog_bootstrap.sql` viene applicata senza errori. Verificato.
- i quattro seed attesi esistono. Verificato dal test catalogo.
- le FK impediscono relazioni site/title o title/engine inesistenti. Verificato dal test catalogo.
- i test previsti passano. Verificato.
- nessun endpoint o componente frontend nuovo e' stato aggiunto. Verificato dal diff.
- Mines continua a funzionare come prima. Verificato con smoke `test_financial_and_mines_flows.py`.
- `docs/SOURCE_OF_TRUTH.md` cita la tassonomia e questo documento operativo. Verificato.

## Fuori scope esplicito per questo cantiere

La Fase 2 e' aperta nel piano operativo `docs/TITLE_CODE_PROPAGATION_PLAN.md` e riguarda:

- API catalogo read-only
- admin catalog read-only
- `title_code` e `site_code` su round/sessioni
- launch token title/site-aware
- reporting Engine + Title + Site
- rifiuto esplicito di `mode=demo` fino alla Fase 6
