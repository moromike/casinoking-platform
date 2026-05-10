# CasinoKing - Mines skin extended customization plan

## Stato

Piano operativo. Nessuna implementazione codice in questo task.

Questo documento definisce l'evoluzione professionale della skin Mines per
Title/versione, oltre alla prima Fase 5 gia' implementata con theme tokens e
asset registry.

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
| Formato consigliato | PNG trasparente o SVG servito come immagine |
| Dimensione sorgente consigliata | 720 x 180 px |
| Aspect ratio consigliato | 4:1 |
| Safe area | lasciare margine interno 48 px orizzontale e 24 px verticale |
| Display desktop indicativo | max 280 x 70 px |
| Display mobile indicativo | max 220 x 56 px |
| Peso massimo V1 | 512 KB |

Perche' 720 x 180:

- abbastanza grande per schermi retina;
- rapporto 4:1 naturale per wordmark/logo;
- si riduce bene su mobile;
- evita loghi troppo verticali che rompono header, board e payout chips.

SVG e' ammesso solo se resta asset immagine servito dal registry, mai HTML
inline editoriale. Prima del codice va verificato se il registry oggi sanitizza
davvero SVG; se non lo fa, per questa fase la scelta piu' sicura e' limitare
il logo a PNG oppure aggiungere sanitizzazione esplicita.

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
| Formato consigliato | PNG quadrato o SVG semplice |
| Dimensione sorgente consigliata | 512 x 512 px |
| Aspect ratio | 1:1 obbligatorio |
| Peso massimo V1 | 512 KB |
| Uso | `background-size: cover` o pattern controllato |

La texture deve essere abbastanza semplice da lasciare leggibile safe/mine,
focus, hover e stato disabled.

### 3. Background area gioco

Lo sfondo richiesto riguarda solo la zona visiva del gioco, cioe' il pannello
che contiene board/scena. Non riguarda:

- rail parametri;
- cassa/bet controls;
- footer saldo;
- modali;
- lobby;
- site banner.

Asset raccomandato:

| Proprieta' | Valore |
| --- | --- |
| Formato consigliato | PNG ottimizzato |
| Dimensione sorgente consigliata | 1600 x 900 px |
| Aspect ratio consigliato | 16:9 |
| Peso massimo V1 | 1 MB |
| Focal point | centro, evitando dettagli critici sui bordi |

Regola professionale:

- lo sfondo deve essere scenografico ma non deve competere con la board;
- serve sempre un overlay/tint configurabile per garantire contrasto;
- su mobile lo sfondo puo' essere croppato, non deformato;
- se l'asset manca, fallback a token colore/gradiente.

### 4. Pulsanti: padding e forma controllati

Il backoffice non deve esporre CSS libero.

Esporre invece preset e token validati:

| Controllo | Valori ammessi V1 |
| --- | --- |
| Button density | `compact`, `default`, `large` |
| Button radius | `square`, `soft`, `rounded` |
| Button border style | `flat`, `outlined`, `raised` |
| Button emphasis | token colore gia' validati |

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

| asset_kind | Uso |
| --- | --- |
| `title_logo` | logo/wordmark in-game alternativo al testo |
| `game_area_background` | sfondo della sola area gioco |
| `cell_face_down_background` | texture o sfondo della cella coperta |

Nota: lo schema attuale ha gia' kind generici come `logo` e `background`, ma
per questa estensione e' piu' sicuro usare nomi espliciti. Riutilizzare
`background` senza qualificatore rischia di confondere sfondo gioco, sfondo
site, lobby banner e futuri asset CMS.

### Theme tokens

I token attuali `--ck-*` restano validi.

Nuovi token candidati:

| Token | Uso |
| --- | --- |
| `--ck-game-area-bg` | fallback colore/gradiente area gioco |
| `--ck-game-area-overlay` | overlay sopra background area gioco |
| `--ck-cell-face-bg` | fallback cella coperta |
| `--ck-cell-face-border` | bordo cella coperta |
| `--ck-button-padding-y` | padding verticale controllato |
| `--ck-button-padding-x` | padding orizzontale controllato |
| `--ck-button-radius` | radius bottoni runtime |
| `--ck-button-border-width` | bordo bottoni runtime |

