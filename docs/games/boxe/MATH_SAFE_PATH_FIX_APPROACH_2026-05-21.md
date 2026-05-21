Status: ACTIVE
Last meaningful update: 2026-05-21

# BOXE - Math Safe Path Fix Approach

## Scope

Wave 6 Parte A, doc-only. No production code is changed here.

Bug reported by Michele: some terminal BOXE pyramids have no complete safe path
bottom-to-top, including 8 rows / HARD and 4 rows / HARD examples. That means a
terminal full reveal can show at least one row with zero diamonds, so the board
looks structurally impossible.

This approach treats "safe path" according to the current BOXE spec: the game
requires exactly one pick per row and does not define adjacency between rows.
Therefore, a complete path exists when every row has at least one safe cell. If
Product wants adjacency constraints later, that is a new math/gameplay rule and
must Stop-and-Ask before implementation.

## 1. Files Audited

| File | Lines | Finding |
| --- | ---: | --- |
| `docs/games/boxe/SPEC.md` | 194-208 | Board is a bottom-to-top pyramid; rows above active row are hidden; terminal responses expose `pyramid_full_reveal`. |
| `docs/games/boxe/SPEC.md` | 210-221 | Difficulty means fewer/more mines and points to `MATH_SPEC.md` for exact probabilities. |
| `docs/games/boxe/SPEC.md` | 223-247 | Payout is backend-owned, RTP target is 98%, and observed multiplier anchors are documented. |
| `docs/games/boxe/MATH_SPEC.md` | 24-76 | Current multiplier ladder is geometric and probabilities are derived from rounded multipliers. |
| `docs/games/boxe/MATH_SPEC.md` | 78-96 | Full multiplier table for 15 rows x difficulty combos. |
| `backend/app/modules/games/boxe/math.py` | 10-13 | RTP target, supported rows and difficulty constants. |
| `backend/app/modules/games/boxe/math.py` | 61-91 | `get_multiplier_ladder` and `get_step_success_probability` derive step probability from the ladder. |
| `backend/app/modules/games/boxe/randomness.py` | 36-79 | `generate_step_outcome` hashes one selected cell and compares the unit interval with step probability. |
| `backend/app/modules/games/boxe/randomness.py` | 82-121 | `generate_pyramid_full_reveal` loops over every cell and resolves each as if independently picked. No row/path constraint exists. |
| `backend/app/modules/games/boxe/service.py` | 78-79 | `cells_for_row(row, rows) = rows - row + 1`; current rows 4-8 therefore have 5-9 cells on the bottom row and 2 cells on the top row. |
| `backend/app/modules/games/boxe/service.py` | 326-334 | Reveal uses `generate_step_outcome` for only the selected cell; no precomputed board is consulted. |
| `backend/app/modules/games/boxe/service.py` | 376-380 | Terminal mine/top-row reveal calls `_pyramid_full_reveal`. |
| `backend/app/modules/games/boxe/service.py` | 880-896 | `_pyramid_full_reveal` regenerates a full board from seeds and picked cells. |
| `backend/app/modules/games/boxe/service.py` | 918-924 | Next-step options use variable `cells_for_row`; frontend can choose any position in the active row. |

## 2. Current Generation Model

Current BOXE does not generate a board at round start.

1. During active play, a pick is resolved by hashing
   `(server_seed, client_seed, nonce, rows, difficulty, step, selected_box_index)`
   and comparing it with `get_step_success_probability`.
2. At terminal reveal, the backend loops over every cell and calls the same
   one-cell resolver for each cell position.
3. Because every cell is independently classified, a row can contain zero safe
   cells.
4. There is no constraint solver, rejection sampling, precomputed path, persisted
   board, or deterministic safe-count table.

This is why Wave 4 full reveal made the issue visible. It exposed a generated
terminal board, but that board is not constrained to be playable.

## 3. Current Impossible-Board Rate

Simulation method:

