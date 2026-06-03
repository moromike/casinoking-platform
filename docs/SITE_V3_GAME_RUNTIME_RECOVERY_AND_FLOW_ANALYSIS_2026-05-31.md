Status: ACTIVE
Last meaningful update: 2026-05-31

# Site V3 - Game Runtime Recovery And Flow Analysis

## 1. Lettura rapida per Michele

Questo documento fotografa lo stato giochi dopo il passaggio di recupero del
2026-05-31 e serve a dare al CTO una base verificabile, non una descrizione a
memoria.

Situazione in parole semplici:

- Il sito pubblico Site V3 serve i giochi da `http://localhost:3000/{game}`.
- La pagina pubblica non contiene il gioco direttamente: apre un iframe interno
  verso `/runtime/{game}`.
- Dentro l'iframe vivono i runtime Mines, BOXE e HI-LO in `frontend-v3`.
- I tre giochi condividono una parte frontend comune: boot, iframe close,
  table-balance gate, intro provider, how-to-play, audio preferences e alcuni
  controlli.
- Ogni gioco mantiene poi il proprio gameplay, CSS, copy, replay e chiamate API.
- Il backend resta un modular monolith: non e' un servizio giochi separato, ma
  ha moduli logici separati per piattaforma, round, table session e singoli
  giochi.

Il problema gestionale principale non e' "un file solo enorme" in senso stretto:
e' che alcuni confini sono ancora troppo porosi. Una modifica al runtime comune,
al CSS globale o alla shell iframe puo' cambiare insieme Mines, BOXE e HI-LO.
Questo e' esattamente il tipo di rischio emerso nella recovery.

## 2. Passaggio interrotto: cosa ho appena chiuso

Ho completato il passaggio che era stato interrotto prima dell'ultimo prompt:

| Area | Stato | Evidenza |
| --- | --- | --- |
| Servizi locali | PASS | `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build` completato; backend, frontend-v3, edge, Postgres, Redis healthy. |
| TypeScript frontend-v3 | PASS | `docker compose ... exec -T frontend-v3 npm run lint` -> `tsc --noEmit` verde. |
| Mines desktop | PASS sul bug segnalato | `DEMO` ora resta nella riga header, campo puntata ha padding, board non sfora il contenitore. Screenshot: `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-mines-desktop-after-gates.png`. |
| HI-LO desktop | PASS sul bug segnalato | Badge demo ora e' `DEMO`, non `DEMO MODE`. Screenshot: `artifacts/site_v3_recovery_game_fix_2026-05-31/current/game-hi-lo-desktop-after-gates.png`. |
| BOXE real gate | PASS sul bug segnalato | Il gate non mostra piu' la riga compatta `Fonte saldo`; mostra le card wallet come gli altri giochi. Screenshot: `artifacts/site_v3_recovery_game_fix_2026-05-31/current/gate-boxe-desktop-table-gate.png`. |
| Table gate condiviso | PASS con nota | Mines, HI-LO e BOXE usano tutti lo stesso componente visuale `GameTableBalanceGate`; copy e quick amounts restano specifici per gioco. |
| Mobile Mines/BOXE | AMBER | Nessuno scroll tecnico, ma la baseline Phase 1 aveva gia' header molto compresso/overlap visivo. Non lo dichiaro "perfetto"; serve decisione product/CTO se aprire un pass dedicato mobile. |

Aggiornamento dopo test manuale REAL di Michele:

