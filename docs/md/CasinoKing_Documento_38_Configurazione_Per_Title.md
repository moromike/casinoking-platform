# CasinoKing - Documento 38

Consolidamento operativo configurazione per Title dopo Fase 3

## Stato del documento

- Documento operativo di consolidamento post Fase 3.
- Non e' un mirror di un DOCX canonico esistente.
- Non sostituisce i Word canonici in `docs/word/`.
- Consolida il modello implementato in `docs/TITLE_CONFIG_PLAN.md`.

## 1. Obiettivo

Registrare il modello stabile con cui CasinoKing configura un Title di gioco separando:

- configurazione generica di pubblicazione del Title
- configurazione specifica dell'engine Mines

Questo permette di avere piu' varianti commerciali dello stesso engine senza duplicare la logica di gioco.

## 2. Modello implementato

La Fase 3 ha spostato la configurazione da una singola tabella legacy:

- `mines_backoffice_config`

a due tabelle nuove:

- `title_configs`
- `mines_title_configs`

Migration:

- `backend/migrations/sql/0025__title_configs_split.sql`

## 3. Responsabilita' delle tabelle

### `title_configs`

Contiene configurazione generica del Title:

- rules sections pubblicate
- UI labels pubblicate
- draft rules sections
- draft UI labels
- metadati di publish/draft
- placeholder per fasi future:
  - `bet_limits_json`
  - `demo_labels_json`
  - `theme_tokens_json`

Questi placeholder sono creati in Fase 3 ma non sono ancora popolati, validati o modificabili da editor.

### `mines_title_configs`

Contiene configurazione engine-specific Mines:

- grid sizes pubblicate
- mine counts pubblicati
- default mine counts
- board assets pubblicati
- draft grid sizes
- draft mine counts
- draft default mine counts
- draft board assets

Gli asset board restano JSON/data-URL come nel modello precedente. L'asset registry filesystem e' fase futura.

## 4. Compatibilita' legacy

La migration Fase 3:

1. rinomina la tabella storica in `mines_backoffice_config_legacy`
2. crea le nuove tabelle
3. copia i dati su `title_code = 'mines_classic'`
4. crea una view read-only `mines_backoffice_config`

La view serve solo come compatibilita' e guard-rail di transizione. I writer nuovi non devono scrivere sulla view.

Il cleanup di:

- `mines_backoffice_config_legacy`
- view `mines_backoffice_config`

e' differito a un micro-task separato, dopo verifica esplicita che nessun reader nascosto dipenda dalla view.

## 5. Service e API

File principali:

- `backend/app/modules/platform/catalog/title_config_service.py`
- `backend/app/modules/games/mines/backoffice_config.py`
- `backend/app/api/routes/admin.py`
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`

Endpoint title-aware:

- `GET /admin/games/titles/{title_code}/config`
- `PUT /admin/games/titles/{title_code}/config`
- `POST /admin/games/titles/{title_code}/config/publish`

Alias legacy mantenuti:

- `GET /admin/games/mines/backoffice-config`
- `PUT /admin/games/mines/backoffice-config`
- `POST /admin/games/mines/backoffice-config/publish`

Gli alias legacy puntano a `title_code = 'mines_classic'`.

## 6. Publish e consistenza

La pubblicazione deve essere atomica fra:

- parte generica in `title_configs`
- parte Mines in `mines_title_configs`

Un publish riuscito non deve lasciare draft o published parzialmente divergenti fra le due tabelle.

## 7. Fuori scope Fase 3

Non sono inclusi:

- creazione Title da UI
- skin/theme editor
- asset registry filesystem
- demo mode
- popolamento di bet limits configurabili
- modifiche a payout runtime, RTP, RNG, fairness
- modifiche a wallet/ledger
- drop della tabella legacy e della view di compatibilita'

## 8. Verifiche di riferimento

Suite rilevanti:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_financial_and_mines_flows.py tests/integration/test_title_code_propagation.py tests/integration/test_platform_catalog_bootstrap.py tests/unit/test_apply_migrations.py
cd frontend
npx tsc --noEmit
```

Verifica rieseguita il 2026-05-04:

- `python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py`
- Esito: `9 passed`

## 9. Debiti aperti

- Promuovere questo consolidamento in un DOCX canonico quando verra' creato il pacchetto Word post Fase 3.
- Eseguire il cleanup legacy solo come task separato.
- Non iniziare F4/F5 prima di aver deciso se i documenti Word nuovi devono essere creati direttamente o gestiti come draft markdown promossi successivamente.
