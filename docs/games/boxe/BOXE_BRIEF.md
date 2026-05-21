Status: ACTIVE
Last meaningful update: 2026-05-21

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

### 2026-05-21 - WP-BO-VISUAL-SPECULARITY
**Discovery / Decision**: BOXE backoffice had the same shared shell as Mines,
but several tabs still used BOXE-only card and helper layouts for status, copy,
rules, assets and theme.
**Why it matters**: Surface 10 cannot be green if the operator gets a different
visual grammar for equivalent backoffice work. Shared containers need matching
content layout and control density.
**What we did**: Reused the existing Mines admin patterns for rules rows, board
asset rows, game-card asset rows and the theme editor panel on BOXE-only files.
No Mines, backend, runtime copy, schema or board code was changed.
**Affects**: `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`

### 2026-05-21 - WP-LEGACY-LABELS-CLOSURE
**Discovery / Decision**: The seven Mines demo/real UI labels were already
present in the i18n manifest, but the old `MinesLegacyLabelsEditor` still kept a
separate compatibility tab alive.
**Why it matters**: BOXE must inherit platform features, not Mines debt. Closing
the Mines legacy editor makes the copy-manifest pattern symmetric without
creating a `BoxeLegacyLabelsEditor`.
**What we did**: Removed the Mines legacy labels editor mount/file and left the
runtime resolver manifest-first with legacy `ui_labels` fallback, so existing
published configs keep rendering the same labels.
**Affects**: `frontend/app/ui/mines/mines-backoffice-editor.tsx`,
`frontend/app/ui/mines/i18n/mines-copy-manifest.ts`,
`docs/BACKOFFICE_MANUAL.md`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`

### 2026-05-21 - WP-BO-CONTENT-RULES-PARITY
**Discovery / Decision**: BOXE aveva gia' sette sezioni regole e la shell
shared, ma i `body_html` runtime erano ancora paragrafi singoli. La parita' BO
richiede corpi ricchi, non solo manifest e container corretti.
**Why it matters**: Operatori e player devono vedere contenuti regole allineati
alla SPEC: bet/pick/collect, payout, fairness, piramide, difficolta e cap devono
essere auditabili senza deduzioni dal codice.
**What we did**: Arricchiti i sette `body_html` BOXE in `it/en/de/es` con
paragrafi, liste, esempi e note allineate a SPEC 1.7-1.10 e MATH_SPEC,
mantenendo inalterate chiavi, sezioni, UI, backend e Mines.
**Affects**: `frontend/app/ui/boxe/boxe-i18n/boxe-copy-defaults.ts`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`

### 2026-05-21 - WP-BO-OVERVIEW-DIAGNOSTICS
**Discovery / Decision**: BOXE had the shared Title Editor Overview container,
but it still exposed only a thin rows/difficulty card while Mines already gave
operators locale, draft/live, runtime and fairness diagnostics.
**Why it matters**: Backoffice parity must include the operator's diagnostic
surface, not only editable tabs. Without this view, BOXE could publish with
hidden copy/rules gaps or unclear math/fairness assumptions.
**What we did**: Added a BOXE Overview diagnostics component using existing
`activePayload`, `adminState` and `runtimeConfig`: published/default locale,
title, per-locale copy and seven-section rules coverage, RTP 98% fairness/math
summary, config rows/difficulty/defaults and draft/live state. Mines, backend,
validation, runtime, schema and migrations were left untouched.
**Affects**: `frontend/app/ui/boxe-backoffice/boxe-config-overview.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`docs/BACKOFFICE_MANUAL.md`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`

### 2026-05-21 - WP-BO-VALIDATION-PARITY
**Discovery / Decision**: After the Wave 5 copy expansion, BOXE had 169
frontend copy keys but validation still behaved like a thin string-list gate
and did not expose manifest metadata as clearly as Mines.
**Why it matters**: A shared editor shell is not enough if operators can miss
empty or overlong copy in the expanded runtime catalog. Full validation parity
keeps Surface 10 honest without touching Mines, backend or runtime behavior.
**What we did**: Added a BOXE frontend copy manifest/validation helper,
validated every locale/key for required and max length, surfaced structured
shared validation-panel issues with paths, and documented placeholder/format
metadata for template keys.
**Affects**: `frontend/app/ui/boxe/boxe-i18n/boxe-copy-manifest.ts`,
`frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`docs/BACKOFFICE_MANUAL.md`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`

