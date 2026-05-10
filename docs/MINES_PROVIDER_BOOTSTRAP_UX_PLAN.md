# Mines Provider Bootstrap UX Plan

Documento di progetto per portare Mines verso un'esperienza piu' vicina a un
gioco casino professionale: intro provider, caricamento, guida iniziale,
orologio, controlli audio e reveal completo al cashout.

## Stato

- Tipo: piano operativo Mines frontend/runtime UX.
- Stato: proposta tecnica pronta per implementazione incrementale; BOOT-1
  cashout reveal implementato.
- Ambito: mini-epic da dividere in Game Boot Shell e Runtime Polish.
- Non sostituisce: `docs/MINES_SOUND_ASSETS_PLAN.md`,
  `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`,
  `docs/MINES_REPLAY_VIEWER_PLAN.md`.
- Fonti metodologiche: `docs/AI_CRITICAL_JUDGMENT_RULES.md` applicato per
  non accettare scorciatoie su asset, audio e configurazione runtime.

## Contesto

I provider riconoscibili mostrano spesso una sequenza di bootstrap prima del
gioco: logo animato, caricamento, messaggio breve e schermata di orientamento.
Il riferimento visivo indicato e' Hacksaw, ma la realizzazione CasinoKing deve
essere ispirata al pattern di qualita', non copiata nel layout, nel logo, nei
tempi, nei colori o nella grafica.

Il provider proprietario V1 si chiama:

```text
moromike lab
```

Il valore del cantiere non e' estetico soltanto:

- rende chiaro chi produce il gioco;
- nasconde in modo elegante il tempo reale di bootstrap;
- prepara il player alle regole minime prima del primo click;
- crea un layer comune riusabile quando arriveranno altri giochi proprietari.

## Confini Non Negoziabili

Questo piano non tocca:

- RNG;
- payout;
- RTP;
- reveal logic server-side;
- wallet;
- ledger;
- settlement;
- fairness.

Tutto cio' che viene aggiunto e' presentazionale o di shell runtime. Il backend
continua a decidere outcome, board e chiusura round.

## Naming Proposto

| Nome | Significato |
| --- | --- |
| Provider Bootstrap | Sequenza iniziale comune ai giochi di un provider. |
| Game Boot Shell | Layer frontend che carica config, asset e mostra intro/loading prima del gioco. |
| How To Play Gate | Schermata iniziale con tre riquadri di orientamento. |
| Runtime Tools | Piccoli strumenti sempre disponibili nel gioco: info, replay, clock, audio. |

Questi nomi evitano di confondere la feature con la skin del Title. La skin
personalizza il gioco; il bootstrap identifica il provider e gestisce il lancio.

## Decisioni Chiuse

1. Il video/logo provider non va salvato in cookie.
2. Il browser deve cacheare l'asset tramite HTTP cache e URL versionato.
3. Cookie/localStorage/sessionStorage possono salvare solo preferenze o policy
   di visualizzazione, mai il file media.
4. V1 usa asset provider statici versionati, non `title_assets`.
5. Se in futuro avremo piu' provider o cambio da backoffice, introdurremo un
   registro `provider_assets`; non si forza ora dentro il registro Title.
6. La schermata How To Play e' contenuto di gioco/Title, non asset provider.
7. L'orologio e' configurazione runtime/compliance del Title, non skin.
8. I controlli audio utente sono locali al browser e non cambiano il Title.
9. Al cashout riuscito il round e' chiuso: mostrare le mine e' corretto e non
   viola sicurezza.
10. La Game Boot Shell non sara' un puro overlay cosmetico: si procede con un
    refactor staged che separa bootstrap/ready state da gameplay. Il wrapper
    veloce resta fallback solo per emergenza, non target tecnico.
11. Le preferenze audio sono globali del player/browser, non del provider.
12. Il clock eredita di default la configurazione dal Site; override per Title
    solo se esiste un requisito esplicito.
13. La progress bar di caricamento non deve essere baked nel video: la disegna
    il frontend per riflettere gli stati reali di boot.

## Provider Intro Asset Strategy

### V1 Consigliata

