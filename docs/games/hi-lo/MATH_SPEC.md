Status: ACTIVE
Last meaningful update: 2026-05-23

# HI-LO - Math, RNG And Fairness Spec

This document defines HI-LO card probabilities, multiplier calculation, RTP
target, deterministic randomness and validation gates.

## 1. Scope

| Field | Value |
| --- | --- |
| Game code | `hi_lo` |
| First title | `hilo001` |
| Deck | Infinite 52-card deck with replacement |
| RTP target | 98% |
| Max win cap | None game-specific in v1 |
| Frontend math | Forbidden |
| Outcome authority | Backend deterministic draw |
| Replay determinism | Required |

## 2. Product Decisions

| Topic | Decision |
| --- | --- |
| Display probability | True probability of the next action. |
| House edge | Applied through multiplier. |
| RTP model | Single-edge cumulative model: every planned cashout target prices to 98% expected return before rounding drift. |
| External 5000x cap | Not adopted. |
| Skip | Free; server-authoritative draw; replayable. |

The single-edge cumulative model is chosen for consistency with Mines/BOXE:
cashout at step `n` remains priced around the same 98% target instead of
compounding house edge as `0.98^n`.

## 3. Card Model

| Concept | Rule |
| --- | --- |
| Suits | Clubs, spades, hearts, diamonds. |
| Colors | Clubs/spades black; hearts/diamonds red. |
| Ranks | A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K. |
| Rank values | A=1, 2=2, ..., J=11, Q=12, K=13. |
| Draw | Uniform from 52 cards every time. |
| Replacement | Yes; previous cards do not change future probabilities. |

## 4. Action Probabilities

For current rank `r` in `[1, 13]`:

```text
p_black = 26 / 52 = 1/2
p_red = 26 / 52 = 1/2
```

Rank action slots:

```text
if r == 1:
  down_slot = SAME
  p_down = 1 / 13
  up_slot = HIGHER
  p_up = 12 / 13
elif r == 13:
  down_slot = LOWER
  p_down = 12 / 13
  up_slot = SAME
  p_up = 1 / 13
else:
  down_slot = LOWER_OR_SAME
  p_down = r / 13
  up_slot = HIGHER_OR_SAME
  p_up = (14 - r) / 13
```

This avoids any guaranteed 100% action at A or K.

## 5. First-Step Probability And Multiplier Table

This table assumes no previous correct prediction, so cumulative probability is
the action probability itself.

| Current rank | Color option | Color probability | Color multiplier | Down label | Down probability | Down multiplier | Up label | Up probability | Up multiplier |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| A | BLACK/RED | 50.00% | 1.9600x | SAME | 7.69% | 12.7400x | HIGHER | 92.31% | 1.0617x |
| 2 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 15.38% | 6.3700x | HIGHER_OR_SAME | 92.31% | 1.0617x |
| 3 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 23.08% | 4.2467x | HIGHER_OR_SAME | 84.62% | 1.1582x |
| 4 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 30.77% | 3.1850x | HIGHER_OR_SAME | 76.92% | 1.2740x |
| 5 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 38.46% | 2.5480x | HIGHER_OR_SAME | 69.23% | 1.4156x |
| 6 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 46.15% | 2.1233x | HIGHER_OR_SAME | 61.54% | 1.5925x |
| 7 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 53.85% | 1.8200x | HIGHER_OR_SAME | 53.85% | 1.8200x |
| 8 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 61.54% | 1.5925x | HIGHER_OR_SAME | 46.15% | 2.1233x |
| 9 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 69.23% | 1.4156x | HIGHER_OR_SAME | 38.46% | 2.5480x |
| 10 | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 76.92% | 1.2740x | HIGHER_OR_SAME | 30.77% | 3.1850x |
| J | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 84.62% | 1.1582x | HIGHER_OR_SAME | 23.08% | 4.2467x |
| Q | BLACK/RED | 50.00% | 1.9600x | LOWER_OR_SAME | 92.31% | 1.0617x | HIGHER_OR_SAME | 15.38% | 6.3700x |
| K | BLACK/RED | 50.00% | 1.9600x | LOWER | 92.31% | 1.0617x | SAME | 7.69% | 12.7400x |