- 10k fast Monte Carlo per `rows x difficulty`.
- Same probability model as production: row `p = get_step_success_probability`.
- Same cell geometry: `cells = rows - row + 1`.
- A board is impossible when any row has zero safe cells.
- Analytical formula included: `1 - product(1 - (1 - p_row) ^ cells_row)`.
- The slow hash/Decimal production helper was intentionally not used for 150k
  boards because it is unnecessary for this structural probability and timed out.

| Rows | Difficulty | Current step safe probabilities | Per-row zero-safe probability | Impossible-board rate |
| ---: | --- | --- | --- | ---: |
| 4 | easy | `71.5%, 78.3%, 78.1%, 78.0%` | `0.2%, 0.2%, 1.0%, 4.8%` | `6.20%` |
| 4 | medium | `48.8%, 58.1%, 58.2%, 58.1%` | `3.5%, 3.1%, 7.3%, 17.6%` | `28.57%` |
| 4 | hard | `33.3%, 43.2%, 43.1%, 43.2%` | `13.2%, 10.4%, 18.4%, 32.3%` | `57.03%` |
| 5 | easy | `67.1%, 78.1%, 78.2%, 78.4%, 78.0%` | `0.1%, 0.1%, 0.2%, 1.0%, 4.8%` | `6.18%` |
| 5 | medium | `45.8%, 59.1%, 59.1%, 59.0%, 59.0%` | `2.5%, 1.1%, 2.8%, 6.9%, 16.8%` | `27.44%` |
| 5 | hard | `31.3%, 44.6%, 44.5%, 44.6%, 44.6%` | `10.5%, 5.2%, 9.5%, 17.0%, 30.7%` | `55.85%` |
| 6 | easy | `63.2%, 77.9%, 78.3%, 78.2%, 78.1%, 78.2%` | `0.1%, 0.0%, 0.0%, 0.2%, 1.0%, 4.8%` | `6.11%` |
| 6 | medium | `43.2%, 59.9%, 60.0%, 60.0%, 60.0%, 60.0%` | `1.9%, 0.4%, 1.0%, 2.6%, 6.4%, 16.0%` | `25.96%` |
| 6 | hard | `29.4%, 46.0%, 46.0%, 46.0%, 46.0%, 46.0%` | `8.7%, 2.5%, 4.6%, 8.5%, 15.7%, 29.1%` | `53.56%` |
| 7 | easy | `59.4%, 78.2%, 77.9%, 78.3%, 78.1%, 78.3%, 78.1%` | `0.1%, 0.0%, 0.0%, 0.0%, 0.2%, 1.0%, 4.8%` | `6.13%` |
| 7 | medium | `40.5%, 61.0%, 60.9%, 61.0%, 61.0%, 61.0%, 61.0%` | `1.6%, 0.1%, 0.4%, 0.9%, 2.3%, 6.0%, 15.2%` | `24.43%` |
| 7 | hard | `27.6%, 47.6%, 47.5%, 47.6%, 47.5%, 47.5%, 47.5%` | `7.5%, 1.1%, 2.1%, 4.0%, 7.6%, 14.4%, 27.5%` | `50.71%` |
| 8 | easy | `55.7%, 78.2%, 78.1%, 78.3%, 78.1%, 78.1%, 78.1%, 78.2%` | `0.1%, 0.0%, 0.0%, 0.0%, 0.1%, 0.2%, 1.0%, 4.7%` | `6.08%` |
| 8 | medium | `38.0%, 62.0%, 61.9%, 62.0%, 61.9%, 61.9%, 62.0%, 62.0%` | `1.4%, 0.0%, 0.1%, 0.3%, 0.8%, 2.1%, 5.5%, 14.5%` | `22.93%` |
| 8 | hard | `25.9%, 49.2%, 49.1%, 49.1%, 49.1%, 49.1%, 49.1%, 49.1%` | `6.7%, 0.4%, 0.9%, 1.7%, 3.4%, 6.7%, 13.2%, 25.9%` | `47.58%` |

Verdict: the bug is systemic, not rare. HARD can produce structurally impossible
terminal pyramids in roughly half of rounds.

## 4. Design Options