Usare asset statici versionati sotto frontend:

```text
frontend/public/brand/moromike-lab/
  moromike-lab-intro.v1.<hash>.mp4
  moromike-lab-intro.v1.<hash>.webm      # futuro/ottimizzazione
  moromike-lab-poster.v1.<hash>.png
  moromike-lab-logo-light.v1.<hash>.png
```

Motivo:

- abbiamo un solo provider proprietario;
- non serve backoffice provider ora;
- non sporca `title_assets`;
- non apre una media library generica;
- e' facile da servire con cache lunga.

Regola importante:

- la cartella locale `assets/` resta area di lavoro non versionata;
- solo gli asset finali, ottimizzati e realmente usati dal runtime entrano nel
  percorso pubblico o in un registry dedicato futuro.

### Cache

Asset media:

- serviti con filename versionato o hash;
- `Cache-Control: public, max-age=31536000, immutable` quando possibile;
- se cambia il file, cambia il filename/versione.

Policy di visualizzazione:

- `sessionStorage`: intro vista in questa sessione browser;
- `localStorage`: preferenze utente, per esempio audio mute/volume;
- niente cookie per media o preferenze non necessarie al server.

Comportamento proposto:

- V1 di validazione locale: intro completa da 8 secondi a ogni mount runtime,
  come richiesto da Michele per provare l'asset ricevuto;
- V2: primo launch della sessione con intro completa, launch successivi nella
  stessa sessione con intro breve o skip animazione, ma mantenendo una micro
  schermata di loading se il gioco non e' ancora pronto;
- se `prefers-reduced-motion` e' attivo: poster statico + fade, niente video.

### Budget Asset

| Asset | Formato | Target |
| --- | --- | --- |
| Intro desktop | WebM VP9 + MP4 H.264 fallback | 2.0-3.0 s, max 1.5 MB, target 600-900 KB |
| Intro mobile | opzionale WebM/MP4 verticale | max 1.0 MB, target 400-700 KB |
| Poster | PNG/WebP | max 150 KB |
| Logo statico | PNG/WebP trasparente | max 120 KB |

V1 puo' partire con un solo video 16:9 e `object-fit: cover`, purche' il logo
resti in safe area centrale su mobile. Se il risultato mobile non e' buono,
aggiungere variante verticale.

Asset V1 ricevuto/implementato per validazione locale: MP4 H.264 1280x720,
8 secondi, circa 1.68 MB. Si accetta temporaneamente la durata da 8 secondi per
testare l'identita' provider completa; il target produzione resta piu' corto o
ottimizzato con WebM/variante mobile.

Costante runtime:

```ts
const PROVIDER_INTRO_BASE = "/brand/moromike-lab";
```

La stringa non va dispersa nei componenti. Quando arrivera' un eventuale
`provider_assets` registry V2, si cambia un punto solo.

Prima di committare asset AI-generated nel path pubblico serve una review umana
IP-sanity: niente somiglianza evidente con Hacksaw o altri provider, niente
loghi, composizioni, font o animazioni riconoscibili di terzi.

La progress bar non deve essere esportata nel video. L'asset deve lasciare area
libera sotto il logo; la barra viene renderizzata dal frontend sopra intro e
poster.

## Game Boot Shell

### Scelta Architetturale

Decisione: **refactor staged**, non wrapper puro.

Motivo:

- oggi molte responsabilita' di bootstrap vivono dentro `mines-standalone.tsx`;
- un overlay esterno non conoscerebbe davvero token, config, theme e ready state;
- una progress bar non deve diventare scenografia scollegata dal caricamento.

Target:

```text
MinesBootShell
  -> legge route params e provider intro policy
  -> orchestra launch/config/theme ready state
  -> mostra Provider Bootstrap / fallback / errore launch
  -> consegna props pronte a MinesGameplay

MinesGameplay
  -> board, bet/collect, replay, runtime tools
```

Esecuzione conservativa:

- prima estrarre solo readiness/bootstrap state;
- poi spostare componenti visuali;
- evitare refactor massivo non verificabile in una sola passata.

Responsabilita':

