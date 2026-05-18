Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE - Math, RNG And Fairness Spec

Output di `WP-BOXE-2A-MATH-RNG-FAIRNESS`.

Questo documento formalizza la matematica BOXE v1 derivata dagli anchor approvati
nel `docs/games/boxe/SPEC.md` sezione 1.10 e dal target RTP 98%.

## 1. Scope

| Campo | Valore |
| --- | --- |
| Game code | `boxe` |
| Supported rows | `4`, `5`, `6`, `7`, `8` |
| Difficulties | `easy`, `medium`, `hard` |
| RTP target | `98%` |
| Max win cap | `null` v1 |
| Frontend math | Forbidden |
| Wallet/ledger/platform rounds | Out of scope 2A |
| External research | Not used |

## 2. Formula

BOXE v1 uses a geometric multiplier ladder.

```text
multiplier(step, rows, difficulty) =
  round_2(first_multiplier(rows, difficulty) * growth_factor(rows, difficulty)^(step - 1))
```

The first multiplier and growth factor are derived in log-space from the
approved anchors.

```text
row_t = (rows - 4) / 4
difficulty_weight = easy: 0, medium: 0.5, hard: 1

easy_first(rows) = log_lerp(1.37, 1.76, row_t)
hard_first(rows) = easy_first(rows) * (2.94 / 1.37)
first_multiplier(rows, difficulty) =
  log_lerp(easy_first(rows), hard_first(rows), difficulty_weight)

easy_growth = (9.87 / 1.76)^(1 / 7)
hard_growth_4 = (36.58 / 2.94)^(1 / 3)
hard_first_8 = 1.76 * (2.94 / 1.37)
hard_growth_8 = (548.80 / hard_first_8)^(1 / 7)
hard_growth(rows) = log_lerp(hard_growth_4, hard_growth_8, row_t)
growth_factor(rows, difficulty) =
  log_lerp(easy_growth, hard_growth(rows), difficulty_weight)
```

`log_lerp(a, b, t) = exp(log(a) + (log(b) - log(a)) * t)`.

Rounding:

| Value | Rule |
| --- | --- |
| Multipliers | Round to 2 decimals, `ROUND_HALF_UP`. |
| Payout amount | `bet_amount * multiplier`, rounded to 2 decimals, `ROUND_HALF_UP`. |
| Probabilities | Derived from rounded multiplier ladder for validation. |

## 3. RTP Model

For every step:

```text
cumulative_success_probability(step) = RTP_TARGET / multiplier(step)
step_success_probability(1) = RTP_TARGET / multiplier(1)
step_success_probability(n) = multiplier(n - 1) / multiplier(n)
```

This means any cashout step is priced to the same theoretical 98% return before
future platform caps or fees. The 2A simulator validates the top-row strategy,
which pays only when the round reaches the final row.

## 4. Complete Multiplier Table

| Rows | Difficulty | Multipliers |
| ---: | --- | --- |
| 4 | easy | `1.37`, `1.75`, `2.24`, `2.87` |
| 4 | medium | `2.01`, `3.46`, `5.95`, `10.24` |
| 4 | hard | `2.94`, `6.81`, `15.79`, `36.58` |
| 5 | easy | `1.46`, `1.87`, `2.39`, `3.05`, `3.91` |
| 5 | medium | `2.14`, `3.62`, `6.13`, `10.39`, `17.60` |
| 5 | hard | `3.13`, `7.02`, `15.76`, `35.35`, `79.31` |
| 6 | easy | `1.55`, `1.99`, `2.54`, `3.25`, `4.16`, `5.32` |
| 6 | medium | `2.27`, `3.79`, `6.32`, `10.54`, `17.57`, `29.29` |
| 6 | hard | `3.33`, `7.24`, `15.73`, `34.16`, `74.21`, `161.21` |
| 7 | easy | `1.65`, `2.11`, `2.71`, `3.46`, `4.43`, `5.66`, `7.25` |
| 7 | medium | `2.42`, `3.97`, `6.52`, `10.69`, `17.53`, `28.76`, `47.18` |
| 7 | hard | `3.55`, `7.46`, `15.70`, `33.01`, `69.44`, `146.05`, `307.20` |
| 8 | easy | `1.76`, `2.25`, `2.88`, `3.68`, `4.71`, `6.03`, `7.72`, `9.87` |
| 8 | medium | `2.58`, `4.16`, `6.72`, `10.84`, `17.50`, `28.25`, `45.60`, `73.60` |
| 8 | hard | `3.78`, `7.69`, `15.67`, `31.90`, `64.97`, `132.32`, `269.47`, `548.80` |

