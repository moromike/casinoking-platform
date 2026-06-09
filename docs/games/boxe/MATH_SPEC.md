Status: ACTIVE
Last meaningful update: 2026-05-22

# BOXE - Math, RNG And Fairness Spec

Output aggiornato da Wave 6 `WP-MATH-SAFE-PATH`.

Questo documento sostituisce la ladder geometrica Fase 2A. La decisione CTO del
2026-05-22 rende hard sia RTP 98% sia safe-path strutturale. Gli anchor osservati
precedenti (es. `1.37x`, `2.94x`, `548.80x`) non sono congelati: sono superseded
dalla ladder ricalibrata sotto.

## 1. Scope

| Campo | Valore |
| --- | --- |
| Game code | `boxe` |
| Supported rows | `4`, `5`, `6`, `7`, `8` |
| Difficulties | `easy`, `medium`, `hard` |
| Target safe densities | EASY `60%`, MEDIUM `50%`, HARD `40%` |
| RTP target | `98%` |
| Max win cap | `null` v1 |
| Frontend math | Forbidden |
| Outcome authority | Backend deterministic board only |
| Replay determinism | Same board derivation for active picks, terminal reveal and replay |

## 2. Board Geometry

Rows are ordered bottom-to-top. For a configured `rows` value and zero-based
`row`:

```text
cells_for_row(row, rows) = rows - row + 1
```

Examples:

| Rows | Cells bottom-to-top |
| ---: | --- |
| 4 | `[5, 4, 3, 2]` |
| 5 | `[6, 5, 4, 3, 2]` |
| 6 | `[7, 6, 5, 4, 3, 2]` |
| 7 | `[8, 7, 6, 5, 4, 3, 2]` |
| 8 | `[9, 8, 7, 6, 5, 4, 3, 2]` |

## 3. Safe Count Policy

Product target densities are directional safe-cell densities:

| Difficulty | Target density |
| --- | ---: |
| EASY | `0.60` |
| MEDIUM | `0.50` |
| HARD | `0.40` |

Because rows contain integer cells, realized per-row probabilities are exact
fractions:

```text
raw_safe_count = target_density[difficulty] * cells_for_row(row, rows)
safe_count = round_half_even(raw_safe_count)
safe_count = clamp(safe_count, 1, cells_for_row(row, rows) - 1)
mine_count = cells_for_row(row, rows) - safe_count
row_success_probability = safe_count / cells_for_row(row, rows)
```

