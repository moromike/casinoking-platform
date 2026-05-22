Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO - SPEC

Contratto prodotto/tecnico Phase 2 per il gioco proprietario HI-LO.

Questo documento traduce la source intake in un contratto eseguibile per le
fasi successive. Non contiene codice e non autorizza ancora implementazione:
prima del codice servono Architecture Mapping e Wave Plan.

## 0. Scope, Sources And Decisions

### 0.1 Status

| Field | Value |
| --- | --- |
| Phase | Phase 2 - SPEC, Math And Experience Contract |
| Type | Documentation-only SPEC |
| Production code touched | No |
| Canonical math doc | `docs/games/hi-lo/MATH_SPEC.md` |
| Source inventory | `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md` |
| Decision map | `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md` |

### 0.2 Sources Read

| Source | Use |
| --- | --- |
| `assets/Games/hi-lo/analisi funzionale hi-lo.md` | Primary HI-LO gameplay/source analysis. |
| `assets/Games/hi-lo/*.png` | Visual composition references for idle, active, loss, win, history, edge K and cashout states. |
| `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md` | Binding/inspirational source classification. |
| `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md` | Phase 1 decisions and open items. |
| `docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md` | Stop-and-Ask register. |
| `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md` | Surface coverage baseline. |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md` | Mandatory admin/backoffice anti-false-green rules. |
| `docs/NEW_GAME_BRIEF_TEMPLATE.md` | Platform defaults and new-game required fields. |

The source video remains excluded because Michele said the analysis document
already represents it.

### 0.3 Product Decisions Approved In Chat

Michele approved the Phase 1 recommended defaults on 2026-05-22, with one
correction: do not adopt the external reference 5000x cap.

| Topic | SPEC decision |
| --- | --- |
| Route | `/hi-lo` |
| Backend module name | `hi_lo` |
| First title code | `hilo001` |
| Visual fidelity | Composition reference, not pixel-perfect external clone. |
| Assets | Screenshots are references only; runtime assets must be owned/licensed/generated. |
| RTP display | Display true action probability; apply 98% target in multiplier. |
| Real-money launch | Must inherit table-balance/launch cashier guard; no full-wallet entry. |
| Max win | No HI-LO-specific max-win cap in v1. |
| Admin | Inherit full Mines/BOXE admin engine page and title editor depth from day one. |
| Lifecycle | Active round resumes or follows platform recovery; never silent loss. |

### 0.4 Remaining Stop-Before-Code Items

These do not block this SPEC, but they block implementation until Architecture
Mapping or a dedicated WP resolves them.

| Item | Required resolution before code |
| --- | --- |
| Asset ownership | Decide exact source for card deck, card back, logo, background and suit/action icons. |
| Platform session recovery implementation | Confirm existing recovery primitives or open platform WP. |
| Admin engine canonicalization for third game | Verify current admin engine page can host `hi_lo` without local shortcuts. |
| Production RTP/legal tuning | 98% is the product/math contract now; production certification may later override through a dedicated math WP. |

## 1. Game Identity

| Field | Value |
| --- | --- |
| Display name | `HI-LO` |
| Game code | `hi_lo` |
| Public route | `/hi-lo?title_code=<title_code>` |
| First title variant | `hilo001` |
| Genre | Arcade card prediction / push-your-luck |
| Runtime authority | Backend/server-authoritative |
| Frontend math authority | Forbidden; display backend values only |
| Bonus rounds | No |
| Progressive jackpot | No |

## 2. Core Rules

### 2.1 Objective

The player places a bet, receives a current card, predicts the next card by
color or rank direction, and may cash out after each successful prediction.

Each correct prediction increases the current multiplier. A wrong prediction
ends the round with zero payout.

### 2.2 Deck And Cards

| Rule | Value |
| --- | --- |
| Deck model | Infinite 52-card deck with replacement. |
| Rank order | A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K. |
| Lowest rank | A |
| Highest rank | K |
| Suits | Clubs, spades, hearts, diamonds. |
| Colors | Black = clubs/spades; red = hearts/diamonds. |
| Prior cards influence future cards | No. |

### 2.3 Prediction Options

Every active decision exposes four option slots.

| Slot | Normal label | Edge label | Win condition |
| --- | --- | --- | --- |
| Color black | Black | Black | Next card is club or spade. |
| Color red | Red | Red | Next card is heart or diamond. |
| Down | Lower or same | A: Same, K: Lower | See `MATH_SPEC.md`. |
| Up | Higher or same | A: Higher, K: Same | See `MATH_SPEC.md`. |

Edge-rank behavior is deliberately not a guaranteed 100% button:

- on A, the down slot becomes `Same` and the up slot becomes `Higher`;
- on K, the down slot becomes `Lower` and the up slot becomes `Same`.

This matches the inspected K reference and prevents a free guaranteed action.

### 2.4 RTP And Payout

| Item | Contract |
| --- | --- |
| RTP target | 98% for the current math contract. |
| Multiplier formula | `0.98 / cumulative_success_probability`, rounded by backend. |
| Probability display | True probability of the next action. |
| Payout basis | Initial bet multiplied by current reached multiplier. |
| Cashout owner | Backend/platform settlement. |
| Max-win cap | None game-specific in v1. |

The math, rounding and validation rules live in `MATH_SPEC.md`.

## 3. Game Loop

### 3.1 Idle

| Element | Behavior |
| --- | --- |
| Current card | Visible. |
| BET CTA | Enabled when bet and table session are valid. |
| COLLECT CTA | Hidden/disabled. |
| Prediction buttons | Hidden or disabled. |
| Skip | Enabled, unlimited and free before bet. |
| Bet/config | Editable according to live title config. |

### 3.2 Start Round

When the player presses BET:

1. frontend sends a server-authoritative start request with idempotency key;
2. backend validates title, mode, table session, bet and active-round absence;
3. backend debits/reserves through platform flow;
4. backend returns active round state, current card and option quotes;
5. frontend locks bet/config while the round is active.

### 3.3 Active Decision

| Element | Behavior |
| --- | --- |
| Current card | Visible and immutable until action resolves. |
| Four options | Visible with icon, label, total multiplier and probability. |
| Collect | Visible after at least one successful prediction. |
| Skip | Available until active skip limit is reached. |
| History | Shows recent cards from the current round. |

### 3.4 Correct Prediction

On a correct prediction:

1. backend draws the next card from the infinite deck model;
2. backend appends the old/current card to round history;
3. backend updates cumulative success probability and multiplier;
4. the new card becomes the current card;
5. frontend updates quotes and collect amount from backend response.

### 3.5 Wrong Prediction

On a wrong prediction:

1. backend returns terminal loss;
2. frontend reveals the losing card briefly;
3. history/replay records the losing draw;
4. active controls disappear;
5. primary CTA returns to BET after terminal resolution.

No large blocking "you lost" modal is required in v1.

After terminal resolution, the losing drawn card becomes the next idle base
card. The game must not draw a hidden fresh base card unless the player uses
idle skip.

### 3.6 Cashout

On COLLECT:

1. frontend sends cashout with idempotency key;
2. backend/platform settles payout;
3. round closes as `completed_cashout`;
4. active buttons disappear;
5. last active card remains the next idle base card unless recovery/platform
   state requires a fresh card.

This same "terminal card becomes next base card" rule applies after both
cashout and loss. It keeps card continuity visible and avoids hidden RNG.

## 4. Skip Contract

| Scenario | Decision |
| --- | --- |
| Idle skip | Unlimited, free, server-authoritative card refresh. |
| Active skip limit | 5 skips per active round. |
| After 5 active skips | Skip disabled until the player makes a prediction. |
| Skip reset | A successful prediction resets the active skip counter for the next decision window. |
| Skip after loss/cashout | Round terminal; skip returns to idle behavior. |
| Skip economics | No direct charge. |
| Skip fairness | Same seed/deck model, deterministic and replayable. |

If product later wants a different reset rule, it must be a SPEC change before
implementation.

## 5. History And Replay

### 5.1 Runtime History Bar

| Rule | Value |
| --- | --- |
| Visible size | Last 5 cards. |
| Overflow | FIFO: oldest visible card leaves the bar. |
| Current round only | Yes. |
| Correct card indicator | Show positive result marker. |
| Losing card indicator | Show terminal/loss marker during loss transition and replay. |

### 5.2 Replay Payload

Replay must be deterministic and include:

- starting card;
- every skip card;
- every prediction action;
- every drawn card;
- multiplier before/after each correct prediction;
- terminal outcome;
- payout amount;
- server seed hash, client seed and nonce/fairness data;
- table session/platform round ids when applicable.

## 6. Visual Experience Contract

### 6.1 Composition

HI-LO uses the CasinoKing shared runtime shell. The external screenshots guide
composition, not pixel-perfect CSS.

| Region | Requirement |
| --- | --- |
| Control rail | Shared CasinoKing game rail. |
| Stage | HI-LO-specific card stage. |
| Main card | Central, largest gameplay object. |
| Options | Around the card; four clear choices. |
| Skip | Near current card, reachable but secondary. |
| History | Bottom center inside stage. |
| Primary CTA | Under card/stage or in shared action slot depending on shell. |

### 6.2 Visual States

| State | Required visual proof in implementation |
| --- | --- |
| Idle desktop | One card, BET, no active quotes. |
| Active desktop | Four option buttons with probability and multiplier. |
| Correct prediction | Card transition plus history update. |
| Wrong prediction | Losing reveal, quiet reset to BET. |
| Cashout | COLLECT amount settles and returns to idle. |
| K edge | Higher slot becomes Same; down slot becomes Lower. |
| A edge | Down slot becomes Same; up slot becomes Higher. |
| Mobile portrait | No scrollbars/clipping. |
| Landscape short | Shared rotation/short-viewport behavior or fit proof. |

### 6.3 No-Scrollbar Rule

All HI-LO configurations must fit their runtime space without gameplay
scrollbars. If a viewport is too short, use the shared short-viewport/rotation
gate, not an internal scroll area.

## 7. Backend State Machine

### 7.1 States

| State | Meaning | Terminal |
| --- | --- | --- |
| `idle` | No active round; current base card may exist. | No |
| `starting` | Start request in progress. | No |
| `active` | Round active, waiting for prediction/skip/cashout. | No |
| `action_pending` | Prediction or skip request in progress. | No |
| `cashout_pending` | Cashout settlement in progress. | No |
| `completed_cashout` | Player collected. | Yes |
| `failed_prediction` | Player guessed wrong. | Yes |
| `expired` | Platform recovery/timeout closure. | Yes |
| `quarantined` | Inconsistent state requiring admin/backend review. | Yes |

### 7.2 Legal Transitions

| From | Event | To |
| --- | --- | --- |
| `idle` | start round | `starting` -> `active` |
| `idle` | idle skip | `idle` |
| `active` | active skip allowed | `action_pending` -> `active` |
| `active` | correct prediction | `action_pending` -> `active` |
| `active` | wrong prediction | `action_pending` -> `failed_prediction` |
| `active` | collect | `cashout_pending` -> `completed_cashout` |
| `active` | recovery auto-cashout/resume policy | platform-defined terminal or resumed `active` |
| any non-terminal | unrecoverable inconsistency | `quarantined` |

### 7.3 Illegal Transitions

| Attempt | Required result |
| --- | --- |
| Prediction before BET | Reject. |
| Collect before any correct prediction | Reject. |
| Skip after active skip limit | Reject or return disabled-state error. |
| Start second round while active | Reject or resume existing active round. |
| Cashout after loss | Return terminal loss; no payout. |
| Same idempotency key with different payload | Reject idempotency conflict. |

## 8. Idempotency And Concurrency

All mutating operations require idempotency keys:

- start round;
- idle skip;
- active skip;
- prediction;
- cashout;
- recovery closure.

Backend must lock per active round. First mutation wins; retries with the same
key return the same result; conflicting payloads with the same key reject.

## 9. Wallet, Real Money And Recovery

### 9.1 Launch And Table Session

HI-LO must inherit the platform launch cashier/table-balance guard.

| Requirement | Reason |
| --- | --- |
| No full-wallet auto-entry | Real-money safety/legal guard. |
| Explicit stake amount before real play | Player intent. |
| Default/max follows platform safe launch setting | Current platform decision after BOXE closure. |
| Demo, real cash and bonus tested separately | Wallet separation. |

### 9.2 Balance And Bet

| Scenario | Behavior |
| --- | --- |
| Balance/table amount below bet | BET disabled or clear insufficient balance error. |
| Bet edited during active round | Not allowed. |
| Config edited during active round | Not allowed for that round. |
| Active round after reload | Resume or recover; never silently start a new round. |

### 9.3 Disconnect

If an active round has a collectible amount, the platform must either resume it
or apply an explicit recovery policy. Silent loss is forbidden.

If the recovery engine is not ready for HI-LO, implementation must open a
platform lifecycle WP before real-money release.

## 10. Admin And Backoffice

Surface 10 is decomposed into 10A-F from day one.

| Layer | HI-LO requirement |
| --- | --- |
| 10A Admin engine page | Full Mines/BOXE master/variant page, editable titles, filters, create variant, inline save/preview/archive, status badges, lobby toggles. |
| 10B Title detail shell | Shared Title Editor shell with command/status/tab frame. |
| 10C Tabs | Overview, copy, rules, config, assets, theme, sound, validation, replay/history if platform exposes it. |
| 10D Field depth | Field-by-field parity with reference, plus HI-LO-specific card/config fields. |
| 10E Workflow | Draft save activates on every change, publish persists, runtime consumes. |
| 10F Adjacent pages | Asset library, manifest preview, finance/replay links where platform has them. |

### 10.1 HI-LO Config Fields

| Field | Owner | v1 decision |
| --- | --- | --- |
| Bet min/max/default | Platform/title config | Use platform defaults unless Phase 3 finds a required adapter. |
| Active skip limit | Game config | Default 5. |
| RTP target | Math/code | 98%, not operator-editable v1. |
| Card deck skin | Assets/theme | Required asset capability. |
| Card back | Assets/theme | Required asset capability. |
| Stage background | Theme/assets | Required if visual spec chooses image background. |
| Sounds | Sound assets | Inherit platform pattern. |
| Max-win cap | Not present | No HI-LO-specific field. |

## 11. Content And Localization

| Area | Requirement |
| --- | --- |
| Locales | `it`, `en`, `de`, `es` unless Phase 3 finds platform mismatch. |
| Info/rules modal | Shared container, rich HI-LO-specific content. |
| How-to-play | 3 cards: Bet, Predict, Collect. |
| Error copy | No raw backend strings. |
| Admin copy editor | Full manifest coverage, not partial content. |

### 11.1 Rules Sections

Minimum v1 sections:

1. Bet and collect.
2. Card predictions.
3. Multipliers and payout.
4. RTP and fairness.
5. Skip feature.
6. History and replay.
7. Real-money/session safety note.

No HI-LO-specific max-win section.

## 12. Asset Contract

| Asset | Required handling |
| --- | --- |
| Card faces | Owned/licensed/generated full 52-card set. |
| Card back | Owned/licensed/generated asset. |
| Suit icons | Owned icon assets or code-native icons. |
| Prediction action icons | Owned/code-native icons. |
| Stage background | Owned/generated asset or theme token background. |
| Logo/title | Text title acceptable unless product wants image logo. |
| Sounds | Platform defaults unless a HI-LO pack is provided. |

Do not import external screenshot pixels as runtime assets.

## 13. Testing And Evidence Gates

| Gate | Required before green |
| --- | --- |
| Math | Analytical RTP proof and deterministic RNG tests. |
| Backend | Start, prediction win/loss, skip, cashout, idempotency, resume/recovery tests. |
| Frontend | Idle/active/win/loss/cashout/edge A/edge K visual states. |
| No-scroll | Desktop/mobile/landscape DOM measurement. |
| Real money | Launch cashier guard, no full-wallet entry, cash/bonus separation. |
| Admin | 10A-F side-by-side and draft/save/publish/runtime consume. |
| Replay | Deterministic playback from persisted payload. |
| Product owner | `localhost:3000` walkthrough for player and admin closure. |

## 14. Phase 3 Handoff

Phase 3 must produce:

- `docs/games/hi-lo/ARCHITECTURE_MAPPING.md`;
- `docs/games/hi-lo/HI_LO_WAVE_PLAN.md`;
- shared vs HI-LO-specific vs platform-extension matrix;
- file ownership plan;
- worktree/branch plan;
- protected surfaces list;
- 12-surface tracker update.

No implementation starts before Phase 3 approves the architecture/WP split.

## 15. Decision Brief For Michele

Current Phase 2 decision state:

- approved defaults are now encoded;
- no 5000x cap is present;
- math formula is single-edge cumulative RTP 98%;
- real-money safety inherits platform launch cashier;
- admin must start full-depth, not as a simplified list;
- asset ownership remains the main practical blocker before UI implementation.

If Michele says OK to this SPEC, Codex proceeds to Phase 3 architecture mapping.