| Area | Stato | Evidenza |
| --- | --- | --- |
| Mines real mode | PASS sul bug segnalato | Prima decideva `DEMO` in base all'assenza immediata di `accessToken`; ora segue BOXE/HI-LO e decide demo solo da `bootRequest.forceDemoMode`. Maschera tavolo visibile anche senza token: `current/real-no-auth-mines-desktop.png`. |
| Mines real dopo ingresso tavolo | PASS | Con player tecnico e `wallet_source=cash`, dopo `Spiel starten` non compare `DEMO`; compare saldo tavolo `Tischguthaben 100.00 CHIP`. Screenshot: `current/real-flow-mines-desktop-after-enter.png`. |
| HI-LO real dopo ingresso tavolo | PASS | Gate tavolo e gameplay restano `REAL MODE`. Screenshot: `current/real-flow-hi-lo-desktop-after-enter.png`. |
| BOXE real dopo ingresso tavolo | PASS | Gate tavolo e gameplay restano `REAL MODE`. Screenshot: `current/real-flow-boxe-desktop-after-enter.png`. |
| Mines audio popup | PASS sul clipping | Il rail embedded ora usa `overflow: visible`, come BOXE, quindi la tendina audio non viene tagliata dal contenitore sinistro. Screenshot: `current/audio-mines-desktop-open.png`; confronto: `current/audio-boxe-desktop-open.png`. |
| Launch cashier REAL | PASS dopo fix specifico | Il bug reale era nel link pubblico: Mines/HI-LO non impostavano `mode`, quindi `GameFramePage` aggiungeva `mode=demo`. Ora il launcher genera `mode=real&wallet_source=real` per tutti i giochi. Smoke dal launcher: `metadata/launch-cashier-real-mode-check.json`; screenshot Mines: `current/cashier-real-mines-after-enter.png`. |

Aggiornamento 2026-06-01 sui due debiti residui segnalati da Michele:

| Area | Stato | Evidenza |
| --- | --- | --- |
| Mines badge real nel gameplay | PASS | In real mode il rail Mines mostra ora `REAL MODE`, allineato a BOXE/HI-LO. File: `frontend-v3/app/ui/mines/mines-gameplay.tsx:643`. Screenshot: `current/mines-real-mode-badge-audio-open.png`; smoke launcher: `metadata/launch-cashier-real-mode-check.json`. |
| Mines audio control visual parity | PASS mirato | Il componente Mines conserva i locator legacy `.mines-audio-*`, ma aggiunge le classi comuni `.game-audio-*` e override scoped per avvicinarsi al controllo BOXE senza cambiare logica audio. File: `frontend-v3/app/ui/mines/mines-runtime-tools.tsx:76`, `frontend-v3/app/ui/mines/mines.css:140`. Screenshot: `current/mines-real-mode-badge-audio-open.png`; metriche: `metadata/mines-real-badge-audio-check.json`. |
| Launcher pubblico REAL | PASS ricontrollato | Dopo rebuild, dalla home Mines/HI-LO/BOXE generano `mode=real&wallet_source=real`; Mines entra con `REAL MODE`, non `DEMO`. Metadata: `metadata/launch-cashier-real-mode-check.json`. |
| Mobile Mines | AMBER invariato | Il capture desktop/mobile non mostra scroll tecnico; l'header mobile resta molto compresso come nella baseline Phase 1. Non e' stato corretto in questo micro-fix per non aprire un redesign mobile. |

Patch applicate in questo passaggio:

- `frontend-v3/app/ui/mines/mines.css`
  - `:1433` aggiunge padding locale al campo puntata embedded.
  - `:1422` riporta il rail embedded a `overflow: visible`, allineandolo al comportamento BOXE per evitare clipping della tendina audio.
  - `:1893` ripristina layout flex locale del rail header.
  - `:1901` forza il badge `DEMO` come inline-flex no-wrap.
  - `:2256` riduce la board embedded da `100dvh - 260px` a `100dvh - 270px`.
- `frontend-v3/app/ui/mines/mines-standalone.tsx:279,303,351`
  - riallinea la decisione demo/real a BOXE/HI-LO: `isDemoMode` deriva da `forceDemoMode`, non dall'autenticazione locale; il table gate real non viene saltato solo per assenza immediata del token.
- `frontend-v3/app/ui/mines/i18n/mines-copy-defaults.ts:164`
  - inglese Mines: `DEMO MODE` -> `DEMO`.
