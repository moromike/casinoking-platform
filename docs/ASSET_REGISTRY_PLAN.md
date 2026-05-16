# CasinoKing - Asset registry plan - Fase 4

## Stato

Cantiere aperto come piano operativo.

Avanzamento:

- piano operativo creato
- migration `backend/migrations/sql/0026__title_assets.sql` creata
- config env e mount statico backend creati
- modulo backend `platform/asset_registry` creato
- router admin asset creato e testato
- integrazione frontend board/backoffice eseguita
- migrazione data-URL legacy implementata come comando applicativo idempotente
- validazione locale reale su stack Docker completata
- estensione asset kind completata per lobby card (`game_card`) e skin Title Mines (`title_logo`, `game_area_background`, `cell_face_down_background`)

Questo piano definisce la Fase 4 della roadmap "Suite giochi single-player
skinnabili": spostare gli asset grandi dei Title da data-URL nel JSON di config a
file persistiti su storage locale, serviti tramite URL pubblici versionati per
checksum.

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/TITLE_CONFIG_PLAN.md`
- `docs/md/CasinoKing_Documento_37_Catalogo_Engine_Title_Site.md`
- `docs/md/CasinoKing_Documento_38_Configurazione_Per_Title.md`
- roadmap v3 esterna: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/api/router.py`
- `backend/app/api/routes/admin.py`
- `backend/migrations/sql/0025__title_configs_split.sql`
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `frontend/app/ui/mines/mines-board.tsx`

File individuati ma non letti integralmente:

- documenti Word canonici in `docs/word/`
- allegati runtime Mines in `docs/runtime/`

Motivo: Fase 4 riguarda storage, backoffice assets e serving statico. Non cambia
matematica, payout runtime, RTP, RNG, fairness, wallet o ledger.

## Obiettivo

Sostituire progressivamente i data-URL grandi usati per gli asset board Mines con
asset persistiti su filesystem locale, tracciati in DB e serviti con URL stabili
ma versionati dal checksum.

Contratto target:

```text
/static/games/{title_code}/{asset_kind}/{checksum8}.{ext}
```

Regola di cache:

- se il file non cambia, l'URL resta uguale
- se il file cambia, il checksum cambia e quindi cambia anche l'URL
- il futuro passaggio a CDN deve richiedere solo cambio di base URL/storage adapter,
  non migrazione dei record DB

## Scope Fase 4

Incluso:

- nuovo piano operativo `docs/ASSET_REGISTRY_PLAN.md`
- migration `backend/migrations/sql/0026__title_assets.sql`
- nuova tabella `title_assets`
- nuovo modulo `backend/app/modules/platform/asset_registry/`
- storage locale filesystem con interfaccia sostituibile
- mount statico FastAPI per `/static/games`
- env `ASSET_PUBLIC_BASE_URL` e `ASSET_STORAGE_ROOT`
- nuovo router admin dedicato agli asset Title
- upload/list/delete asset per Title con validazione MIME e size cap
- idempotenza checksum: stesso file per stesso Title/kind non duplica record attivi
- integrazione minima con config Mines per usare URL asset invece di data-URL
- migrazione one-shot dei data-URL legacy gia' presenti in `mines_title_configs`
- test backend per migration, service, API e serving statico
- aggiornamento atlas e indici documentali se cambia il mapping reale dei file

Escluso:

- theme system e CSS variables (Fase 5)
- demo mode (Fase 6)
- editor Title riusabile/wizard creazione Title (Fase 7)
- CDN reale o upload cloud
- audio runtime nel player, salvo tracciamento DB come asset kind futuro
- modifica payout runtime, RTP, RNG, fairness
- modifica wallet, ledger, platform rounds o idempotenza finanziaria
- redesign UI backoffice

## Modello dati previsto

Migration: `backend/migrations/sql/0026__title_assets.sql`

