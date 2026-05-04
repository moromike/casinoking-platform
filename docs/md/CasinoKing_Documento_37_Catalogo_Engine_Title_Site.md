# CasinoKing - Documento 37

Consolidamento operativo catalogo Engine / Title / Site dopo Fase 1-3

## Stato del documento

- Documento operativo di consolidamento post Fase 3.
- Non e' un mirror di un DOCX canonico esistente.
- Non sostituisce i Word canonici in `docs/word/`.
- Consolida le decisioni gia' implementate nei piani:
  - `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md`
  - `docs/TITLE_CODE_PROPAGATION_PLAN.md`
  - `docs/TITLE_CONFIG_PLAN.md`

## 1. Obiettivo

Definire in modo stabile la tassonomia giochi usata da CasinoKing per supportare giochi proprietari, varianti commerciali e distribuzione su uno o piu' siti.

La tassonomia separa:

- Engine: implementazione tecnica di un gioco.
- Title: prodotto commerciale pubblicato a partire da un engine.
- Site: destinazione o brand dove un title e' disponibile.

## 2. Modello concettuale

### Engine

Un engine rappresenta codice, regole, matematica, RNG, fairness e payout runtime di un tipo di gioco.

Esempio attuale:

- `engine_code = 'mines'`

L'engine non identifica una variante commerciale pubblicata. Identifica il modulo tecnico riusabile.

### Title

Un title rappresenta un gioco pubblicabile con identita' commerciale e configurazione propria.

Esempio attuale:

- `title_code = 'mines_classic'`
- `engine_code = 'mines'`

Un engine puo' avere piu' title in futuro. La creazione di title aggiuntivi da UI non e' inclusa nelle Fasi 1-3.

### Site

Un site rappresenta il sito, brand o canale di distribuzione.

Esempio attuale:

- `site_code = 'casinoking'`

La disponibilita' di un title su un site passa dalla relazione `site_titles`.

## 3. Schema dati implementato

La Fase 1 ha introdotto:

- `game_engines`
- `game_titles`
- `sites`
- `site_titles`

Migration:

- `backend/migrations/sql/0023__platform_catalog_bootstrap.sql`

Seed minimo:

- engine `mines`
- title `mines_classic`
- site `casinoking`
- relazione active `(casinoking, mines_classic)`

## 4. Propagazione runtime implementata

La Fase 2 ha propagato `title_code` e `site_code` nei flussi runtime, senza cambiare matematica o conti.

Migration:

- `backend/migrations/sql/0024__title_and_site_code_propagation.sql`

Tabelle coinvolte:

- `platform_rounds`
- `game_access_sessions`
- `game_table_sessions`
- `mines_game_rounds`

Regola:

- `game_code` resta codice legacy/engine.
- `title_code` identifica il prodotto commerciale.
- `site_code` identifica la distribuzione.

## 5. API e backoffice implementati

La Fase 2 ha introdotto catalogo read-only e propagazione nei token/sessioni.

File principali:

- `backend/app/modules/platform/catalog/service.py`
- `backend/app/api/routes/platform_catalog.py`
- `backend/app/modules/platform/game_launch/service.py`
- `frontend/app/ui/platform-catalog-panel.tsx`

Il backoffice catalogo e' solo read-only. Non esistono in F1-F3:

- creazione Title da UI
- modifica Site/Title da UI
- demo mode funzionante
- asset registry filesystem
- theme editor

## 6. Decisioni vincolanti

- Non rinominare `game_code` in modo opportunistico.
- Non usare `game_code` come chiave commerciale dei nuovi sviluppi.
- Usare `title_code` per configurazione e pubblicazione del gioco.
- Usare `site_code` per distribuzione, reporting e audit.
- Fino a nuove istruzioni, il solo title supportato operativamente e' `mines_classic` su site `casinoking`.
- La modalita' `demo` resta rifiutata fino alla fase dedicata.

## 7. Verifiche di riferimento

Suite rilevanti:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/integration/test_platform_catalog_bootstrap.py
python -m pytest tests/integration/test_title_code_propagation.py
python -m pytest tests/integration/test_financial_and_mines_flows.py
```

## 8. Debiti aperti

- Promuovere questo consolidamento in un DOCX canonico quando verra' creato il pacchetto Word post Fase 3.
- Non sovrascrivere gli attuali documenti operativi 31/32, che trattano temi diversi e sono ancora referenziati.
