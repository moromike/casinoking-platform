Status: COMPLETED
Last meaningful update: 2026-05-06

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
- F7-B: creazione nuovi Title da UI. Prima slice applicata con duplicazione
  conservativa di varianti Mines da master bloccato.
- F7-C: estrazione profonda del vecchio editor Mines in componenti
  Title-level/engine-specific piu' piccoli. Prima slice applicata: UI
  `Grid & mines` e tab `Tema` estratte dal container principale.
- F7-D: pubblicazione leggera delle varianti nel sito e lancio demo
  title-aware. Prima slice applicata.

## Fotografia corrente e next step

Aggiornamento operativo del 2026-05-06.

### Stato corrente

La Fase 7 e' arrivata a una prima chiusura funzionale, ma non a una chiusura
UX/prodotto definitiva.

Gia' funzionante:

- il catalogo backoffice distingue Engine, master e varianti;
- `mines_classic` e' il master Mines bloccato;
- le varianti Mines sono duplicabili dal master;
- le varianti sono rinominabili;
- solo le varianti sono modificabili in config, tema e asset;
- il master e le varianti sono apribili in preview demo;
- le varianti possono essere pubblicate nella libreria sito in demo oppure
  demo+real;
- la lobby player legge la libreria pubblica dal backend;
- il player Mines legge `title_code` dall'URL e usa quel Title per config,
  tema, launch token, access session, table session e round real/demo.

Fix importante applicato durante F7-D:

- nel real-play title-aware, il frontend deve creare `access_session` e
  `table_session` con lo stesso `title_code` del launch token; il backend deve
  continuare a rifiutare mismatch fra Title di sessione tavolo e Title del round.

### Next step consigliato

Prima di aprire nuovi cantieri prodotto, chiudere Fase 7 con una passata di
consolidamento:

1. Smoke manuale completo:
   backoffice -> crea/renomina variante -> personalizza config/tema -> publish
   config/tema -> pubblica demo+real -> lobby -> demo -> real Bet/Collect.
2. Riallineamento test:
   aggiornare i test legacy che assumono catalogo con solo `mines_classic`,
   perche' ora il catalogo puo' contenere master e varianti reali.
3. Commit ordinato della slice F7:
   separare, se possibile, migrazioni/backend/frontend/test/documentazione.
4. Revisione UX dedicata del backoffice giochi:
   trasformare la vista attuale tecnica in una pagina chiara con categorie,
   master, varianti, creazione variante e dettaglio personalizzazione.

### Remind futuri non ancora analizzati

Questi punti sono registrati ma non autorizzano implementazione automatica:

- UI editoriale sito/lobby per pubblicazione giochi: card, asset immagine,
  descrizioni, ordinamento, grouping, stati demo/real e visibilita';
- redesign backoffice giochi e sezione Tema, inclusi controlli piu' leggibili e
  meno tecnici;
- libreria persistente di skin nominate da DB;
- creazione nuovi Title vuoti, separata dalla duplicazione del master;
- creazione nuovi engine e supporto engine non-Mines;
- CMS generale del sito, distinto dalla pubblicazione leggera dei giochi;
- identificativo spin/round/reporting visibile in modo auditabile;
- produzione/external HTTP adapter Fase 9b/c;
- eventuale crypto wallet proprietario, con design finanziario dedicato.

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

Nota UI da ricordare per la revisione backoffice: la sezione `Tema` ora ha un
componente dedicato e preset frontend che compilano la bozza. Resta fuori scope
la libreria persistente di skin nominate da DB.

## F7-B - Master Mines e varianti

La prima slice F7-B e' stata corretta in F7-B2: la duplicazione non vive dentro
il dettaglio editor, ma nella vista catalogo/varianti dell'engine Mines.

Regola architetturale:

```text
Engine/Categoria
  -> Master non modificabile
  -> Varianti modificabili
```

Per Mines il master corrente e' `mines_classic`. Il master e' la base stabile da
cui creare varianti, non un Title da personalizzare direttamente.

Endpoint introdotto:

```text
POST /api/v1/admin/games/titles/{source_title_code}/duplicate
PUT  /api/v1/admin/games/titles/{title_code}/profile
```

Payload minimo:

```json
{
  "title_code": "mines_lagoon",
  "display_name": "Mines Lagoon",
  "site_code": "casinoking"
}
```

La duplicazione e' consentita solo se `{source_title_code}` e' un master Mines.
Crea in una singola transazione:

- `game_titles` con engine `mines`;
- metadata `is_master=false` e `source_title_code=<master>`;
- `site_titles` per il Site richiesto;
- `title_configs` copiando la configurazione pubblicata del sorgente e
  inizializzando la bozza allo stesso contenuto;
