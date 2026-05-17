Status: ACTIVE
Last meaningful update: 2026-05-17

# CasinoKing - Mines skin extended customization plan

## Stato

Piano operativo aggiornato dopo review CTO. Nessuna implementazione codice in
questo task.

Questo documento definisce l'evoluzione professionale della skin Mines per
Title/versione, oltre alla prima Fase 5 gia' implementata con theme tokens e
asset registry.

Decisioni hard recepite prima di SKIN-X1:

- V1 accetta solo immagini PNG/WebP; SVG escluso per rischio XSS persistente.
- La source of truth della skin e' `theme_tokens_json`, non
  `presentation_config.skin`.
- I controlli button sono enum/preset, non valori CSS liberi salvati in DB.
- Lo sfondo area gioco V1 si applica solo a `.mines-stage-board`.

## Fonti lette

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/THEME_SYSTEM_PLAN.md`
- `docs/ASSET_REGISTRY_PLAN.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`

File individuati ma non letti integralmente:

- documenti Word canonici in `docs/word/`
- allegati runtime Mines in `docs/runtime/`

Motivo: il task riguarda configurazione visuale, asset, tema e backoffice.
Non cambia matematica, payout runtime, RTP, RNG, fairness, wallet o ledger.

## Obiettivo

Permettere a ogni Title Mines di avere una skin visuale molto piu' ricca senza
toccare il core del gioco.

Richieste coperte:

- titolo in-game come testo oppure immagine;
- dimensioni raccomandate per immagine titolo;
- background configurabile per le celle face-down;
- background configurabile per la sola area gioco, non per il rail parametri;
- padding e forma dei pulsanti configurabili entro limiti sicuri;
- possibilita' di creare varianti belle e molto diverse tra loro;
- nessun impatto su RNG, payout, settlement, wallet, ledger, saldo o report.

## Regola di confine

Questa feature e' SKIN, non CORE.

```text
Consentito:
  testo, logo, colori, texture, sfondi, radius, padding, densita' controllata

Non consentito:
  modificare board, probabilita', RTP, payout, reveal, cashout, ledger, wallet