## 5. Anchor Reconciliation

| Anchor | Expected | Calculated | Delta |
| --- | ---: | ---: | ---: |
| 4 rows / easy / first | `1.37` | `1.37` | `0.00` |
| 4 rows / hard / first | `2.94` | `2.94` | `0.00` |
| 4 rows / hard / top | `36.58` | `36.58` | `0.00` |
| 8 rows / easy / first | `1.76` | `1.76` | `0.00` |
| 8 rows / easy / top | `9.87` | `9.87` | `0.00` |
| 8 rows / hard / top | `548.80` | `548.80` | `0.00` |

Tolerance declared for this WP: exact at 2 decimal multiplier precision.

## 6. 100k CI Validation Results

The standard CI validation uses deterministic stratified uniforms, not naive
Monte Carlo. This keeps the 100k gate stable for high-volatility configurations
while validating the same probability model.

| Rows | Difficulty | Empirical RTP | Hit rate |
| ---: | --- | ---: | ---: |
| 4 | easy | `0.9800` | `0.341460` |
| 4 | medium | `0.9800` | `0.095700` |
| 4 | hard | `0.9800` | `0.026790` |
| 5 | easy | `0.9800` | `0.250640` |
| 5 | medium | `0.9800` | `0.055680` |
| 5 | hard | `0.9803` | `0.012360` |
| 6 | easy | `0.9800` | `0.184210` |
| 6 | medium | `0.9800` | `0.033460` |
| 6 | hard | `0.9802` | `0.006080` |
| 7 | easy | `0.9800` | `0.135170` |
| 7 | medium | `0.9799` | `0.020770` |
| 7 | hard | `0.9800` | `0.003190` |
| 8 | easy | `0.9800` | `0.099290` |
| 8 | medium | `0.9804` | `0.013320` |
| 8 | hard | `0.9824` | `0.001790` |

CI acceptance band: `97.5% <= empirical RTP <= 98.5%`.

## 7. RNG And Fairness Pattern

BOXE v1 uses server-authoritative deterministic seed material.

| Artifact | Contract |
| --- | --- |
| `server_seed` | Secret server-side seed. |
| `server_seed_hash` | SHA-256 commitment stored/exposed for audit. |
| `client_seed` | Client/session seed included in RNG material. |
| `nonce` | Round nonce. |
| `selected_box_index` | Player choice included per step. |
| `rng_material` | SHA-256 of canonical JSON seed payload. |
| `round_path_hash` | SHA-256 hash of resolved step outcomes. |

The step outcome converts the first 64 bits of `rng_material` into a unit
interval decimal and compares it with the step success probability.

This is conceptually aligned with Mines fairness but uses BOXE-specific seed
payloads and outcome semantics. No Mines code is imported by BOXE.

## 8. External Validator

Standalone simulator:

```powershell
python tools/boxe_math_simulator.py --rows 8 --difficulty hard --bet 1.00 --seed boxe-ci --num-rounds 100000
```

The simulator reimplements the formula outside the backend module and is tested
against backend math for fixed seeds.

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--rows` | One of `4`, `5`, `6`, `7`, `8`. |
| `--difficulty` | `easy`, `medium`, `hard`. |
| `--bet` | Decimal bet amount. |
| `--seed` | Deterministic simulator seed. |
| `--num-rounds` | Number of validation rounds. |
| `--round-by-round` | Print each round result after aggregate summary. |

## 9. Stress Framework

On-demand stress tests live in `tests/stress/boxe_math/`.

```powershell
$env:RUN_BOXE_STRESS='1'
python -m pytest tests/stress/boxe_math -q
```

Optional extensive run:

```powershell
$env:BOXE_STRESS_ROUNDS='10000000'
python -m pytest tests/stress/boxe_math -q
```

Default stress target: 1M rounds per configuration across all 15 configs.

Stress acceptance band: `97.9% <= empirical RTP <= 98.1%`.

## 10. Edge Cases

| Edge case | Decision |
| --- | --- |
| Unsupported rows | Raise validation error. |
| Unsupported difficulty | Raise validation error. |
| Step outside row count | Raise validation error. |
| Max win cap | Not applied in v1. |
| Payout frontend calculation | Forbidden. |
| Wallet/ledger settlement | Out of scope; Fase 2D only. |
| Schema/API persistence | Out of scope; Fase 2B/2C. |
