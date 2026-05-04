# Title / Site code propagation - Piano operativo Fase 2

## Stato

Cantiere implementato e verificato localmente.

Questo documento definisce il piano operativo della Fase 2 della roadmap "Suite giochi single-player skinnabili". La Fase 2 rende il runtime esistente title-aware e site-aware, senza cambiare la matematica, il payout runtime, RNG/fairness, wallet/ledger double-entry o il gameplay Mines.

La Fase 1 e' completata e documentata in `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md`.

## Mappa documenti del cantiere

| Documento | Tipo | Ruolo in questa attivita' | Quando leggerlo |
| --- | --- | --- | --- |
| `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md` | Roadmap completa v3 esterna | Documento di origine della roadmap a 7 fasi. Definisce la Fase 2 come title-aware launch, rounds e sessioni. | Prima di modificare scope o ordine delle fasi. |
| `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md` | Piano operativo Fase 1 | Stato completato del catalogo DB minimo, prerequisito della Fase 2. | Prima di usare tabelle `game_engines`, `game_titles`, `sites`, `site_titles`. |
| `docs/TITLE_CODE_PROPAGATION_PLAN.md` | Piano operativo Fase 2 | Questo documento. Definisce schema, file, test e limiti per propagare `title_code` e `site_code`. | Durante implementazione e verifica della Fase 2. |
| `docs/SOURCE_OF_TRUTH.md` | Fonte ufficiale progetto | Registra tassonomia Engine / Title / Site e rimanda ai piani operativi attivi. | Sempre prima di lavorare sul progetto. |
| `docs/README.md` | Indice documentale | Permette a una nuova AI o al CTO di trovare Fase 1 e Fase 2 sotto Platform/Game split. | Per orientamento documentale. |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | Atlas Mines | Mappa i blocchi Mines coinvolti: API, launch token, engine service, platform boundary, platform rounds. | Prima di toccare Mines API/service/platform client. |
| `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md` | Atlas Platform/Frontend | Mappa game launch, access sessions, table sessions, admin frontend e reporting. | Prima di toccare platform modules, admin catalog o reporting. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Checklist obbligatoria | Impone scope minimo, verifica reale e distinzione tra file letti e solo individuati. | Inizio e fine task. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Regole manutenzione docs | Dice quali docs aggiornare se cambiano schema, API, atlas o flussi. | Prima di chiudere il task. |

Regola pratica: la roadmap v3 spiega **la direzione complessiva**; questo documento spiega **il lavoro Fase 2**; gli atlas spiegano **dove si trova il codice reale**.

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md`
- roadmap v3 esterna: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/modules/platform/rounds/service.py`
- `backend/app/modules/platform/access_sessions/service.py`
- `backend/app/modules/platform/table_sessions/service.py`
- ricerca mirata con `rg` su route, tests, platform rounds/sessioni, Mines boundary e admin/frontend

File letti durante implementazione:

- `backend/app/api/routes/mines.py`
- `backend/app/api/router.py`
- `backend/app/api/routes/platform_access.py`
- `backend/app/api/routes/platform_table_sessions.py`
- `backend/app/modules/games/mines/service.py`
- `backend/app/modules/games/mines/platform_client.py`
- `backend/app/modules/games/mines/round_gateway.py`
- `frontend/app/ui/casinoking-console.tsx`
- `frontend/app/ui/admin-shell-panel.tsx`
- `frontend/app/lib/api.ts`
- `tests/integration/test_title_code_propagation.py`
- `tests/contract/test_api_contract.py`

File individuati ma non letti integralmente:

- `frontend/app/admin/page.tsx`
- test browser/concurrency non direttamente toccati dalla Fase 2

Motivo: la Fase 2 e' stata integrata nella shell admin esistente, quindi non e' servita una route Next dedicata in `frontend/app/admin/catalog/page.tsx`.

## Avanzamento implementazione

