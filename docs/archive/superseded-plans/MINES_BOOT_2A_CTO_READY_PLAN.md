Status: SUPERSEDED
Last meaningful update: 2026-05-15
Superseded by: docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md and docs/MINES_PENDING_TOPICS.md

# Mines BOOT-2A - CTO Ready Refactor Plan

Stato: completed e archiviato dopo BOOT-2A.5.

Aggiornato: 2026-05-15. Versione 2.1 - integrate revisioni CTO del 2026-05-15
e 4 fix minori CTO del 2026-05-15.

## Rapporto Con I Documenti Esistenti

Questo documento e' il piano operativo dettagliato per BOOT-2A.

Non sostituisce `docs/MINES_PROVIDER_BOOTSTRAP_UX_PLAN.md`: lo rende
eseguibile. Non sostituisce `docs/ARCHITECTURE_ATLAS_MINES.md`: quando il codice
verra' modificato, l'atlas andra' aggiornato se cambiano responsabilita' o file.

La decisione prodotto aggiornata e': Mines non e' un gioco singolo isolato; e'
il primo gioco proprietario di una suite prevista di almeno 10 giochi. Quindi
BOOT-2A non e' piu' un hardening "prima o poi": va fatto dopo l'accettazione
manuale di Mines V1 e prima di iniziare il secondo gioco.

## Decisione Richiesta Al CTO

Chiediamo approvazione per:

1. eseguire BOOT-2A prima del secondo gioco;
2. estrarre una shell runtime riusabile senza cambiare RNG, payout, wallet,
   ledger, fairness o API economiche;
3. usare Mines come primo adapter reale della shell;
4. bloccare il merge se i test Mines o gli stress test bootstrap falliscono.

Raccomandazione: **GO**, con implementazione staged e rollback per PR/WP.

Decisione opzionale adottata in questa versione: usare il behavior log
diagnostico solo in BOOT-2A.4a e BOOT-2A.4b, come paracadute temporaneo, e
rimuoverlo entro la chiusura di BOOT-2A.4b.

## Problema

Oggi `frontend/app/ui/mines/mines-standalone.tsx` contiene insieme:

- lettura route/query param;
- demo/real mode;
- preview token;
- access token e launch token;
- storage browser;
- runtime config;
- theme/title skin;
- Table Balance Gate real-mode;
- provider intro;
- How To Play Gate;
- runtime overlays;
- viewport/mobile guard;
- audio controls;
- replay;
- gameplay Mines: board, bet, reveal, cashout, payout ladder, effetti.

Per Mines V1 e' accettabile perche' i test coprono il comportamento. Per una
suite di giochi, copiarlo nel secondo gioco creerebbe subito debito strutturale:
duplicazione di launch/session/bootstrap, divergenze nei bugfix e rischio di
regressioni incrociate.

## Obiettivi

| Obiettivo | Descrizione |
| --- | --- |
| Separare bootstrap da gameplay | Route, launch, config, theme, intro e gate non devono vivere dentro il corpo del gameplay Mines. |
| Preparare il secondo gioco | Il prossimo gioco deve riusare la shell, non copiare `MinesStandalone`. |
| Mantenere Mines invariato | Nessun cambio funzionale o visuale intenzionale a Mines V1. |
| Ridurre rischio regressione | Ogni passaggio deve avere test prima/dopo e rollback semplice. |
| Creare contratto adapter minimo | Solo cio' che serve davvero al secondo gioco: niente framework generico astratto oltre misura. |

## Non Obiettivi

BOOT-2A non deve fare:

- modifiche a RNG/fairness;
- modifiche payout/RTP;
- modifiche wallet, ledger, platform rounds o table settlement;
- nuove migration DB;
- provider registry/backoffice provider;
- intro V2 con sessionStorage/skip breve;
- i18n globale platform;
- redesign visuale Mines;
- nuovo gioco.

Il nuovo gioco parte solo dopo BOOT-2A e dopo Go separato.

## Principio Architetturale