### 2026-05-21 - WP-WAVE5-BO-COPY-MANIFEST-PARITY
**Discovery / Decision**: Surface 10 had the same false-green risk as the
rules modal: BOXE had a shared admin shell, but the copy editor still exposed
only the old partial key subset and one rules section.
**Why it matters**: Backoffice parity requires container, content, visual and
functional coverage. Operators must be able to inspect the same rich rules and
copy model the player UI renders.
**What we did**: Expanded the BOXE frontend copy catalog for `it/en/de/es`,
switched BOXE rules to seven Mines-structured sections with BOXE-specific
content, and made the BOXE backoffice hydrate/display the expanded catalog and
rules sections without touching Mines or the BOXE backend service.
**Affects**: `frontend/app/ui/boxe/boxe-i18n/boxe-copy-defaults.ts`,
`frontend/app/ui/boxe/boxe-rules-modal.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`docs/games/boxe/BACKOFFICE_PARITY_APPROACH_2026-05-20.md`,
`docs/BACKOFFICE_MANUAL.md`

### 2026-05-21 - WP-INFO-RULES-CONTENT-FOLLOW-UP
**Discovery / Decision**: Surface 5 was falsely marked green after WP-INFO
because BOXE inherited the shared modal shell but still rendered only the
single `bet_collect` rule paragraph.
**Why it matters**: A runtime surface is not green when the container is shared
but the game-specific content is partial. Future audits must verify both shell
and manifest/content parity.
**What we did**: Populated the BOXE frontend rules manifest for `it/en/de/es`
with seven sections adapted from SPEC, BRIEF and MATH_SPEC, and made the BOXE
modal adapter merge legacy runtime `rules_html` with those defaults.
**Affects**: `frontend/app/ui/boxe/boxe-i18n/boxe-copy-defaults.ts`,
`frontend/app/ui/boxe/boxe-rules-modal.tsx`,
`docs/games/boxe/INFO_RULES_PARITY_APPROACH_2026-05-21.md`

### 2026-05-21 - WP-REVEAL-WAVE-4B
**Discovery / Decision**: BOXE terminal reveal is server-authoritative but does
not need a new persisted board snapshot. The shipped math model is
probability-based per row/position, so Wave 4B derives `pyramid_full_reveal`
deterministically from the persisted server seed, client seed and nonce.
**Why it matters**: This preserves replay determinism without changing RTP,
schema or wallet/ledger behavior. It also gives WP-REPLAY a concrete payload
contract to consume later instead of asking replay to infer hidden cells.
**What we did**: Added terminal full-pyramid payloads for loss, cashout and
top-row win, exposed the same payload in replay, and made the BOXE board render
that payload only when the round is terminal.
**Affects**: `backend/app/modules/games/boxe/randomness.py`,
`backend/app/modules/games/boxe/service.py`,
`frontend/app/ui/boxe/boxe-gameplay.tsx`,
`frontend/app/ui/boxe/boxe-pyramid-board.tsx`,
`docs/games/boxe/REVEAL_FULL_PYRAMID_APPROACH_2026-05-21.md`,
`docs/games/boxe/SPEC.md`

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

### 2026-05-18 - WP-MINES-MATH-FIX-RTP-98
**Discovery / Decision**: La certification-ready pass retroattiva su Mines ha
surfaciato che la tabella runtime demo era circa 90% RTP, mentre il product
owner ha confermato il target demo 98% per allineamento cross-game con BOXE.
**Why it matters**: Il pattern sistema a 3 pezzi, MATH_SPEC + simulator esterno
+ stress framework, ha funzionato end-to-end: discovery, decisione product,
fix runtime e validazione parity/stress senza cambiare gameplay flow.
**What we did**: Mines math demo aggiornata da RTP 90% a 98% tramite formula
derivata dal success probability step-by-step; simulator, stress target e spec
Mines riallineati al runtime attivo.
**Generalization candidate**: Rendere il target RTP parametro per ambiente
(`rtp_demo` / `rtp_production`) e valutare l'aggiunta esplicita dei due campi in
`NEW_GAME_BRIEF_TEMPLATE.md` alla closure BOXE.

### 2026-05-18 - WP-FRONTEND-GAME-RUNTIME-AGNOSTIC
**Discovery / Decision**: BOXE 3A ha surfaciato il pattern speculare al backend
adapter: il frontend `game-runtime` era formalmente shared ma
`game-storage.ts` accettava solo il namespace `mines`. BOXE 3A resta in pausa
finche' il runtime storage non diventa whitelist-based.
**Why it matters**: Evita il workaround anti-pattern in cui BOXE avrebbe usato
lo storage namespace Mines. Il boot shell diventa realmente riusabile per il
secondo gioco e per HI-LO.
**What we did**: Audit completo di `frontend/app/ui/game-runtime/`, refactor di
`game-storage.ts` con `ALLOWED_GAME_NAMESPACES = ["mines", "boxe"]`, chiavi
Mines backward-compatible, chiavi BOXE dedicate, test contract per namespace
BOXE/reject non-whitelisted e boundary runtime/BOXE/Mines, atlas runtime
aggiornato.
**Affects**: `frontend/app/ui/game-runtime/game-storage.ts`,
`tests/contract/test_game_runtime_frontend_boundary.py`,
`tests/contract/test_game_runtime_storage.py`,
`docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`

Generalization candidate: Pre-Fase 3A frontend architecture mapping deve
verificare game-runtime hardcoding per nuovo gioco. Audit equivalente al
backend platform adapter audit.

### 2026-05-18 - WP-BOXE-3A-STANDALONE-BOOT
**Discovery / Decision**: 3A ha sbloccato dopo refactor frontend game-runtime
agnostic (`WP-FRONTEND-GAME-RUNTIME-AGNOSTIC`). Usare
`useGameLaunchContext` con namespace `boxe` ora e' supportato dalla whitelist.
Pattern simmetrico al backend.
**Why it matters**: Conferma che il pattern game-agnostic shell funziona
end-to-end: backend platform adapter + frontend game-runtime. Il risk
strutturale #1 del Playbook v0 e' ufficialmente esteso anche al frontend.
**What we did**: Page route `/boxe`, `BoxeStandalone` wrapper, content gates
BOXE-specific, table balance provvisorio, `BoxeGameplay` placeholder, contract
test boundary esteso e demo smoke minimal con rotation gate.
**Affects**: `frontend/app/boxe/`, `frontend/app/ui/boxe/`,
`tests/integration/test_boxe_smoke.py`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

Generalization candidate: Pre-Fase 3A frontend architecture mapping deve
includere game-agnosticity audit di `game-runtime/` (storage, context, audio,
theme, gates). Pattern: hardcoded namespace/game_code in qualsiasi file di
`game-runtime/` blocca nuovo gioco. Stesso pattern del backend audit pre-Fase
2D.

### 2026-05-18 - WP-BOXE-3B-GAMEPLAY
**Discovery / Decision**: Il gameplay BOXE resta interamente game-specific e
display-only rispetto a math/RNG/payout. Il backend non espone contenuto
nascosto delle righe: in loss il frontend mostra la mina selezionata e rende le
altre box della riga corrente `opaque`, senza inventare diamond/mine nascosti.
**Why it matters**: Mantiene la separazione certificabile: backend owner di
outcome/payout/fairness, frontend owner solo di stato visivo, retry idempotente
e controlli player.
**What we did**: Board piramide 4-8 righe, payout ladder, settings
rows/difficulty, bet/collect panel, state handling start/reveal/cashout con
UUID idempotency key, copy defaults `it/en/de/es`, demo smoke per
cashout/loss/top-row/retry.
**Affects**: `frontend/app/ui/boxe/`,
`tests/integration/test_boxe_smoke.py`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

### 2026-05-18 - WP-BOXE-3C-ANIMATIONS-POLISH
**Discovery / Decision**: Le animazioni BOXE sono state implementate come
layer puramente visuale sopra lo state model 3B. Audio event hook presente ma
silenzioso finche' non arrivano asset sonori dedicati, senza estendere
`game-runtime`.
**Why it matters**: Mantiene separazione certificabile tra outcome/payout
backend e feedback frontend. Reduced motion e visual baseline rendono la polish
verificabile senza introdurre timing gameplay fragile.
**What we did**: Aggiunte reveal animation safe/mine, pill slide payout,
current-row opaque stagger su loss, win celebration cashout/top-row, hook audio
BOXE, reduced-motion CSS, visual baseline BOXE desktop/mobile e smoke esteso
per audio/reduced-motion.
**Affects**: `frontend/app/ui/boxe/`,
`tests/integration/test_boxe_smoke.py`,
`tests/integration/test_boxe_visual_regression.py`,
`tests/visual/baselines/boxe_3c/`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

### 2026-05-18 - WP-PLATFORM-TITLE-EDITOR-AGNOSTIC
**Discovery / Decision**: BOXE 4A ha surfaciato la terza occorrenza del
pattern game-agnosticity dopo backend platform adapter e frontend game-runtime
storage. La shell Title Editor era Mines-shaped in 5 punti: registry, types,
command bar actions, config loading e fairness diagnostics.
**Why it matters**: BOXE 4A puo' restare un plugin game-specific senza
modificare la shell platform. Il refactor rende il Title Editor ospitabile per
HI-LO e giochi futuri senza workaround Mines.
**What we did**: Refactor whitelist-based con registry lazy `mines`/`boxe`,
`EngineEditorProps<TConfig>` generico, command bar `admin-${engineCode}`,
runtime config caricata da `/games/${engineCode}/config`, diagnostics slot per
engine e stub `BoxeEngineEditor` accessibile dal Title Editor.
**Affects**: `frontend/app/ui/title-editor/`,
`frontend/app/ui/casinoking-console.tsx`,
`frontend/app/ui/mines/mines-engine-diagnostics.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`tests/contract/test_title_editor_agnostic.py`,
`tests/integration/test_title_editor_agnostic_frontend.py`,
`docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`

