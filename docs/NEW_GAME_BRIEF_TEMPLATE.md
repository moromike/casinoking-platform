Status: ACTIVE
Last meaningful update: 2026-05-19

# New Game Brief Template (v2)

Template di input per lanciare un gioco nuovo sulla piattaforma CasinoKing.

## Come si usa

Il product owner compila questo template per il gioco N+2 (giochi 3-20). Le
risposte alimentano la Fase 0 (SPEC) del Playbook
`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` (v2, aggiornato dopo audit BOXE).

Per ogni sezione, le opzioni sono:

- **Fill**: valore specifico da fornire
- **Use default**: si usa il default platform (vedi colonna riferimento)
- **Open**: domanda non risolta, da chiudere prima di Fase 0

Stato del template v2: arricchito dopo BOXE con default, audit parity,
decisioni product owner 2026-05-19 e gate visuali obbligatori. I campi aperti
bloccano Fase 0.

---

## 0. Pre-Phase Checklist

Da completare prima o durante Fase 1, prima dei WP che consumano le capability
shared:

- [ ] Backend platform adapter game-agnosticity audit completato?
- [ ] Frontend game-runtime storage/context audit completato?
- [ ] Title Editor engine-agnosticity audit completato?
- [ ] Backend lifecycle symmetry audit completato (table-session, access-session, settlement)?
- [ ] GameRuntimeShell consume audit completato (componenti shared consumati davvero, non solo esistenti)?
- [ ] Visual reference gates documentati (mockup -> DOM region -> component -> baseline)?
- [ ] Left rail decision dichiarata (ergonomica simile / pixel-perfect / custom)?
- [ ] GameControlRail / GameRuntimeTools / GameStageHeader consume confermato?
- [ ] Asset kind decision documentata?
- [ ] Math input strategy chiara: formula/table, anchor reconciliation o ricerca esterna autorizzata?
- [ ] RTP demo e RTP production dichiarati o esplicitamente deferred?
- [ ] Game-over reveal logic dichiarata?
- [ ] Demo, real cash e real bonus testabili separatamente?

## 1. Identification

| Campo | Valore | Note |
|---|---|---|
| Game name (display) | _Fill_ | Es. "Mines Classic", "BOXE Adventure" |
| Game code (slug) | _Fill_ | Es. `mines`, `boxe`. Usato in URL e DB. |
| Game family | _Fill_ | Famiglia engine: `mines`, `boxe`, ... |
| First-variant code | _Fill_ | Es. `mines001`, `boxe001` |
| Demo enabled | _Use default: yes_ | |
| Real enabled | _Use default: yes_ | |
| Bonus wallet supported | _Use default: yes_ | |

## 2. Visuals & Assets

| Campo | Valore | Note |
|---|---|---|
| Game icon | _Fill: path_ | PNG/WebP, dimensioni in linea con altri giochi |
| Reference mockups (binding visual gates) | _Fill: path list_ | Ogni mockup deve mappare frame -> DOM region -> component -> baseline screenshot. |
| Visual fidelity level v1 | _Fill: composition reference / pixel-perfect / inspirational_ | Default consigliato: composition reference. Pixel-perfect richiede decisione product esplicita. |
| Color palette | _Use default: shared Mines default_ o _Fill: variante esplicita_ | Variante colore richiede product decision; evitare skin game-specific per default. |
| Lobby card image | _Fill: path_ | Vedi `docs/BACKOFFICE_MANUAL.md` § Lobby card per spec |
| Lobby card asset kind decision | _Use default: `game_card`_ | Usare kind condiviso salvo semantica divergente. |
| Board symbol asset kinds | _Fill or Use default if semantic match_ | Es. BOXE riusa `symbol_safe` / `symbol_mine`; se il significato cambia, usare kind dedicati. |
| Theme tokens (color palette) | _Use default: Mines tokens_ o _Fill: skin completa_ | Override tema vedi atlas tema |
| Sound effects pack | _Use default: platform sounds_ o _Fill: path_ | Bet, reveal, win, loss |
| Animations | _Use default: pattern Mines_ o _Fill: specs_ | Reveal, win celebration, loss |
| Provider intro video | _Use default: moromike lab 8s_ | Override sconsigliato, è brand |