1. montare la route `/mines`;
2. leggere `title_code`, `mode`, `preview_token`;
3. preparare launch token/demo token se serve;
4. caricare runtime config, theme e asset minimi;
5. mostrare Provider Bootstrap mentre il gioco diventa pronto;
6. mostrare How To Play Gate quando applicabile;
7. consegnare il controllo al gioco senza layout shift.

Progress bar:

- non deve fingere precisione al byte;
- rappresenta stati reali di bootstrap;
- arriva al 100% solo quando il gioco puo' renderizzare.

Stati V1:

| Percentuale | Stato |
| --- | --- |
| 0-15 | Shell montata e parametri URL letti |
| 15-40 | Token/identita' demo o real risolta |
| 40-65 | Config runtime e theme caricati |
| 65-85 | Asset critici pronti o fallback deciso |
| 85-100 | Board pronta e transizione verso gioco |

Regola UX:

- durata V1 validazione locale: 8000 ms, senza taglio del video;
- target produzione futuro: durata minima intro completa 1200 ms, durata
  massima hard 4500 ms salvo decisione prodotto esplicita;
- se un asset intro fallisce, usare poster/logo e continuare;
- se config/launch fallisce, mostrare errore di launch, non restare su loading.

## Specifiche Per AI Creativa Esterna

### Direzione Artistica

Brand:

```text
moromike lab
```

Mood:

- black premium;
- laboratory / creator studio;
- digitale, nitido, non horror;
- micro glitch controllato, non caotico;
- luce fredda con accenti verde/acqua o bianco;
- logo leggibile anche su mobile.

Vincoli:

- non copiare Hacksaw;
- non usare simboli, font o composizioni riconoscibili di provider esistenti;
- niente personaggi;
- niente icone casino generiche come fiches giganti o slot machine;
- niente audio nel video V1.

### Prompt Logo Statico

```text
Create a premium black-background game provider logo for "moromike lab".
Style: minimal digital laboratory, precise, sharp, high-end casino game studio,
subtle cyan/green highlights, clean lowercase wordmark, no mascot, no slot
machine symbols, no copied provider style. The logo must be readable at small
mobile size. Deliver transparent PNG and black-background preview. Safe area:
center 60% width and 40% height.
```

### Prompt Intro Animata

```text
Create a 2.5 second animated intro for a fictional casino game provider named
"moromike lab". Black premium background, centered wordmark, subtle laboratory
scan line, controlled micro-glitch, soft cyan/green light pulse, ending on a
clean readable static logo. Add a thin loading/progress line below the logo
only as an empty reserved space: do not animate a real progress bar inside the
video, because the application will render loading progress separately. No
sound. Do not imitate or copy Hacksaw, Pragmatic, Evolution, Nolimit City or
any existing provider. The animation must work as a game loading splash and
remain readable on mobile. Export 1920x1080 WebM and MP4, plus a final-frame
PNG poster.
```

### Prompt Mobile Check

```text
Reframe the same "moromike lab" intro for mobile portrait. Keep the logo inside
the central safe area, avoid cropped text, leave reserved empty space below the
logo for an app-rendered progress bar, preserve black premium laboratory style,
no sound, no existing provider visual identity.
```

## How To Play Gate

Obiettivo:

Mostrare prima del gioco tre riquadri chiari che spiegano il ciclo Mines senza
trasformarli in manuale.

Posizione:

- dopo Provider Bootstrap;
- prima del primo round interattivo;
- sempre accessibile anche dopo tramite Game Info/Regole.

Policy:

- primo launch per Title/sessione: mostrato;
- dopo click "Gioca" entra nel gioco;
- in V1 non serve "non mostrare piu'" permanente;
- V2: aggiungere CTA "Non mostrare piu'" con localStorage per Title e versione
  copy:

```text
ck.howToPlay.<title_code>.dismissed = true
```

Default: mostrato. La V2 non deve usare cookie.

Tre card proposte:

| Card | Titolo | Messaggio |
| --- | --- | --- |
| 1 | Scegli la puntata | Imposta puntata, griglia e numero di mine prima di iniziare. |
| 2 | Trova i diamanti | Ogni cella sicura aumenta la vincita potenziale. |
| 3 | Incassa in tempo | Puoi incassare dopo almeno un diamante. Se trovi una mina, perdi la puntata. |