Generalization candidate: Pre-Fase 4A title-editor agnosticity audit step
obbligatorio in Playbook v1.

### 2026-05-18 - WP-BOXE-4A-ADMIN-CONFIG-COPY
**Discovery / Decision**: 4A ha sbloccato dopo
`WP-PLATFORM-TITLE-EDITOR-AGNOSTIC`. Lo stub BOXE engine editor creato dal
refactor platform e' stato espanso in editor completo con config
rows/difficulty, copy/rules HTML, draft/publish e validation.
**Why it matters**: L'operatore puo' configurare BOXE end-to-end nel
backoffice. Il pattern admin Title Editor multi-game e' confermato con il
primo plugin non-Mines concreto.
**What we did**: Backend `boxe_admin_config` schema + endpoint admin,
frontend admin editor BOXE con tabs e workflow draft/publish, integrazione del
runtime config endpoint su `published_payload`, audit log publish, manuale
backoffice e atlas aggiornati.
**Affects**: `backend/app/modules/games/boxe/`,
`backend/migrations/sql/0040__boxe_admin_config.sql`,
`backend/app/api/routes/admin.py`, `frontend/app/ui/boxe-backoffice/`,
`frontend/app/ui/boxe/use-boxe-runtime.ts`, `docs/BACKOFFICE_MANUAL.md`,
`docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md`

