# CasinoKing - Title Editor Shell Plan - Fase 7

## Stato

Piano operativo corretto e riallineato. Prima slice F7-A applicata in forma
conservativa: selezione Title dal catalogo, shell frontend, registry engine e
Mines editor pilotato da `title_code` dinamico.

Questo documento sostituisce il piano preliminare generato per Fase 7. La
direzione architetturale resta valida, ma l'esecuzione viene divisa in due
slice per evitare di mischiare refactor frontend, creazione Title, backend
mutation e redesign backoffice.

- F7-A: Title Editor Shell per Title esistenti. In corso, prima slice applicata.
- F7-B: wizard/creazione nuovi Title da UI. Fuori scope F7-A.
- F7-C: estrazione profonda del vecchio editor Mines in componenti
  Title-level/engine-specific piu' piccoli. Prima slice applicata: UI
  `Grid & mines` e tab `Tema` estratte dal container principale.

## Fonti e contesto

F7 si appoggia alle fasi gia' introdotte:

- F1: catalogo Engine / Title / Site.
- F2: runtime title-aware e site-aware.
- F3: configurazione backoffice per Title, con split fra `title_configs` e
  `mines_title_configs`.
- F4: asset registry per Title.
- F5: theme runtime e admin theme draft/publish.
- F6: demo mode anonima chiusa. F6-A/B/C hanno introdotto infrastruttura,
  wallet demo e branching Mines; F6-D/F6-E hanno chiuso frontend anonimo,
  reset sessione demo e verifica/documentazione finale.

Nota importante: F7 non deve riaprire F6 salvo bug reali. La parte demo resta
un cantiere chiuso; eventuali evoluzioni future, come demo da utente loggato o
preview iframe/modal, sono fuori scope F7-A.

## Obiettivo F7-A

Creare una shell frontend riusabile per configurare un Title esistente dal
backoffice, separando:

- responsabilita' platform/Title: caricamento del Title, config generica,
  theme, asset, stato draft/publish e orchestrazione UI;
- responsabilita' engine-specific: campi tecnici propri del gioco, per ora
  solo Mines.

Il primo target reale e' `mines_classic`, ma la shell deve ricevere `title_code`
e `engine_code` come dati dinamici, senza costanti hardcoded nel nuovo flusso.

## Decisioni vincolanti

- Non creare subito la route Next `frontend/app/admin/titles/[title_code]/page.tsx`.
  In F2/F3 e' gia' stata scelta l'integrazione nella shell admin esistente.
  Una route dedicata resta possibile in una fase successiva se porta un vantaggio
  reale.
- Non introdurre creazione Title da UI in F7-A.
- Non modificare payout, RTP, RNG, fairness, wallet, ledger o round economici.
- Non cambiare gli endpoint backend se non emerge un bug reale.
- Non fingere supporto backend universale per engine non-Mines: oggi gli endpoint
  config title-aware sono ancora Mines-aware lato backend.
- Non trasformare l'editor in un redesign generale del backoffice.
- Conservare gli endpoint legacy Mines e la retrocompatibilita'.

## Contratti API da usare

F7-A deve usare gli endpoint gia' esistenti:

```text
GET  /api/v1/catalog/sites/casinoking/titles
GET  /api/v1/admin/games/titles/{title_code}/config
PUT  /api/v1/admin/games/titles/{title_code}/config
POST /api/v1/admin/games/titles/{title_code}/config/publish
GET  /api/v1/admin/titles/{title_code}/assets
POST /api/v1/admin/titles/{title_code}/assets
DELETE /api/v1/admin/titles/{title_code}/assets/{asset_kind}
GET  /api/v1/admin/titles/{title_code}/theme
PUT  /api/v1/admin/titles/{title_code}/theme
POST /api/v1/admin/titles/{title_code}/theme/publish
```

Endpoint da NON inventare in F7-A:

```text
/api/v1/admin/titles/{title_code}/config
/api/v1/admin/titles
/api/v1/admin/engines
```

## Architettura frontend target

### Title selection

`frontend/app/ui/platform-catalog-panel.tsx` resta il punto di lettura del
catalogo, ma puo' esporre una azione minima di selezione/configurazione del
Title.