| Area | Stato | File principali |
| --- | --- | --- |
| Migration 0024 | Completata e applicata localmente | `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| Catalogo backend read-only | Completato | `backend/app/modules/platform/catalog/service.py`, `backend/app/api/routes/platform_catalog.py`, `backend/app/api/router.py` |
| Launch token title/site/mode | Completato | `backend/app/modules/platform/game_launch/service.py`, `backend/app/api/routes/mines.py` |
| Access sessions | Completato | `backend/app/modules/platform/access_sessions/service.py`, `backend/app/api/routes/platform_access.py` |
| Table sessions | Completato | `backend/app/modules/platform/table_sessions/service.py`, `backend/app/api/routes/platform_table_sessions.py` |
| Platform/Mines round propagation | Completato | `backend/app/modules/platform/rounds/service.py`, `backend/app/modules/games/mines/service.py`, `backend/app/modules/games/mines/platform_client.py`, `backend/app/modules/games/mines/round_gateway.py` |
| Reporting Engine/Title/Site | Completato | `backend/app/modules/admin/service.py`, `backend/app/api/routes/admin.py`, `frontend/app/ui/admin-finance-panel.tsx` |
| Admin catalog read-only | Completato nella shell backoffice esistente | `frontend/app/ui/platform-catalog-panel.tsx`, `frontend/app/ui/casinoking-console.tsx` |
| Test | Completati localmente | `tests/integration/test_title_code_propagation.py`, `tests/contract/test_api_contract.py` |

## Verifiche eseguite

| Verifica | Esito |
| --- | --- |
| `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env exec -T backend python -m app.tools.apply_migrations` | OK, applicata `0024__title_and_site_code_propagation.sql` |
| Query DB su `platform_rounds`, `game_access_sessions`, `game_table_sessions`, `mines_game_rounds` | OK, 0 record con `title_code`/`site_code` NULL e migration 0024 registrata |
| `python -m compileall ...` sui moduli backend modificati | OK |
| `python -m pytest tests/integration/test_title_code_propagation.py` | OK, 3 passed |
| `python -m pytest tests/integration/test_financial_and_mines_flows.py` | OK, 20 passed |
| `python -m pytest tests/unit/test_apply_migrations.py tests/integration/test_platform_catalog_bootstrap.py` | OK, 12 passed |
| `python -m pytest tests/integration/test_platform_access_sessions.py tests/integration/test_game_table_sessions.py tests/integration/test_session_cascade_close.py tests/integration/test_mines_player_session_history.py` | OK, 14 passed |
| `python -m pytest tests/contract/test_api_contract.py tests/contract/test_mines_player_session_history_contract.py` | OK, 17 passed |
| `python -m pytest tests/integration/test_title_code_propagation.py tests/contract/test_api_contract.py` | OK, 18 passed |
| `python -m pytest tests/integration/test_admin_financial_reports.py` | OK, 6 passed |
| `npx tsc --noEmit` in `frontend/` | OK |

Nota ambiente test: i comandi pytest locali sono stati lanciati con `DATABASE_URL=postgresql://casinoking:casinoking@localhost:55432/casinoking`, perche' da host Windows il nome Docker interno `postgres` non risolve.

## Decisioni vincolanti

- `game_code` resta legacy/engine code. Non rinominarlo e non cambiarne la semantica storica.
- `title_code` identifica il Title pubblicato, per ora `mines_classic`.
- `site_code` identifica il sito/distribuzione, per ora `casinoking`.
- Fase 2 deve persistere `title_code` e `site_code` accanto a `game_code` sulle tabelle per round/sessione.
- `fairness_seed_rotations` resta invariata ed engine-scoped.
- Il launch token puo' trasportare `mode`, ma in Fase 2 solo `real` e' abilitato. `demo` deve essere rifiutato esplicitamente fino alla Fase 6.
- Nessuna scrittura finanziaria nuova puo' bypassare `backend/app/modules/platform/rounds/service.py`.
- Nessun cambio a RTP, payout runtime, RNG, fairness o outcome client-side.

## Scope Fase 2

Incluso:

- migration `backend/migrations/sql/0024__title_and_site_code_propagation.sql`
- `title_code` e `site_code` su:
  - `platform_rounds`
  - `game_access_sessions`
  - `game_table_sessions`
  - `mines_game_rounds`
- backfill storico:
  - `title_code = 'mines_classic'`
  - `site_code = 'casinoking'`
- catalog service read-only lato backend
- public catalog API read-only
- launch token con `title_code`, `site_code`, `mode`
- validazione `(site_code, title_code)` active sul catalogo
- propagation `title_code` / `site_code` in access sessions, table sessions, platform rounds e Mines round
- admin catalog page read-only minima
- test DB/API/integration mirati
- aggiornamento atlas e documenti operativi