### 2026-05-18 - WP-BOXE-4B-5-6-COMPLETAMENTO
**Discovery / Decision**: 4B+5+6 sono stati chiusi in un WP combinato. BOXE
riusa `game_card`, `symbol_safe` e `symbol_mine` invece di introdurre asset
kind duplicati; i sounds custom restano deferred/default v1. Catalog seed
registra `boxe` master e `boxe001` variant; il player lobby/Launch Cashier
routea BOXE verso `/boxe` per demo, real cash e bonus.
**Why it matters**: BOXE diventa pubblicabile e lanciabile end-to-end dal
backoffice e dalla lobby senza nuove estensioni platform. Conferma che asset
registry, Site/Lobby, Launch Cashier e theme shared scalano al secondo gioco.
**What we did**: Aggiunti tab BOXE Assets e Theme, migration seed catalog
0041, wiring lobby route game-specific, preview admin route game-specific,
test asset/theme/lobby launch, atlas BOXE finale ACTIVE, manuale backoffice e
README aggiornati.
**Affects**: `frontend/app/ui/boxe-backoffice/`,
`frontend/app/ui/player-lobby-page.tsx`,
`frontend/app/ui/casinoking-console.tsx`, `backend/app/api/routes/admin.py`,
`backend/migrations/sql/0041__boxe_catalog_seed.sql`,
`docs/ARCHITECTURE_ATLAS_BOXE.md`, `docs/BACKOFFICE_MANUAL.md`,
`docs/README.md`

