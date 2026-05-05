# CasinoKing - Theme system plan - Fase 5

## Stato

Cantiere aperto come piano operativo.

Avanzamento:

- piano operativo creato
- prima slice definita: theme runtime pubblico, ThemeProvider frontend e CSS variables
- resolver backend `theme_service.py` creato
- endpoint pubblico `/titles/{title_code}/theme` creato
- provider frontend `TitleThemeProvider` creato
- `mines.css` avviato verso CSS custom properties
- API admin minimale draft/publish theme creata
- atlas e indice documentale aggiornati
- tab "Tema" aggiunta nel backoffice editor Mines: carica stato admin, campi colore (type=color) e testo (type=text) per tutti e 14 i token ammessi, salva bozza e pubblica live con lo stesso pattern draft/publish del config editor
- F7-C: UI della tab "Tema" estratta in `frontend/app/ui/mines/mines-theme-editor.tsx`, pronta per una futura rifinitura skin/preset senza cambiare i contratti theme

Questo piano definisce la Fase 5 della roadmap "Suite giochi single-player
skinnabili": spostare la skin visuale dei Title da valori CSS hardcoded a design
tokens risolti per `title_code`.

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/TITLE_CONFIG_PLAN.md`
- roadmap v3 esterna: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- `backend/app/modules/platform/catalog/title_config_service.py`
- `backend/app/api/router.py`
- `frontend/app/lib/api.ts`
- `frontend/app/lib/types.ts`
- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/mines/mines.css`

File individuati ma non letti integralmente:

- documenti Word canonici in `docs/word/`
- allegati runtime Mines in `docs/runtime/`

Motivo: Fase 5 riguarda skin/config visuale e CSS runtime. Non cambia
matematica, payout runtime, RTP, RNG, fairness, wallet o ledger.

## Obiettivo

Rendere il tema visuale di un Title risolvibile da API e applicabile a runtime
dal frontend senza rebuild.

Contratto iniziale:

```text
GET /api/v1/titles/{title_code}/theme
```

Contratto admin minimo:

```text
GET /api/v1/admin/titles/{title_code}/theme
PUT /api/v1/admin/titles/{title_code}/theme
POST /api/v1/admin/titles/{title_code}/theme/publish
```

La risposta contiene:

- `title_code`
- `tokens`: design tokens CSS custom properties
- `assets`: asset URL attivi dal registry per il Title
- `etag`: hash del payload risolto

## Scope prima slice F5

Incluso:

- nuovo piano operativo `docs/THEME_SYSTEM_PLAN.md`
- resolver backend per tema pubblicato da `title_configs.theme_tokens_json`
- default theme se il Title non ha ancora tokens pubblicati
- endpoint pubblico `/titles/{title_code}/theme`
- risposta con asset URLs versionati presi da `title_assets`
- frontend `TitleThemeProvider`
- refactor iniziale di `mines.css` verso `var(--ck-*)`
- endpoint admin minimi per leggere, salvare draft e pubblicare tokens tema
- test backend per default theme, override da DB e validazione
- typecheck frontend
- aggiornamento atlas e indice documentale

Escluso:

- preview iframe/modal
- editor visuale avanzato con preview live, preset, validazione contrasto e controlli guidati oltre ai campi token minimi
- creazione UI di nuovi Title
- marketplace skin
- cambio di gameplay, payout, RTP, RNG/fairness
- cambio wallet/ledger/platform rounds

## Design tokens F5 iniziali

Tokens ammessi:

| Token | Significato |
| --- | --- |
| `--ck-bg` | Background shell gioco. |
| `--ck-surface` | Superficie pannelli principali. |
| `--ck-surface-strong` | Superficie board/card forti. |
| `--ck-fg` | Testo principale su tema Mines. |
| `--ck-muted` | Testo secondario. |
| `--ck-accent` | Accento primario. |
| `--ck-accent-strong` | Accento primario forte. |
| `--ck-good` | Safe/win/success. |
| `--ck-danger` | Mine/loss/danger. |
| `--ck-border` | Bordi principali. |
| `--ck-radius-panel` | Radius pannelli. |
| `--ck-radius-cell` | Radius celle board. |
| `--ck-shadow-panel` | Ombra pannelli. |
| `--ck-font-family` | Font stack runtime. |

I tokens non validi vengono rifiutati dal resolver per evitare CSS arbitrario.

## Sequenza di implementazione