Questa azione:

- non crea Title;
- non modifica catalogo;
- non pubblica Site/Title;
- passa `title_code` ed `engine_code` alla shell admin esistente.

### Title Editor Shell

Nuovo componente candidato:

```text
frontend/app/ui/title-editor/title-editor-shell.tsx
```

Responsabilita' target:

- ricevere `titleCode`, `engineCode`, `accessToken`, stato busy e callback status;
- caricare config draft/published del Title;
- caricare theme admin del Title;
- caricare assets attivi del Title;
- mantenere lo stato locale dei form;
- coordinare save draft e publish sui contratti gia' esistenti;
- montare l'editor engine-specific risolto dal registry;
- mostrare uno stato chiaro se l'engine non ha editor registrato.

Nella prima slice applicata la shell risolve l'editor engine-specific e passa
`titleCode` dinamico; il caricamento effettivo di config/theme/assets resta nel
vecchio `MinesBackofficeEditor`, ora parametrizzato per Title. La separazione
fisica completa delle responsabilita' resta F7-C.

### Engine Editor Registry

Nuovo modulo candidato:

```text
frontend/app/ui/title-editor/engine-editor-registry.ts
```

Prima registrazione:

```text
mines -> MinesEngineEditor
```

Per engine non registrati:

- mostrare uno stato non distruttivo;
- non tentare fallback su Mines;
- non permettere salvataggi engine-specific.

### Mines Engine Editor

Nuovo componente candidato:

```text
frontend/app/ui/mines/mines-engine-editor.tsx
```

Responsabilita' Mines-specific target:

- `published_grid_sizes`
- `published_mine_counts`
- `default_mine_counts`

Responsabilita' da NON spostare automaticamente nel Mines editor:

- `rules_sections`: vive in `title_configs` ed e' trattato come config
  Title-level nel modello F3, anche se il contenuto attuale parla di Mines.
- `ui_labels`: vive in `title_configs` ed e' trattato come config Title-level.
- theme tokens: gestiti dal theme service.
- asset registry: platform-owned; la shell puo' mostrare i kind rilevanti per
  l'engine corrente, ma lo storage resta platform.

### Wrapper legacy

`frontend/app/ui/mines/mines-backoffice-editor.tsx` non deve essere cancellato
subito. In F7-A puo':

- restare temporaneamente come implementazione concreta del Mines editor,
  parametrizzata da `titleCode`;
- essere poi ridotto in F7-C quando la shell avra' assorbito davvero le parti
  Title-level comuni.

La deprecazione definitiva va fatta solo dopo typecheck, test e smoke admin.

## Sequenza operativa F7-A

1. Correggere questo piano operativo e mantenere il riferimento in `docs/README.md`.
2. Preparare i tipi frontend minimi, senza rinominare payload backend funzionanti.
3. Aggiungere stato di selezione Title nella shell admin esistente.
4. Aggiungere azione minima in `PlatformCatalogPanel` per selezionare un Title
   configurabile.
5. Creare `TitleEditorShell` usando gli endpoint esistenti.
6. Creare `engine-editor-registry.ts`.
7. Creare `MinesEngineEditor` come adapter conservativo verso l'editor Mines
   esistente.
8. Parametrizzare `MinesBackofficeEditor` con `titleCode` dinamico.
9. Eseguire typecheck frontend.
10. Eseguire test backend mirati solo se il refactor tocca indirettamente payload
    o contratti API.
11. Smoke admin reale: catalogo -> selezione Title -> carica config/theme/assets
    -> salva bozza -> publish -> ricarica.
12. Aggiornare gli atlas solo se il cambio reale sposta responsabilita' o mapping
    file.

## F7-C - Refactor editor Mines, registrato ma non incluso nella prima slice

La prima slice F7-A abilita il flusso funzionale senza riscrivere il grande
editor Mines. F7-C spezza gradualmente `mines-backoffice-editor.tsx` in
componenti piu' piccoli senza cambiare endpoint o payload.

Prima slice F7-C applicata:

- `frontend/app/ui/mines/mines-grid-config-editor.tsx`
- `frontend/app/ui/mines/mines-theme-editor.tsx`

Questi componenti sono ancora presentational: stato, validazioni e chiamate API
restano nel container `MinesBackofficeEditor`. Questo e' intenzionale per
ridurre il rischio e mantenere invariati i contratti F3/F4/F5.

Obiettivi minimi F7-C:

- spostare caricamento/salvataggio di config generica, theme e assets nella
  shell o in hook Title-level;
- lasciare nel Mines editor solo griglie, mine counts, default e UI specifica
  Mines;
- mantenere invariati endpoint e payload;
- aggiungere test/smoke focalizzati sul cambio Title e sui publish flow.

Nota UI da ricordare per la revisione backoffice: la sezione `Tema` funziona ma
i controlli/bottoni non sono ancora rifiniti visivamente; ora ha pero' un
componente dedicato su cui costruire un futuro skin/preset manager.

## F7-B - Fuori scope ma registrata

La creazione di nuovi Title da UI e' una fase distinta.

F7-B richiedera' almeno:

- API admin per creare `game_titles`;
- API admin per associare `site_titles`;
- inizializzazione sicura di `title_configs`;
- inizializzazione sicura della tabella engine-specific, per Mines
  `mines_title_configs`;
- validazioni su `engine_code`, `title_code`, permessi admin, stato active/inactive;
- strategia di rollback se una creazione parziale fallisce;
- test integration/contract dedicati;
- decisione UX su wizard, duplicazione da Title esistente o creazione vuota.

F7-B non va implementata insieme a F7-A.

## Cosa sara' possibile dopo F7-A

Dopo F7-A sara' possibile:

- configurare `mines_classic` senza dipendere da costanti hardcoded nel nuovo
  editor;
- configurare un secondo Title Mines gia' esistente e correttamente seedato a DB;
- riusare la shell come base per futuri engine editor;
- risolvere in modo esplicito gli engine supportati tramite registry frontend;
- preparare una successiva revisione di backoffice e sito web con confini piu'
  chiari.

## Cosa non sara' ancora possibile dopo F7-A

Dopo F7-A non sara' ancora possibile:

- creare nuovi Title da UI;
- creare nuovi engine da UI;
- lanciare automaticamente dal player una libreria completa multi-title, se la
  UI player resta hardcoded su Mines Classic;
- editare engine non-Mines;
- modificare payout, RTP, RNG o fairness;
- usare il backoffice come CMS completo del sito;
- considerare completata la separazione interna del grande editor Mines:
  l'adapter `MinesEngineEditor` oggi incapsula ancora il vecchio editor
  parametrizzato;
- andare in modalita' produzione o external HTTP adapter: Fase 9b/c resta
  rinviata finche' Michele non dira' esplicitamente di voler pubblicare in
  produzione.

Questi limiti sono intenzionali: vanno valutati in cantieri successivi, con
probabile revisione dedicata di sito web e backoffice.

## Test e verifiche minime

Frontend:

```powershell
cd frontend
npx tsc --noEmit
```

Backend, solo se si toccano contratti o payload:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:55432/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/contract/test_admin_assets_contract.py tests/contract/test_title_theme_contract.py
```

Smoke manuale/admin:

- login backoffice;
- apertura sezione giochi;
- caricamento catalogo;
- selezione `mines_classic`;
- caricamento config/theme/assets;
- save draft config;
- publish config;
- save/publish theme se toccato;
- upload/delete asset se toccato;
- ricarica pagina e verifica assenza di regressioni evidenti.

## Criteri di accettazione F7-A

F7-A e' accettabile solo se:

- `title_code` e `engine_code` sono dinamici nel nuovo flusso;
- `mines_classic` resta funzionante come prima;
- gli endpoint F3/F4/F5 non cambiano contratto;
- l'editor Mines usa path API derivati dal `title_code` selezionato;
- la shell gestisce ordinatamente selezione Title e registry engine;
- engine non supportati non causano salvataggi errati;
- nessuna feature fuori scope viene introdotta;
- typecheck e verifiche mirate sono verdi;
- l'impatto documentale e' dichiarato a fine task.