### 2026-05-18 - WP-BOXE-7-E2E-VALIDATION
**Discovery / Decision**: BOXE e' funzionalmente completo dopo 4B+5+6; la
Fase 7 resta validation-only. L'atlas ACTIVE e' stato verificato contro il
delivered e corretto dove conservava descrizioni storiche di 2C/3A
("wallet/frontend out of scope", cashout senza settlement, placeholder 3A).
**Why it matters**: Chiude il contratto end-to-end prima della distillazione:
boot, demo, real cash, bonus, loss, top-row, retry, visual, Mines regression,
finance/replay/history e checklist manuale sono tracciati come gate finale,
senza introdurre nuove feature.
**What we did**: Esteso smoke browser BOXE ai launch mode demo/real cash/real
bonus e ai wallet settlement real/bonus, creato manual playthrough checklist,
verificato/aggiornato atlas ACTIVE, aggiornato il test isolation 2B per convivere
con tabelle BOXE successive, refresh Mines visual baseline post RTP 98% e
riesecuzione regression/contract suite.
**Affects**: `tests/integration/test_boxe_smoke.py`,
`tests/integration/test_boxe_state_machine.py`,
`docs/games/boxe/MANUAL_PLAYTHROUGH_CHECKLIST.md`,
`docs/ARCHITECTURE_ATLAS_BOXE.md`, `docs/README.md`,
`tests/visual/baselines/mines_classic/`,
`tests/visual/baselines/boot_2a/`