| Option | Description | RTP impact | Replay determinism | Verdict |
| --- | --- | --- | --- | --- |
| A. Repair terminal reveal only | Keep current selected-cell RNG, but when full reveal has an all-mine row, flip one unpicked cell to safe. | Gameplay RTP unchanged because pick outcome still uses current probabilities. | Replay deterministic if repair is seed-derived. | Not recommended as the main fix. It creates a board display that is not the board used for picks. |
| B. Rejection sampling | Generate full boards with current independent per-cell probabilities until every row has a safe. | Changes conditional probability distribution and therefore pick RTP unless ladder is rederived. | Deterministic if seed cursor is deterministic. | Expensive/opaque, especially HARD; not a good audit surface. |
| C. Deterministic safe-count board | For each row choose exact safe count from product probabilities, shuffle positions from seed, and resolve picks from that board. | Clean if multiplier ladder is recalculated from exact row probabilities. | Strong: same helper resolves picks, reveal and replay. | Recommended. |
| D. Persist precomputed board at round start | Same as C, but store the board JSON. | Same as C. | Strong, but adds schema/storage surface. | Only needed if audit requires immutable board snapshots independent from seed retention. |

Recommended architecture: **Option C, derive-deterministic-from-seed**.

This keeps scope smaller than a migration while making the board truly
server-authoritative. The same deterministic helper must be consumed by:

- active pick resolution;
- terminal `pyramid_full_reveal`;
- player replay;
- admin replay;
- fairness verifier/tests.

## 5. Proposed Algorithm

### 5.1 Definitions

```text
cells_for_row(row, rows) = rows - row + 1
safe_count_for_row(row, rows, difficulty) =
  clamp(round_half_up(target_safe_probability[difficulty] * cells_for_row), 1, cells_for_row - 1)
row_success_probability = safe_count_for_row / cells_for_row
```

`cells_for_row - 1` is safe because the current geometry never has fewer than 2
cells. This preserves "at least one safe" and "at least one mine" in every row.

### 5.2 Board Derivation

For each row:

1. Build row RNG material from `fairness_version`, `game_code`, `server_seed`,
   `client_seed`, `nonce`, `rows`, `difficulty`, and `row`.
2. Deterministically shuffle positions `0..cells_for_row-1`.
3. Mark the first `safe_count_for_row` shuffled positions as safe; all remaining
   positions are mines.
4. Active pick outcome is `board[row][selected_box_index]`.
5. `pyramid_full_reveal` is the same board plus picked metadata.

This guarantees:

- 100% path existence by construction;
- no active-round exposure of hidden board contents;
- deterministic replay without storing the board;
- no contradiction between a picked outcome and terminal reveal.

### 5.3 Multiplier Formula Under Board-Authoritative Math

If pick outcomes come from exact row safe counts, the fair multiplier must be:

```text
cumulative_probability(step) =
  product(row_success_probability(row) for row in 0..step-1)

multiplier(step) =
  round_2(RTP_TARGET / cumulative_probability(step))
```

This is the same RTP philosophy as current `MATH_SPEC.md`, but probability
becomes board-derived instead of multiplier-derived.

## 6. Product Probability Candidate Analysis

Michele's guidance is directional: `EASY > MEDIUM > HARD`, roughly EASY
60-70%, MEDIUM 45-55%, HARD 30-40%. The exact values should be selected after
simulating with safe-path constraints and preserving 98% RTP.

The table below shows four candidate sets. `Old top RTP` is what happens if we
keep today's multiplier ladder while changing pick math to exact safe-count
boards. `Fair M1 -> top` is the recalculated ladder range needed to restore 98%
for every cashout step.