```sql
BEGIN;

CREATE TABLE title_assets (
    id uuid PRIMARY KEY,
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    asset_kind varchar(32) NOT NULL,
    file_path text NOT NULL,
    public_url text NOT NULL,
    mime varchar(64) NOT NULL,
    byte_size int NOT NULL,
    checksum_sha256 varchar(64) NOT NULL,
    uploaded_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    status varchar(16) NOT NULL,
    CONSTRAINT title_assets_status_check
        CHECK (status IN ('active', 'deleted')),
    CONSTRAINT title_assets_kind_check
        CHECK (asset_kind IN (
            'logo',
            'background',
            'symbol_safe',
            'symbol_mine',
            'audio_win',
            'audio_lose',
            'audio_click',
            'font'
        )),
    CONSTRAINT title_assets_byte_size_positive_check
        CHECK (byte_size > 0),
    CONSTRAINT title_assets_checksum_sha256_length_check
        CHECK (length(checksum_sha256) = 64)
);

CREATE UNIQUE INDEX title_assets_one_active_kind_per_title_idx
    ON title_assets (title_code, asset_kind)
    WHERE status = 'active';

CREATE UNIQUE INDEX title_assets_checksum_per_title_kind_idx
    ON title_assets (title_code, asset_kind, checksum_sha256);

COMMIT;
```

Decisione operativa:

- `file_path` e' relativo allo storage root, non assoluto.
- `public_url` e' derivato dal contratto versionato e salvato per semplificare le
  risposte API.
- Il record storico resta con `status='deleted'` quando viene sostituito o rimosso.

## Asset kind Fase 4+Audio V1

Per Mines il primo uso reale e':

| asset_kind | Uso/campo equivalente |
| --- | --- |
| `symbol_safe` | `safe_icon_data_url` |
| `symbol_mine` | `mine_icon_data_url` |
| `audio_safe_reveal` | suono diamante trovato |
| `audio_mine_hit` | suono mina/loss |
| `audio_collect` | suono cashout riuscito |
| `audio_win` | suono win automatico |
| `game_card` | immagine quadrata card lobby |
| `title_logo` | logo/titolo immagine in-game |
| `game_area_background` | background della sola area gioco |
| `cell_face_down_background` | texture delle celle face-down |

I kind legacy `audio_lose` e `audio_click` restano ammessi dal constraint DB per
compatibilita' storica, ma il service e la UI nuova non li espongono in
scrittura.

I kind skin accettano solo PNG/WebP, hanno cap dedicati e sono risolti dal runtime
Mines soltanto se presenti nella skin pubblicata del Title. Il master
`mines_classic` resta invariato quando non ha chiave `skin`.

## Backend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `backend/migrations/sql/0026__title_assets.sql` | Creata: `title_assets`, vincoli e indici. |
| `backend/migrations/sql/0035__title_audio_asset_kinds.sql` | Creata: estende il constraint `title_assets_kind_check` ai kind audio runtime Mines. |
| `backend/migrations/sql/0037__title_game_card_asset_kind.sql` | Creata: estende il constraint `title_assets_kind_check` a `game_card`. |
| `backend/migrations/sql/0038__title_skin_asset_kinds.sql` | Creata: estende il constraint `title_assets_kind_check` a `title_logo`, `game_area_background` e `cell_face_down_background`. |
| `backend/app/core/config.py` | Completato: aggiunge `asset_storage_root` e `asset_public_base_url`. |
| `backend/app/main.py` | Completato: monta `StaticFiles` su `/static/games` leggendo dallo storage root. |
| `backend/app/modules/platform/asset_registry/__init__.py` | Completato: nuovo package platform. |
| `backend/app/modules/platform/asset_registry/storage.py` | Completato: interfaccia `AssetStorage` e implementazione `FilesystemAssetStorage`. |
| `backend/app/modules/platform/asset_registry/service.py` | Completato: validazione, checksum, upsert logico, list, delete e generazione URL. |
| `backend/app/api/routes/admin_assets.py` | Completato: endpoint admin `/admin/titles/{title_code}/assets`. |
| `backend/app/api/router.py` | Completato: include il router asset. |
| `backend/app/modules/games/mines/backoffice_config.py` | Completato: accetta URL statici asset oltre ai data-URL legacy nel payload board assets. |

Regola importante: l'asset registry e' platform/CMS-like. Mines lo consuma, ma non
deve diventare proprietario dello storage.