### 2026-05-19 - WP-BOXE-CLOSURE
**Discovery / Decision**: BOXE e' formalmente chiuso: il gioco e'
funzionalmente completo/E2E-validato e il deliverable metodologico e' stato
distillato in Playbook v1 + Template v1.
**Why it matters**: HI-LO parte con audit game-agnosticity upfront, template piu'
ricco e costo stimato 40-50% inferiore a BOXE per la parte metodologica, se non
emergono nuovi gap platform.
**What we did**: Distillazione completa dell'Implementation Log, tracking del
`BOXE_PROJECT_BRIEF.md`, aggiornamento Playbook/Template/Capability
Inventory/Game Runtime Atlas/README, creazione closure report e formalizzazione
dei pending production RTP.
**Affects**: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`,
`docs/NEW_GAME_BRIEF_TEMPLATE.md`,
`docs/CAPABILITY_INVENTORY_2026-05-17.md`,
`docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`,
`docs/BOXE_PROJECT_BRIEF.md`, `docs/games/boxe/CLOSURE_REPORT.md`

### 2026-05-19 - WP-BOXE-SHELL-UNIFORMITY-FIX
**Discovery / Decision**: L'audit ha confermato che BOXE consuma
`GameBootShell`, ma passa superfici pre-game locali per Provider Intro,
How-To-Play layout e Table Balance Gate. La divergenza e' strutturale, non un
semplice token/CSS drift.
**Why it matters**: Il product contract richiede uguaglianza visiva nella zona
protetta lobby -> cashier -> boot -> game ready. Un fix BOXE-only creerebbe un
fork nascosto o violerebbe il boundary BOXE/Mines; la correzione pulita richiede
un WP platform/shared dedicato.
**What we did**: Creato audit read-only con evidence file/line, root cause per
fase e stop recommendation. Nessun codice runtime modificato; Step 2 e' sospeso
finche' non viene autorizzata l'estrazione platform/shared delle superfici
pre-game.
**Affects**: `docs/games/boxe/SHELL_UNIFORMITY_AUDIT_2026-05-19.md`

### 2026-05-19 - WP-BOXE-TABLE-SESSION-LIFECYCLE-PARITY Parte A
**Discovery / Decision**: L'approach validation ha confermato che BOXE ha gia'
FK nullable verso `game_access_sessions` e `game_table_sessions` su
`boxe_sessions`, mentre `platform_rounds` ha gia' `table_session_id`; non serve
migration per la parity richiesta.
**Why it matters**: Il debito e' nel wiring lifecycle, non nella platform API:
BOXE puo' consumare il pattern table balance Mines senza toccare Mines e senza
estendere `platform/table_sessions`.
**What we did**: Creato il documento di approach con payload additivo,
diagramma state-machine, scope adapter, test plan e stop-and-ask prima della
Parte B. Nessun codice runtime modificato.
**Affects**: `docs/games/boxe/TABLE_SESSION_LIFECYCLE_APPROACH_2026-05-19.md`

### 2026-05-19 - WP-PLATFORM-PREGAME-SHELL-EXTRACTION
**Discovery / Decision**: BOOT-2A.6 aveva estratto lo scaffolding shell, ma non
le implementazioni pre-game reali. Mines manteneva implementazioni locali;
BOXE 3A aveva replicato il pattern con fork locali invece di consumare
implementazioni shared. Lo Stop-and-Ask Step 3 ha rivelato un submit lifecycle
Table Balance asimmetrico: BOXE backend non supporta ancora `table_session_id`.
Decisione CTO: shell visual shared, submit lifecycle come callback
game-specific; il debito BOXE va in `WP-BOXE-TABLE-SESSION-INTEGRATION`.
**Why it matters**: La platform ora e' game-agnostic anche al livello
implementazione shell pre-game, non solo scaffolding. HI-LO potra' partire con
provider intro, how-to-play e table balance shared funzionanti. Il pattern
callback evita di forzare backend symmetry quando i consumer non sono ancora
allineati.
**What we did**: Estratti Provider Bootstrap, How-To-Play Gate e Table Balance
Gate da Mines-local a `game-runtime/`. Refactor Mines per consumare shared
senza cambiare comportamento funzionale o baseline visuale; refactor BOXE per
consumare le stesse implementazioni e rimuovere fork/CSS pre-game. Pulizia CSS
step-by-step su entrambi i lati, con Table Balance visual shared e callback
specifica Mines/BOXE. Step 5 ha allineato anche il gate sequencing BOXE
real-mode al reference Mines: Table Balance -> Provider Intro -> How-To ->
Gameplay, senza modifiche backend/API.
**Affects**: `frontend/app/ui/game-runtime/`, `frontend/app/ui/mines/`,
`frontend/app/ui/boxe/`, `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`,
`docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/ARCHITECTURE_ATLAS_BOXE.md`

Generalization candidates per Playbook v2 distillation post-merge:

- Estrarre scaffolding shell senza estrarre implementazioni e' incompleto.
- Pattern shared shell + game-specific visual.
- Pattern shared visual + game-specific submit callback.
- CSS scoped residuo post-extraction: cleanup deve coprire entrambi i lati,
  gioco target e gioco di riferimento.
- Pre-Fase 3A audit upgrade: verificare consume effettivo e backend lifecycle
  symmetry.
- Nuovi giochi devono replicare il gate sequencing del reference game Mines;
  l'audit pre-Fase 3A deve verificare anche l'ordine del flow, non solo visual
  e CSS.

### 2026-05-19 - WP-TITLE-EDITOR-TABS-SHARED-EXTRACTION Parte A
**Discovery / Decision**: L'audit dei tab admin Mines ha confermato che la
shell Title Editor e il command bar sono gia' buoni, ma i tab non hanno tutti
la stessa natura: copy/rules/assets/theme sono descriptor-driven, config
richiede adapter, fairness e legacy Demo/Real labels restano capability
Mines-specific.
**Why it matters**: Estrarre "8 tab" in un solo colpo rischierebbe di rompere
la baseline Mines e di forzare BOXE dentro una shape Mines. Il pattern corretto
per giochi 3-20 e' shared tab renderer + engine schema/adapter + capability
flags, non branch `if boxe/mines` nella platform.
**What we did**: Creato approach doc Parte A con coupling table, schema
TypeScript proposto, piano Parte B in 3 sub-WP, decisione registry e
Stop-and-Ask attesi. Nessun codice, endpoint, schema, migration o gameplay e'
stato modificato.
**Affects**:
`docs/games/boxe/TITLE_EDITOR_TABS_EXTRACTION_APPROACH_2026-05-19.md`,
`frontend/app/ui/title-editor/`, `frontend/app/ui/mines/`,
`frontend/app/ui/boxe-backoffice/`

### 2026-05-19 - WP-TITLE-EDITOR-TABS-SHARED-EXTRACTION B1
**Discovery / Decision**: B1 e' stata implementata come wrapper extraction per
Mines e renderer shared reale per BOXE. Questo mantiene stabile la baseline
Mines mentre introduce `TitleEditorTabFrame`, status, validation, overview e
config tab sotto `title-editor/tabs`.
**Why it matters**: Il primo slice conferma il boundary corretto: shared tabs
renderizzano layout e field descriptor, mentre i plugin engine mantengono
schema, adapter e orchestrazione API. Nessun endpoint o schema backend cambia.
**What we did**: Mines consuma status/tab frame e overview/config wrappers;
BOXE consuma overview/config/validation shared per rows/difficulty. Aggiunto
contract test per impedire branch `mines/boxe` nei tab shared e aggiornato il
manuale backoffice.
**Affects**: `frontend/app/ui/title-editor/tabs/`,
`frontend/app/ui/mines/mines-backoffice-editor.tsx`,
`frontend/app/ui/mines/mines-config-overview.tsx`,
`frontend/app/ui/mines/mines-grid-config-editor.tsx`,
`frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`,
`tests/contract/test_title_editor_agnostic.py`,
`docs/BACKOFFICE_MANUAL.md`

### 2026-05-19 - WP-BOXE-TABLE-SESSION-LIFECYCLE-PARITY Parte B
**Discovery / Decision**: BOXE poteva gia' usare la pipeline table-session
platform, ma route/service non propagavano `table_session_id` e
`access_session_id`; il frontend mostrava il gate tavolo come placeholder.
Decisione CTO confermata: BOXE real mode e' strict, quindi cash/bonus senza
`table_session_id` viene rigettato con `VALIDATION_ERROR`.
**Why it matters**: BOXE ora usa lo stesso lifecycle economico reale della
platform: access session, table session, round platform, riserva limite tavolo
e saldo wallet. Il demo resta backward compatible e Mines resta lazy/legacy
senza cambio funzionale.
**What we did**: Esteso payload `/games/boxe/start`, service BOXE e response
additiva; collegato `BoxeStandalone` a `/table-sessions/limits`,
`/access-sessions` e `/table-sessions`; `startBoxeRound` invia i nuovi id e
aggiorna la table session dalla response. Aggiunti test integration per cash,
bonus, reject strict, demo e mismatch.
**Affects**: `backend/app/api/routes/boxe.py`,
`backend/app/modules/games/boxe/service.py`,
`frontend/app/ui/boxe/boxe-standalone.tsx`,
`frontend/app/ui/boxe/use-boxe-runtime.ts`,
`frontend/app/ui/boxe/boxe-gameplay.tsx`,
`tests/integration/test_boxe_api.py`

### 2026-05-20 - WP-V-VISUAL-UNIFORMITY Parte B
**Discovery / Decision**: CTO ha confermato che Mines resta reference intoccato:
BOXE deve ereditare primitive visual condivise senza introdurre header, badge o
stati BOXE-only.
**Why it matters**: La parita' visuale player-facing non si ottiene copiando una
seconda shell nel gioco nuovo. Le differenze non presenti in Mines diventano
debito prodotto e vanno rimosse, non giustificate localmente.
**What we did**: Aggiunte primitive visual opt-in in `game-runtime`, BOXE consuma
top bar/chip/action/footer shared, rimuovendo RTP tag, eyebrow `title_code` e
round status footer. Aggiornato lo smoke che dipendeva dal testo `98% RTP` e
prodotta evidence side-by-side in sei stati.
**Affects**: `frontend/app/ui/game-runtime/`,
`frontend/app/ui/boxe/boxe-standalone.tsx`,
`frontend/app/ui/boxe/boxe-gameplay.tsx`,
`frontend/app/ui/boxe/boxe-settings-panel.tsx`,
`frontend/app/ui/boxe/boxe.css`,

### 2026-05-20 - WP-G-GAMEPLAY-BOARD-PYRAMID Parte B
**Discovery / Decision**: CTO ha approvato una piccola estensione backend BOXE
per allineare le `next_step_options` alla geometria visuale della piramide:
`cells_for_row(row, rows) = rows - row + 1`, indipendente dalla difficulty.
**Why it matters**: La board non e' piu' una griglia rettangolare 3xN mascherata.
Il frontend e il payload API ora parlano lo stesso linguaggio di posizioni per
riga senza riaprire il contratto math: probabilita' e multiplier restano in
`math.py`.
**What we did**: Board BOXE a celle variabili bottom-to-top, righe centrate,
active row evidenziata, future rows coperte, safe/mine reveal con asset
fallback versionati in `frontend/public/game-assets/boxe/`. Aggiornato smoke
BOXE e prodotto evidence screenshot 4/6/8 rows per easy/medium/hard.
**Affects**: `frontend/app/ui/boxe/boxe-pyramid-board.tsx`,
`frontend/app/ui/boxe/boxe.css`, `frontend/app/ui/boxe/boxe-payout-display.tsx`,
`backend/app/modules/games/boxe/service.py`,
`tests/integration/test_boxe_smoke.py`

### 2026-05-21 - WP-RTP-WAVE4-PARTE-B
**Discovery / Decision**: La verifica RTP finale deve separare formula esatta,
campionamento variance-reduced e Monte Carlo naive informativo. La Monte Carlo
naive non e' un gate valido per hard/high-row perche' puo' produrre outlier
oltre 2pp anche quando il modello esatto resta 98%.
**Why it matters**: Protegge `math.py` da fix non necessari guidati da varianza
statistica e lascia una procedura riproducibile per audit CTO, CI locale e
futuri giochi con payout rari.
**What we did**: Aggiunto verifier standalone con matrice esatta per 15
configurazioni, importance-sampling stratificato per early/typical/top,
appendice naive report-only e report finale con raccomandazione no-fix.
**Affects**: `tools/boxe_rtp_verify.py`,
`backend/tests/unit/test_boxe_rtp_verify.py`,
`docs/games/boxe/ENGINE_RTP_VERIFY_APPROACH_2026-05-21.md`,
`docs/games/boxe/ENGINE_RTP_VERIFY_REPORT_2026-05-21.md`

### 2026-05-21 - WP-INFO-WAVE-4-PARTE-B
**Discovery / Decision**: Il pulsante runtime `i` non e' un alias del gate
How To Play: per BOXE deve aprire la stessa superficie regole usata da Mines,
mentre il replay resta nascosto finche' WP-REPLAY non fornisce un viewer reale.
**Why it matters**: Separare onboarding e regole runtime evita una divergenza
player-facing sulla superficie 5/7 del Playbook. Il nuovo shell condiviso
impedisce di copiare una seconda modale locale per i prossimi giochi.
**What we did**: Estratto `GameInfoRulesModal` in `game-runtime`, lasciando Mines
come adapter visualmente invariato; BOXE aggiunge `BoxeRulesModal` con
`presentation_config.rules_html` e copy fallback, rimuovendo il reset HTP dal
trigger info. Aggiunti test boundary/smoke per replay nascosto e separazione HTP.
**Affects**: `frontend/app/ui/game-runtime/game-info-rules-modal.tsx`,
`frontend/app/ui/mines/mines-rules-modal.tsx`,
`frontend/app/ui/boxe/boxe-rules-modal.tsx`,
`frontend/app/ui/boxe/boxe-gameplay.tsx`,
`docs/games/boxe/INFO_RULES_PARITY_APPROACH_2026-05-21.md`

### Distillazione finale (a chiusura BOXE)

Checklist obbligatoria prima di dichiarare BOXE chiuso (vedi anche
`docs/BOXE_PROJECT_BRIEF.md` § 11):

- [x] Tutte le entry del log sono state riviste
- [x] Le decisioni ricorrenti sono diventate default nel `NEW_GAME_BRIEF_TEMPLATE.md`
- [x] Gli anti-pattern emersi sono stati formalizzati nel `NEW_GAME_INTEGRATION_PLAYBOOK.md` Anti-Pattern Catalog
- [x] Le naming convention adottate sono documentate nel Playbook
- [x] I rischi strutturali emersi sono nel Playbook Known Structural Risks
- [x] Eventuali estensioni platform sono documentate e referenziate
- [x] Template e' abbastanza ricco da permettere a un product owner di compilarlo per gioco 3 (HI-LO) senza riaprire le stesse discussioni metodologiche

---

## Riferimenti

- Metodologia: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- Template di input: `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- Brief progetto BOXE storico/metodologico: `docs/BOXE_PROJECT_BRIEF.md`
- Closure report BOXE: `docs/games/boxe/CLOSURE_REPORT.md`
- Capability platform riusabili: `docs/CAPABILITY_INVENTORY_2026-05-17.md`
- Architettura runtime shell: `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`
- Gioco di riferimento: `docs/ARCHITECTURE_ATLAS_MINES.md`
- Recovery policy: `docs/SESSION_RECOVERY_ENGINE_DESIGN.md`
- Regole permanenti: `docs/TASK_EXECUTION_GUARDRAILS.md`
- Audit shell pre-BOXE: `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md`