Rounding policy is intentionally `ROUND_HALF_EVEN` (Python/banker's rounding).
The Parte A candidate table approved for `60/50/40` used this policy in its
integer safe-count examples. This avoids a systematic upward bias on `.5` rows
and keeps the realized table aligned with the approved analysis.

The target densities are not a promise that every row is exactly 60/50/40. The
runtime probability used for RTP is always the realized fraction
`safe_count / cells_for_row`.

Every row has at least one safe cell and at least one mine by construction.
Given BOXE currently has no adjacency rule, this guarantees at least one
complete bottom-to-top safe path.

## 4. Deterministic Board Derivation

BOXE now derives a full board from seed material before resolving an active pick
or terminal reveal. The board is not exposed while a round is active.

Per row:

1. Build deterministic cell material from `fairness_version`, `game_code`,
   `server_seed`, `client_seed`, `nonce`, `rows`, `difficulty`, `row`,
   `position`, and source `safe_count_board`.
2. Sort row positions by SHA-256 digest.
3. Mark the first `safe_count` positions as safe.
4. Mark remaining positions as mines.
5. Resolve active pick by looking up the selected cell in that same board.
6. Generate `pyramid_full_reveal` and replay from the same helper.

Fairness version for new rounds: `boxe_seed_v2`.

## 5. Multiplier Formula

Multipliers are derived from the realized board probabilities:

```text
cumulative_success_probability(step) =
  product(row_success_probability(row) for row in 0..step-1)

multiplier(step) =
  round_4(0.98 / cumulative_success_probability(step), ROUND_HALF_UP)

theoretical_rtp(step) =
  cumulative_success_probability(step) * multiplier(step)
```

Multiplier precision is four decimals because the database column for pick
multiplier snapshots is `numeric(18,4)`. RTP is exact to multiplier precision;
the largest observed rounding drift in the table below is `0.0014 percentage
points`, far below the hard 98% gate tolerance used by tests.

Payout amount remains:

```text
payout = round_2(bet_amount * multiplier, ROUND_HALF_UP)
```

## 6. Complete Safe Count And Multiplier Table

| Rows | Difficulty | Cells | Safe counts | Mine counts | Row probabilities | Multipliers | RTP range |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 4 | easy | `[5, 4, 3, 2]` | `[3, 2, 2, 1]` | `[2, 2, 1, 1]` | `60.00%, 50.00%, 66.67%, 50.00%` | `1.6333, 3.2667, 4.9000, 9.8000` | `97.9980% - 98.0010%` |
| 4 | medium | `[5, 4, 3, 2]` | `[2, 2, 2, 1]` | `[3, 2, 1, 1]` | `40.00%, 50.00%, 66.67%, 50.00%` | `2.4500, 4.9000, 7.3500, 14.7000` | `98.0000% - 98.0000%` |
| 4 | hard | `[5, 4, 3, 2]` | `[2, 2, 1, 1]` | `[3, 2, 2, 1]` | `40.00%, 50.00%, 33.33%, 50.00%` | `2.4500, 4.9000, 14.7000, 29.4000` | `98.0000% - 98.0000%` |
| 5 | easy | `[6, 5, 4, 3, 2]` | `[4, 3, 2, 2, 1]` | `[2, 2, 2, 1, 1]` | `66.67%, 60.00%, 50.00%, 66.67%, 50.00%` | `1.4700, 2.4500, 4.9000, 7.3500, 14.7000` | `98.0000% - 98.0000%` |
| 5 | medium | `[6, 5, 4, 3, 2]` | `[3, 2, 2, 2, 1]` | `[3, 3, 2, 1, 1]` | `50.00%, 40.00%, 50.00%, 66.67%, 50.00%` | `1.9600, 4.9000, 9.8000, 14.7000, 29.4000` | `98.0000% - 98.0000%` |
| 5 | hard | `[6, 5, 4, 3, 2]` | `[2, 2, 2, 1, 1]` | `[4, 3, 2, 2, 1]` | `33.33%, 40.00%, 50.00%, 33.33%, 50.00%` | `2.9400, 7.3500, 14.7000, 44.1000, 88.2000` | `98.0000% - 98.0000%` |
| 6 | easy | `[7, 6, 5, 4, 3, 2]` | `[4, 4, 3, 2, 2, 1]` | `[3, 2, 2, 2, 1, 1]` | `57.14%, 66.67%, 60.00%, 50.00%, 66.67%, 50.00%` | `1.7150, 2.5725, 4.2875, 8.5750, 12.8625, 25.7250` | `98.0000% - 98.0000%` |
| 6 | medium | `[7, 6, 5, 4, 3, 2]` | `[4, 3, 2, 2, 2, 1]` | `[3, 3, 3, 2, 1, 1]` | `57.14%, 50.00%, 40.00%, 50.00%, 66.67%, 50.00%` | `1.7150, 3.4300, 8.5750, 17.1500, 25.7250, 51.4500` | `98.0000% - 98.0000%` |
| 6 | hard | `[7, 6, 5, 4, 3, 2]` | `[3, 2, 2, 2, 1, 1]` | `[4, 4, 3, 2, 2, 1]` | `42.86%, 33.33%, 40.00%, 50.00%, 33.33%, 50.00%` | `2.2867, 6.8600, 17.1500, 34.3000, 102.9000, 205.8000` | `98.0000% - 98.0014%` |
| 7 | easy | `[8, 7, 6, 5, 4, 3, 2]` | `[5, 4, 4, 3, 2, 2, 1]` | `[3, 3, 2, 2, 2, 1, 1]` | `62.50%, 57.14%, 66.67%, 60.00%, 50.00%, 66.67%, 50.00%` | `1.5680, 2.7440, 4.1160, 6.8600, 13.7200, 20.5800, 41.1600` | `98.0000% - 98.0000%` |
| 7 | medium | `[8, 7, 6, 5, 4, 3, 2]` | `[4, 4, 3, 2, 2, 2, 1]` | `[4, 3, 3, 3, 2, 1, 1]` | `50.00%, 57.14%, 50.00%, 40.00%, 50.00%, 66.67%, 50.00%` | `1.9600, 3.4300, 6.8600, 17.1500, 34.3000, 51.4500, 102.9000` | `98.0000% - 98.0000%` |
| 7 | hard | `[8, 7, 6, 5, 4, 3, 2]` | `[3, 3, 2, 2, 2, 1, 1]` | `[5, 4, 4, 3, 2, 2, 1]` | `37.50%, 42.86%, 33.33%, 40.00%, 50.00%, 33.33%, 50.00%` | `2.6133, 6.0978, 18.2933, 45.7333, 91.4667, 274.4000, 548.8000` | `97.9988% - 98.0004%` |
| 8 | easy | `[9, 8, 7, 6, 5, 4, 3, 2]` | `[5, 5, 4, 4, 3, 2, 2, 1]` | `[4, 3, 3, 2, 2, 2, 1, 1]` | `55.56%, 62.50%, 57.14%, 66.67%, 60.00%, 50.00%, 66.67%, 50.00%` | `1.7640, 2.8224, 4.9392, 7.4088, 12.3480, 24.6960, 37.0440, 74.0880` | `98.0000% - 98.0000%` |
| 8 | medium | `[9, 8, 7, 6, 5, 4, 3, 2]` | `[4, 4, 4, 3, 2, 2, 2, 1]` | `[5, 4, 3, 3, 3, 2, 1, 1]` | `44.44%, 50.00%, 57.14%, 50.00%, 40.00%, 50.00%, 66.67%, 50.00%` | `2.2050, 4.4100, 7.7175, 15.4350, 38.5875, 77.1750, 115.7625, 231.5250` | `98.0000% - 98.0000%` |
| 8 | hard | `[9, 8, 7, 6, 5, 4, 3, 2]` | `[4, 3, 3, 2, 2, 2, 1, 1]` | `[5, 5, 4, 4, 3, 2, 2, 1]` | `44.44%, 37.50%, 42.86%, 33.33%, 40.00%, 50.00%, 33.33%, 50.00%` | `2.2050, 5.8800, 13.7200, 41.1600, 102.9000, 205.8000, 617.4000, 1234.8000` | `98.0000% - 98.0000%` |

## 7. Validation Contract

| Gate | Requirement |
| --- | --- |
| Safe path | 100k generated boards per `rows x difficulty`; every row has at least one safe and one mine. |
| Exact counts | Every generated row has `safe_count_for_row` safe cells and the complement mines. |
| Determinism | Same seed/config/nonce produces identical board, pick outcome, terminal reveal and replay. |
| RTP theoretical | Every cashout step is within `0.0001` absolute RTP of `0.98` after multiplier precision. |
| RTP simulation | Stratified top-row simulation remains inside `97.5%..98.5%` at 100k rounds. |
| Mines | No Mines math/runtime code is imported or changed. |

## 8. External Validator

Standalone simulator:

```powershell
python tools/boxe_math_simulator.py --rows 8 --difficulty hard --bet 1.00 --seed boxe-ci --num-rounds 100000
```

RTP report:

```powershell
python tools/boxe_rtp_verify.py --write-report artifacts/wave6_math_safe_path_2026-05-22/rtp_safe_path_report.md
```

Safe-path stress:

```powershell
$env:RUN_BOXE_STRESS='1'
$env:BOXE_SAFE_PATH_STRESS_BOARDS='100000'
python -m pytest tests/stress/boxe_math/test_boxe_safe_path_stress.py -q
```

## 9. Edge Cases

| Edge case | Decision |
| --- | --- |
| Unsupported rows | Raise validation error. |
| Unsupported difficulty | Raise validation error. |
| Step outside row count | Raise validation error. |
| Position outside row geometry | Reject as invalid position. |
| Max win cap | Not applied in v1. |
| Payout frontend calculation | Forbidden. |
| Wallet/ledger settlement | Platform-owned. |
| Persisted board snapshot | Not needed in Wave 6; board derives deterministically from seed/config/nonce. |