## Frontend - file e responsabilita'

| File | Azione prevista |
| --- | --- |
| `frontend/app/lib/types.ts` | Completato: aggiunge il tipo `TitleAsset` per le risposte asset registry. |
| `frontend/app/lib/api.ts` | Completato: aggiunge helper multipart/delete e risoluzione URL statici backend. |
| `frontend/app/ui/mines/mines-board.tsx` | Completato: continua a ricevere `assets`, ma risolve gli URL statici backend quando presenti. |
| `frontend/app/ui/mines/mines-backoffice-editor.tsx` | Completato: sostituisce il read-as-data-url locale con upload verso API asset per i due simboli board e aggiunge sezione Sounds per i kind audio V1. |
| `frontend/app/ui/mines/mines-sound-assets-editor.tsx` | Completato: upload/preview/delete dei suoni Mines per Title. |

Fase 4 non deve introdurre nuove tab o redesign. Il pannello "Board assets" resta
il punto operativo, cambiando solo il modo in cui il file viene persistito.

## API admin previste

Prefisso: `/admin/titles/{title_code}/assets`

Endpoint:

- `GET /admin/titles/{title_code}/assets`
- `POST /admin/titles/{title_code}/assets`
- `DELETE /admin/titles/{title_code}/assets/{asset_kind}`

Payload upload:

- `multipart/form-data`
- campo `asset_kind`
- campo `file`

Risposta asset:

```json
{
  "id": "uuid",
  "title_code": "mines_classic",
  "asset_kind": "symbol_safe",
  "public_url": "/static/games/mines_classic/symbol_safe/abcdef12.png",
  "mime": "image/png",
  "byte_size": 12345,
  "checksum_sha256": "...",
  "status": "active",
  "created_at": "..."
}
```

Validazioni minime:

- title esistente
- admin con area `mines` per asset Mines nella prima fase
- MIME immagini: `image/png`, `image/svg+xml`
- MIME audio V1: `audio/mpeg`, `audio/ogg`, `audio/wav`, `audio/webm`
- size cap iniziale immagini: 512 KB
- size cap audio V1: 1 MB
- estensione derivata dal MIME, non dal nome file utente

## Migrazione data-URL legacy

Fase 4 deve includere una migrazione one-shot applicativa o testabile che:

1. legge `published_board_assets_json` e `draft_board_assets_json` da
   `mines_title_configs`
2. per `safe_icon_data_url` crea asset `symbol_safe`
3. per `mine_icon_data_url` crea asset `symbol_mine`
4. scrive i file su storage
5. crea record `title_assets`
6. sostituisce il payload config con riferimenti URL compatibili

La migrazione non deve droppare subito il supporto data-URL. Il frontend e il
backend devono accettare data-URL legacy finche' gli ambienti non sono migrati.

## Strategia di compatibilita'

Per ridurre rischio:

- `MinesBoard` deve continuare a renderizzare sia data-URL sia URL statici.
- Gli endpoint config title-aware restano compatibili con `board_assets`.
- Gli alias legacy `/admin/games/mines/backoffice-config*` restano invariati.
- Il supporto data-URL viene considerato deprecated, non rimosso in F4.

## Sequenza di implementazione proposta

1. Creare `0026__title_assets.sql`. Completato.
2. Aggiungere config env e mount statico. Completato.
3. Creare `asset_registry/storage.py`. Completato.
4. Creare `asset_registry/service.py`. Completato.
5. Aggiungere router admin asset e includerlo in `api/router.py`. Completato.
6. Scrivere test migration/service/API. Completato per service/API backend.
7. Integrare `mines-backoffice-editor.tsx` con upload asset. Completato.
8. Integrare `mines-board.tsx` e tipi frontend per URL asset. Completato.
9. Aggiungere migrazione one-shot per data-URL esistenti. Completato con `backend/app/tools/migrate_mines_board_asset_data_urls.py`.
10. Aggiornare `ARCHITECTURE_ATLAS_MINES.md` e `ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`.
11. Eseguire verifiche backend/frontend mirate.
12. Rileggere guardrail e document maintenance.