## 3. Math & RNG

| Campo | Valore | Note |
|---|---|---|
| Game type | _Fill_ | grid / ladder / spin / piramide / altro |
| Configuration tunables | _Fill_ | Es. Mines: grid_size + mines_count. BOXE: rows + difficulty. |
| Payout formula | _Fill_ | Multiplier table o formula |
| Math input strategy | _Fill_ | Table product-approved, derivazione da anchor, o ricerca esterna autorizzata. Stop se non chiara. |
| RTP demo | _Use default: 98%_ | Demo/local target. Se diverso, product decision esplicita. |
| RTP production | _Fill or Deferred: pre-launch WP_ | Default operativo: deferred fino a production hardening; target atteso circa 92% salvo decisione product/certificazione. |
| RNG fairness contract | _Use default: server seed + client seed deterministic per session_ | Override richiede capability matrix dedicata |
| Max win cap | _Fill: valore_ | Per gioco. Es. BOXE: 1M chip. |
| Math validator / stress framework | _Use default: standalone simulator + stress tests_ | Pattern BOXE standard: validator deterministico, stress rapido, report riproducibile. |
| Round duration / timeout | _Use default: platform access-session timeout_ o _Fill_ | |

## 4. Rules & Copy

| Campo | Valore | Note |
|---|---|---|
| Rules text (player-facing, short) | _Fill_ | Testo regole, italiano + lingue al lancio |
| How-to-play (3-step tutorial) | _Fill_ | Solo se diverso dal default. Es. BOXE ha tutorial specifico. |
| Edge case copy | _Use default: platform standard_ o _Fill_ | Game over, win celebration, error states |
| Localization | _Fill: lista lingue_ | Es. it, en. Italiano obbligatorio. |

## 5. Configuration limits

| Campo | Valore | Note |
|---|---|---|
| Bet range (min, max) | _Fill_ | In chip |
| Allowed wallet types | _Use default: cash + bonus_ | |
| Title variants supportate | _Fill: lista_ | Es. `<game>001`, `<game>002` |
| Operator-configurable settings | _Fill_ | Cosa l'operatore può cambiare dal Title Editor |
| Hardcoded settings | _Fill_ | Cosa è fisso e non configurabile |

## 6. Platform shell overrides

Il gioco di default usa tutta la game-runtime shell. Qui si dichiarano i casi in
cui il gioco si discosta dal default.

| Componente shell | Use default? | Note se override |
|---|---|---|
| GameBootDecisionFlow | _Yes_ | Override solo con decisione architetturale |
| GameProviderIntroGate (video brand) | _Yes_ | Override sconsigliato |
| GameHowToPlayGate (overlay) | _Yes_ | Contenuti specifici passati come prop |
| GameTableBalanceGate (wallet picker) | _Yes_ | Limiti passati come prop |
| GameShortViewportGate (rotation gate mobile) | _Yes_ | |
| GameControlRail | _Yes_ | Default: settings + bet + balance + action buttons + quick chips. Override sconsigliato. |
| GameRuntimeTools | _Yes_ | Default: audio toggle + rules + replay/info tools; contenuto game-specific via adapter. |
| GameStageHeader | _Yes_ | Default: title + payout/tools area; board/payout game-specific via slot. |
| Audio infra | _Yes_ | |
| Theme provider | _Yes_ | |
| Storage / launch context | _Yes_ | |
| History / replay | _Yes_ | Vedi anche sezione 8 |
| Launch Cashier (player lobby modal) | _Yes_ | |

## 7. Backend lifecycle parity

La parita' lifecycle e' un gate architetturale, non un dettaglio frontend. Ogni
gioco deve dichiarare se segue Mines o se apre un WP platform prima del lancio.