Varianti copy:

- la copy deve entrare nel sistema i18n/copy Mines, non hardcoded in modo
  permanente;
- se mancano copy pubblicate, usare default locali nel bundle;
- le card non modificano regole gioco, sono solo onboarding.

UI:

- full-screen overlay sopra sfondo gioco sfocato/scuro;
- 3 riquadri orizzontali desktop, stack mobile;
- icone semplici: bet/chip, diamond, collect/shield;
- CTA unica: "Gioca" / "Play";
- link secondario: "Regole" apre la modal esistente.

## Clock Runtime

L'orologio deve essere piccolo, stabile e leggibile. Non deve competere con
saldo, puntata o board.

Posizione consigliata:

- utility cluster alto, vicino a Info/Replay e audio;
- a destra dell'icona info se lo spazio lo permette;
- su mobile: nella stessa riga strumenti, testo tabular 11-12px.

Formato:

```text
HH:mm
```

Sempre 24h, zero-padded.

Configurazione:

Il clock vive di default nella configurazione Site perche' l'ora e' di solito
giurisdizionale. Il Title puo' solo fare override esplicito se un requisito
futuro lo giustifica.

```json
{
  "site_runtime_tools": {
    "clock": {
      "enabled": true,
      "timezone": "Europe/Rome",
      "label": "Rome",
      "format": "HH:mm"
    }
  }
}
```

Decisione timezone:

- usare timezone IANA, per esempio `Europe/Rome`, `Europe/Paris`, `UTC`;
- evitare `UTC+1` come configurazione primaria, perche' non gestisce ora legale;
- se serve fixed offset in un mercato futuro, va aggiunta allowlist dedicata.

Rendering:

- `Intl.DateTimeFormat` client-side con timezone configurata;
- update al cambio minuto, non ogni secondo;
- `font-variant-numeric: tabular-nums`;
- se timezone non valida non deve succedere in publish; a runtime fallback UTC e
  warning tecnico.

Nota compliance:

- V1 mostra ora configurata usando clock del browser;
- se un mercato richiede ora autorevole certificata, V2 sincronizza offset con
  server o endpoint time dedicato. Non fingere compliance dove serve server time.
- il clock V1 e' solo display informativo: non puo' essere usato per session
  timer, responsible gambling limits, cooldown o qualunque feature che richieda
  tempo non manipolabile dal client.

## Audio Runtime Controls

Stato attuale:

I suoni Mines non sono implementati nel runtime. Non e' un problema di volume:
non esiste ancora hook audio che carica e riproduce gli asset.

V1 controlli:

- un solo bottone effetti nella utility bar;
- click apre popover compatto;
- toggle effetti on/off;
- slider volume effetti 0-100;
- preview/test opzionale se asset esiste;
- persistenza in localStorage.

Non mostrare un bottone musica finto in V1. La musica di sottofondo resta
preparata concettualmente, ma non visibile finche' non esiste un asset/runtime
`music_loop`.

Storage preferenze:

```text
ck.audio.effectsMuted = "true|false"
ck.audio.effectsVolume = "0.00..1.00"
```

Default:

- effetti attivi;
- volume 0.45;
- se browser blocca audio finche' non c'e' interazione, il primo click player
  sblocca il contesto audio senza bloccare il gioco.

Integrazione con `docs/MINES_SOUND_ASSETS_PLAN.md`:

- `audio_safe_reveal`: reveal safe;
- `audio_mine_hit`: reveal mine/loss;
- `audio_collect`: cashout riuscito;
- `audio_win`: win automatico o celebrazione finale;
- nessun fallback bundled V1: se manca asset, silenzio.

## Cashout Reveal Mine Positions

Comportamento desiderato:

Quando il player clicca "Incassa" e il cashout riesce, la board mostra subito le
posizioni delle mine, mantenendo visibili i diamanti gia' rivelati.

Motivo:

- il round e' chiuso;
- il player vede la fotografia finale della mano;
- l'esperienza e' piu' leggibile e coerente con i provider professionali.

Regola di sicurezza:

- round active: non esporre mine al frontend;
- round closed per loss/cashout/auto-win: le mine possono essere esposte;
- il frontend visualizza solo quello che arriva dal backend.

Implementation note:

- estendere `POST /games/mines/cashout` per restituire `mine_positions` dopo la
  chiusura;
- demo e real devono comportarsi uguale;
- risposta idempotente dello stesso cashout deve restituire le stesse mine;
- frontend: dopo cashout riuscito impostare `revealedMinePositions` invece di
  svuotarle.

## Sequenza Di Esecuzione Consigliata

### BOOT-1 Gia' Implementato

| Step | Cosa | Stato |
| --- | --- | --- |
| BOOT-0 | Contratto + atlas/README | Fatto |
| BOOT-1 | Cashout reveal mines | Fatto |

### Epic A - Game Boot Shell

| Step | Cosa | Perche' |
| --- | --- | --- |
| BOOT-2A | Refactor staged `MinesBootShell` readiness/config | Da fare: evita overlay finto e riduce debito in `mines-standalone.tsx`. |
| BOOT-2B | Intro provider statico/video + fallback | Implementato V1 come overlay bootstrap isolato con MP4 8s, poster fallback, progress bar frontend e readiness runtime. |
| BOOT-2C | Review mobile/reduced-motion/IP-sanity | Parziale: reduced-motion gestito con poster; restano review mobile reale e IP-sanity umana finale. |

### Epic B - Runtime Polish

| Step | Cosa | Perche' |
| --- | --- | --- |
| BOOT-3 | How To Play Gate con copy default/i18n | Qualita' prodotto prima del primo round. |
| BOOT-4 | Clock runtime ereditato da Site, override Title raro | Requisito mercato e utility discreta. |
| BOOT-5 | Audio controls + hook + asset registry audio | Completa il piano audio gia' esistente. |
| BOOT-6 | Backoffice minimo per clock/copy gate | Solo dopo runtime stabile. |

Suoni completi richiedono anche il backend asset registry del piano audio.
Quindi BOOT-5 dipende da `MINES_SOUND_ASSETS_PLAN.md` lato backend, oppure puo'
partire con hook silenzioso e controlli disabilitati, ma non avrebbe valore
player finche' non carichiamo asset.

## Verifiche Minime

Cashout reveal:

- real: start, reveal safe, cashout, board mostra mine;
- demo: start, reveal safe, cashout, board mostra mine;
- active round: nessun endpoint player espone mine;
- idempotency cashout: risposta replay include stesse mine.

Bootstrap:

- desktop e mobile 375px;
- slow network simulato;
- asset intro mancante o fallito;
- `prefers-reduced-motion`;
- refresh diretto con `title_code`;
- preview admin token.

Clock:

- `Europe/Rome`;
- `UTC`;
- label lunga troncata senza layout shift;
- cambio minuto senza reflow della board.

Audio:

- browser fresh profile;
- primo click sblocca audio;
- mute persiste;
- volume persiste;
- assenza asset non genera errori visibili.

## Documentazione Da Aggiornare Quando Si Implementa

- `docs/ARCHITECTURE_ATLAS_MINES.md`: separare Boot Shell e Runtime Tools quando
  parte il codice BOOT-2/3/4/5.
- `docs/MINES_SOUND_ASSETS_PLAN.md`: controlli volume effetti e musica futura.
- documento Site config / atlas platform: se si aggiunge `site_runtime_tools.clock`.
- `docs/TITLE_CONFIG_PLAN.md`: solo se si aggiunge override Title per clock.
- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`: se le card entrano nella
  locale map.
- `docs/README.md`: indice operativo.

## Decisioni Aperte Dopo BOOT-2B V1

1. Confermare se `moromike lab` e' brand pubblico definitivo, lowercase, oppure
   placeholder.
2. Fare review IP-sanity umana finale sugli asset pubblici.
3. Decidere se mantenere sempre gli 8 secondi o introdurre in V2 la policy
   sessionStorage/intro breve.