Questi token non devono essere campi testuali CSS arbitrari senza validazione.
Il service deve normalizzare e rifiutare valori fuori range.

### Presentation config

Campi concettuali pubblicati per Title:

```json
{
  "skin": {
    "title_render_mode": "text",
    "button_density": "default",
    "button_radius": "soft",
    "button_style": "raised",
    "game_area_background_fit": "cover",
    "game_area_background_position": "center"
  }
}
```

Regole:

- `title_render_mode` puo' essere solo `text` o `image`;
- valori assenti usano default compatibili con la skin corrente;
- player vede solo published;
- draft resta nel backoffice fino al publish;
- preview admin usa published, salvo futuro piano preview draft dedicato.

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
   - warning contrasto;
   - warning asset mancanti;
   - warning mobile 375 px se titolo/logo troppo largo.

Scelta severa:

- niente editor CSS;
- niente campi "inserisci URL esterno";
- niente immagini banner site dentro questa tab;
- niente controlli che cambiano layout globale del gioco.

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

Output:

- checklist tecnica;
- nessun cambio visibile al player.

### SKIN-X1 - Backend asset/theme contract

Obiettivo: rendere pubblicabili i nuovi asset/tokens per Title.

Attivita':

1. migration asset kind espliciti;
2. validazioni MIME/peso per kind;
3. validazione token nuova allowlist;
4. campi presentation `skin` in draft/published config;
5. test API asset/theme/config.

Accettazione:

- asset uploadabili solo da backoffice autorizzato;
- valori invalidi rifiutati;
- fallback published completo per Title senza skin avanzata.

### SKIN-X2 - Runtime frontend

Obiettivo: consumare la skin senza cambiare il game core.

Attivita':

1. title text/image con fallback;
2. background area gioco limitato allo stage visuale;
3. texture cella face-down senza cambiare griglia;
4. button density/radius/style controllati;
5. nessun layout shift durante round, reveal, cashout o replay.

Accettazione:

- Mines resta giocabile con default;
- skin custom cambia solo presentazione;
- viewport 375 px senza overlap;
- board e rail parametri non si deformano.

### SKIN-X3 - Backoffice editor

Obiettivo: rendere la skin gestibile da operatore senza rischi.

Attivita':

1. UI guidata nella tab Tema/Skin avanzata;
2. upload via asset registry;
3. preview statica locale;
4. save draft e publish coerenti con pattern Title;
5. audit log per upload/delete/publish se gia' previsto dal registry/theme.

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
- title text resta `game.title`;
- title image ha fallback testuale;
- game area background non tocca rail parametri;
- board cells restano quadrate;
- button controls sono preset/allowlist, non CSS libero;
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
| Logo immagine sostituisce source testuale | fallback obbligatorio a `game.title` |
| Texture cella rende invisibili stati | preview 5x5 e contrast warning |
| Background area disturba board | overlay/tint e scope solo stage visuale |
| Backoffice diventa editor CSS | controlli guidati, nessun campo CSS arbitrario |

## Decisioni aperte

Da confermare prima del codice:

1. Usare i kind espliciti `title_logo`, `game_area_background`,
   `cell_face_down_background` con migration dedicata.
2. Accettare PNG e SVG in V1; valutare WebP solo se il registry viene esteso.
3. Confermare peso massimo: 512 KB logo/cella, 1 MB background area.
4. Collocare la UI dentro `Tema` o come sotto-tab `Skin avanzata`.
5. Confermare se preview admin continua a usare published o se serve una futura
   preview draft separata.

## Relazione con piani esistenti

- `docs/THEME_SYSTEM_PLAN.md`: resta il piano base per token runtime.
- `docs/ASSET_REGISTRY_PLAN.md`: resta la regola per upload, storage e URL
  versionati.
- `docs/MINES_IN_GAME_TITLE_PLAN.md`: resta la source del titolo testuale
  `game.title`.
- `docs/MINES_SOUND_ASSETS_PLAN.md`: separato; gli audio non entrano in questo
  piano.
- `docs/MINES_VISUAL_EFFECTS_PLAN.md`: separato; animazioni/effetti non entrano
  in questa fase.
