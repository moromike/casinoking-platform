Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Project Brief

Documento di progetto BOXE come primo caso reale di metodo riusabile per aggiungere giochi proprietari alla piattaforma CasinoKing.

Stato: reference storica attiva. Il piano e' stato eseguito e chiuso con
`WP-BOXE-CLOSURE`; il risultato finale e la distillazione vivono in
`docs/games/boxe/CLOSURE_REPORT.md`, `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
v1 e `docs/NEW_GAME_BRIEF_TEMPLATE.md` v1.

---

## 1. Obiettivo del progetto

BOXE non è solo "il secondo gioco". È il primo caso reale a cui applichiamo un metodo riusabile per portare sulla piattaforma i prossimi otto giochi proprietari.

Il deliverable di questo progetto è doppio:

1. **BOXE in produzione**: gioco funzionante, demo + real + bonus, gestibile dal backoffice e giocabile dal player site.
2. **Playbook documentato**: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`, battle-tested durante BOXE, riusabile per i giochi successivi.

Se a fine progetto abbiamo BOXE ma non abbiamo il Playbook, il progetto è riuscito a metà. Se per il gioco numero tre dobbiamo rifare le stesse discussioni metodologiche fatte per BOXE, il Playbook ha fallito.

## 2. Principio guida

**Riuso massimo. Rifacciamo solo l'indispensabile.**

Tutto ciò che la piattaforma offre già va usato così com'è. Niente duplicazione, niente "versioni BOXE" di componenti esistenti.

Capability platform già pronte e che NON vanno duplicate:

- game-runtime shell (decision flow, provider intro gate, how-to-play gate, table balance gate)
- audio infrastructure (post BOOT-2A.3)
- i18n system (manifest + copy resolver)
- theme system (tokens + advanced skin)
- fairness (server-side, deterministic)
- history / replay infrastructure
- table session API
- Launch Cashier (player lobby modal, ripristinato post recovery)
- wallet integration (read-only su /wallets, niente mutazioni dal gameplay)
- storage / launch context
- Game Adapter (platform round, finance, ledger)

Capability gioco-specifiche che vanno scritte nuove per BOXE:

- piramide layout e progressione riga-per-riga
- math e RNG specifici BOXE
- payout calculation BOXE
- asset (board, animazioni, sounds)
- copy player (regole, etichette UI)
- settings configurabili da operatore (rows, difficulty)
- max win cap BOXE-specifico

Se durante l'implementazione emerge il bisogno di estendere la platform shell, **STOP**: decisione architetturale separata, analisi, decisione esplicita, poi avanti. Non si estende la platform "al volo".

## 3. Input disponibile e cosa serve nello SPEC

L'analisi attuale è in `games/boxe/analisi/`:

- documento GDD funzionale (.docx)
- screenshot di riferimento (boxe1-7)

Lo SPEC di Fase 0 deve consolidare **undici blocchi obbligatori**. Se uno è incompleto nell'analisi attuale, va chiusa la lacuna prima di toccare codice. Senza questi blocchi, le decisioni tecniche finiscono dentro al codice invece che nel contratto.

### 3.1 Regole di gioco

- RNG: come si genera il round (seed, nonce, fairness deterministica server-side)
- Math: numero di rows, livelli di difficulty, multipliers per ogni step
- Payout: come si calcola il payout per riga raggiunta
- Condizioni: vittoria, perdita, cashout
- Max win cap: valore BOXE-specifico

### 3.2 Layout visuale

- Proporzioni piramide
- Rows configurabili?
- Posizione score, bet, cashout buttons
- Stati visivi: idle, playing, won, lost, reveal
- Animazioni richieste: reveal cella, ascensore verso la riga superiore, esplosione/punch su perdita

### 3.3 Settings configurabili da operatore

- Cosa si configura dal Title Editor (rows? difficulty? entrambe? niente?)
- Cosa è hardcoded
- Cosa è draft vs live

### 3.4 Vincoli product espliciti

- Demo abilitato sì/no
- Real abilitato sì/no
- Bonus wallet supportato sì/no
- Lingue al lancio
- Asset filesystem statici vs caricabili da admin