1. Creare `docs/THEME_SYSTEM_PLAN.md`. Completato.
2. Creare `backend/app/modules/platform/catalog/theme_service.py`. Completato.
3. Creare route pubblica `/titles/{title_code}/theme`. Completato.
4. Includere la route nel router principale. Completato.
5. Aggiungere tipi frontend `TitleTheme`. Completato.
6. Creare `frontend/app/lib/theme/title-theme-provider.tsx`. Completato.
7. Wrappare `MinesStandalone` con il provider per `mines_classic`. Completato.
8. Spostare i colori principali di `mines.css` su `var(--ck-*)`. Completato per prima slice.
9. Aggiungere test backend mirati. Completato.
10. Aggiornare atlas e `docs/README.md`. Completato.
11. Aggiungere API admin minima per draft/publish del tema. Completato.
12. Aggiungere tab "Tema" in `mines-backoffice-editor.tsx` con campi controllati per i 14 token ammessi, azioni Ricarica/Salva/Pubblica e stato draft/published. Completato.

## Verifiche richieste

Backend:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/contract/test_title_theme_contract.py tests/integration/test_title_configs_split.py tests/unit/test_apply_migrations.py
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
```

Verifica eseguita dopo la prima slice runtime:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
$env:CASINOKING_API_BASE_URL='http://localhost:8000/api/v1'
python -m pytest tests/contract/test_title_theme_contract.py tests/contract/test_admin_assets_contract.py tests/integration/test_title_configs_split.py tests/unit/test_apply_migrations.py
cd frontend
npx tsc --noEmit
```

Esito: backend `23 passed`; frontend TypeScript OK.

Verifica rieseguita dopo API admin draft/publish theme:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
$env:CASINOKING_API_BASE_URL='http://localhost:8000/api/v1'
python -m pytest tests/contract/test_title_theme_contract.py tests/integration/test_title_configs_split.py tests/unit/test_apply_migrations.py
cd frontend
npx tsc --noEmit
```

Esito: backend `23 passed`; frontend TypeScript OK.

Verifica rieseguita dopo tab backoffice Tema:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
$env:CASINOKING_API_BASE_URL='http://localhost:8000/api/v1'
python -m pytest tests/contract/test_title_theme_contract.py tests/integration/test_title_configs_split.py tests/unit/test_apply_migrations.py
cd frontend
npx tsc --noEmit
```

Esito: backend `23 passed`; frontend TypeScript OK.

Smoke manuale minimo:

- `GET /api/v1/titles/mines_classic/theme` ritorna HTTP 200
- modificando `title_configs.theme_tokens_json` i tokens cambiano senza rebuild
- Mines resta giocabile e usa i default se il tema non e' popolato

## Criteri di accettazione

Fase 5 runtime e' accettabile se:

- il tema e' risolto per `title_code`
- i tokens non validi vengono rifiutati
- i default mantengono l'aspetto corrente se il DB non ha tema
- il frontend applica CSS variables a runtime
- asset e theme convivono nello stesso payload pubblico
- gameplay, matematica, fairness, wallet e ledger non cambiano

## Debiti e decisioni aperte

- Il backoffice "Tema" esiste come prima slice minima; resta da progettare una versione guidata con preview e validazione visiva.
- La preview live va progettata dopo il runtime theme, non prima.
- La validazione contrasto/leggibilita' resta fuori dalla prima slice.

## Backlog UI Tema

Da riprendere in una fase di rifinitura UI, non durante il cantiere tecnico
runtime:

- Rendere la tab "Tema" piu' compatta: i campi colore non devono occupare righe
  orizzontali enormi.
- Affiancare ai color picker il valore testuale corrente, per esempio `#56dc49`,
  modificabile o almeno leggibile.
- Aggiungere un pulsante "Ripristina default" che ricarichi i token default
  ufficiali della skin Mines senza pubblicare automaticamente.
- Valutare un layout a griglia densa per colori, radius, shadow e font.
- Distinguere meglio campi semplici e campi tecnici come `box-shadow` e
  `font-family`.
- Aggiungere una legenda dei token tema. I nomi `--ck-*` sono design tokens
  interni CasinoKing, non uno standard esterno: vanno documentati come contratto
  di progetto.
- Valutare se la legenda resta in questo piano operativo, in un documento
  tecnico dedicato, o in un allegato Word quando la fase tema diventa stabile.

Legenda minima da formalizzare:

| Token | Uso |
| --- | --- |
| `--ck-bg` | Sfondo principale della shell gioco. |
| `--ck-surface` | Pannelli principali e rail di controllo. |
| `--ck-surface-strong` | Board e superfici visualmente piu' marcate. |
| `--ck-fg` | Testo principale. |
| `--ck-muted` | Testo secondario. |
| `--ck-accent` | Azione primaria e highlight. |
| `--ck-accent-strong` | Variante forte dell'accento. |
| `--ck-good` | Stato safe, win o positivo. |
| `--ck-danger` | Stato mine, loss o pericolo. |
| `--ck-border` | Bordi principali del tema. |
| `--ck-radius-panel` | Arrotondamento pannelli. |
| `--ck-radius-cell` | Arrotondamento celle board. |
| `--ck-shadow-panel` | Ombra pannelli. |
| `--ck-font-family` | Font stack applicato alla scope Mines. |