- `frontend-v3/app/ui/hi-lo/hi-lo-i18n/hi-lo-copy-defaults.ts:225,352,479,606`
  - HI-LO: `DEMO MODE` -> `DEMO` in tutte le locale default.
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:717`
  - BOXE: `DEMO MODE` -> `DEMO`.
- `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx:97,138`
  - il gate saldo rende sempre le card wallet; se `wallet_source` e' locked,
    la card selezionata resta attiva e le altre sono disabilitate.
- `frontend-v3/app/ui/game-runtime/game-boot-request.ts:37`
  - accetta sia `wallet_source=real` sia `wallet_source=cash` come wallet cash.
- `frontend-v3/app/ui/site-v3-render-helpers.ts:145`
  - il launch cashier pubblico imposta sempre `mode=real` per REAL e
    `mode=real_bonus` per BONUS, evitando che `GameFramePage` applichi il
    default `mode=demo` ai giochi non-BOXE.
- `frontend-v3/app/ui/mines/mines-gameplay.tsx:643`
  - il rail Mines mostra sempre il badge di modalita': `DEMO`, `BONUS MODE`
    o `REAL MODE`, invece di mostrare il badge solo in demo.
- `frontend-v3/app/ui/mines/mines-runtime-tools.tsx:76`
  - il controllo audio Mines mantiene le classi legacy `mines-audio-*` per
    test e compatibilita', aggiungendo le classi comuni `game-audio-*`.
- `frontend-v3/app/ui/mines/mines.css:140`
  - override scoped per rendere il popup audio Mines coerente con il controllo
    comune usato da BOXE/HI-LO, senza toccare preferenze audio o sound logic.

Non ho modificato in questo passaggio:

- backend GMP;
- game logic;
- RNG;
- payout/math;
- board generation;
- reveal/cashout semantics;
- replay payload backend.

## 3. Evidenze screenshot prodotte

Root artifact: `artifacts/site_v3_recovery_game_fix_2026-05-31/`.

| Superficie | Screenshot corrente | Side-by-side baseline |
| --- | --- | --- |
| Mines desktop gameplay | `current/game-mines-desktop-after-gates.png` | `side-by-side/game-mines-desktop-after-gates-side-by-side.png` |
| Mines mobile gameplay | `current/game-mines-mobile-after-gates.png` | `side-by-side/game-mines-mobile-after-gates-side-by-side.png` |
| HI-LO desktop gameplay | `current/game-hi-lo-desktop-after-gates.png` | `side-by-side/game-hi-lo-desktop-after-gates-side-by-side.png` |
| HI-LO mobile gameplay | `current/game-hi-lo-mobile-after-gates.png` | `side-by-side/game-hi-lo-mobile-after-gates-side-by-side.png` |
| BOXE desktop gameplay | `current/game-boxe-desktop-after-gates.png` | `side-by-side/game-boxe-desktop-after-gates-side-by-side.png` |
| BOXE mobile gameplay | `current/game-boxe-mobile-after-gates.png` | `side-by-side/game-boxe-mobile-after-gates-side-by-side.png` |
| Mines real table gate | `current/gate-mines-desktop-table-gate.png` | n/a |
| HI-LO real table gate | `current/gate-hi-lo-desktop-table-gate.png` | n/a |
| BOXE real table gate | `current/gate-boxe-desktop-table-gate.png` | n/a |
| Mines real no-auth gate | `current/real-no-auth-mines-desktop.png` | n/a |
| HI-LO real no-auth gate | `current/real-no-auth-hi-lo-desktop.png` | n/a |
| BOXE real no-auth gate | `current/real-no-auth-boxe-desktop.png` | n/a |
| Mines real after enter | `current/real-flow-mines-desktop-after-enter.png` | n/a |
| HI-LO real after enter | `current/real-flow-hi-lo-desktop-after-enter.png` | n/a |
| BOXE real after enter | `current/real-flow-boxe-desktop-after-enter.png` | n/a |
| Mines audio popup | `current/audio-mines-desktop-open.png` | n/a |
| BOXE audio popup reference | `current/audio-boxe-desktop-open.png` | n/a |
| Mines launch-cashier real gate | `current/cashier-real-mines-gate.png` | n/a |
| Mines launch-cashier real after enter | `current/cashier-real-mines-after-enter.png` | n/a |
| HI-LO launch-cashier real after enter | `current/cashier-real-hi_lo-after-enter.png` | n/a |
| BOXE launch-cashier real after enter | `current/cashier-real-boxe-after-enter.png` | n/a |
| Mines real badge + audio open | `current/mines-real-mode-badge-audio-open.png` | n/a |

Metriche principali dal capture:

| Superficie | Scroll host | Scroll runtime | Nota |
| --- | --- | --- | --- |
| Mines desktop | no | no | Board 546x546, badge `DEMO`, gate superati. |
| Mines mobile | no | no | Full viewport mobile; header visivamente compresso come baseline. |
| HI-LO desktop | no | no | Badge `DEMO`, shell non fullscreen. |
| HI-LO mobile | no | no | Badge `DEMO`, layout comparabile alla baseline. |
| BOXE desktop | no | no | Badge `DEMO`, board dentro host. |
| BOXE mobile | no | no | Full viewport mobile; header molto denso come baseline. |
| Table gates desktop | no | no | Mines, HI-LO e BOXE gate centrati 460x566. |
| Real after enter desktop | no | no | Mines/HI-LO/BOXE entrano nel gameplay real con table balance, senza ricadere in demo. |
| Mines audio popup | no | no | Rail computed `overflow: visible`; popup non tagliata dal rail embedded. |
| Launch cashier real mode | no | no | Link Mines/HI-LO/BOXE generati dalla home hanno `mode=real`; iframe runtime riceve `mode=real`, non `mode=demo`. |
| Mines real badge + audio parity | no | no | Badge `REAL MODE` presente; popover audio usa classi `game-audio-*` e `mines-audio-*`, con screenshot dedicato. |

Script e metadata:

- `artifacts/site_v3_recovery_game_fix_2026-05-31/capture_game_fix.py`
  rigenerato dopo rebuild del bundle.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/real_flow_after_enter_check.py`
  crea player tecnico, apre Mines/HI-LO/BOXE in real mode, conferma il saldo tavolo
  e cattura il gameplay post-ingresso.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/metadata/real-mode-audio-regression-check.json`
  registra real no-auth + popup audio.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/metadata/real-flow-after-enter-check.json`
  registra il player tecnico e le metriche post-ingresso real.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/launch_cashier_real_mode_check.py`
  riproduce il flusso utente dalla home: click card, scelta Real money,
  navigazione iframe, gate tavolo e ingresso gameplay.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/metadata/launch-cashier-real-mode-check.json`
  registra href e iframe URL reali; Mines risulta
  `/mines?title_code=mines001b&mode=real&wallet_source=real...`.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/mines_real_badge_audio_check.py`
  entra in Mines real con player tecnico, supera gate/intro/how-to, apre il
  controllo audio e cattura badge/modalita' + popup.
- `artifacts/site_v3_recovery_game_fix_2026-05-31/metadata/mines-real-badge-audio-check.json`
  registra `modeBadge.text = REAL MODE` e metriche del popup audio.

## 4. Rappresentazione funzionale comune

Flusso pubblico real mode:

```text
Player
  -> /mines | /boxe | /hi-lo su :3000
  -> Site V3 public shell
  -> GameFramePage costruisce iframe /runtime/{game}
  -> Runtime standalone del gioco
  -> useGameLaunchContext
  -> GameTableBalanceGate
  -> Provider intro
  -> How To Play
  -> Gameplay
  -> API gioco
  -> Platform Game Runtime Layer
  -> wallet / ledger / table session / platform round