## 6. Multiplier Formula

Let:

```text
target_rtp = 0.98
cumulative_success_probability = product(probability_of_each_correct_prediction)
```

Then:

```text
multiplier = round_4(target_rtp / cumulative_success_probability)
potential_payout = round_2(bet_amount * multiplier)
```

For the next visible action quote during an active round:

```text
next_cumulative_probability =
  current_cumulative_success_probability * action_success_probability

next_total_multiplier =
  round_4(target_rtp / next_cumulative_probability)
```

The multiplier displayed on option buttons is the total multiplier after that
choice succeeds, not an incremental multiplier.

## 7. RTP Proof

For any chosen cashout target after `n` correct predictions:

```text
expected_return =
  cumulative_success_probability * multiplier

expected_return ~= cumulative_success_probability *
  (0.98 / cumulative_success_probability)

expected_return ~= 0.98
```

Rounding to 4 decimal multiplier and 2 decimal payout creates small drift.
Validation tests must measure the drift and assert it remains inside the
approved tolerance.

## 8. Example Sequences

### 8.1 First Card 7, Choose Red

```text
p = 1/2
multiplier = 0.98 / 0.5 = 1.9600x
```

Displayed option:

```text
RED
1.9600x
50.00%
```

### 8.2 First Card 7, Choose Lower Or Same

```text
p = 7/13 = 53.846153...
multiplier = 0.98 / (7/13) = 1.8200x
```

Displayed option:

```text
LOWER OR SAME
1.8200x
53.85%
```

### 8.3 Current Card K After Previous Successes

At K:

```text
LOWER probability = 12/13 = 92.31%
SAME probability = 1/13 = 7.69%
```

If current cumulative probability is `c`, the option multipliers are:

```text
LOWER multiplier = round_4(0.98 / (c * 12/13))
SAME multiplier = round_4(0.98 / (c * 1/13))
```

The UI labels must be `LOWER` and `SAME`, not `LOWER OR SAME` and
`HIGHER OR SAME`.

## 9. Rounding And Precision

| Value | Rule |
| --- | --- |
| Action probability display | Percent with 2 decimals. |
| Multiplier storage/display | Decimal rounded to 4 decimals, half-up. |
| Payout amount | Platform decimal money/chip rule; default half-up to 2 decimals unless platform requires another scale. |
| Ledger amount | Platform wallet/ledger owner, not frontend. |

Frontend must never recompute wallet payout from visual text.

## 10. RNG And Fairness

### 10.1 Seed Material

HI-LO uses deterministic backend draw from seed material:

```text
fairness_version
game_code
server_seed
client_seed
round_nonce
draw_index
draw_purpose
```

`draw_purpose` must distinguish:

- idle skip card;
- start/base card if needed;
- active skip card;
- prediction draw.

### 10.2 Draw Algorithm Contract

Implementation may choose the exact helper in Phase 3/5A, but it must satisfy:

| Requirement | Rule |
| --- | --- |
| Uniformity | Every one of 52 cards has equal probability. |
| Determinism | Same seed material produces same card. |
| Replay | Persist enough seed/draw data to reproduce round. |
| Independence | Replacement model; each draw independent in probability. |
| No frontend authority | Browser never chooses outcome. |

Recommended derivation:

1. Hash seed material with SHA-256 or existing platform helper.
2. Convert digest to integer.
3. Use rejection sampling or modulo-bias-safe mapping to 0..51.
4. Map index to suit/rank.

Do not use biased modulo unless the platform helper already proves acceptable
uniformity.

## 11. Skip Math

Skip draws a new card but does not change payout multiplier directly.

| Scenario | Math effect |
| --- | --- |
| Idle skip | New base card, no multiplier, no bet. |
| Active skip | New current card, same current multiplier, same current cumulative probability. |
| Prediction after skip | Uses probability for the new current card. |
| Skip count | UX/state constraint, not payout math. |