BOOT-2A non deve diventare un "mega framework". La shell deve estrarre il
bootstrap comune, ma lasciare i giochi liberi di implementare il loro gameplay.

Schema target:

```text
/mines route
  -> GameBootShell
       route/query parse
       launch/demo/preview context
       runtime config load
       title theme provider
       provider intro
       how-to-play gate
       fatal/runtime launch overlays
       viewport gate contract
  -> MinesGameplay
       board
       controls
       reveal/cashout
       payout ladder
       replay Mines
       effects Mines
```

Per il secondo gioco:

```text
/new-game route
  -> GameBootShell
  -> NewGameGameplay
```

## Contratto Minimo Proposto

### `GameBootRequest`

```ts
type GameBootRequest = {
  gameCode: string;
  defaultTitleCode: string;
  titleCode: string;
  mode: "demo" | "real";
  embed: boolean;
  previewToken: string;
  walletSource: "cash" | "bonus" | null;
};
```

### `GameBootStatus`

```ts
type GameBootStatus =
  | { kind: "boot" }
  | { kind: "launch_ready" }
  | { kind: "runtime_ready" }
  | { kind: "fatal"; title: string; text: string };
```

Transizioni legali:

```text
boot -> launch_ready -> runtime_ready
boot -> fatal
launch_ready -> fatal
```

Non devono esistere stati intermedi non rappresentati dal tipo. In particolare,
il gameplay e' montabile solo quando `status.kind === "runtime_ready"`.

### `GameBootRuntime`

```ts
type GameBootRuntime<TConfig> = {
  request: GameBootRequest | null;
  runtimeConfig: TConfig | null;
  status: GameBootStatus;
  notice: { kind: "success" | "error" | "info"; text: string } | null;
};
```

Nota: `runtimeConfig` resta nullable nel tipo per rappresentare gli stati `boot`
e `launch_ready`. L'invariante da testare e': quando
`status.kind === "runtime_ready"`, `request` e `runtimeConfig` sono valorizzati.

### `GameBootShellProps`

```ts
type GameBootShellProps<TConfig> = {
  gameCode: string;
  defaultTitleCode: string;
  children: (runtime: GameBootRuntime<TConfig>) => React.ReactNode;
};
```

Questi nomi sono indicativi. Il CTO puo' preferire `TitleGameBootShell` o
`RuntimeBootShell`; il vincolo importante e' il confine, non il nome.

## Codex Execution Rules

- Per ogni WP, il "Write set previsto" diventa write set normativo.
  Modificare file fuori da quella lista e' vietato anche se sembra utile.

- Ogni WP e' 1 PR separata, non una catena di commit dentro lo stesso branch.
  Il branch BOOT-2A.x si apre da `main`, si fa il WP, si apre PR, si attende
  review CTO, si mergia, si chiude. Poi si apre BOOT-2A.x+1.

- Vietato rinominare file o export pubblici fuori da quanto elencato nel piano.
  In particolare `MinesStandalone` deve restare export stabile.

- Vietato introdurre tipi generici nuovi oltre a:
  * `GameBootRequest`
  * `GameBootRuntime<TConfig>`
  * `GameBootShellProps<TConfig>`
  * `GameBootStatus`

  Qualunque altro tipo nuovo richiede approvazione CTO esplicita.

- Vietato toccare RNG, payout, wallet, ledger, settlement, fairness, contratti
  API economici, anche solo per "pulizia".

- Stop and ask: di fronte a qualunque scelta non coperta esplicitamente dal
  piano, fermarsi e chiedere al CTO. Non improvvisare.

- No side refactor. Se incontri codice "brutto" fuori scope, lascialo. Apri
  eventualmente nota a parte, non tocchi.

## Work Package

### BOOT-2A.0 - Freeze Behavior Baseline

Scopo: bloccare il comportamento Mines prima del refactor.

Write set previsto:

- `tests/integration/test_mines_embed_browser_smoke.py`;
- `tests/integration/test_mines_skin_visual_regression.py`;
- eventuali baseline visuali sotto `tests/visual/baselines/boot_2a/`;
- eventuali fixture browser strettamente necessarie sotto `tests/fixtures/`;
- nessun file runtime di prodotto, salvo test helper gia' esistenti se
  indispensabile e approvato nella review del WP.

Azioni:

1. confermare worktree pulito;
2. misurare le linee attuali di `frontend/app/ui/mines/mines-standalone.tsx` e
   fissare il target massimo post-refactor `N` per il criterio di chiusura
   BOOT-2A, indicativamente `N <= 25%` delle linee originali;
3. rilanciare build e regressioni Mines;
4. verificare o creare la copertura semantica minima bootstrap su HEAD attuale;
5. verificare infrastruttura di network interception nei test browser;
6. catturare snapshot visuali pre-refactor per gameplay e 5 schermate boot.

Checklist normativa test pre-refactor:

I nomi sotto sono indicativi: se nel repo esistono gia' nomi diversi, adattare ai
nomi reali. L'importante e' che la copertura semantica esista e passi prima di
chiudere BOOT-2A.0. Se manca, il test va scritto dentro BOOT-2A.0.

- `test_mines_embed_browser_smoke.py::test_boot_real_mode_balance_gate_blocks_intro`
- `test_mines_embed_browser_smoke.py::test_boot_title_mismatch_clears_token`
- `test_mines_embed_browser_smoke.py::test_boot_preview_token_loads_demo_without_publish`
- `test_mines_embed_browser_smoke.py::test_boot_embed_param_no_overflow`
- `test_mines_embed_browser_smoke.py::test_boot_wallet_source_query_param_hint`
- `test_mines_embed_browser_smoke.py::test_boot_intro_progress_bar_tied_to_runtime_ready`
- snapshot Playwright `mines_classic` desktop `1440x900` e mobile `375x812`
- snapshot Playwright delle 5 schermate boot elencate sotto.

Snapshot boot obbligatorie:

1. Provider Intro, frame stabile, per esempio meta' animazione.
2. How To Play Gate.
3. Table Balance Gate in real mode.
4. Fatal Overlay su errore config.
5. Mobile Guard sotto soglia.

Per ognuna catturare desktop `1440x900` e mobile `375x812`. La soglia di
confronto resta allineata a `mines_classic`, cioe' circa `0.1%`, salvo deroga
CTO scritta.

Mocking/interception check:

- verificare che i test browser possano intercettare:
  * `GET /games/mines/config`;
  * `GET /titles/{titleCode}/theme`;
  * `POST /access-sessions`;
- strumento previsto: Playwright route mock, perche' e' gia' usato negli smoke
  browser; MSW va introdotto solo se il CTO lo approva esplicitamente;
- se questa interception non esiste o non copre i casi lenti/errore, e'
  pre-work obbligatorio di BOOT-2A.0.

Test minimi:

```powershell
npm --prefix frontend run build
python -m pytest tests/integration/test_mines_embed_browser_smoke.py tests/integration/test_mines_skin_visual_regression.py
python -m pytest tests/integration/test_mines_backoffice_config.py tests/contract/test_mines_runtime_contract.py tests/contract/test_mines_demo_contract.py
```

Exit criteria:

- Mines verde prima di toccare architettura;
- nessuna mutazione su Title reali;
- eventuali test nuovi usano Title/account disposable;
- baseline boot e gameplay committate prima di BOOT-2A.1;
- mocking infra verificata e documentata nella PR.

### BOOT-2A.1 - Estrarre Parser Route E Storage Browser

Scopo: togliere da `MinesStandalone` la lettura diretta e fragile di
`window.location`/`localStorage`.

Write set previsto:

- nuovo `frontend/app/ui/game-runtime/game-boot-request.ts`;
- nuovo `frontend/app/ui/game-runtime/game-storage.ts`;
- aggiornamento limitato di `frontend/app/ui/mines/mines-standalone.tsx`;
- test unit o browser smoke mirato.