```

Se una richiesta di skin richiede di cambiare regole, moltiplicatori, stato
round o settlement, esce da questo piano e diventa un task Mines core dedicato.

## Decisioni principali

### 1. Titolo in-game: testo o immagine

Il titolo testuale resta la source of truth editoriale:

```text
title_locale_maps.locales_json[locale].copy["game.title"]
```

Regola:

- se `title_render_mode = "text"`, il gioco mostra `game.title`;
- se `title_render_mode = "image"`, il gioco mostra l'asset titolo;
- se l'immagine manca, non carica o viene cancellata, fallback obbligatorio a
  `game.title`;
- il titolo non deve mai diventare stringa vuota o immagine rotta.

Non si introduce una seconda source testuale parallela.

Asset raccomandato per title image:

| Proprieta' | Valore |
| --- | --- |
| Formato consigliato V1 | PNG trasparente o WebP |
| Dimensione sorgente consigliata | 720 x 180 px |
| Aspect ratio consigliato | 4:1 |
| Safe area | lasciare margine interno 48 px orizzontale e 24 px verticale |
| Display desktop indicativo | max 280 x 70 px |
| Display mobile indicativo | max 220 x 56 px |
| Peso massimo V1 | 150 KB |
| Rendering runtime | `object-fit: contain`, nessun crop/stretch |

Perche' 720 x 180:

- abbastanza grande per schermi retina;
- rapporto 4:1 naturale per wordmark/logo;
- si riduce bene su mobile;
- evita loghi troppo verticali che rompono header, board e payout chips.

Decisione sicurezza V1:

- SVG escluso.
- Non basta servire SVG come immagine: senza sanitizzazione forte lato upload e
  serving sandbox/CSP dedicati, SVG puo' diventare XSS persistente lato player.
- SVG entra solo in V2 con piano dedicato di sanitizzazione, serving sandbox e
  test di sicurezza.

### 2. Background celle face-down

La cella coperta puo' ricevere:

- colore/token;
- gradiente controllato;
- texture immagine;
- overlay leggero per contrasto.

Non deve cambiare:

- dimensione della cella;
- aspect ratio quadrato;
- hit target;
- logica reveal;
- safe/mine icon.

Asset raccomandato:

| Proprieta' | Valore |
| --- | --- |
| Formato consigliato V1 | PNG o WebP quadrato |
| Dimensione sorgente consigliata | 256 x 256 px |
| Aspect ratio | 1:1 obbligatorio |
| Peso massimo V1 | 256 KB |
| Uso | una sola fetch asset, applicazione via CSS background `cover` su ogni cella |

La texture deve essere abbastanza semplice da lasciare leggibile safe/mine,
focus, hover e stato disabled.

Regola performance:

- la texture e' un asset unico referenziato da CSS;
- non deve essere emessa come immagine per ogni cella;
- la board puo' avere 25+ celle, ma il browser deve scaricare il file una sola
  volta.

### 3. Background area gioco

Lo sfondo richiesto riguarda solo la zona visuale della board.

Target CSS V1 obbligatorio:

```text
article.board-shell.mines-stage-board
```

In pratica:

- applicare lo sfondo a `.mines-stage-board`;
- non applicarlo a `.mines-grid`;
- non applicarlo a `.mines-grid > .stack:last-child`;
- non applicarlo a `.mines-stage-card`;
- non applicarlo a `.mines-control-rail`.

Motivo: oggi il layout desktop ha un rail parametri separato
(`.mines-control-rail`) e una stack gioco che contiene sia header
(`.mines-stage-card`) sia board (`.mines-stage-board`). Attaccare lo sfondo alla
stack intera rischia di contaminare aree non previste o rendere il gioco
illeggibile.

Non riguarda:

- rail parametri;
- cassa/bet controls;
- footer saldo;
- modali;
- replay mani, che resta su skin base semplificata;
- lobby;
- site banner.

Asset raccomandato:

| Proprieta' | Valore |
| --- | --- |
| Formato consigliato V1 | PNG/WebP gia' ottimizzato |
| Dimensione sorgente consigliata | 1280 x 720 px |
| Aspect ratio consigliato | 16:9 |
| Peso massimo V1 | 400 KB |
| Focal point | centro, evitando dettagli critici sui bordi |
| Rendering runtime | Cover croppa, Contain preserva tutta l'immagine; nessuno stretch |

Regola professionale:

- lo sfondo deve essere scenografico ma non deve competere con la board;
- serve sempre un overlay/tint configurabile per garantire contrasto;
- su mobile lo sfondo puo' essere croppato, non deformato;
- se l'asset manca, fallback a token colore/gradiente.

Decisione performance V1:

- non si introduce una pipeline immagine automatica in SKIN-X1;
- il backend rifiuta `game_area_background` sopra 400 KB;
- l'operatore deve caricare un asset gia' ottimizzato;
- la pipeline professionale con derivati `@1x`/`@2x` WebP/JPG resta V2
  dedicata, non prerequisito della prima slice.

### 4. Pulsanti: padding e forma controllati

Il backoffice non deve esporre CSS libero.

Esporre solo preset enum persistiti:

| Controllo | Valori ammessi V1 |
| --- | --- |
| Button density | `compact`, `default`, `large` |
| Button radius | `square`, `soft`, `rounded` |
| Button border style | `flat`, `outlined`, `raised` |
| Button emphasis | `primary`, `secondary`, `danger`, `neutral` |

Regola di persistenza:

- il DB salva solo enum/preset;
- il frontend mappa i preset a valori CSS hardcoded;
- `button_emphasis` e' un enum che mappa solo token colore gia' validati; non
  accetta hex/rgb arbitrari;
- i token CSS `--ck-button-*` possono esistere solo come derivati runtime;
- il backoffice non puo' inviare `padding: 27px`, `border-radius: 999px` o
  valori arbitrari.

Limiti hard:

- altezza touch minima 44 px;
- nessun bottone pill estremo nel frame Mines;
- nessun padding negativo o arbitrario;
- nessuna modifica alla sequenza funzionale Bet / Collect;
- nessuna animazione che ritardi stato o click successivi.

Interpretazione di "sempre quadrata":

- i pulsanti possono essere piu' o meno morbidi;
- non devono diventare pill, blob o forme decorative che riducono leggibilita';
- le celle board restano sempre quadrate tramite `aspect-ratio: 1 / 1`.

## Modello dati concettuale

### Asset registry

Non usare data-URL e non committare asset dentro `assets/`.

Gli asset di prodotto entrano tramite asset registry.

Asset kind consigliati per questa fase:

| asset_kind | Uso | MIME V1 | Cap V1 |
| --- | --- | --- | --- |
| `title_logo` | logo/wordmark in-game alternativo al testo | PNG/WebP | 150 KB |
| `game_area_background` | sfondo della sola area gioco | PNG/WebP | 400 KB |
| `cell_face_down_background` | texture o sfondo della cella coperta | PNG/WebP | 256 KB |

Nota: lo schema attuale ha gia' kind generici come `logo` e `background`, ma
per questa estensione e' piu' sicuro usare nomi espliciti. Riutilizzare
`background` senza qualificatore rischia di confondere sfondo gioco, sfondo
site, lobby banner e futuri asset CMS.

SVG resta escluso per questi tre kind in V1, anche se altri kind legacy del
registry possono averlo accettato in passato.

Retrocompatibilita':

- i kind legacy `logo` e `background` restano leggibili in lettura per Title
  pre-esistenti;
- il nuovo editor SKIN-X3 scrive solo i kind espliciti V1;
- nessuna migration distruttiva cancella o riscrive asset legacy.

### Theme source of truth

Decisione architetturale: Opzione A.

Tutta la skin visuale vive in `title_configs.theme_tokens_json` e
`draft_theme_tokens_json`.

Non si introduce `presentation_config.skin` come seconda fonte persistente.

Motivo:

- oggi il Theme System gia' risolve `theme_tokens_json` per `title_code`;
- il public endpoint theme restituisce `tokens` e `assets`;
- mettere parte della skin in `presentation_config` e parte nel tema crea drift;
- `presentation_config` resta per configurazione runtime Mines, copy/rules,
  griglie e board assets legacy, non per nuove scelte visuali.

I token attuali `--ck-*` restano validi.

Nuovi token/valori derivati candidati:

| Token | Uso |
| --- | --- |
| `--ck-game-area-bg` | fallback colore/gradiente area gioco |
| `--ck-game-area-overlay` | overlay sopra background area gioco |
| `--ck-cell-face-bg` | fallback cella coperta |
| `--ck-cell-face-border` | bordo cella coperta |
| `--ck-button-padding-y` | derivato frontend da `button_density` |
| `--ck-button-padding-x` | derivato frontend da `button_density` |
| `--ck-button-radius` | derivato frontend da `button_radius` |
| `--ck-button-border-width` | derivato frontend da `button_style` |

Regola:

- i token colore/bordo/fallback restano valori validati come nel Theme System;
- i button token non sono campi DB liberi;
- il DB salva solo preset enum come `button_density`, `button_radius` e
  `button_style`;
- il frontend traduce gli enum in CSS variables finali.
- il resolver theme non deve passare oggetti annidati come `CSSProperties`:
  legge `skin`, valida enum/asset e produce solo CSS variables finali nel campo
  `tokens` pubblico; se serve al runtime un flag semantico, lo espone in un
  campo tipizzato separato, non dentro `style`.

### Shape concettuale in theme_tokens_json

Campi concettuali pubblicati per Title dentro `theme_tokens_json`:

```json
{
  "skin": {
    "title_render_mode": "text",
    "button_density": "default",
    "button_radius": "soft",
    "button_style": "raised",
    "button_emphasis": "primary",
    "game_area_background_fit": "cover",
    "game_area_background_position": "center"
  }
}
```

Regole:

- `title_render_mode` puo' essere solo `text` o `image`;
- `button_density`, `button_radius`, `button_style` e `button_emphasis` sono
  enum;
- valori assenti usano default compatibili con la skin corrente;
- player vede solo published;
- draft resta nel backoffice fino al publish;
- preview admin draft non viene risolta da questo piano: e' una decisione
  piattaforma cross-engine separata.

## Backoffice UX proposta

Collocazione: tab `Tema` o nuova sottosezione `Skin avanzata` nel detail Title.

Struttura consigliata:

1. `Titolo`
   - radio/segmented control: testo / immagine;
   - anteprima testo da `game.title`;
   - upload logo titolo;
   - fallback visibile quando manca immagine.

2. `Area gioco`
   - upload sfondo area gioco;
   - fit/position solo da valori ammessi;
   - overlay intensity controllata.

3. `Celle`
   - upload texture face-down;
   - fallback colore;
   - preview 5x5 statica con safe/mine simulati.

4. `Pulsanti`
   - density preset;
   - radius preset;
   - border style preset;
   - preview Bet/Collect non interattiva.

5. `Validazione`
   - warning/blocco contrasto con soglie WCAG definite;
   - warning asset mancanti;
   - warning mobile 375 px se titolo/logo troppo largo.

Scelta severa:

- niente editor CSS;
- niente campi "inserisci URL esterno";
- niente immagini banner site dentro questa tab;
- niente controlli che cambiano layout globale del gioco.

Soglie contrasto:

- testo normale: contrast ratio minimo 4.5:1;
- testo grande e componenti UI: contrast ratio minimo 3:1;
- calcolo sui token finali pubblicati, inclusi overlay e fallback;
- combinazioni sotto soglia non devono essere pubblicabili in SKIN-X3/X4.

Formula operativa V1:

- il contrast check si esegue sulla combinazione worst-case token colore +
  overlay opaco, non sui pixel dell'immagine di background;
- l'operatore resta responsabile di caricare immagini con focal point
  compatibile con la board;
- se serve garanzia hard sul testo sopra immagine, l'overlay V1 deve essere
  abbastanza opaco da rendere irrilevante l'immagine sottostante.

## Sequenza implementativa proposta

### SKIN-X0 - Audit e contratto finale

Obiettivo: evitare di implementare campi sbagliati.

Attivita':

1. verificare shape attuale di `theme_tokens_json`, `title_assets` e public
   config Mines;
2. confermare se aggiungere asset kind espliciti con migration;
3. fissare limiti peso per `title_logo`, `game_area_background`,
   `cell_face_down_background`;
4. fissare default per retrocompatibilita'.
5. audit effettivo del registry asset attuale:
   - quali MIME accetta oggi;
   - se SVG e' sanitizzato o solo servito;
   - quali audit log vengono scritti per upload/delete;
   - nessuna apertura SVG nei nuovi kind V1.
6. confermare nel codice il target runtime `.mines-stage-board` per
   `game_area_background`.

Output:

- checklist tecnica in `docs/MINES_SKIN_X0_AUDIT.md`;
- nessun cambio visibile al player.

### SKIN-X1 - Backend asset/theme contract

Obiettivo: rendere pubblicabili i nuovi asset/tokens per Title.

Attivita':

1. migration asset kind espliciti;
2. validazioni MIME/peso per kind: PNG/WebP only, SVG escluso;
3. estendere `theme_tokens_json`/`draft_theme_tokens_json` come unica source
   della skin;
4. aggiornare il validator theme per accettare lo schema strutturato `skin`
   senza accettare CSS arbitrario;
5. validazione enum/preset nuova allowlist;
6. test API asset/theme/config.
7. retrocompatibilita' asset legacy: `logo` e `background` restano leggibili in
   lettura, mentre il nuovo editor scrive solo `title_logo`,
   `game_area_background` e `cell_face_down_background`.

Accettazione:

- asset uploadabili solo da backoffice autorizzato;
- valori invalidi rifiutati;
- fallback published completo per Title senza skin avanzata.
- publish skin/theme scrive evento operativo in `admin_audit_log` con pattern
  equivalente a `theme_publish` / `title_config_publish`;
- upload/delete asset restano tracciati dal registry asset.

### SKIN-X2 - Runtime frontend

Obiettivo: consumare la skin senza cambiare il game core.

Attivita':

1. title text/image con fallback;
2. background area gioco limitato a `.mines-stage-board`;
3. texture cella face-down senza cambiare griglia;
4. button density/radius/style controllati;
5. nessun layout shift durante round, reveal, cashout o replay.

Accettazione:

- Mines resta giocabile con default;
- skin custom cambia solo presentazione;
- viewport 375 px senza overlap;
- board e rail parametri non si deformano.
- lo sfondo non appare su `.mines-control-rail`, `.mines-stage-card`, modali,
  replay o lobby.
- il replay mani continua a usare icone default mina/diamante e non eredita
  asset skin del Title.

### SKIN-X3 - Backoffice editor

Obiettivo: rendere la skin gestibile da operatore senza rischi.

Attivita':

1. UI guidata nella tab Tema/Skin avanzata;
2. upload via asset registry;
3. preview statica locale;
4. save draft e publish coerenti con pattern Title;
5. audit log obbligatorio per upload/delete/publish;
6. blocco publish se contrast ratio finale non rispetta 4.5:1 per testo
   normale e 3:1 per componenti UI/testo grande.

Accettazione:

- operatore non deve conoscere CSS;
- non puo' salvare combinazioni fuori range;
- master resta read-only se la regola corrente lo impone.

### SKIN-X4 - QA e visual smoke

Obiettivo: chiudere il rischio di skin belle ma rotte.

Checklist minima:

- desktop e mobile 375 px;
- titolo testo lungo;
- titolo immagine mancante;
- background area scuro/chiaro;
- texture cella molto contrastata;
- pulsanti compact/large;
- Title senza blocco `skin` in `theme_tokens_json` renderizza identico a oggi:
  stesso layout, stessi colori, stessi bottoni; smoke specifico su
  `mines_classic` master;
- safe/mine icon ancora leggibili;
- modal rules/replay non contaminata dallo sfondo area gioco;
- nessun cambio a payload start/reveal/cashout;
- nessun test wallet/ledger da aggiornare perche' il core non cambia.

## Criteri di accettazione

La feature e' accettabile solo se:

- ogni customizzazione e' per `title_code`;
- player vede solo published;
- asset passano dal registry;
- nessun asset raw viene committato;
- nuovi asset skin V1 accettano solo PNG/WebP;
- SVG resta fuori dalla V1;
- title text resta `game.title`;
- title image ha fallback testuale;
- game area background si applica solo a `.mines-stage-board` e non tocca rail
  parametri;
- board cells restano quadrate;
- button controls sono preset/allowlist, non CSS libero;
- button preset sono enum salvati in theme, non valori padding/radius liberi;
- skin visuale vive in `theme_tokens_json`, non in un secondo
  `presentation_config.skin`;
- publish skin/theme e upload/delete asset sono tracciati in
  `admin_audit_log`;
- contrast ratio finale rispetta WCAG: 4.5:1 testo normale, 3:1 componenti UI
  e testo grande;
- skin non cambia RNG, payout, RTP, wallet, ledger o settlement;
- backoffice impedisce combinazioni manifestamente rotte.

## Fuori scope

- banner homepage/site media;
- mockup sito;
- suoni Mines;
- effetti visuali nuovi;
- replay mani;
- nuove meccaniche Mines;
- nuovo engine di gioco;
- marketplace skin;
- upload da URL esterni;
- CSS custom libero da backoffice;
- provider esterni o real money.

## Rischi e mitigazioni

| Rischio | Mitigazione |
| --- | --- |
| Skin troppo libera rompe layout mobile | preset, clamp e smoke 375 px obbligatorio |
| Asset ambigui fra gioco e sito | asset kind espliciti, niente riuso di banner/site assets |
| SVG come XSS persistente | SVG escluso dalla V1; V2 solo con sanitizzazione e serving sandbox |
| Logo immagine sostituisce source testuale | fallback obbligatorio a `game.title` |
| Texture cella rende invisibili stati | preview 5x5 e blocco contrasto sotto soglia |
| Background area disturba board | overlay/tint e scope solo stage visuale |
| Backoffice diventa editor CSS | controlli guidati, nessun campo CSS arbitrario |
| Doppia source fra theme e presentation_config | scelta A: skin persistita in `theme_tokens_json` |

## Decisioni chiuse prima del codice

1. Usare i kind espliciti `title_logo`, `game_area_background`,
   `cell_face_down_background` con migration dedicata.
2. V1 accetta solo PNG/WebP. SVG escluso.
3. Cap V1:
   - `title_logo`: 150 KB;
   - `game_area_background`: 400 KB;
   - `cell_face_down_background`: 256 KB.
4. Skin visuale persistita in `theme_tokens_json` / `draft_theme_tokens_json`;
   non creare `presentation_config.skin`.
5. Button styling persistito come enum/preset; CSS variables finali derivate
   dal frontend.
6. `game_area_background` applicato solo a `.mines-stage-board`.
7. UI collocata dentro `Tema`, eventualmente come sotto-sezione `Skin avanzata`.

## Follow-up separato

- Preview admin draft cross-engine: non e' una decisione skin. Va affrontata in
  un piano piattaforma dedicato quando servira' una preview draft non published
  per tutti gli engine.
- Pipeline immagini `@1x`/`@2x` WebP/JPG: resta V2 dedicata. In V1 il backend
  rifiuta asset non ottimizzati oltre cap.

## Relazione con piani esistenti

- `docs/THEME_SYSTEM_PLAN.md`: resta il piano base per token runtime e diventa
  la source persistente della skin estesa tramite `theme_tokens_json`.
- `docs/ASSET_REGISTRY_PLAN.md`: resta la regola per upload, storage e URL
  versionati; SKIN-X1 dovra' aggiungere i tre nuovi asset kind e la regola
  PNG/WebP-only.
- `docs/MINES_IN_GAME_TITLE_PLAN.md`: resta la source del titolo testuale
  `game.title`; `title_render_mode=image` cambia solo il rendering, non la
  source editoriale.
- `docs/MINES_SOUND_ASSETS_PLAN.md`: separato; gli audio non entrano in questo
  piano.
- `docs/MINES_VISUAL_EFFECTS_PLAN.md`: separato; animazioni/effetti non entrano
  in questa fase.

## Aggiornamenti documentali richiesti quando parte SKIN-X1

- `docs/ARCHITECTURE_ATLAS_MINES.md`: estendere `MINES_SKIN_01010` o dettagliare
  il nuovo mapping file/responsabilita'.
- `docs/ASSET_REGISTRY_PLAN.md`: aggiungere `title_logo`,
  `game_area_background`, `cell_face_down_background`, MIME PNG/WebP e cap V1.
- `docs/THEME_SYSTEM_PLAN.md`: dichiarare la convergenza su
  `theme_tokens_json` e i preset enum non-CSS-libero.
- `docs/README.md`: aggiornare indice/stato solo se SKIN-X1 diventa cantiere
  attivo.
- `docs/MINES_IN_GAME_TITLE_PLAN.md`: aggiungere nota che il render mode
  text/image non sostituisce `game.title`.