Escluso:

- demo mode funzionante
- editor Title/config
- asset registry
- theme system
- creazione Title da backoffice
- modifiche a payout runtime, RTP, RNG/fairness
- modifiche a ledger model, wallet snapshot o double-entry
- rinomina `game_code` in `engine_code`

## Migration prevista

File:

`backend/migrations/sql/0024__title_and_site_code_propagation.sql`

Schema previsto:

- `platform_rounds`
  - add `title_code varchar(64) NULL`
  - add `site_code varchar(32) NULL`
  - backfill `mines_classic` / `casinoking` where `game_code = 'mines'`
  - set both NOT NULL
  - indexes:
    - `idx_platform_rounds_title_code_created_at`
    - `idx_platform_rounds_site_code_created_at`
    - optional transition/reporting index `(game_code, title_code)`

- `game_access_sessions`
  - add `title_code varchar(64) NULL`
  - add `site_code varchar(32) NULL`
  - backfill
  - set both NOT NULL
  - indexes:
    - `(user_id, title_code, started_at DESC)`
    - `(user_id, site_code, started_at DESC)`

- `game_table_sessions`
  - add `title_code varchar(64) NULL`
  - add `site_code varchar(32) NULL`
  - backfill
  - set both NOT NULL
  - indexes:
    - `(user_id, title_code, created_at DESC)`
    - `(user_id, site_code, created_at DESC)`

- `mines_game_rounds`
  - add `title_code varchar(64) NULL`
  - add `site_code varchar(32) NULL`
  - backfill via joined `platform_rounds` after platform backfill
  - set both NOT NULL

FK strategy:

- Prefer FK to `game_titles(title_code)` and `sites(site_code)` for new columns if migration ordering and existing data allow it.
- If FK creates friction with legacy tests, do not remove the columns: document the reason and use validation in service layer for Fase 2, with FK revisit in Fase 3.

Importantissimo:

- `fairness_seed_rotations` non viene modificata.
- Nessuna migration su ledger/wallet.

## Backend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `backend/app/modules/platform/catalog/service.py` | Nuovo modulo read-only per leggere engines/titles/sites e validare `is_title_published_on_site(site_code, title_code)`. |
| `backend/app/api/routes/platform_catalog.py` | Nuovo router pubblico read-only: title detail e titles per site. Nessuna mutazione. |
| `backend/app/api/router.py` | Registrare router catalog. |
| `backend/app/modules/platform/game_launch/service.py` | Rimuovere supporto hardcoded solo `GAME_CODE_MINES` come unica identita' pubblicabile; accettare/fallback `title_code=mines_classic`, `site_code=casinoking`, `mode=real`; validare catalogo; rifiutare `mode=demo`. |
| `backend/app/api/routes/mines.py` | Request/response launch token estesi; estrarre contesto token e passare `title_code`/`site_code` ai service. |
| `backend/app/modules/platform/access_sessions/service.py` | `create_access_session` e controlli correlati ricevono e persistono `title_code`/`site_code`; fallback legacy verso `mines_classic`/`casinoking`. |
| `backend/app/api/routes/platform_access.py` | Payload accetta opzionalmente `title_code`/`site_code`, con default compatibile. |
| `backend/app/modules/platform/table_sessions/service.py` | Table session create/validate/serialize include `title_code`/`site_code`. |
| `backend/app/api/routes/platform_table_sessions.py` | Payload/response estesi con default compatibile. |
| `backend/app/modules/platform/rounds/service.py` | `open_mines_round` riceve `title_code`/`site_code`, li persiste in `platform_rounds` e li aggiunge a metadata_json ledger senza alterare accounting. |
| `backend/app/modules/games/mines/platform_client.py` | Protocol e `InProcessPlatformGameClient.open_round` propagano `title_code`/`site_code`. |
| `backend/app/modules/games/mines/service.py` | Start session riceve contesto title/site e lo persiste in `mines_game_rounds`; math invariata. |
| `backend/app/modules/admin/service.py` | Reporting/admin views da valutare: dove pertinente, esporre Engine/Title/Site se la query tocca round/sessioni. Non allargare oltre le viste realmente coinvolte dai test. |