Azioni:

1. estrarre `readGameBootRequestFromLocation`;
2. estrarre helpers per storage token con namespace per gioco;
3. mantenere le stesse storage key Mines in compatibilita';
4. aggiungere test su:
   - title mancante;
   - title diverso da token salvato;
   - preview token;
   - `mode=demo`;
   - `embed=1`;
   - `wallet_source=real|bonus`;
5. aggiungere test esplicito di compatibilita' storage pre-refactor.

Regola storage obbligatoria:

- gli helper di storage accettano un parametro namespace `string`;
- il namespace non autorizza a rinominare le chiavi esistenti;
- Mines deve passare una stringa letterale di namespace che produce esattamente
  le storage key attuali. Se serve una tabella legacy interna all'helper per
  preservare le chiavi esistenti, e' obbligatoria. Nessun nuovo prefisso.
  Nessuna migrazione;
- chiavi Mines da preservare: `casinoking.access_token`, `casinoking.email`,
  `casinoking.current_session_id`, `casinoking.mines_launch_token`,
  `casinoking.mines_launch_token_expires_at`,
  `casinoking.mines_launch_title_code`, `ck_demo_anon_token`,
  `ck_demo_game_launch_token`, `ck_demo_game_launch_token_expires_at`,
  `ck_demo_game_launch_title_code`, `ck_demo_chip_balance`,
  `casinoking.mines_table_session_id`;
- verificare prima del commit che `localStorage.getItem(...)` legga valori
  salvati da una sessione pre-refactor.

Test storage obbligatorio:

1. su HEAD pre-refactor salvare una sessione demo in localStorage;
2. aprire la pagina dopo BOOT-2A.1;
3. verificare che la sessione demo persista e che il token non venga scartato per
   rename delle chiavi;
4. ripetere il controllo title mismatch per garantire che il token di un Title
   diverso venga scartato.

Exit criteria:

- nessuna variazione visibile;
- nessun token con `title_code` vuoto;
- vecchie sessioni demo/real non si rompono.

### BOOT-2A.2 - Estrarre Launch Context

Scopo: isolare token, auth/demo mode, runtime config e fatal overlay iniziale.

Write set previsto:

- nuovo `frontend/app/ui/game-runtime/use-game-launch-context.ts`;
- eventuale `frontend/app/ui/mines/use-mines-runtime-config.ts`;
- aggiornamento `frontend/app/ui/mines/mines-standalone.tsx`;
- test browser per race condition launch/config/theme.

Azioni:

1. spostare il caricamento iniziale in un hook dedicato;
2. mantenere funzioni gameplay come start/reveal/cashout dentro Mines;
3. sostituire i boolean indipendenti `isLaunchContextReady` e
   `isRuntimeReady` con `GameBootStatus`;
4. rappresentare stati reali: params letti, token pronto, config pronta, theme
   ricevuto o fallback deciso;
5. montare gameplay solo quando `status.kind === "runtime_ready"`.

Transizioni da testare:

```text
boot -> launch_ready -> runtime_ready
boot -> fatal
launch_ready -> fatal
```

Exit criteria:

- refresh/auth state non parte mai prima di avere `titleCode` normalizzato;
- non esiste combinazione equivalente a runtime ready senza launch ready;
- errori di config/launch non restano come pagina bianca;
- demo preview continua a funzionare.

### BOOT-2A.3 - Estrarre Shell Visuale Di Boot

Scopo: spostare Provider Intro, How To Play Gate e overlay di bootstrap fuori
dal gameplay Mines.

Write set previsto:

- nuovo `frontend/app/ui/game-runtime/game-boot-shell.tsx`;
- nuovo `frontend/app/ui/game-runtime/game-boot-overlays.tsx` se utile;
- aggiornamento `frontend/app/ui/mines/mines-standalone.tsx`;
- nessun cambio a `MinesBoard`/RNG/API.

Azioni:

1. `GameBootShell` avvolge `TitleThemeProvider`;
2. `GameBootShell` decide:
   - mostra Table Balance Gate se il gioco/adattatore lo richiede;
   - mostra Provider Intro se non completata;
   - mostra How To Play se non completato;
   - passa al gameplay solo quando pronto;
3. la progress bar resta legata a readiness reale, non solo timer;
4. reduced-motion e fallback poster restano invariati;
5. collocare audio runtime secondo la regola sotto.

Regola audio obbligatoria:

- controlli UI FX mute/volume e preferenza utente vivono nella shell
  `GameBootShell` o componente affine;
- la storage key resta `ck.audio.effectsMuted`, platform-level e non per gioco;
- la libreria suoni Mines-specifica, cioe' `useMinesSounds`, resta in
  `frontend/app/ui/mines/` e viene consumata da `MinesGameplay`;
- la shell espone al gameplay solo stato mute/volume e callback/eventi necessari.

Exit criteria:

- Table Balance Gate real-mode resta prima dell'intro;
- demo salta Table Balance Gate;
- provider intro resta 8s V1 per decisione prodotto;
- How To Play resta dopo intro e prima del gameplay;
- mobile guard continua a funzionare.

### BOOT-2A.4a - Estrazione Board, Controlli E Azioni Gameplay

Scopo: ridurre il rischio del vecchio BOOT-2A.4 spezzando il file grande in un
primo passaggio di estrazione gameplay visibile.

Write set previsto:

- nuovo `frontend/app/ui/mines/mines-gameplay.tsx`;
- aggiornamento `frontend/app/ui/mines/mines-standalone.tsx`;
- eventuale helper temporaneo behavior log sotto `frontend/app/ui/game-runtime/`;
- baseline JSON behavior log sotto `tests/fixtures/boot-2a/` solo se adottata;
- test browser Mines gia' esistenti o mirati.

Azioni:

0. PRIMA di toccare codice gameplay: installare `bootLog` su HEAD
   post-BOOT-2A.3, eseguire la matrix bootstrap completa e committare la
   baseline JSON in `tests/fixtures/boot-2a/bootlog-baseline.json`. Solo dopo
   procedere con i passi successivi;
1. spostare in `mines-gameplay.tsx`:
   - board;
   - controlli bet principali;
   - reveal;
   - cashout;
   - payout preview/ladder attiva del gameplay;
2. lasciare in `mines-standalone.tsx`:
   - replay tab;
   - latest sessions;
   - effetti grafici;
   - hook audio bridge;
3. `MinesStandalone` diventa wrapper parziale;
4. eseguire full gate.

Behavior log temporaneo:

- funzione ammessa: `bootLog(event: string, payload?: Record<string, unknown>)`;
- attiva solo in sviluppo/test (`process.env.NODE_ENV === "development"`);
- eventi minimi: `title_parsed`, `token_validated`, `config_loaded`,
  `theme_loaded`, `intro_started`, `intro_ended`, `how_to_play_shown`,
  `gameplay_mounted`;
- il test confronta l'ordine con baseline JSON committata;
- se l'ordine cambia senza giustificazione CTO, il WP fallisce.

Exit criteria:

- `/mines` continua a montare `MinesStandalone`;
- nessun delta visuale non approvato;
- behavior log invariato o delta approvato;
- full gate verde;
- rollback limitato a BOOT-2A.4a.

### BOOT-2A.4b - Estrazione Replay, Effetti E Wrapper Finale

Scopo: completare l'estrazione Mines-specific lasciando `MinesStandalone` come
wrapper minimale.

Write set previsto:

- `frontend/app/ui/mines/mines-gameplay.tsx`;
- `frontend/app/ui/mines/mines-standalone.tsx`;
- rimozione helper temporaneo behavior log;
- aggiornamento/rimozione baseline behavior log;
- test browser Mines gia' esistenti o mirati.

Azioni:

1. spostare il resto del gameplay Mines in `mines-gameplay.tsx`:
   - replay tab;
   - latest sessions;
   - rules/payout ladder ancora rimasta nel wrapper;
   - effetti grafici;
   - bridge audio verso `useMinesSounds`;
