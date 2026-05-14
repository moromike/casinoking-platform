# Mines BOOT-2A - CTO Ready Refactor Plan

Aggiornato: 2026-05-15.

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

Raccomandazione: **GO**, con implementazione staged e rollback per commit.

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

### `GameBootRuntime`

```ts
type GameBootRuntime<TConfig> = {
  request: GameBootRequest;
  runtimeConfig: TConfig | null;
  fatalOverlay: { title: string; text: string } | null;
  status: { kind: "success" | "error" | "info"; text: string } | null;
  isLaunchContextReady: boolean;
  isRuntimeReady: boolean;
};
```

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

## Work Package

### BOOT-2A.0 - Freeze Behavior Baseline

Scopo: bloccare il comportamento Mines prima del refactor.

Azioni:

1. confermare worktree pulito;
2. rilanciare build e regressioni Mines;
3. aggiungere eventuali test mancanti su bootstrap prima del refactor;
4. salvare screenshot/baseline solo se necessari e approvati.

Test minimi:

```powershell
npm --prefix frontend run build
python -m pytest tests/integration/test_mines_embed_browser_smoke.py tests/integration/test_mines_skin_visual_regression.py
python -m pytest tests/integration/test_mines_backoffice_config.py tests/contract/test_mines_runtime_contract.py tests/contract/test_mines_demo_contract.py
```

Exit criteria:

- Mines verde prima di toccare architettura;
- nessuna mutazione su Title reali;
- eventuali test nuovi usano Title/account disposable.

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
   - `wallet_source=real|bonus`.

Exit criteria:

- nessuna variazione visibile;
- nessun token con `title_code` vuoto;
- vecchie sessioni demo/real non si rompono.

### BOOT-2A.2 - Estrarre Launch Context

Scopo: isolare token, auth/demo mode, runtime config e fatal overlay iniziale.

Write set previsto:

- nuovo `frontend/app/ui/game-runtime/use-game-launch-context.ts`;
- eventuale `frontend/app/ui/mines/use-mines-runtime-config.ts`;
- aggiornamento `MinesStandalone`.

Azioni:

1. spostare il caricamento iniziale in un hook dedicato;
2. mantenere funzioni gameplay come start/reveal/cashout dentro Mines;
3. separare `isLaunchContextReady` da `isRuntimeReady`;
4. rappresentare stati reali: params letti, token pronto, config pronta, theme
   ricevuto o fallback deciso.

Exit criteria:

- refresh/auth state non parte mai prima di avere `titleCode` normalizzato;
- errori di config/launch non restano come pagina bianca;
- demo preview continua a funzionare.

### BOOT-2A.3 - Estrarre Shell Visuale Di Boot

Scopo: spostare Provider Intro, How To Play Gate e overlay di bootstrap fuori
dal gameplay Mines.

Write set previsto:

- nuovo `frontend/app/ui/game-runtime/game-boot-shell.tsx`;
- nuovo `frontend/app/ui/game-runtime/game-boot-overlays.tsx` se utile;
- aggiornamento `MinesStandalone`;
- nessun cambio a `MinesBoard`/RNG/API.

Azioni:

1. `GameBootShell` avvolge `TitleThemeProvider`;
2. `GameBootShell` decide:
   - mostra Table Balance Gate se il gioco/adattatore lo richiede;
   - mostra Provider Intro se non completata;
   - mostra How To Play se non completato;
   - passa al gameplay solo quando pronto;
3. la progress bar resta legata a readiness reale, non solo timer;
4. reduced-motion e fallback poster restano invariati.

Exit criteria:

- Table Balance Gate real-mode resta prima dell'intro;
- demo salta Table Balance Gate;
- provider intro resta 8s V1 per decisione prodotto;
- How To Play resta dopo intro e prima del gameplay;
- mobile guard continua a funzionare.

### BOOT-2A.4 - Estrarre `MinesGameplay`

Scopo: rendere evidente cosa e' Mines-specific.

Write set previsto:

- nuovo `frontend/app/ui/mines/mines-gameplay.tsx`;
- `frontend/app/ui/mines/mines-standalone.tsx` diventa wrapper sottile o viene
  rinominato mantenendo export compatibile;
- nessun cambio backend.

Azioni:

1. spostare board, controlli, replay, payout ladder, effetti e azioni di gioco;
2. lasciare hook/handler start/reveal/cashout in modulo Mines;
3. passare al gameplay solo props/hook Mines-specific;
4. mantenere export `MinesStandalone` per non rompere route/import.

Exit criteria:

- `/mines` continua a montare `MinesStandalone`;
- il file principale non orchestra piu' sia boot sia gameplay;
- il secondo gioco puo' leggere `GameBootShell` senza importare Mines.

### BOOT-2A.5 - Adapter Contract Per Il Secondo Gioco

Scopo: preparare il minimo contratto che il prossimo gioco dovra' implementare.

Azioni:

1. documentare `GameRuntimeAdapter` minimo;
2. non implementare ancora il secondo gioco;
3. aggiungere esempio commentato o test fixture, non UI prodotto;
4. aggiornare atlas e README.

Exit criteria:

- esiste una checklist per creare `NewGameStandalone`;
- non c'e' dipendenza da `mines-*` nella shell comune;
- il prossimo gioco riusa boot/intro/how-to/theme invece di copiarli.

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

## Go / No-Go

### GO

Il CTO puo' approvare se:

- Mines V1 e' accettata manualmente o congelata come baseline;
- il piano resta frontend/refactor senza backend economico;
- ogni WP ha commit separato;
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

1. branch dedicato `feature/boot-2a-game-shell`;
2. un commit per WP;
3. non modificare baseline visuali finche' il CTO non approva eventuale delta;
4. mantenere `MinesStandalone` come export pubblico stabile;
5. se BOOT-2A.3 o BOOT-2A.4 falliscono, revertire solo quel commit e lasciare
   gli helper puri gia' validati se non introducono regressioni.

Rollback tecnico:

```powershell
git revert <commit_boot2a_wp>
npm --prefix frontend run build
python -m pytest tests/integration/test_mines_embed_browser_smoke.py -k "mobile or how_to_play or runtime_values"
```

## Sequenza Consigliata

1. Michele fa ultimo test manuale Mines V1.
2. Se emergono bug blocker, si correggono senza BOOT-2A.
3. Quando Mines e' accettata, aprire branch BOOT-2A.
4. Eseguire BOOT-2A.0.
5. Implementare BOOT-2A.1 -> test -> commit.
6. Implementare BOOT-2A.2 -> test -> commit.
7. Implementare BOOT-2A.3 -> stress test boot/mobile -> commit.
8. Implementare BOOT-2A.4 -> full gate -> commit.
9. Aggiornare atlas/README/pending topics.
10. Solo dopo, aprire piano del secondo gioco.

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