Under the single-edge cumulative formula, active skip does not create extra RTP
by itself. Whatever current card the player receives, the next successful
prediction is repriced from:

```text
next_multiplier = 0.98 / (current_cumulative_probability * next_action_probability)
```

So the ideal expected value of continuing from the current state remains equal
to the current cashout value before rounding drift:

```text
next_action_probability * next_multiplier =
  0.98 / current_cumulative_probability
```

Active skip changes volatility and player preference, not theoretical EV in the
ideal model.

Implementation must still log skipped cards and include them in replay/fairness.
The game remains server-authoritative because the player cannot choose the
skipped result.

## 12. No Max-Win Cap

HI-LO v1 does not implement the external reference 5000x cap.

| Item | Decision |
| --- | --- |
| Game-specific cap | No. |
| Disabled options due to cap | No. |
| Auto-collect due to cap | No. |
| Admin max-win field | No. |
| Future platform risk limit | Possible only as a platform-wide WP. |

## 13. Validation Contract

### 13.1 Analytical Tests

| Test | Requirement |
| --- | --- |
| Rank probability table | All 13 rank rows match this spec. |
| Edge labels | A and K labels/probabilities match edge rules. |
| First-step multipliers | Match table after rounding. |
| Sequence multiplier | `0.98 / cumulative_probability` for arbitrary sequences. |
| Skip strategy | Active skip does not increase theoretical EV above current cashout value before rounding drift. |
| RTP drift | Expected return per cashout target stays inside approved tolerance. |
| No cap | No math branch for HI-LO-specific max-win cap. |

### 13.2 RNG Tests

| Test | Requirement |
| --- | --- |
| Determinism | Same seed/draw index gives same card. |
| Different draw index | Produces independent deterministic stream. |
| Replay | Stored round can reconstruct all cards/actions. |
| Uniformity smoke | Large sample distribution within statistical tolerance. |
| Replacement | Same card can appear on consecutive draws. |

### 13.3 Integration Tests

| Flow | Requirement |
| --- | --- |
| Start round | Debits/opens platform round and returns current card/options. |
| Correct prediction | Updates multiplier/history/current card. |
| Wrong prediction | Terminal loss, no payout. |
| Cashout | Settles once and idempotently. |
| Active skip limit | Allows 5 active skips, blocks 6th until prediction. |
| Idle skip | Unlimited and no bet debit. |
| Real-money guard | Cannot bypass table-balance launch. |

## 14. Implementation Notes For Phase 3

Phase 3 must decide where the shared fairness helper lives. If Mines/BOXE
helpers are game-specific, open a platform fairness extraction WP instead of
copying code into HI-LO.

The backend should expose option quotes from server state so the frontend only
renders:

- label;
- icon key;
- probability percent;
- total multiplier;
- disabled reason if any.

## H1 Implementation Note - 2026-05-23

The pure backend math/RNG/fairness nucleus now lives in:

| File | Responsibility |
| --- | --- |
| `backend/app/modules/games/hi_lo/math.py` | Card model, action probabilities, labels, prediction success, 98% cumulative multiplier and payout rounding. |
| `backend/app/modules/games/hi_lo/randomness.py` | Deterministic seed-based card draw with SHA-256 and modulo-bias-safe rejection sampling. |
| `backend/app/modules/games/hi_lo/fairness.py` | Pure draw-sequence fairness artifacts and verification helpers. |
| `tests/unit/test_hi_lo_math_randomness.py` | Contract tests for probability table, edge ranks, RTP, skip EV, deterministic RNG, replacement and fairness verification. |

H1 deliberately does not implement API routes, persistence, wallet/ledger,
round state, replay endpoints or frontend gameplay.

## 15. Decision Brief For Michele

Current math contract:

- true probabilities in UI;
- 98% single-edge cumulative RTP model;
- no 5000x HI-LO cap;
- A/K edge rules avoid guaranteed options;
- active skip is free but logged/replayable;
- backend owns every draw and every payout.

If this is approved, Phase 3 maps backend modules, APIs, frontend shell,
admin fields, replay and tests.