| Campo | Valore | Note |
|---|---|---|
| Table session integration | _Fill: required at launch / placeholder v1 + future WP / N/A_ | Placeholder ammesso solo per demo/prototype, mai come stato production implicito. |
| Access session | _Use default: pattern Mines_ o _Fill: variante_ | Variante richiede audit backend lifecycle symmetry. |
| Settlement | _Use default: Game Adapter standard_ o _Fill: variante_ | Variante richiede contract test dedicato e review finance. |
| Bonus wallet lifecycle | _Use default: Mines real bonus pattern_ o _Fill_ | Deve essere testabile separatamente da real cash. |

## 8. Special behaviors

| Campo | Valore | Note |
|---|---|---|
| Game-over reveal logic | _Fill_ | Mines: full grid. BOXE: current row only. Altri giochi: definire visibile/nascosto per ogni area. |
| Auto-cashout policy | _Use default: Session Recovery Engine_ | Vedi `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` |
| Bonus rounds | _Fill: yes/no + come_ | Se sì, vedi Session Recovery design § scenario 5 |
| Replay format | _Use default: platform_ o _Fill_ | Sequenza decisioni + stato finale + seed |
| Session recovery special handling | _Use default_ o _Fill_ | Vedi Session Recovery scenari 1-11 |

## 9. State machine backend

| Campo | Valore | Note |
|---|---|---|
| Stati possibili round | _Use default pattern or Fill_ | Default ladder/pick pattern: created, active, row_revealed, cashout_pending, completed_cashout/completed_top_row, failed_mine, expired, quarantined. |
| Transizioni illegali | _Fill_ | Quali transizioni il backend deve rifiutare |
| Comportamento concurrent reveals | _Fill_ | Serializzazione |
| Comportamento concurrent cashout | _Fill_ | Race cashout vs reveal in volo |
| Idempotency contract | _Use default: Idempotency-Key header su mutazioni_ | Vedi pattern Mines |
| Active-round config publish behavior | _Use default: active round unaffected_ | Future rounds use newly published config. |

## 10. Failure UX

Tutti gli scenari di errore visibili al player o operatore. Lista minima:

- Config gioco mancante: _Fill comportamento_
- Title non pubblicato: _Fill_
- Table session scaduta: _Fill_
- Saldo insufficiente: _Fill_
- Wallet bonus vuoto: _Fill_
- Rete intermittente: _Fill_
- Backend irraggiungibile: _Fill_
- Round già chiuso, retry cashout: _Fill_

## 11. Integration outputs (forniti dal sistema, non da compilare)

Questi valori sono derivati dai precedenti, elencati qui per chiarezza:

- Backend module path: `backend/app/modules/games/<game_code>/`
- Frontend page route: `/<game_code>?title_code=<variant>&...`
- Admin backoffice tab: Title Editor (sezione gioco)
- Lobby category placement: catalogo platform (default)

## 12. Open questions

Sezione attiva durante Fase 0 SPEC. Domande da chiudere prima di toccare codice.

- _Nessuna ancora._

## 13. Implementation Log

Sezione attiva dopo Fase 0. Si applica la regola `docs/TASK_EXECUTION_GUARDRAILS.md`
§ Project Implementation Log.

---

## Roadmap del Template

v0 (2026-05-17): scheletro. Default placeholder, da arricchire.

v1 (2026-05-19): default reali ereditati da Mines + BOXE. Include audit
game-agnosticity, RTP demo/production, asset kind decision, state machine
pattern e reveal logic upfront.

v2 (questo doc, 2026-05-19 post-audit BOXE): aggiunge lifecycle parity,
visual reference gates, left rail decision, GameRuntimeShell consume audit e
default GameControlRail/RuntimeTools/StageHeader.

v3 (post-gioco 3): consolidato. Idealmente un product owner compila <50% dei
campi (resto sono default), e il gioco è pronto per Fase 0 in 1 prompt.

vN (post-gioco 5+): se il sistema regge, gioco N è quasi automatico. Se non
regge, va rivisto.