## Verifiche richieste

Backend:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/unit/test_apply_migrations.py
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_asset_registry.py
python -m pytest tests/contract/test_admin_assets_contract.py
```

Verifica eseguita dopo gli step backend 2-6:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
$env:CASINOKING_API_BASE_URL='http://127.0.0.1:8001/api/v1'
python -m pytest tests/integration/test_asset_registry.py tests/contract/test_admin_assets_contract.py tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py tests/unit/test_apply_migrations.py
```

Esito: `25 passed`.

Verifica rieseguita dopo gli step frontend 7-9:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
$env:CASINOKING_API_BASE_URL='http://127.0.0.1:8001/api/v1'
python -m pytest tests/integration/test_asset_registry.py tests/contract/test_admin_assets_contract.py tests/integration/test_mines_backoffice_config.py tests/integration/test_title_configs_split.py tests/unit/test_apply_migrations.py
cd frontend
npx tsc --noEmit
```

Esito: backend `26 passed`; frontend TypeScript OK.

Verifica locale su stack Docker rieseguita il 2026-05-04:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env ps
Invoke-WebRequest -UseBasicParsing http://localhost:3000
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health/live
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health/ready
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env exec -T postgres psql -U casinoking -d casinoking -c "select migration_name, applied_at from schema_migrations where migration_name = '0026__title_assets.sql';"
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env exec -T postgres psql -U casinoking -d casinoking -c "select to_regclass('public.title_assets') as title_assets_table;"
```

Esito:

- container frontend, backend, postgres e redis `healthy`
- frontend `http://localhost:3000`: HTTP 200
- backend live/ready: HTTP 200
- DB raggiungibile con query reale
- migration `0026__title_assets.sql` applicata
- tabella `title_assets` presente
- smoke API asset registry completato: upload PNG `symbol_safe`, static URL HTTP 200,
  list asset, delete asset con `status='deleted'`
- test mirati contro DB Docker: `26 passed`
- frontend TypeScript OK

Frontend:

```powershell
cd frontend
npx tsc --noEmit
```

Smoke manuale minimo:

- upload PNG per `symbol_safe`
- upload SVG per `symbol_mine`
- verificare file su storage
- verificare URL `/static/games/...` con HTTP 200
- ricaricare Mines e verificare rendering asset
- upload identico due volte: un solo record attivo, URL invariato
- delete asset: fallback a icona default o asset precedente previsto dal payload

## Criteri di accettazione

Fase 4 e' completata solo se:

- `title_assets` esiste con vincoli e indici attesi
- gli asset sono persistiti su filesystem fuori dal DB
- gli URL sono versionati per checksum
- upload duplicato dello stesso file non crea duplicati attivi
- un solo asset per `title_code + asset_kind` e' active
- il frontend Mines renderizza gli asset via URL
- i data-URL legacy restano supportati per compatibilita'
- non cambia gameplay, matematica, payout, fairness, wallet o ledger
- gli atlas sono aggiornati solo dopo il cambio reale di mapping file/responsabilita'

## Debiti e decisioni aperte

- Decidere se `public_url` va salvato in DB o sempre derivato al volo. Il piano lo
  salva per risposte API semplici, ma il service deve poterlo rigenerare.
- La migrazione data-URL legacy e' un comando applicativo idempotente perche'
  deve scrivere file su filesystem e calcolare checksum.
- Il cleanup definitivo dei data-URL legacy resta fuori scope F4.
- `assets/` resta cartella locale di servizio non versionata per sorgenti e
  prove grafiche. Gli asset di prodotto devono entrare tramite upload nel
  registry o pipeline documentata, non tramite commit diretto della cartella di
  lavoro.
- I suoni Mines sono coperti dal piano dedicato
  `docs/MINES_SOUND_ASSETS_PLAN.md`: V1 estende service, UI e runtime per
  `audio_safe_reveal`, `audio_mine_hit`, `audio_collect`, `audio_win`.
  I kind legacy `audio_lose` e `audio_click` restano solo compatibilita' DB e
  non devono essere esposti in scrittura dalla nuova UI.