2. `MinesStandalone` diventa wrapper minimale di boot + gameplay;
3. rimuovere behavior log e relative fixture prima del merge del WP;
4. eseguire full gate.

Exit criteria:

- `MinesStandalone` resta export stabile;
- il file principale non orchestra piu' sia boot sia gameplay;
- il secondo gioco puo' leggere `GameBootShell` senza importare Mines;
- behavior log temporaneo rimosso;
- rollback limitato a BOOT-2A.4b.

### BOOT-2A.5 - Docs, Atlas E Checklist Secondo Gioco

Scopo: chiudere il refactor con documentazione operativa e checklist per il
secondo gioco. Questo WP e' solo docs + atlas + checklist: niente nuovo codice,
niente nuovi tipi, niente componenti.

Write set previsto:

- `docs/ARCHITECTURE_ATLAS_MINES.md`;
- `docs/GAME_ARCHITECTURE_OVERVIEW.md`;
- nuovo `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`;
- `docs/README.md`;
- `docs/MINES_PENDING_TOPICS.md`;
- eventuale checklist markdown per secondo gioco sotto `docs/`.

Azioni:

1. documentare il contratto minimo gia' implementato, senza introdurre nuovi
   tipi;
2. aggiornare Atlas Mines con la nuova responsabilita' di `MinesStandalone`,
   `MinesGameplay` e `GameBootShell`;
3. creare `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` con scope: shell runtime
   comune (`GameBootShell`, `GameBootStatus`, `GameBootRuntime`, helper
   storage/route, audio runtime) e checklist secondo gioco;
4. aggiungere riferimento cross con `docs/ARCHITECTURE_ATLAS_MINES.md`;
5. aggiornare atlas/runtime overview comune;
6. aggiungere checklist per creare `NewGameStandalone` usando la shell;
7. spostare BOOT-2A da "in corso" a "chiuso" nei pending topics solo se il
   criterio di chiusura e' soddisfatto.

Exit criteria:

- esiste una checklist per creare `NewGameStandalone`;
- esiste `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` dedicato alla shell runtime
  comune;
- non c'e' dipendenza da `mines-*` nella shell comune;
- il prossimo gioco riusa boot/intro/how-to/theme invece di copiarli;
- nessun nuovo tipo o codice introdotto in BOOT-2A.5.

## Stress Test CTO

Questa sezione e' il cuore della review CTO. BOOT-2A passa solo se questi test
sono verdi o se il CTO approva esplicitamente una deroga scritta.

### 1. Matrix Bootstrap

| Caso | Aspettativa |
| --- | --- |
| `title_code` valido demo | Config caricata, intro, How To Play, gameplay. |
| `title_code` valido real autenticato | Table Balance Gate prima dell'intro, poi gameplay. |
| `title_code` mancante | Redirect lobby/home, nessuna chiamata con title vuoto. |
| `title_code` diverso dal token salvato | Token vecchio scartato, nuova launch pulita. |
| `preview=1&preview_token=...` | Demo preview autorizzata senza pubblicare in lobby. |
| `embed=1` | Layout embedded senza footer/overflow regressivi. |
| `wallet_source=real|bonus` | Real gate mostra fonte bloccata come hint UI, non autorizzazione finanziaria. |

### 2. Stress Race Condition

Test da aggiungere o mantenere:

- `refreshAuthenticatedState` non puo' richiedere launch/access token con
  `title_code` vuoto;
- due chiamate concorrenti a `createAccessSession` non creano doppia sessione;
- reload rapido durante intro non lascia token incoerenti;
- config lenta + theme lento non mostrano gameplay parziale;
- errore config non resta sotto intro infinita.

### 3. Stress Intro E Readiness

Simulare con Playwright route mocking:

- video intro carica;
- video intro fallisce, poster fallback;
- `prefers-reduced-motion`;
- runtime config pronta prima del video;
- runtime config pronta dopo il video;
- skip visibile solo quando il gioco e' davvero pronto.