```

Flusso demo mode:

```text
Player
  -> /{game}?mode=demo
  -> Site V3 public shell
  -> iframe /runtime/{game}?mode=demo&embed=1
  -> Runtime standalone
  -> demo token/demo launch dove previsto
  -> Provider intro
  -> How To Play
  -> Gameplay demo
  -> API demo/game
```

Confine importante:

- Il frontend mostra stati, invia azioni e riceve payload.
- Il frontend non deve decidere outcome, board, payout, RNG o saldo.
- La piattaforma possiede wallet, ledger, table session, access session e
  platform round.
- Il gioco possiede stato round, regole del gioco, outcome server-side,
  replay e matematica.

## 5. Moduli frontend condivisi

| Blocco | Responsabilita' | File |
| --- | --- | --- |
| Public shell | Route pubblica, title selector, iframe host. | `frontend-v3/app/mines/page.tsx`, `frontend-v3/app/boxe/page.tsx`, `frontend-v3/app/hi-lo/page.tsx`, `frontend-v3/app/ui/game-frame-page.tsx` |
| Runtime route | Entry interna iframe. | `frontend-v3/app/runtime/mines/page.tsx`, `frontend-v3/app/runtime/boxe/page.tsx`, `frontend-v3/app/runtime/hi-lo/page.tsx` |
| Boot request | Query `title_code`, `mode`, `wallet_source`, `embed`, `return_to`. | `frontend-v3/app/ui/game-runtime/game-boot-request.ts` |
| Launch context | Stato boot/launch/runtime/fatal. | `frontend-v3/app/ui/game-runtime/use-game-launch-context.ts` |
| Embed bridge | Close e fullscreen-state via postMessage. | `frontend-v3/app/ui/game-runtime/use-game-embed-bridge.ts` |
| Boot shell | Theme e orchestration visuale. | `frontend-v3/app/ui/game-runtime/game-boot-shell.tsx` |
| Decision flow | Sequenza table gate, intro, how-to, gameplay. | `frontend-v3/app/ui/game-runtime/game-boot-decision-flow.tsx` |
| Table balance gate | UI saldo tavolo condivisa. | `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx` |
| Provider intro/how-to | Overlay condivisi, contenuti game-specific. | `frontend-v3/app/ui/game-runtime/game-provider-bootstrap.tsx`, `frontend-v3/app/ui/game-runtime/game-how-to-play-gate.tsx` |
| Control rail primitives | Input puntata, chip, Bet/Collect, balance. | `frontend-v3/app/ui/game-runtime/game-control-rail.tsx` e componenti vicini |
| Runtime CSS comune | Stile gate/intro/how-to/shared controls. | `frontend-v3/app/ui/game-runtime/game-runtime.css` |

## 6. Per gioco: moduli, backend, matematica, dipendenze

### Mines

| Layer | Stato |
| --- | --- |
| Public shell | `frontend-v3/app/mines/page.tsx` -> iframe `/runtime/mines`. |
| Runtime entry | `frontend-v3/app/runtime/mines/page.tsx` -> `MinesStandalone`. |
| Frontend gameplay | `frontend-v3/app/ui/mines/mines-standalone.tsx`, `mines-gameplay.tsx`, `mines.css`, replay viewer e i18n. |
| Backend API | `backend/app/api/routes/mines.py` espone config, fairness, start, reveal, cashout, sessions, replay. |
| Backend game module | `backend/app/modules/games/mines/service.py`, fairness e backoffice config. |
| Platform deps | table sessions, platform rounds, wallet/ledger, access sessions, demo token. |
| Matematica | Payout runtime ufficiale da allegati `docs/runtime/*`; backend calcola multiplier/payout. |
| Workflow gameplay | Config griglia/mine/puntata -> start -> reveal celle -> cashout/win/loss -> replay. |
| Differenze note | Mines ha CSS e standalone molto piu' grandi; mantiene compatibilita' storage legacy. |

Workflow tecnico Mines:

```text
/mines
  -> GameFramePage
  -> /runtime/mines
  -> MinesStandalone
     -> real: GameTableBalanceGate -> /table-sessions
     -> demo: demo launch/token
     -> ProviderIntro -> HowToPlay
     -> MinesGameplay
        -> POST /games/mines/start
        -> POST /games/mines/reveal
        -> POST /games/mines/cashout
        -> GET /games/mines/session/{id}/replay
```

### BOXE

| Layer | Stato |
| --- | --- |
| Public shell | `frontend-v3/app/boxe/page.tsx` -> iframe `/runtime/boxe`. |
| Runtime entry | `frontend-v3/app/runtime/boxe/page.tsx` -> `BoxeStandalone`. |
| Frontend gameplay | `frontend-v3/app/ui/boxe/boxe-standalone.tsx`, `boxe-gameplay.tsx`, `use-boxe-runtime.ts`, CSS/replay/i18n. |
| Backend API | `backend/app/api/routes/boxe.py` espone config, launch-token, start, reveal, cashout, session, replay. |
| Backend game module | `backend/app/modules/games/boxe/service.py`, `state_machine.py`, `platform_client.py`, admin config. |
| Platform deps | table sessions, platform rounds, wallet/ledger; GMP launch-token slice gia' presente lato backend. |
| Matematica | Piramide righe/difficolta'/multiplier server-side nel modulo BOXE. |
| Workflow gameplay | Selezione righe/difficolta'/puntata -> start -> reveal pick nella piramide -> cashout/top/loss -> replay. |
| Differenze note | BOXE ha manifest/GMP piu' avanti degli altri su portabilita' backend; frontend action-token strict e' ancora futuro. |

Workflow tecnico BOXE:

```text
/boxe
  -> GameFramePage
  -> /runtime/boxe
  -> BoxeStandalone
     -> real: GameTableBalanceGate -> /table-sessions
     -> ProviderIntro -> HowToPlay
     -> BoxeGameplay
        -> POST /games/boxe/start
        -> POST /games/boxe/reveal
        -> POST /games/boxe/cashout
        -> GET /games/boxe/round/{id}/replay
```

### HI-LO

| Layer | Stato |
| --- | --- |
| Public shell | `frontend-v3/app/hi-lo/page.tsx` -> iframe `/runtime/hi-lo`. |
| Runtime entry | `frontend-v3/app/runtime/hi-lo/page.tsx` -> `HiLoStandalone`. |
| Frontend gameplay | `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx`, `hi-lo-gameplay.tsx`, `use-hi-lo-runtime.ts`, CSS/replay/i18n. |
| Backend API | `backend/app/api/routes/hi_lo.py` espone config, start, predict, skip, cashout, active-round, sessions, replay. |
| Backend game module | `backend/app/modules/games/hi_lo/service.py`, randomness/fairness/admin config. |
| Platform deps | table sessions, platform rounds, wallet/ledger. |
| Matematica | Probabilita' carte e multiplier server-side; frontend visualizza valori ricevuti. |
| Workflow gameplay | Puntata -> start -> carta iniziale -> predict red/black/up/down -> skip/cashout/loss -> replay. |
| Differenze note | HI-LO e' il piu' diverso come UX: non ha board grid/piramide ma superficie carta/predizioni. |

Workflow tecnico HI-LO:

```text
/hi-lo
  -> GameFramePage
  -> /runtime/hi-lo
  -> HiLoStandalone
     -> real: GameTableBalanceGate -> /table-sessions
     -> ProviderIntro -> HowToPlay
     -> HiLoGameplay
        -> POST /games/hi-lo/start
        -> POST /games/hi-lo/predict
        -> POST /games/hi-lo/skip
        -> POST /games/hi-lo/cashout
        -> GET /games/hi-lo/round/{id}/replay
```

## 7. Differenze importanti tra i giochi

| Tema | Mines | BOXE | HI-LO |
| --- | --- | --- | --- |
| Shape visuale | Griglia quadrata con immagine background. | Piramide di celle. | Carta centrale + predizioni. |
| Azione primaria | Reveal cell. | Reveal/pick nella piramide. | Predict red/black/up/down. |
| Azione secondaria | Cashout. | Cashout. | Skip e cashout. |
| Config runtime player | Griglia, mine, puntata. | Righe, difficolta', puntata. | Puntata, skip limit, predizioni. |
| Replay | Board + mine positions/fairness. | Piramide + pick history. | Timeline azioni + carte/fairness. |
| Storage frontend | Legacy Mines keys. | Namespace dedicato BOXE. | Namespace dedicato HI-LO. |
| Stato portabilita' | Integrato V3, non package esterno. | Primo candidato GMP/package-first. | Integrato V3, non package esterno. |
| Rischio CSS | Alto: CSS molto grande e storico. | Medio: usa classi `mines-*` per eredita' runtime. | Medio-basso: CSS piu' autonomo. |

## 8. Dipendenze con il frontend Site V3

Dipendenze legittime:

- Site V3 decide URL pubblica, title selector e iframe host.
- Site V3 forwarda query consentite tramite `GameFramePage`.
- Site V3 imposta `embed=1` e `embed_origin`.
- Site V3/CMS puo' generare link gioco con `wallet_source=real|bonus`.
- Runtime V3 carica theme/copy/asset del title pubblicato.

Dipendenze rischiose:

- CSS globale o admin che entra nel DOM iframe.
- Classi storiche `mines-*` riusate da BOXE come base visuale.
- Un unico `game-runtime.css` che influenza table gate, intro, how-to e shared controls di tutti i giochi.
- Standalone game-specific molto grandi che mischiano boot, API calls, table gate, intro, gameplay state e error handling.

## 9. Analisi gestionale del problema

### Versione comprensibile

Oggi i giochi non sono "esterni" nel senso forte del termine. Sono separati
come cartelle e domini, ma girano nello stesso frontend V3 e nello stesso backend
applicativo. Questo rende facile lanciare tutto in locale, ma rende anche facile
rompere piu' superfici con un singolo CSS o componente condiviso.

La parte piu' delicata e' il frontend:

- il sito pubblico ha la shell;
- l'iframe ospita il gioco;
- il runtime comune prepara il flusso;
- il gioco disegna e chiama API;
- CSS comuni e CSS game-specific possono sovrapporsi.

Se non c'e' una baseline visuale automatica, ogni recovery diventa "a occhio".
Questo non e' accettabile per giochi, perche' le regressioni visuali sono molto
visibili anche quando la logica economica e' intatta.

### Versione tecnica

Il backend e' un modular monolith ragionevole: wallet/ledger/platform/game sono
ancora nello stesso processo, ma i confini principali sono leggibili.

Il frontend e' piu' fragile:

- `frontend-v3/app/ui/game-runtime/**` e' shared ma non e' un package isolato.
- `frontend-v3/app/ui/mines/**`, `boxe/**`, `hi-lo/**` vivono nello stesso bundle.
- CSS e classi storiche non sono incapsulate come CSS Modules/Shadow DOM.
- Alcuni componenti BOXE riusano classi `mines-*`, aumentando coupling visuale.
- Il gate saldo e' condiviso, ma callback, copy e quick amounts sono per gioco.
- Mobile e desktop non hanno ancora una matrice golden obbligatoria per ogni stato.

Il monolite backend non e' il blocco piu' urgente. Il blocco urgente e' creare
una barriera di qualita' sul runtime frontend giochi: golden screenshot, DOM
assertion e regole di scoping CSS.

## 10. Suggerimenti operativi

1. Congelare baseline visive esplicite per i 3 giochi.
   Non basta "baseline main" storica se il mobile baseline e' gia' brutto. Serve
   una decisione: baseline accettata o nuova baseline mobile pulita.

2. Introdurre una suite visuale obbligatoria.
   Per ogni gioco: desktop/mobile, demo gameplay, real table gate, replay,
   volume menu, close X. Ogni fix CSS deve passare questa suite.

3. Separare il runtime shared come contratto piu' stretto.
   Target consigliato: `packages/game-runtime` o equivalente interno, con CSS
   scoped e test di import boundary. Non serve subito un microservizio.

4. Ridurre riuso di classi `mines-*` nei nuovi giochi.
   BOXE eredita ancora classi Mines per rail/buttons/layout. Questo e' debito
   tecnico concreto e spiega parte della fragilita'.

5. Tenere backend modular monolith per ora.
   Spostare subito tutto in servizi separati sarebbe prematuro. Prima serve
   chiudere il contratto Game Module: launch, table session, actions, replay,
   assets/theme/i18n e reporting.

6. Aprire un WP dedicato mobile gameplay.
   Non come restyle casuale. Deve partire da screenshot baseline scelti dal CTO,
   con obiettivo: header non sovrapposto, board leggibile, controls accessibili,
   no scroll inatteso, X/audio/info coerenti.

## 11. Next step consigliato

Il prossimo passo non dovrebbe essere altro codice sparso.

Sequenza consigliata:

1. CTO rivede questo documento e gli screenshot.
2. Michele/CTO decidono se la baseline mobile Phase 1 e' accettabile oppure no.
3. Se non e' accettabile, aprire `WP-GAME-MOBILE-BASELINE`: un solo WP per
   normalizzare mobile Mines/BOXE/HI-LO, con screenshot golden e nessun cambio
   di backend/game logic.
4. Dopo il gate mobile, riprendere GMP/portabilita' giochi, partendo da BOXE
   come candidato package-first, senza toccare visual gameplay.

## 12. File/documenti letti per questa analisi

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ACTIVE_OPEN_LOOPS.md`
- `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`
- `docs/GAME_ARCHITECTURE_OVERVIEW.md`
- `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md`
- codice frontend/backend indicato nelle tabelle sopra