## Frontend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `frontend/app/ui/platform-catalog-panel.tsx` | Pannello admin read-only per ispezionare engine/title/site/site_titles. |
| `frontend/app/ui/casinoking-console.tsx` | Collega il pannello catalogo alla sezione giochi esistente, evitando una nuova navigazione. |
| `frontend/app/lib/api.ts` | Nessuna modifica necessaria; il client generico esistente copre il catalogo. |
| `frontend/app/mines/page.tsx` | Passare `title_code`/`site_code` al componente solo se il flusso esistente lo richiede. Default `mines_classic`/`casinoking`. |
| `frontend/app/ui/mines/mines-standalone.tsx` | Consumare/propagare `title_code`/`site_code` in modo inerte. Non cambiare UX gioco. |

Nota UI: la pagina admin catalog e' read-only. Non aggiungere editor, pulsanti crea/modifica, upload asset, tema, demo toggle o gestione publishing.

## Compatibilita' legacy

Default compatibili richiesti:

- token vecchio senza `title_code`: `mines_classic`
- token vecchio senza `site_code`: `casinoking`
- token vecchio senza `mode`: `real`
- richieste esistenti con `game_code='mines'` continuano a funzionare

Questi fallback servono solo per transizione. Le nuove response dovrebbero includere `game_code`, `title_code`, `site_code`, `mode`.

## Test previsti

Nuovi o aggiornati:

- catalog DB/API:
  - `GET /catalog/titles/mines_classic`
  - `GET /sites/casinoking/titles`
  - title/site non esistente -> errore coerente
- launch:
  - token nuovo include `game_code=mines`, `title_code=mines_classic`, `site_code=casinoking`, `mode=real`
  - richiesta con site/title non active -> 403
  - richiesta con `mode=demo` -> errore esplicito fino a Fase 6
  - token legacy senza nuovi campi -> fallback
- round/session persistence:
  - new `platform_rounds` row ha `title_code`/`site_code`
  - new `game_access_sessions` row ha `title_code`/`site_code`
  - new `game_table_sessions` row ha `title_code`/`site_code`
  - new `mines_game_rounds` row ha `title_code`/`site_code`
- invarianti:
  - `fairness_seed_rotations` schema invariato
  - ledger/wallet reconciliation invariata
  - RTP/runtime tests invariati

Comandi candidati:

```powershell
python -m pytest tests/integration/test_platform_catalog_bootstrap.py
python -m pytest tests/unit/test_apply_migrations.py
python -m pytest tests/integration/test_financial_and_mines_flows.py
python -m pytest tests/integration/test_platform_access_sessions.py
python -m pytest tests/integration/test_game_table_sessions.py
```

Se si tocca admin/frontend, almeno:

```powershell
cd frontend
npx tsc --noEmit
```

## Sequenza di implementazione proposta

1. Creare/validare migration `0024__title_and_site_code_propagation.sql`.
2. Applicare migration e verificare backfill DB.
3. Aggiungere catalog service + router read-only.
4. Estendere launch token con `title_code`, `site_code`, `mode`, fallback legacy e rifiuto demo.
5. Propagare title/site in access session, table session, platform round, Mines round.
6. Aggiungere o aggiornare test backend.
7. Aggiungere admin catalog read-only minimo.
8. Aggiornare test frontend/admin se la pagina viene collegata alla shell.
9. Aggiornare `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, `docs/SOURCE_OF_TRUTH.md`, `docs/README.md` se non gia' aggiornati.
10. Rileggere guardrail e manutenzione documentale.

## Criteri di accettazione

Fase 2 e' completata solo se:

- migration `0024` applicata senza errori
- tutte le tabelle target hanno `title_code='mines_classic'` e `site_code='casinoking'` per record storici e nuovi
- launch token nuovo include title/site/mode
- `mode=demo` viene rifiutato esplicitamente
- catalog API e admin catalog sono read-only
- Mines flow reale resta funzionante
- wallet/ledger reconciliation resta verde
- documentazione e atlas sono aggiornati
- nessuna feature fuori scope e' stata introdotta

## Fuori scope esplicito

- nessuna demo funzionante
- nessuna creazione/modifica Title da UI
- nessuna configurazione per Title
- nessun asset upload
- nessun theme editor
- nessuna modifica a payout/RTP/RNG/fairness
- nessuna riscrittura del backoffice Mines