- `mines_title_configs` copiando griglie/mine/default pubblicati e
  inizializzando la bozza allo stesso contenuto;
- board assets azzerati a `null` per evitare riferimenti accidentali agli asset
  visuali del Title sorgente.

Validazioni applicate:

- solo sorgenti con engine `mines` e `is_master=true`;
- `title_code` nuovo, 3-64 caratteri, solo lettere minuscole, numeri e `_`;
- `display_name` obbligatorio;
- Site esistente;
- status `active`/`inactive`;
- permesso backoffice area `mines`.

Resta fuori scope F7-B:

- creare engine da UI;
- creare Title vuoti da zero;
- modificare il master Mines;
- pubblicare/disattivare Site/Title da UI;
- duplicare asset fisici o librerie di skin nominate;
- rendere la lobby/player una libreria multi-title automatica;
- supportare engine non-Mines.

Regole di immutabilita' master:

- `PUT /admin/games/titles/{title_code}/profile` rifiuta master;
- `PUT /admin/games/titles/{title_code}/config` rifiuta master;
- `POST /admin/games/titles/{title_code}/config/publish` rifiuta master;
- `PUT /admin/titles/{title_code}/theme` rifiuta master;
- `POST /admin/titles/{title_code}/theme/publish` rifiuta master;
- upload/delete asset admin rifiutano master.

La UI deve riflettere lo stesso confine:

- vista giochi -> categoria `Mines`;
- sezione `Master` con `mines_classic` bloccato ma apribile almeno in preview demo;
- sezione `Varianti` con i Title modificabili, incluso il nome variante;
- azione `Crea variante da master` nella vista categoria, non dentro l'editor;
- dettaglio editor completo solo per varianti.

## Cosa sara' possibile dopo F7-A

Dopo F7-A sara' possibile:

- configurare `mines_classic` senza dipendere da costanti hardcoded nel nuovo
  editor;
- configurare un secondo Title Mines gia' esistente e correttamente seedato a DB;
- riusare la shell come base per futuri engine editor;
- risolvere in modo esplicito gli engine supportati tramite registry frontend;
- preparare una successiva revisione di backoffice e sito web con confini piu'
  chiari.

## F7-D - Game library pubblica e preview demo

F7-D introduce uno strato separato da editor e runtime:

```text
configurazione variante -> pubblicazione su sito -> libreria player -> launch demo/real
```

Questo livello non e' un CMS generale. Serve solo a decidere quali varianti
appaiono nella libreria del sito e con quali modalita' di lancio.

Schema esteso:

- `site_titles.lobby_visibility`: `hidden`/`visible`;
- `site_titles.demo_enabled`;
- `site_titles.real_enabled`;
- `site_titles.lobby_display_name`;
- `site_titles.lobby_description`;
- `site_titles.featured`;
- `site_titles.position`.

Contratti introdotti:

```text
GET /api/v1/games/library
PUT /api/v1/admin/sites/{site_code}/titles/{title_code}/publication
GET /api/v1/games/mines/config?title_code={title_code}
```

Regole:

- la libreria pubblica esclude sempre i master;
- una variante appare nel sito solo se `lobby_visibility=visible` e almeno una
  modalita' fra demo/real e' attiva;
- la pubblicazione demo e la pubblicazione real sono flag distinti; la UI
  minima puo' esporre azioni separate o una azione combinata demo+real;
- la pubblicazione sito e' separata dal publish della config: una variante puo'
  avere config live ma restare nascosta dalla lobby;
- il player Mines legge `title_code` dall'URL e usa quel Title per config,
  theme e launch token;
- la preview demo da backoffice apre il player Mines con `mode=demo` e
  `title_code` del master o della variante, senza pubblicare il master in lobby.

Fuori scope F7-D:

- CMS generale del sito;
- UI editoriale completa per pubblicazione sito/frontend: ordinamento visuale,
  card assets, descrizioni, stati demo/real avanzati, grouping e revisione UX
  della libreria;
- preview della bozza non pubblicata;
- immagini card gestite da CMS;
- lobby multi-engine avanzata;
- external adapter produzione.

## Cosa non sara' ancora possibile dopo F7-A

Dopo F7-A non sara' ancora possibile:

- creare nuovi Title vuoti da UI; e' possibile solo creare varianti duplicando
  il master Mines;
- creare nuovi engine da UI;
- gestire una lobby multi-engine avanzata o un CMS completo: la libreria player
  oggi espone solo varianti pubblicate con metadati leggeri;
- editare engine non-Mines;
- modificare payout, RTP, RNG o fairness;
- usare il backoffice come CMS completo del sito;
- salvare una libreria backend di skin nominate o creare skin persistenti come
  entita' autonome: i preset Tema attuali compilano solo la bozza token;
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
