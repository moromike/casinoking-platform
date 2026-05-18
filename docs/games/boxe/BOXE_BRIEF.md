Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE — Game Brief (compiled)

Brief compilato da `docs/NEW_GAME_BRIEF_TEMPLATE.md` v0 con le informazioni
dell'analisi funzionale Hacksaw BOXES + decisioni del product owner del
2026-05-18. Riferimento metodologico: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`.

Fonti di input:

- `assets/Games/boxe/BOXE - DOCUMENTO DI DESIGN FUNZIONALE.docx` (untracked,
  analisi funzionale completa basata su Hacksaw Gaming "BOXES")
- Screenshot di riferimento `assets/Games/boxe/boxe1-7.png` (untracked)
- Asset preparati `assets/Games/boxe/boxe_icon001_512px.webp`,
  `diamond_green_v001.png`, `mine_fucsia_002.png` (untracked)

Stato: pronto per Fase 0 (Discovery & SPEC) del Playbook.

---

## 1. Identification

| Campo | Valore | Note |
|---|---|---|
| Game name (display) | BOXE | Da rinominare in futuro (decisione product 2026-05-18) |
| Game code (slug) | `boxe` | Singolare italiano, differenziazione da Hacksaw BOXES |
| Game family | `boxe` | Famiglia engine |
| First-variant code | `boxe001` | Pattern Mines (mines001, mines001a, mines001b, ...) |
| Demo enabled | yes | Default platform |
| Real enabled | yes | Default platform |
| Bonus wallet supported | yes | Default platform |

## 2. Visuals & Assets

| Campo | Valore | Note |
|---|---|---|
| Lobby card (production-ready) | `assets/Games/boxe/boxe_icon001_512px.webp` | 512x512 px, WebP, 33 KB — sotto limit 300 KB |
| Lobby card (originale, backup) | `assets/Games/boxe/boxe_icon001.png` | 1254x1254, 2 MB — conservato per future re-export |
| Diamond board asset | `assets/Games/boxe/diamond_green_v001.png` | 233x201 px, 60 KB — identico a `mines001d/symbol_safe` |
| Mine board asset | `assets/Games/boxe/mine_fucsia_002.png` | 194x252 px, 63 KB — identico a `mines001d/symbol_mine` |
| Theme tokens | Pattern Mines, riuso default platform | Skin advanced a posteriori se serve |
| Sound effects | Default platform (FX da definire, BGM da definire) | Cue dall'analisi: click bet, reveal diamond, reveal mine/explosion, cashout |
| Animations richieste | Reveal scatola (rotazione 3D, diamante azzurro), esplosione mina (rosso, espansione), pillola moltiplicatore (slide su step), transizione configurazione rows (fade-in righe) | Riferimenti screenshot e analisi §6 .docx |
| Provider intro video | Default platform (moromike lab 8s) | Nessun override |
| Screenshot di ispirazione | `boxe1` splash, `boxe2` idle base, `boxe4`-`boxe7` stati gameplay | `boxe3` mancante (nice-to-have, recupero opzionale) |

## 3. Math & RNG

| Campo | Valore | Note |
|---|---|---|
| Game type | Piramide a righe verticali, progressione bottom-to-top | "Tower/Mines" genre, Dare2Win arcade |
| Configuration tunables | `rows` (4, 5, 6, 7, 8) + `difficulty` (EASY, MEDIUM, HARD) | Operator-owned, configurabile da Title Editor |
| Payout formula | Multiplier deterministico computato da (`rows` × `difficulty`); ogni step ha multiplier crescente | Da formalizzare matematicamente in SPEC Fase 0 |
| Range moltiplicatori osservati | 1.37x (4 rows / Easy start) → 548.80x (max 8 rows / Hard top row) | Da analisi Hacksaw originale; va verificato in Fase 2A se replicato 1:1 o ricostruito |
| RTP target | 98% | Da analisi Hacksaw; deterministico, verificabile via simulazione |
| RNG fairness contract | Server-side deterministic, server seed + client seed | Pattern Mines (`mines_seeds` table, rotation via admin) |
| Max win cap | `null` per ora (no cap) | Vedi `docs/MINES_PENDING_TOPICS.md` — WP futuro per parametro inheritable master → skin con alert override |
| Free picks dopo bet | Yes | Pattern game-doc Hacksaw |
| Round duration / timeout | Default platform access-session timeout | No override |

## 4. Rules & Copy

| Campo | Valore | Note |
|---|---|---|
| Rules text (player-facing) | Da scrivere in Fase 0 SPEC; baseline = traduzione del §10 "GAME INFO - BOXES" del .docx (ENG) | Italiano + en + de + es |
| How-to-play tutorial 3-step | **Specifico BOXE** (diverso da Mines): "Bet → Pick (riga per riga) → Collect" | Da scrivere ad hoc, screenshot `boxe1` splash come riferimento |
| Edge case copy | Standard platform + game-over su mina + win celebration su cashout + top row auto-collect | Da definire in Fase 0 |
| Localization | `it`, `en`, `de`, `es` (default `it`, fallback `it`) | Pattern Mines (`ALLOWED_LOCALES`) |

## 5. Configuration limits

| Campo | Valore | Note |
|---|---|---|
| Bet range | Pattern Mines: no min/max espliciti, solo balance check | Decision Michele 2026-05-18 — UX a frecce ± Hacksaw deferred, parte con input libero |
| Allowed wallet types | cash + bonus | Default platform |
| Title variants | `boxe001` iniziale; futuri `boxe002`, `boxe001a`, ecc. | Pattern Mines |
| Operator-configurable settings | `rows`, `difficulty`, `max_win_cap` (quando implementato), theme tokens, copy, rules HTML, assets | Title Editor sezione BOXE-specifica |
| Hardcoded settings | Payout formula, RTP 98%, fairness contract | Math è game-specific code, non config |

## 6. Platform shell overrides

Tutti default. Nessun override.

| Componente shell | Use default? | Note |
|---|---|---|
| GameBootShell | Yes | |
| GameBootDecisionFlow | Yes | |
| GameProviderIntroGate | Yes | Brand intro `moromike lab` invariato |
| GameHowToPlayGate | Yes | Contenuti BOXE-specifici passati come children/prop |
| GameTableBalanceGate | Yes | Limits non sovrascritti per ora (segue balance check) |
| GameShortViewportGate | Yes | Rotation gate landscape-short attivo |
| Audio infra | Yes | |
| Theme provider | Yes | |
| Storage / launch context | Yes | |
| History / replay | Yes (infra), No (render BOXE-specifico) | Infra platform, render piramide game-specific |
| Launch Cashier | Yes | |

## 7. Special behaviors

| Campo | Valore | Note |
|---|---|---|
| Game-over reveal logic | **Rivela SOLO la riga corrente** (scatole non cliccate diventano opache per mostrare diamanti/mine residue); le righe superiori NON vengono rivelate | Diverso da Mines che rivela tutta la griglia |
| Auto-cashout policy | Session Recovery Engine default: su disconnect mid-round con multiplier > 1 → auto-cashout al multiplier corrente | Vedi `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` scenario #2 |
| Top row auto-collect | **Yes**: quando giocatore raggiunge l'ultima riga senza esplodere → auto-cashout vincita massima per quella configurazione | Comportamento specifico BOXE, da animare con feedback dedicato (Open question #2) |
| Bonus rounds / free spins | **No** | Pure core loop, niente bonus features |
| Replay format | Pattern platform; payload BOXE-specifico = sequenza di (riga, posizione, esito) per ogni pick + multiplier finale + reason di chiusura | Render frontend ricostruisce la piramide a round chiuso |
| Session recovery special handling | Nessuno specifico — segue design generale | Bonus rounds = no, quindi scenario #5 Recovery non applicabile |

## 8. State machine backend

| Campo | Valore | Note |
|---|---|---|
| Stati possibili round | `created`, `active`, `row_revealed`, `cashout_pending`, `completed_cashout`, `completed_top_row`, `failed_mine`, `expired` | Da formalizzare in Fase 0 SPEC §3.5 |
| Transizioni illegali | Cashout su round `failed_mine`/`expired`; reveal su round `completed_*`; reveal su riga superiore prima di rivelare la corrente; multiple bet su stesso round attivo | Server-side enforcement |
| Comportamento concurrent reveals | Serializzazione server-side (lock per round_id); idempotent reply su retry | Pattern Mines |
| Comportamento concurrent cashout | Race cashout vs reveal: il primo che arriva vince; il secondo riceve risposta idempotent del nuovo stato | Pattern Mines |
| Idempotency contract | `Idempotency-Key` header su start, reveal, cashout | Pattern Mines (vedi `mines/service.py`) |

## 9. Failure UX

| Scenario | Comportamento atteso |
|---|---|
| Config gioco mancante | Errore "BOXE configuration not loaded", retry button, no soft-fail |
| Title non pubblicato | 404 platform standard |
| Master title launch attempt | 422 LAUNCH_REJECTED_MASTER (pattern Mines) |
| Table session scaduta | Redirect a lobby con messaggio "Session expired" |
| Saldo insufficiente | Button BET disabilitato con tooltip "Insufficient balance" |
| Wallet bonus vuoto | Warning "Bonus wallet empty"; allow switch to cash |
| Rete intermittente | Spinner + retry automatico; dopo 3 fail → overlay "Connection issue, please retry" |
| Backend irraggiungibile | Error overlay "Game temporarily unavailable" |
| Round già chiuso, retry cashout | Idempotent reply (no error, conferma stato precedente) |
| Disconnessione mid-round con multiplier > 1 | Auto-cashout via Session Recovery Engine (default scenario #2) |

## 10. Integration outputs (derivati dal sistema)

- Backend module path: `backend/app/modules/games/boxe/`
- Frontend page route: `/boxe?title_code=<variant>&mode=demo|real`
- Admin backoffice tab: `Backoffice → Games → BOXE → Title detail` (struttura analoga a Mines)
- Lobby category placement: catalogo platform default
- Asset registry kinds: `lobby_card` (riuso platform), `symbol_safe` / `symbol_mine` (riuso platform), eventuali nuovi kind game-specific da decidere in Fase 1
- Replay endpoint: `/api/v1/games/boxe/session/{id}/replay` (pattern Mines)

## 11. Open questions (da chiudere prima di toccare codice)

Decisioni product/design ancora aperte. Fase 0 SPEC le risolve.

1. **Provably fair UI**: vogliamo mostrare al player la UI di verifica fairness (hash, seed)? Mines non ce l'ha visibile, BOXE Hacksaw originale neanche, ma è valutabile per differenziazione.
2. **Top row auto-collect feedback**: qual è l'animazione/messaggio quando il giocatore completa l'ultima riga? Da definire visualmente in Fase 0 / Fase 3C.
3. **Balance < bet behavior**: se il saldo scende sotto la puntata corrente, il selettore si auto-adegua al massimo disponibile o mostra errore esplicito? Coerenza con Mines da verificare.
4. **Max win cap concreto**: il valore (es. €1M come Hacksaw originale) lo decidiamo ora o aspettiamo il WP "max win cap inherited"? Default per BOXE v1 = null.
5. **Bet UX (input libero vs frecce ±)**: confermato Mines pattern (input libero). Frecce ± deferred. Da registrare in SPEC come "out of scope v1".
6. **Naming "BOXE" definitivo**: Michele ha indicato che rinominerà sia BOXE che Mines in futuro. Per BOXE v1 partiamo con `boxe`. SPEC nota questa decisione come reversibile.
7. **Skin advanced (theme MSK V2)**: BOXE v1 usa theme tokens pattern Mines base. Skin advanced (post-recovery WP MSK V2 deferred) non applicabile.

## 12. Implementation Log

Sezione attiva da Fase 0 in poi. Format e regole in
`docs/TASK_EXECUTION_GUARDRAILS.md` § Project Implementation Log e
§ Reading previous game logs.

### Entries

### 2026-05-18 - WP-BOXE-FASE-0
**Discovery / Decision**: Fase 0 ha consolidato il brief BOXE in uno SPEC
autosufficiente con gli 11 blocchi obbligatori del Playbook. Le 7 open
questions sono state chiuse o differite esplicitamente; la matematica completa
resta vincolata a una tabella/formula product-approved prima della Fase 2A.
**Why it matters**: BOXE e' il primo stress-test reale del metodo multi-game:
senza SPEC chiaro le decisioni su math, replay, admin config e recovery
finirebbero nel codice. La scelta di non inventare i moltiplicatori evita di
trasformare un riferimento visivo Hacksaw in una matematica non verificata.
**What we did**: SPEC.md scritto con 11 blocchi, 6 open questions chiuse e 1
deferred motivato (`max_win_cap=null` v1, WP futuro). Nessun codice runtime,
wallet, ledger, RNG, payout, fairness o math e' stato modificato.
**Affects**: `docs/games/boxe/SPEC.md`, `docs/README.md`

### 2026-05-18 - WP-BOXE-FASE-1
**Discovery / Decision**: Fase 1 ha classificato le capability BOXE: runtime
shell, wallet/ledger/platform rounds, launch, catalog, cashier, table sessions,
theme, i18n, assets e finance restano common; math/RNG/state/API/gameplay/admin
editor/replay renderer sono game-specific. Nessuna platform extension e'
necessaria ora; il Title Editor resta watchpoint per Fase 4A.
**Why it matters**: La mappa riduce il rischio di copiare Mines o infilare BOXE
nei layer platform. Le Fasi 2-7 ora hanno confini, branch suggeriti,
dipendenze, aree protette e test contract prima che parta codice.
**What we did**: Creata matrice common/game-specific/platform-extension, lista
WP Fasi 2-7, protected areas, contract test, smoke/visual baseline plan, admin
manual update plan e capability matrix skeleton. Il math gap resta separato:
Fase 2A e' bloccata fino all'input product-approved.
**Affects**: `docs/games/boxe/ARCHITECTURE_MAPPING.md`, `docs/README.md`

### 2026-05-18 - WP-BOXE-2A-MATH-RNG-FAIRNESS
**Discovery / Decision**: Product ha approvato Opzione C: derivazione math da
anchor osservati e target RTP 98%, senza fonti esterne. La formula v1 usa una
ladder geometrica in log-space, riconcilia tutti gli anchor a 2 decimali e usa
probabilita' implicite `RTP / multiplier` per validare il ritorno teorico.
**Why it matters**: Questo WP crea il primo pacchetto certification-ready del
progetto: math spec, backend math, fairness deterministica, simulator esterno e
stress framework on-demand. Evita math nel frontend e mantiene separati
wallet/ledger/platform rounds fino alla Fase 2D.
**What we did**: Aggiunti moduli backend BOXE math/RNG/fairness, simulator
standalone, test unit/integration rapidi, stress test manuale e
`MATH_SPEC.md` con formula, tabella completa, anchor reconciliation e risultati
RTP 100k per 15 configurazioni.
**Affects**: `backend/app/modules/games/boxe/`, `tools/boxe_math_simulator.py`,
`backend/tests/unit/test_boxe_math.py`, `tests/integration/test_boxe_fairness.py`,
`tests/stress/boxe_math/`, `docs/games/boxe/MATH_SPEC.md`

### 2026-05-18 - WP-BOXE-2B-SCHEMA-STATE
**Discovery / Decision**: La persistenza BOXE resta auto-contenuta in tabelle
game-specific (`boxe_sessions`, `boxe_rounds`, `boxe_picks`,
`boxe_idempotency_keys`) con sole FK nullable verso sessioni/platform round
esistenti. Nessuna estensione platform richiesta.
**Why it matters**: Fase 2C potra' consumare repository, lock per-round e
idempotency primitive senza riaprire schema o toccare wallet/ledger. Le race
reveal/cashout sono serializzate tramite `SELECT ... FOR UPDATE`.
**What we did**: Aggiunta migration 0039, repository BOXE, state machine con 9
stati SPEC, validatori per transizioni illegali, interfaccia recovery
auto-cashout scenario #2, test migration/state/concurrency/idempotency e bozza
atlas BOXE.
**Affects**: `backend/migrations/sql/0039__boxe_session_tables.sql`,
`backend/app/modules/games/boxe/repository.py`,
`backend/app/modules/games/boxe/state_machine.py`,
`tests/integration/test_boxe_state_machine.py`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

### 2026-05-18 - WP-BOXE-2C-API
**Discovery / Decision**: Gli endpoint BOXE sono game-specific sotto
`/api/v1/games/boxe/*` e consumano math/repository/state machine esistenti. I
POST richiedono sempre `Idempotency-Key`; stesso payload ritorna la risposta
salvata, payload diverso ritorna `IDEMPOTENCY_CONFLICT`.
**Why it matters**: Fase 3 puo' integrare player UI contro un contratto API
stabile, mentre wallet/ledger/adapter restano protetti fino alla Fase 2D.
Replay e history espongono solo round terminali.
**What we did**: Aggiunti config/start/reveal/cashout/session/replay/history,
error mapping da SPEC §11, test integration API con 36 casi, sezione API
nell'atlas draft. Backoffice manual update non applicabile: nessuna admin UI.
**Affects**: `backend/app/api/routes/boxe.py`,
`backend/app/api/router.py`, `backend/app/modules/games/boxe/service.py`,
`tests/integration/test_boxe_api.py`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

### 2026-05-18 - WP-PLATFORM-GAME-AGNOSTIC-ADAPTER
**Discovery / Decision**: Fase 2D BOXE ha surfaciato il risk strutturale #1 del
Playbook: il platform adapter era ancora Mines-shaped su round, launch, table
session e serialization finance/account. BOXE 2D resta in pausa e riparte dopo
il merge del WP platform.
**Why it matters**: La generalizzazione evita di copiare infrastruttura Mines
in BOXE e crea un prerequisito riusabile per HI-LO e i giochi successivi.
Generalization candidate registrato: la mappatura pre-Fase 2 deve verificare la
game-agnosticity del platform adapter per ogni nuovo gioco.
**What we did**: Introdotta whitelist centrale `('mines', 'boxe')`, rinominato
il servizio round platform in API `*_game_round_*`, aggiornati call site Mines,
generalizzati launch/table checks e predisposti serializer finance/account
polymorphic basati su `platform_rounds.game_code`.
**Affects**: `backend/app/modules/platform/game_codes.py`,
`backend/app/modules/platform/rounds/service.py`,
`backend/app/modules/platform/game_launch/service.py`,
`backend/app/modules/platform/table_sessions/service.py`,
`backend/app/modules/admin/service.py`, `backend/app/modules/account/service.py`,
`docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`

### 2026-05-18 - WP-BOXE-2D-ADAPTER-FINANCE-REPLAY
**Discovery / Decision**: 2D ha sbloccato dopo refactor platform adapter
game-agnostic (`WP-PLATFORM-GAME-AGNOSTIC-ADAPTER`). BOXE consuma le nuove API
`*_game_round_*` con `game_code="boxe"` e mantiene demo isolato dal platform
settlement.
**Why it matters**: Conferma che il pattern adapter generalizzato funziona per
il secondo gioco. Il risk #1 del Playbook v0, multi-game adapter non
battle-tested, e' risolto in pratica senza copiare infrastruttura Mines dentro
BOXE.
**What we did**: Aggiunti adapter BOXE, round gateway, platform round wiring,
settlement cashout/loss/top-row, finance/history wiring polymorphic, replay
post-settlement, manifest i18n backend e test integration per demo, real,
bonus, loss, top-row e retry idempotente. Backoffice manual update non
applicabile: nessuna admin UI.
**Affects**: `backend/app/modules/games/boxe/`,
`backend/app/api/routes/boxe.py`, `backend/app/modules/account/service.py`,
`tests/integration/test_boxe_api.py`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

Generalization candidate: Pre-Fase 2 architecture mapping deve verificare
game-agnosticity del platform adapter per ogni gioco nuovo. Se trova hardcoding
`game_code`, aprire WP platform refactor PRIMA di Fase 2D.

### Distillazione finale (a chiusura BOXE)

Checklist obbligatoria prima di dichiarare BOXE chiuso (vedi anche
`docs/BOXE_PROJECT_BRIEF.md` § 11):

- [ ] Tutte le entry del log sono state riviste
- [ ] Le decisioni ricorrenti sono diventate default nel `NEW_GAME_BRIEF_TEMPLATE.md`
- [ ] Gli anti-pattern emersi sono stati formalizzati nel `NEW_GAME_INTEGRATION_PLAYBOOK.md` § Anti-pattern
- [ ] Le naming convention adottate sono documentate nel Playbook
- [ ] I rischi strutturali emersi sono nel Playbook § Rischi
- [ ] Eventuali estensioni platform sono documentate e referenziate
- [ ] Template è abbastanza ricco da permettere a un product owner di compilarlo per gioco 3 (HI-LO) senza riaprire le stesse discussioni metodologiche

---

## Riferimenti

- Metodologia: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- Template di input: `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- Brief progetto BOXE (ancora untracked, metodologico): `docs/BOXE_PROJECT_BRIEF.md`
- Capability platform riusabili: `docs/CAPABILITY_INVENTORY_2026-05-17.md`
- Architettura runtime shell: `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`
- Gioco di riferimento: `docs/ARCHITECTURE_ATLAS_MINES.md`
- Recovery policy: `docs/SESSION_RECOVERY_ENGINE_DESIGN.md`
- Regole permanenti: `docs/TASK_EXECUTION_GUARDRAILS.md`
- Audit shell pre-BOXE: `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md`