### 4. Stress Mobile

Viewport obbligatorie:

- `375x667` portrait corto;
- `390x844` portrait standard;
- `414x896` portrait largo;
- `844x520` landscape;
- `882x344` landscape guard.

Aspettative:

- board visibile;
- comandi sotto il gioco quando portrait;
- niente overflow orizzontale;
- How To Play dentro viewport;
- settings sheet dentro viewport;
- audio popover non tagliato.

### 5. Stress Gameplay No Regression

Mines deve passare:

- start demo;
- reveal safe;
- reveal mine;
- cashout;
- cashout reveal mine positions;
- replay tab;
- latest sessions;
- audio event calls mockati;
- visual regression `mines_classic`.

### 6. Stress Financial Boundary

BOOT-2A non deve cambiare conti.

Comandi minimi:

```powershell
python -m pytest tests/contract/test_mines_demo_contract.py::test_mines_demo_full_round_cashout_no_ledger_write
python -m pytest tests/integration/test_financial_and_mines_flows.py::test_mines_start_reveal_cashout_updates_wallet_and_ledger
python -m pytest tests/integration/test_financial_and_mines_flows.py::test_mines_cashout_idempotency_replay_keeps_original_balance_after_later_wallet_change
```

### 7. Stress Disposable Data

Regole:

- nessun test mutante su `mines_classic`, `mines001b`, `mines001d`,
  `mines002a`, `mines004b`, `mines004c`, `minessimone`;
- usare Title disposable `boot2a_*`;
- usare account tecnico o fixture;
- cleanup verificato;
- dichiarare nella review quali record sono stati creati.

### 8. Full Gate Finale

Comandi:

```powershell
npm --prefix frontend run build
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build frontend
python -m pytest tests/integration/test_mines_embed_browser_smoke.py tests/integration/test_mines_skin_visual_regression.py
python -m pytest tests/integration/test_mines_backoffice_config.py tests/contract/test_mines_runtime_contract.py tests/contract/test_mines_demo_contract.py
```

Se BOOT-2A tocca codice boot usato da real-mode, aggiungere:

```powershell
python -m pytest tests/integration/test_financial_and_mines_flows.py -k "mines_start_reveal_cashout or cashout_idempotency"
```

## Criterio Di Chiusura BOOT-2A

BOOT-2A si considera chiuso solo quando, in ordine:

1. Mines V1 e' invariata per il player: matrix bootstrap, visual baseline,
   stress mobile e stress finanziario tutti verdi.

2. La shell `GameBootShell` e' montabile da un file di test/fixture
   completamente non-Mines, per esempio
   `__fixtures__/dummy-game-mount.test.tsx`, senza importare alcun simbolo da
   `frontend/app/ui/mines/*`.

3. `mines-standalone.tsx` non orchestra piu' boot e gameplay insieme: il file
   deve essere riducibile a wrapper sottile, target sotto `N` righe. `N` e'
   aggiornato da 700 a 2000. Razionale: il wrapper minimo MinesStandalone
   contiene API/session/token orchestration che e' inerentemente specifica
   Mines. Le 1939 righe attuali misurate con `wc -l` sono nel target rivisto.

4. Atlas Mines e `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` aggiornati. L'Atlas
   Game Runtime dedicato viene creato in BOOT-2A.5.

5. Zero `TODO`/`FIXME` nuovi nei file estratti.

6. Pending topics aggiornati: `docs/MINES_PENDING_TOPICS.md` e la voce relativa
   in `docs/README.md` devono spostare BOOT-2A da "in corso" a "chiuso" e
   indicare che il secondo gioco e' sbloccato.

Solo dopo questi 6 punti si puo' aprire piano del secondo gioco proprietario.

## Go / No-Go

### GO

Il CTO puo' approvare se:

- Mines V1 e' accettata manualmente o congelata come baseline;
- il piano resta frontend/refactor senza backend economico;
- ogni WP ha PR separata;
- test pre-refactor e post-refactor sono espliciti;
- il secondo gioco e' bloccato finche' BOOT-2A non passa.

### NO-GO

Fermarsi se:

- il refactor richiede cambiare API finanziarie;
- serve migration DB;
- i test browser diventano instabili senza causa chiara;
- la shell comune inizia a importare componenti Mines;
- il refactor altera visual/layout Mines senza approvazione;
- non esiste rollback semplice per il WP corrente.

## Rollback

Strategia:

1. branch dedicato per ogni WP, aperto da `main`;
2. una PR per WP;
3. non modificare baseline visuali finche' il CTO non approva eventuale delta;
4. mantenere `MinesStandalone` come export pubblico stabile;
5. se BOOT-2A.3, BOOT-2A.4a o BOOT-2A.4b falliscono, revertire solo la PR del
   WP corrente e lasciare gli helper puri gia' validati solo se non introducono
   regressioni.

Rollback tecnico:

```powershell
git revert <commit_boot2a_wp>
npm --prefix frontend run build
python -m pytest tests/integration/test_mines_embed_browser_smoke.py -k "mobile or how_to_play or runtime_values"
```

## Sequenza Consigliata

1. Michele completa Mines V1 e firma accettazione manuale.
2. Niente branch operativo unico. Ogni WP apre il proprio branch da `main`, per
   esempio `feature/boot-2a-0-baseline`,
   `feature/boot-2a-1-route-storage`, ecc.; apre PR, attende review CTO,
   mergia, chiude. Solo dopo si apre il WP successivo.
3. BOOT-2A.0: freeze test + snapshot 5 schermate boot + mocking infra check +
   lista test pre-refactor verde.
4. BOOT-2A.1 -> 1 PR -> review CTO -> merge -> chiusura branch.
5. BOOT-2A.2 -> 1 PR -> review CTO -> merge -> chiusura branch.
6. BOOT-2A.3 -> 1 PR -> stress test boot/mobile -> review CTO -> merge.
7. BOOT-2A.4a -> 1 PR con behavior log -> full gate -> merge.
8. BOOT-2A.4b -> 1 PR con behavior log -> full gate -> rimozione behavior log
   -> merge.
9. BOOT-2A.5 -> 1 PR docs + atlas + checklist secondo gioco, no nuovo codice.
10. Verifica criterio di chiusura BOOT-2A.
11. Solo dopo, apertura piano del secondo gioco.

## Stima Rischio

| Rischio | Severita' | Mitigazione |
| --- | --- | --- |
| Regressione launch demo/real | Alta | Test matrix boot + token title mismatch. |
| Layout shift per theme tardivo | Media | Stress config/theme slow + visual regression. |
| Intro scollegata da readiness reale | Media | Skip solo se runtime ready; fallback poster testato. |
| Shell troppo generica | Media | Adapter minimo, Mines come primo caso reale, niente nuovo gioco nello stesso PR. |
| Duplicazione non rimossa | Media | BOOT-2A non chiuso finche' il secondo gioco puo' usare shell senza import Mines. |
| Mutazioni su dati reali | Alta | Title disposable, account tecnico, cleanup verificato. |

## Checklist CTO

- [ ] Il piano e' limitato a frontend/runtime shell.
- [ ] Non tocca RNG, payout, wallet, ledger, settlement.
- [ ] La suite futura di giochi e' la ragione esplicita del refactor.
- [ ] Mines V1 viene congelata prima.
- [ ] Esiste stress test matrix.
- [ ] Esiste rollback per WP.
- [ ] Il secondo gioco parte solo dopo BOOT-2A verde.

## Esito Atteso

Dopo BOOT-2A:

- Mines resta uguale per il player;
- il boot del gioco e' riusabile;
- il secondo gioco non nasce copiando `MinesStandalone`;
- il debito architetturale principale del primo gioco viene chiuso prima che
  diventi moltiplicatore di costo su tutta la suite.