### 3.5 State machine backend BOXE

- Stati possibili di un round (es. created, active, row_revealed, cashout_pending, completed, failed, expired)
- Transizioni ammesse tra stati e quali sono illegali
- Comportamento su retry: cosa succede se il frontend ritenta una reveal/cashout
- Comportamento su reveal concorrente: due click sullo stesso step, come si serializzano
- Comportamento su cashout concorrente: cashout mentre reveal è in volo
- Comportamento su round già chiuso: errore esplicito o noop idempotente
- Timeout/expiry: dopo quanto un round abbandonato si chiude

### 3.6 Idempotency contract

- Quali endpoint richiedono idempotency key
- Formato della key (chi la genera, lato client o server)
- Comportamento atteso se la stessa key arriva due volte: stesso esito o errore
- Conservazione delle key (TTL, scope di sessione)
- Comportamento se ritento start dopo timeout senza risposta

### 3.7 Rounding, precision e cap

- Precisione dei moltiplicatori (decimali ammessi)
- Regole di rounding per i chip (banker's rounding, troncamento, eccetera)
- Interazione tra payout teorico e max win cap: cosa succede se il payout calcolato eccede il cap
- Interazione tra max win cap di sessione e limite singolo round
- Visualizzazione del cap nel client: trasparente o nascosto

### 3.8 Replay e history contract

- Cosa si salva per replay (sequenza decisioni, stato finale, seed/nonce)
- Cosa vede il player nello storico account
- Cosa vede il finance nel drilldown round
- Come si ricostruisce visivamente una piramide a round chiuso
- Quale formato dati lega replay viewer e backend

### 3.9 Admin config lifecycle

- Default del master title BOXE
- Comportamento draft vs live: dove i round attivi pescano la config
- Cosa succede ai round già aperti se cambio rows/difficulty/max win nel draft
- Cosa succede ai round già aperti al momento del publish live
- Audit di chi ha pubblicato cosa e quando

### 3.10 Asset contract

- Formati ammessi per board, sounds, lobby card, theme skin assets (PNG/JPEG/WebP, MP3/WAV)
- Limiti di peso per kind
- Dimensioni consigliate
- Comportamento di fit visuale: cover, contain, no-stretch
- Validazione client e backend
- Messaggi di errore esplicitamente leggibili dall'operatore

### 3.11 Failure UX

Tutti gli scenari di errore visibili al player o all'operatore devono essere specificati:

- Config gioco mancante
- Title non pubblicato
- Table session scaduta o invalida
- Saldo insufficiente
- Wallet bonus vuoto
- Rete lenta o intermittente
- Backend irraggiungibile
- Round già chiuso e ritenta cashout

## 4. Fasi di esecuzione

Sette fasi macro, alcune con sotto-WP per evitare PR troppo grandi. Ogni fase produce un output, ha un criterio di "fase chiusa", e si valida prima di passare alla successiva.

### Fase 0 — Discovery & Spec

- **Output**: `docs/games/boxe/SPEC.md`
- Contiene tutti gli undici blocchi del §3
- **Owner**: product, con stress-test tecnico
- **Criterio chiusura**: nessuna domanda aperta product. Se manca anche solo un multiplier o un comportamento failure UX, non si chiude.

### Fase 1 — Architecture Mapping

- **Output**: matrice "comune vs specifico vs estensione" + lista WP per le Fasi 2-7
- Comune = riusa platform shell senza modifiche
- Specifico = nuovo codice in `frontend/app/ui/boxe/` e `backend/app/modules/games/boxe/`
- Estensione platform = decisione architetturale separata, da minimizzare. Se ne emerge una, va trattata in un WP dedicato e approvata prima di Fase 2.
- **Criterio chiusura**: matrice approvata. Ogni voce della matrice ha categoria (comune/specifico/estensione) e WP di riferimento.

### Fase 2 — Backend Foundation (split in 4 WP)

#### Fase 2A — Math / RNG / Fairness puro

- Math BOXE in isolamento (nessuna dipendenza wallet/platform)
- RNG deterministico server-side
- Test fairness con seed fissi e payout attesi
- **Output**: PR backend math puro con capability matrix
- **Criterio chiusura**: fairness verde, payout calcolati corretti per tutti i cap, edge case (max win cap, rounding) coperti

#### Fase 2B — Schema DB + Repository + State Machine

- Migration per `game_boxe_sessions`, `game_boxe_rounds` (o equivalenti, da decidere in Fase 1)
- Repository pattern per persistere stati
- State machine: implementa stati e transizioni del §3.5
- Test integration su transizioni illegali, concurrent reveals, idempotency primitive
- **Output**: PR DB + state machine
- **Criterio chiusura**: state machine copre tutti i casi del §3.5, test concurrent passano

#### Fase 2C — API endpoints

- Endpoint: session start, reveal step, cashout, replay
- Idempotency key implementata come da §3.6
- Failure UX come da §3.11
- Test integration per ogni endpoint
- **Output**: PR API
- **Criterio chiusura**: tutti gli endpoint hanno test, error path coperti

#### Fase 2D — Game Adapter + Platform + Finance + Replay wiring

- Aggancio al Game Adapter platform per platform round
- Ledger wiring (wallet read-only, mutazioni passano per Game Adapter)
- Finance round drilldown popolato per round BOXE
- Replay infrastructure popolata
- i18n manifest backend con copy keys BOXE
- **Output**: PR wiring platform
- **Criterio chiusura**: round BOXE compare in finance, replay leggibile, wallet/ledger non toccati direttamente da BOXE

### Fase 3 — Frontend Gameplay (split in 3 WP)

#### Fase 3A — BoxeStandalone + boot + demo smoke

- Componente `boxe-standalone.tsx` che usa game-runtime shell
- Decision flow, intro, how-to, cashier sono platform: non si duplicano
- Demo smoke minimale: il gioco si apre, mostra placeholder, accetta una mossa
- **Output**: PR standalone bootstrap
- **Criterio chiusura**: demo smoke verde, contract test verde

#### Fase 3B — Gameplay piramide

- Layout piramide
- Stati visivi (idle/playing/won/lost/reveal)
- Progressione riga-per-riga
- Score/bet/cashout display
- i18n copy keys BOXE in `frontend/app/ui/boxe/i18n/`
- **Output**: PR gameplay piramide
- **Criterio chiusura**: round demo giocabile end-to-end senza animazioni

#### Fase 3C — Animazioni e polish

- Animazione reveal cella
- Animazione ascensore verso riga superiore
- Animazione esplosione/punch su perdita
- Win celebration coerente con pattern Mines
- **Output**: PR animations
- **Criterio chiusura**: animazioni fluide, niente regressioni gameplay

### Fase 4 — Title Editor Integration (split in 2 WP)

#### Fase 4A — Config / Copy / Rules

- Sezione admin per BOXE nel Title Editor
- Settings editor specifico BOXE (rows/difficulty se configurabili)
- Copy/i18n editor
- Rules HTML editor
- Aggiornamento `docs/BACKOFFICE_MANUAL.md`: sezione BOXE config/copy/rules
- **Output**: PR admin config
- **Criterio chiusura**: workflow operatore config funzionante, manuale aggiornato

#### Fase 4B — Assets / Sounds / Theme / Lobby card

- Board assets BOXE-specifici
- Sounds BOXE-specifici
- Theme tokens (riusa pattern Mines, niente di nuovo se non strettamente necessario)
- Lobby card BOXE
- Aggiornamento `BACKOFFICE_MANUAL.md`: sezione BOXE assets/sounds/theme
- **Output**: PR admin assets
- **Criterio chiusura**: upload/preview/delete funzionanti, manuale aggiornato

### Fase 5 — Site/Lobby Integration

- Title BOXE pubblicabile su site
- Card lobby renderizzata
- Launch Cashier già pronto a lanciare BOXE (è platform, non va toccato)
- Routing `/boxe?title_code=...&mode=demo|wallet_source=real|bonus`
- **Output**: PR lobby (piccola: gran parte è già fatta dalla shell)
- **Criterio chiusura**: lancio demo + real + bonus end-to-end funzionante

### Fase 6 — Documentation

- `docs/ARCHITECTURE_ATLAS_BOXE.md` (analogo a `ARCHITECTURE_ATLAS_MINES.md`)
- Aggiornamento `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` solo se la shell ha richiesto estensioni in Fase 1
- Aggiornamento `BACKOFFICE_MANUAL.md` finale (può stare in Fase 4 per evitare PR docs separato)
- **Output**: PR docs (o inglobato in Fase 4/5)
- **Criterio chiusura**: nessuna capability BOXE senza documentazione

### Fase 7 — End-to-end Validation

- Smoke browser BOXE
- Visual regression baseline BOXE (non solo smoke)
- Manual playthrough: demo + real + bonus, testati SEPARATAMENTE
- Operatore prova flow completo: backoffice → publish → player gioca → finance vede il round → replay leggibile
- Smoke Mines: verde (zero regressioni sul gioco esistente)
- **Output**: test verdi + OK product
- **Criterio chiusura**: nessun bug bloccante, BOXE in produzione

## 5. Analisi preliminari necessarie

Prima di aprire WP, servono tre analisi tecniche.

### 5.1 Gap analysis sull'input

Confronto tra cosa serve nello SPEC (§3, undici blocchi) e cosa è effettivamente coperto dall'analisi attuale in `games/boxe/analisi/`.

**Output**: lista di domande product da chiudere prima di Fase 0. Se l'analisi copre tutto, l'output è vuoto e si passa direttamente alla stesura formale dello SPEC.

### 5.2 Architecture mapping vs Mines

Verifica concreta che ogni capability platform usata da Mines funzioni anche per BOXE senza estensioni. Per ogni capability:

- riuso atteso al 100% sì/no
- se no: descrivere il delta e proporre se trattarlo come capability specifica BOXE (preferibile) o come estensione platform (eccezionale, va giustificata)

Capability da verificare una a una:

**Runtime e shell**:

- game-runtime decision flow
- game-runtime provider intro gate
- game-runtime how-to-play gate
- game-runtime table balance gate
- audio infra
- i18n system
- theme system (tokens + advanced skin)
- fairness server-side
- history / replay infra
- table session API
- Launch Cashier
- wallet integration (read-only)
- storage / launch context
- Game Adapter (platform round, finance, ledger)

**Catalogo e admin**:

- Catalog/Engine/Title/Site seeding: engine boxe, master title, site title defaults
- Preview launch admin: BOXE deve supportare preview come Mines?
- Admin audit log: publish config/theme/assets/lobby per BOXE
- Asset registry kinds: decidere se generici per game o boxe_*

**Finance**:

- Finance reporting/drilldown: come appaiono round BOXE, display id, movement labels

**Test e contratti**:

- Visual regression baseline (non solo smoke): screenshot di riferimento BOXE
- Contract test anti-import bidirezionali: boxe non importa mines E game-runtime non importa boxe

**Routing**:

- Route ownership: `/boxe` e Launch Cashier devono essere platform-compatible senza eccezioni

**Backoffice manual rule**: vedi §6, applicabile a Fase 4.

**Output**: matrice con verdetto per ogni capability.

### 5.3 Regression risk analysis

Quali modifiche BOXE potrebbero accidentalmente toccare Mines o platform shared?

**Output**: lista di file/aree platform da considerare "protetti": nessun cambio se non strettamente necessario, ogni cambio richiede capability matrix end-to-end per dimostrare assenza di regressione.

## 6. Vincoli non negoziabili

- Wallet/ledger/RNG/payout/math platform-side: **INTOCCABILI**
- Capability matrix end-to-end (DB/Backend/API/Admin/Player/CSS/Test/Docs) obbligatoria in ogni PR. Regola già nei guardrails, applicarla da Fase 2A in poi.
- Aggiornamento `BACKOFFICE_MANUAL.md` obbligatorio quando una fase tocca admin UI. Regola già nei guardrails.
- Stop-and-Ask obbligatorio su:
  - divergenze dallo SPEC.md (regole, layout, settings, vincoli, state machine, idempotency, rounding, replay, lifecycle, asset, failure UX)
  - bisogno di estendere la platform shell
  - scope creep ("aggiungo X mentre ci sono")
  - decisioni product non coperte da SPEC
  - tool atteso non disponibile (es. GitHub PR create), prima di applicare workaround
- Comunicazione di consegna esplicita per ogni handoff: "pushed on branch" / "merged on main" / "merged and visible on localhost after rebuild". "Fatto" senza qualificatore non ammesso. Regola permanente.

## 7. Deliverable paralleli: BOXE + Playbook

I due deliverable si producono insieme, non in serie. La mitigazione esplicita del rischio "Playbook documento dopo" (§8) è che la v0 si scrive PRIMA di Fase 0. Senza v0, Fase 0 non parte.

### 7.1 BOXE

Esegue le Fasi 0-7 come sopra.

### 7.2 Playbook

`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`. Si scrive incrementalmente con sequenza vincolata:

- **v0 PRIMA di Fase 0**: stesura iniziale con template SPEC (gli undici blocchi del §3), checklist per fase, matrice "comune vs specifico" pre-compilata sulle astrazioni esistenti, lista anti-pattern. Senza v0, Fase 0 BOXE non parte.
- **Aggiornamento dopo ogni fase BOXE**: lezioni apprese, anti-pattern emersi, refinement di checklist. Una fase non si chiude se il Playbook non riflette quanto imparato.
- **v2 "battle-tested"** alla chiusura di BOXE: pronto per il gioco numero 3 senza ulteriori meta-discussioni.

### 7.3 Anti-pattern formalizzati nel Playbook

Lista iniziale per la v0. Va estesa durante BOXE ogni volta che ne emerge uno.

**Anti-pattern architetturali**:

- Non copiare MinesStandalone in BoxeStandalone
- Non duplicare il decision flow (vive nella shell game-runtime)
- Non duplicare il cashier (vive nella shell)
- Non duplicare audio, i18n, theme system
- Non usare la config shape di Mines come base implicita per BOXE
- Non infilare `if game === "boxe"` in componenti platform
- Non creare endpoint economici BOXE paralleli al Game Adapter
- Non estendere la platform shell senza decisione architetturale esplicita

**Anti-pattern di implementazione**:

- Non mettere math o payout in frontend "per preview"
- Non riusare asset kind Mines se il significato per BOXE è diverso
- Non fare fallback silenti su title_code, config, difficulty
- Non hardcodare configurazioni che dovrebbero essere in Title Editor
- Non considerare demo/real/bonus "uguali tranne wallet": vanno testati separatamente
- Non rimandare replay/history a "polish dopo": per un gioco nuovo è parte del contratto, non polish

**Anti-pattern di processo**:

- Non saltare la capability matrix end-to-end
- Non aggiornare il manuale "dopo": va aggiornato nello stesso PR del cambio admin
- Non chiudere una fase senza aggiornare il Playbook con quanto imparato
- Non comunicare "fatto" senza qualificatore di consegna

## 8. Rischi strutturali identificati

Il piano è valido, ma cinque rischi vanno gestiti esplicitamente.

### 8.1 Backend multi-game non battle-tested

Il Game Adapter platform è stato disegnato per multi-game, ma testato finora solo con Mines. BOXE sarà il vero stress-test.

**Mitigazione**: Fase 1 architecture mapping deve verificare il Game Adapter capability per capability. Fase 2D (wiring) è dove il test reale avviene: se il Game Adapter rivela limiti, vanno trattati come decisione architetturale separata, non come patch BOXE.

### 8.2 Title Editor potenzialmente Mines-shaped

L'attuale Title Editor è stato disegnato sulle esigenze Mines. Potrebbe non scalare a BOXE (es. settings rows/difficulty invece di grid/mines).

**Mitigazione**: Fase 1 deve testare l'editor su uno scenario BOXE. Se l'editor è troppo Mines-shaped, va valutato un Registry/editor per engine prima di Fase 4. Decisione architetturale, non patch.

### 8.3 Replay e finance arrivano tardi

Se replay/history e finance drilldown vengono lasciati per la fine, scopriamo troppo tardi che lo schema round non basta.

**Mitigazione**: replay/history sono nel §3.8 dello SPEC come blocco obbligatorio. Fase 2D li wira esplicitamente. Niente "polish dopo".

### 8.4 Fase 0 product percepita come burocratica

Compilare 11 blocchi prima di scrivere codice può sembrare overkill.

**Mitigazione esplicita**: ogni blocco del §3 ha già un riferimento concreto a una decisione che, se non presa qui, finisce dentro al codice. Lo SPEC è il contratto. Senza contratto si negozia in tribunale (il codice), e costa di più.

### 8.5 Playbook diventa "documento dopo"

Rischio strutturale del piano stesso: il Playbook potrebbe essere scritto solo a fine BOXE, perdendo l'occasione di farlo evolvere.

**Mitigazione esplicita** (vedi §7.2): v0 PRIMA di Fase 0. Aggiornamento obbligatorio dopo ogni fase BOXE. Una fase non si chiude se il Playbook non riflette quanto imparato.

## 9. Successo come si misura

1. BOXE in produzione: demo + real + bonus funzionanti, smoke + visual verdi, finance vede i round, replay leggibile
2. Zero regressioni su Mines: verificato con smoke Mines verde
3. Playbook scritto, applicato durante BOXE, validato come riusabile
4. Tempo di Fase 0-1 BOXE = baseline. Per il gioco 3, le stesse fasi devono richiedere meno tempo. Se non succede, il Playbook va rivisto.

## 10. Ordine operativo proposto

```
A. Chiusura sospesi tecnici (asset upload merge + rebuild, docs title_logo cap, analisi smoke legacy)
B. Stesura NEW_GAME_INTEGRATION_PLAYBOOK.md v0 (template + checklist + anti-pattern + matrice pre-compilata)
C. Fase 0 BOXE: stesura SPEC.md (11 blocchi)
D. Fase 1 BOXE: architecture mapping + regression risk analysis
E. Fase 2A → 7 BOXE: esecuzione
```

Le fasi A-B-C-D sono il "tax" metodologico. Si ammortizzano sui giochi 3-10.

## 11. Implementation Log

Sezione attiva da Fase 0 in poi. Ogni WP che tocca BOXE aggiunge una entry qui
nello stesso PR del codice, secondo il formato definito in
`docs/TASK_EXECUTION_GUARDRAILS.md` § Project Implementation Log.

Scopo: catturare decisioni, sorprese, edge case e naming convention emersi
durante l'implementazione BOXE, in modo che:

- un lettore futuro (o agente Codex fresco) capisca il PERCHÉ di scelte non
  ovvie dal codice
- alla chiusura di BOXE, le entry vengano distillate in aggiornamenti del
  `NEW_GAME_BRIEF_TEMPLATE.md` (nuove domande/default) e del
  `NEW_GAME_INTEGRATION_PLAYBOOK.md` (nuovi step/anti-pattern)

### Entries

Il log operativo completo vive in `docs/games/boxe/BOXE_BRIEF.md` sezione 12.
Questo brief e' stato lasciato come reference metodologica storica fino alla
closure BOXE e viene tracciato ora per conservare il razionale di kickoff.

### Distillazione finale (a chiusura BOXE)

Checklist obbligatoria prima di dichiarare BOXE chiuso:

- [x] Tutte le entry del log sono state riviste
- [x] Le decisioni ricorrenti sono diventate default nel `NEW_GAME_BRIEF_TEMPLATE.md`
- [x] Gli anti-pattern emersi sono stati formalizzati nel `NEW_GAME_INTEGRATION_PLAYBOOK.md` anti-pattern catalog
- [x] Le naming convention adottate sono documentate nel Playbook
- [x] I rischi strutturali emersi sono nel Playbook Known Structural Risks
- [x] Eventuali estensioni platform sono documentate e referenziate
- [x] Il Template e' abbastanza ricco da permettere a un product owner di compilarlo per gioco 3 senza riaprire le stesse discussioni metodologiche