| Candidate | Rows | Difficulty | Safe counts bottom-to-top | Realized row probabilities | Safe-path rate | Old top RTP | Worst old-step delta | Fair M1 -> top |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 70/50/30 | 4 | easy | `[4, 3, 2, 1]` | `80.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.574` | `0.406` | `1.22x -> 4.90x` |
| 70/50/30 | 4 | medium | `[2, 2, 2, 1]` | `40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.683` | `0.297` | `2.45x -> 14.70x` |
| 70/50/30 | 4 | hard | `[2, 1, 1, 1]` | `40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.610` | `0.454` | `2.45x -> 58.80x` |
| 70/50/30 | 5 | easy | `[4, 4, 3, 2, 1]` | `66.7%, 80.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.521` | `0.459` | `1.47x -> 7.35x` |
| 70/50/30 | 5 | medium | `[3, 2, 2, 2, 1]` | `50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.587` | `0.393` | `1.96x -> 29.40x` |
| 70/50/30 | 5 | hard | `[2, 2, 1, 1, 1]` | `33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.441` | `0.587` | `2.94x -> 176.40x` |
| 70/50/30 | 6 | easy | `[5, 4, 4, 3, 2, 1]` | `71.4%, 66.7%, 80.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.507` | `0.473` | `1.37x -> 10.29x` |
| 70/50/30 | 6 | medium | `[4, 3, 2, 2, 2, 1]` | `57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.558` | `0.422` | `1.72x -> 51.45x` |
| 70/50/30 | 6 | hard | `[2, 2, 2, 1, 1, 1]` | `28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.256` | `0.744` | `3.43x -> 617.40x` |
| 70/50/30 | 7 | easy | `[6, 5, 4, 4, 3, 2, 1]` | `75.0%, 71.4%, 66.7%, 80.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.518` | `0.462` | `1.31x -> 13.72x` |
| 70/50/30 | 7 | medium | `[4, 4, 3, 2, 2, 2, 1]` | `50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.449` | `0.531` | `1.96x -> 102.90x` |
| 70/50/30 | 7 | hard | `[2, 2, 2, 2, 1, 1, 1]` | `25.0%, 28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.122` | `0.864` | `3.92x -> 2469.60x` |
| 70/50/30 | 8 | easy | `[6, 6, 5, 4, 4, 3, 2, 1]` | `66.7%, 75.0%, 71.4%, 66.7%, 80.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.470` | `0.510` | `1.47x -> 20.58x` |
| 70/50/30 | 8 | medium | `[4, 4, 4, 3, 2, 2, 2, 1]` | `44.4%, 50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.312` | `0.668` | `2.21x -> 231.53x` |
| 70/50/30 | 8 | hard | `[3, 2, 2, 2, 2, 1, 1, 1]` | `33.3%, 25.0%, 28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.073` | `0.909` | `2.94x -> 7408.80x` |
| 65/50/35 | 4 | easy | `[3, 3, 2, 1]` | `60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.430` | `0.550` | `1.63x -> 6.53x` |
| 65/50/35 | 4 | medium | `[2, 2, 2, 1]` | `40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.683` | `0.297` | `2.45x -> 14.70x` |
| 65/50/35 | 4 | hard | `[2, 1, 1, 1]` | `40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.610` | `0.454` | `2.45x -> 58.80x` |
| 65/50/35 | 5 | easy | `[4, 3, 3, 2, 1]` | `66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.391` | `0.589` | `1.47x -> 9.80x` |
| 65/50/35 | 5 | medium | `[3, 2, 2, 2, 1]` | `50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.587` | `0.393` | `1.96x -> 29.40x` |
| 65/50/35 | 5 | hard | `[2, 2, 1, 1, 1]` | `33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.441` | `0.587` | `2.94x -> 176.40x` |
| 65/50/35 | 6 | easy | `[5, 4, 3, 3, 2, 1]` | `71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.380` | `0.600` | `1.37x -> 13.72x` |
| 65/50/35 | 6 | medium | `[4, 3, 2, 2, 2, 1]` | `57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.558` | `0.422` | `1.72x -> 51.45x` |
| 65/50/35 | 6 | hard | `[2, 2, 2, 1, 1, 1]` | `28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.256` | `0.744` | `3.43x -> 617.40x` |
| 65/50/35 | 7 | easy | `[5, 5, 4, 3, 3, 2, 1]` | `62.5%, 71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.324` | `0.656` | `1.57x -> 21.95x` |
| 65/50/35 | 7 | medium | `[4, 4, 3, 2, 2, 2, 1]` | `50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.449` | `0.531` | `1.96x -> 102.90x` |
| 65/50/35 | 7 | hard | `[3, 2, 2, 2, 1, 1, 1]` | `37.5%, 28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.183` | `0.806` | `2.61x -> 1646.40x` |
| 65/50/35 | 8 | easy | `[6, 5, 5, 4, 3, 3, 2, 1]` | `66.7%, 62.5%, 71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.294` | `0.686` | `1.47x -> 32.93x` |
| 65/50/35 | 8 | medium | `[4, 4, 4, 3, 2, 2, 2, 1]` | `44.4%, 50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.312` | `0.668` | `2.21x -> 231.53x` |
| 65/50/35 | 8 | hard | `[3, 3, 2, 2, 2, 1, 1, 1]` | `33.3%, 37.5%, 28.6%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.109` | `0.873` | `2.94x -> 4939.20x` |
| 60/50/40 | 4 | easy | `[3, 2, 2, 1]` | `60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.287` | `0.693` | `1.63x -> 9.80x` |
| 60/50/40 | 4 | medium | `[2, 2, 2, 1]` | `40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.683` | `0.297` | `2.45x -> 14.70x` |
| 60/50/40 | 4 | hard | `[2, 2, 1, 1]` | `40.0%, 50.0%, 33.3%, 50.0%` | `100%` | `1.219` | `0.382` | `2.45x -> 29.40x` |
| 60/50/40 | 5 | easy | `[4, 3, 2, 2, 1]` | `66.7%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.261` | `0.719` | `1.47x -> 14.70x` |
| 60/50/40 | 5 | medium | `[3, 2, 2, 2, 1]` | `50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.587` | `0.393` | `1.96x -> 29.40x` |
| 60/50/40 | 5 | hard | `[2, 2, 2, 1, 1]` | `33.3%, 40.0%, 50.0%, 33.3%, 50.0%` | `100%` | `0.881` | `0.194` | `2.94x -> 88.20x` |
| 60/50/40 | 6 | easy | `[4, 4, 3, 2, 2, 1]` | `57.1%, 66.7%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.203` | `0.777` | `1.72x -> 25.73x` |
| 60/50/40 | 6 | medium | `[4, 3, 2, 2, 2, 1]` | `57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.558` | `0.422` | `1.72x -> 51.45x` |
| 60/50/40 | 6 | hard | `[3, 2, 2, 2, 1, 1]` | `42.9%, 33.3%, 40.0%, 50.0%, 33.3%, 50.0%` | `100%` | `0.768` | `0.447` | `2.29x -> 205.80x` |
| 60/50/40 | 7 | easy | `[5, 4, 4, 3, 2, 2, 1]` | `62.5%, 57.1%, 66.7%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.173` | `0.807` | `1.57x -> 41.16x` |
| 60/50/40 | 7 | medium | `[4, 4, 3, 2, 2, 2, 1]` | `50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.449` | `0.531` | `1.96x -> 102.90x` |
| 60/50/40 | 7 | hard | `[3, 3, 2, 2, 2, 1, 1]` | `37.5%, 42.9%, 33.3%, 40.0%, 50.0%, 33.3%, 50.0%` | `100%` | `0.549` | `0.458` | `2.61x -> 548.80x` |
| 60/50/40 | 8 | easy | `[5, 5, 4, 4, 3, 2, 2, 1]` | `55.6%, 62.5%, 57.1%, 66.7%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.131` | `0.849` | `1.76x -> 74.09x` |
| 60/50/40 | 8 | medium | `[4, 4, 4, 3, 2, 2, 2, 1]` | `44.4%, 50.0%, 57.1%, 50.0%, 40.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.312` | `0.668` | `2.21x -> 231.53x` |
| 60/50/40 | 8 | hard | `[4, 3, 3, 2, 2, 2, 1, 1]` | `44.4%, 37.5%, 42.9%, 33.3%, 40.0%, 50.0%, 33.3%, 50.0%` | `100%` | `0.436` | `0.700` | `2.21x -> 1234.80x` |
| 65/52/37 | 4 | easy | `[3, 3, 2, 1]` | `60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.430` | `0.550` | `1.63x -> 6.53x` |
| 65/52/37 | 4 | medium | `[3, 2, 2, 1]` | `60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `1.024` | `0.226` | `1.63x -> 9.80x` |
| 65/52/37 | 4 | hard | `[2, 1, 1, 1]` | `40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.610` | `0.454` | `2.45x -> 58.80x` |
| 65/52/37 | 5 | easy | `[4, 3, 3, 2, 1]` | `66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.391` | `0.589` | `1.47x -> 9.80x` |
| 65/52/37 | 5 | medium | `[3, 3, 2, 2, 1]` | `50.0%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.880` | `0.106` | `1.96x -> 19.60x` |
| 65/52/37 | 5 | hard | `[2, 2, 1, 1, 1]` | `33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.441` | `0.587` | `2.94x -> 176.40x` |
| 65/52/37 | 6 | easy | `[5, 4, 3, 3, 2, 1]` | `71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.380` | `0.600` | `1.37x -> 13.72x` |
| 65/52/37 | 6 | medium | `[4, 3, 3, 2, 2, 1]` | `57.1%, 50.0%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.837` | `0.317` | `1.72x -> 34.30x` |
| 65/52/37 | 6 | hard | `[3, 2, 2, 1, 1, 1]` | `42.9%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.384` | `0.627` | `2.29x -> 411.60x` |
| 65/52/37 | 7 | easy | `[5, 5, 4, 3, 3, 2, 1]` | `62.5%, 71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.324` | `0.656` | `1.57x -> 21.95x` |
| 65/52/37 | 7 | medium | `[4, 4, 3, 3, 2, 2, 1]` | `50.0%, 57.1%, 50.0%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.674` | `0.306` | `1.96x -> 68.60x` |
| 65/52/37 | 7 | hard | `[3, 3, 2, 2, 1, 1, 1]` | `37.5%, 42.9%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.274` | `0.719` | `2.61x -> 1097.60x` |
| 65/52/37 | 8 | easy | `[6, 5, 5, 4, 3, 3, 2, 1]` | `66.7%, 62.5%, 71.4%, 66.7%, 60.0%, 75.0%, 66.7%, 50.0%` | `100%` | `0.294` | `0.686` | `1.47x -> 32.93x` |
| 65/52/37 | 8 | medium | `[5, 4, 4, 3, 3, 2, 2, 1]` | `55.6%, 50.0%, 57.1%, 50.0%, 60.0%, 50.0%, 66.7%, 50.0%` | `100%` | `0.584` | `0.453` | `1.76x -> 123.48x` |
| 65/52/37 | 8 | hard | `[3, 3, 3, 2, 2, 1, 1, 1]` | `33.3%, 37.5%, 42.9%, 33.3%, 40.0%, 25.0%, 33.3%, 50.0%` | `100%` | `0.163` | `0.820` | `2.94x -> 3292.80x` |

## 7. Recommendation To CTO

No simple product-probability set can both:

1. make the board truly safe-path constrained and server-authoritative;
2. preserve the current geometric multiplier anchors exactly;
3. keep 98% RTP across all cashout steps.

The conflict is structural: exact board-safe probabilities are rational values
`safe_count / cells`, while the current ladder derives probabilities from
rounded multiplier anchors. Once picks are resolved from a real board, RTP must
follow the board probabilities.

Recommended product/math direction for Parte B:

| Decision | Recommendation | Reason |
| --- | --- | --- |
| Board model | Deterministic seed-derived full board with exact safe counts per row. | Fixes safe-path invariant and keeps replay/fairness coherent. |
| Candidate probabilities | Start implementation exploration with `60/50/40` targets. | It is inside Michele's range, keeps `EASY > MEDIUM > HARD`, avoids extreme hard multipliers compared with `30/35` HARD candidates, and is closest to current hard volatility among tested sets. |
| RTP preservation | Recalculate ladder from exact row probabilities with `0.98 / cumulative_probability`. | This is the only clean way to preserve 98% when board cells drive outcomes. |
| Existing anchors | Treat current anchors as superseded unless CTO/Product explicitly freezes them. | Current anchors and exact safe-count board math cannot both hold across 15 combos. |

If Product cares more about preserving the current multiplier anchors than about a
true server-authoritative board, the fallback is Option A: repair only the
terminal reveal. I do not recommend that as the primary solution because it
keeps gameplay outcome and displayed board as separate concepts.

## 8. SPEC Updates Proposed For Parte B

Do not edit `SPEC.md` in Parte A. Proposed text:

### 1.7 Board Model

Add:

```text
Safe-path invariant: every generated BOXE board must contain at least one safe
cell in every row. With the current no-adjacency pick model, this guarantees at
least one complete bottom-to-top safe path. The board is deterministic from
server seed, client seed, nonce, rows, difficulty and fairness version. Active
picks, terminal reveal and replay must consume the same board derivation.
```

### 1.8 Difficulty Semantics

Replace "exact success probabilities are defined by MATH_SPEC" with:

```text
Difficulty defines target safe-cell density. The exact per-row probabilities are
the integer safe counts produced by `safe_count_for_row / cells_for_row`.
Initial Wave 6 candidate targets are EASY 60%, MEDIUM 50%, HARD 40%, pending CTO
approval after RTP/ladders are reviewed.
```

### MATH_SPEC

Update the formula to make multipliers derive from board probabilities:

```text
row_success_probability(row) = safe_count_for_row(row, rows, difficulty) / cells_for_row(row, rows)
cumulative_success_probability(step) = product(row_success_probability(0..step-1))
multiplier(step) = round_2(0.98 / cumulative_success_probability(step))
```

## 9. Parte B Granularity

| Commit | Scope | Files |
| --- | --- | --- |
| `feat(boxe): add deterministic safe path board math` | Add `cells_for_row`, `safe_count_for_row`, `derive_board`, row shuffle helper, and board-based pick resolver. | `backend/app/modules/games/boxe/math.py`, `backend/app/modules/games/boxe/randomness.py` |
| `refactor(boxe): resolve picks and reveal from derived board` | Replace selected-cell independent RNG with board lookup; terminal reveal and replay consume same board. | `backend/app/modules/games/boxe/service.py`, replay payload helpers |
| `feat(boxe): recalculate multipliers from board probabilities` | Rebuild multiplier ladder from exact safe counts and RTP target. | `math.py`, `MATH_SPEC.md`, tests |
| `test(boxe): enforce safe path invariant and rtp` | 100k+ boards per combo path invariant; analytical RTP tests; deterministic replay parity tests. | `tests/unit` or `tests/integration` |
| `docs(boxe): update safe path spec` | Apply SPEC/MATH_SPEC updates after CTO approval. | `docs/games/boxe/SPEC.md`, `docs/games/boxe/MATH_SPEC.md` |

Expected effort: 10-16 prompts, higher if Product freezes current multiplier
anchors and asks for a constrained optimization pass.

## 10. Parte B Test Contract

| Gate | Requirement |
| --- | --- |
| Safe-path invariant | Generate at least 100k boards for each of 15 combos; every board has at least one safe per row. |
| Exact row counts | For every generated board, safe/mine counts equal `safe_count_for_row` and `cells_for_row - safe_count_for_row`. |
| Determinism | Same seed/config produces identical board, pick result, terminal reveal and replay payload. |
| RTP analytical | Every cashout step has theoretical RTP within rounding tolerance of 98%. |
| RTP simulation | Variance-reduced simulation for top-row and typical cashout strategies stays inside agreed CI band. |
| Smoke | Existing BOXE cashout/loss/top-row flows pass with updated safe-path helpers. |
| Replay | Replay uses the same `pyramid_full_reveal`; no deterministic drift. |
| Mines | No Mines code touched. |

## 11. Stop-and-Ask

| Trigger | Why |
| --- | --- |
| CTO/Product requires current observed anchors to remain exact. | Safe-count board probabilities cannot preserve all existing anchors and 98% simultaneously. |
| Product defines adjacency-based path, not just one safe per row. | Current SPEC has no adjacency; algorithm and tests change materially. |
| Product rejects recalculated multipliers above/below current visual expectations. | Need a product-approved complete safe-count and multiplier table. |
| Legal/fairness requires persisted board snapshot rather than seed-derived board. | Requires schema/API migration and replay storage changes. |
| RTP simulation shows >2% deviation after ladder recalculation. | Indicates implementation bug or rounding policy needs a math WP. |

## 12. Capability Matrix

| Capability | DB | Backend | API payload | Frontend | Replay | Tests | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current impossible-board audit | N/A | Audited | N/A | N/A | N/A | 10k fast MC + analytical | This doc | Complete |
| Safe-path invariant | No schema if seed-derived | Planned | Existing reveal shape can stay | Existing board can consume same payload | Planned deterministic | Planned 100k/combo | Proposed SPEC update | Proposed |
| Board-authoritative picks | No schema if seed-derived | Planned | No active hidden state exposure | No player UI math | Planned | Planned | MATH_SPEC update | Proposed |
| RTP 98% preservation | N/A | Requires ladder recalculation | Multiplier payload changes | Display only | Same multipliers | Analytical + simulation | MATH_SPEC update | Stop-and-Ask for anchors |
| Mines zero-diff | N/A | N/A | N/A | Required | N/A | Required | This doc | Guardrail |

## 13. Parte B Implementation Update - 2026-05-22

CTO decisions resolved the Parte A Stop-and-Ask:

- RTP 98% remains hard.
- Safe-path invariant remains hard.
- Product target safe densities are `60/50/40` for EASY/MEDIUM/HARD.
- Existing observed anchors are not frozen.
- Multiplier ladder is recalculated from realized board probabilities.
- Board derivation is deterministic from seed/config/nonce and is consumed by
  active picks, terminal full reveal and replay.

Final implementation notes:

- Rounding policy is explicit `ROUND_HALF_EVEN` (Python/banker's rounding) for
  converting product densities into integer safe counts. This matches the
  approved Parte A `60/50/40` candidate table; the older prose mentioning
  `round_half_up` is superseded by this section and `MATH_SPEC.md`.
- Realized per-row success probability is `safe_count / cells_for_row`, so ties
  and integer cells can make individual rows equal across difficulties. The
  product density still controls the full safe-count curve.
- Multiplier precision is four decimals to match persisted pick snapshots
  (`numeric(18,4)`). Theoretical RTP is 98% within multiplier precision.

Updated capability matrix:

| Capability | DB | Backend | API payload | Frontend | Replay | Tests | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Safe-path invariant | No schema change | `derive_boxe_board` guarantees at least one safe and one mine per row | Existing reveal shape | Existing renderer consumes same payload | Same helper powers replay reveal | Unit + stress gate | SPEC/MATH_SPEC updated | Green |
| Board-authoritative picks | No schema change | `generate_step_outcome` now resolves from derived board | No hidden board exposure during active play | No frontend math | Fairness artifacts recompute same pick outcomes | Deterministic board unit tests | MATH_SPEC updated | Green |
| RTP 98% preservation | No schema change | Ladder recalculated from realized row probabilities | Multiplier strings now four decimals | Display only | Replay uses stored/current multiplier ladder | Unit + verifier | MATH_SPEC table updated | Green |
| Terminal full reveal consistency | No schema change | `generate_pyramid_full_reveal` uses same board | Existing `pyramid_full_reveal` payload | Display only | Replay recomputes same payload if needed | Unit + focused smoke | SPEC updated | Green |
| Mines zero-diff | N/A | No Mines imports/touches | N/A | No Mines frontend touched | N/A | Path check required | This doc | Guardrail maintained |

