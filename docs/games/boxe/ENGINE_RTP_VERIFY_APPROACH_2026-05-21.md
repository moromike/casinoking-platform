# BOXE Engine RTP Verify Approach

Status: ACTIVE - Wave 4 Parte A
Last meaningful update: 2026-05-21

Parte A is audit and simulation only. `backend/app/modules/games/boxe/math.py` is not modified.

## 1. Scope

Verify that all BOXE configurations, `rows x difficulty = 15` combinations, converge to the 98% RTP target under the current math implementation.

The verification must separate:

1. Exact theoretical RTP implied by the multiplier ladder and success probabilities.
2. Monte Carlo observed RTP for player strategies.
3. Sampling volatility, especially in hard/high-row configurations where top payout is rare.
4. Actual fix/no-fix recommendation.

## 2. Sources Audited

| Source | Notes |
| --- | --- |
| `backend/app/modules/games/boxe/math.py:10` | `RTP_TARGET = Decimal("0.98")`. |
| `backend/app/modules/games/boxe/math.py:12` | Supported row counts. |
| `backend/app/modules/games/boxe/math.py:13` | Supported difficulties. |
| `backend/app/modules/games/boxe/math.py:22` | First multiplier anchors by difficulty. |
| `backend/app/modules/games/boxe/math.py:68` | Multiplier ladder calculation. |
| `backend/app/modules/games/boxe/math.py:86` | Safe-pick probability derivation. |
| `backend/app/modules/games/boxe/math.py:99` | Payout calculation. |
| `backend/app/modules/games/boxe/math.py:104` | Built-in simulation helper. |
| `docs/games/boxe/MATH_SPEC.md:13` | Target RTP and max-win cap. |
| `docs/games/boxe/MATH_SPEC.md:24` | Multiplier formula. |
| `docs/games/boxe/MATH_SPEC.md:64` | RTP model. |
| `docs/games/boxe/MATH_SPEC.md:111` | CI validation target. |
| `tests/stress/boxe_math/test_boxe_math_stress.py:1` | Stress test exists but is opt-in. |
| `tools/boxe_math_simulator.py:1` | External math simulator mirrors the current formula. |

## 3. Current Math Model

The current implementation defines multipliers first, then derives each row's safe-pick probability so the expected return remains the target RTP at every cashout depth.

For step `i`:

```text
P(success at i | reached i) = previous_multiplier / current_multiplier
Expected return after cashout at i = cumulative_success_probability(i) * multiplier(i)
```

Because the ladder is rounded to two decimals, theoretical RTP is effectively 98% at each published step, with tiny rounding effects only visible in high-volume simulation.

The frontend must not recalculate the engine math. Runtime must continue to consume server-provided multipliers/probabilities.

## 4. Exact Theoretical Matrix

| Rows | Difficulty | Multipliers | Step safe probabilities | Top cumulative probability | Exact RTP |
| --- | --- | --- | --- | --- | --- |
| 4 | easy | 1.37, 1.75, 2.24, 2.87 | 71.53%, 78.29%, 78.12%, 78.05% | 34.1463% | 98.00% |
| 4 | medium | 2.01, 3.46, 5.95, 10.24 | 48.76%, 58.09%, 58.15%, 58.11% | 9.5703% | 98.00% |
| 4 | hard | 2.94, 6.81, 15.79, 36.58 | 33.33%, 43.17%, 43.13%, 43.17% | 2.6791% | 98.00% |
| 5 | easy | 1.46, 1.87, 2.39, 3.05, 3.91 | 67.12%, 78.07%, 78.24%, 78.36%, 78.01% | 25.0639% | 98.00% |
| 5 | medium | 2.14, 3.62, 6.13, 10.39, 17.60 | 45.79%, 59.12%, 59.05%, 59.00%, 59.03% | 5.5682% | 98.00% |
| 5 | hard | 3.13, 7.02, 15.76, 35.35, 79.31 | 31.31%, 44.59%, 44.54%, 44.58%, 44.57% | 1.2357% | 98.00% |
| 6 | easy | 1.55, 1.99, 2.54, 3.25, 4.16, 5.32 | 63.23%, 77.89%, 78.35%, 78.15%, 78.12%, 78.20% | 18.4211% | 98.00% |
| 6 | medium | 2.27, 3.79, 6.32, 10.54, 17.57, 29.29 | 43.17%, 59.89%, 59.97%, 59.96%, 59.99%, 59.99% | 3.3459% | 98.00% |
| 6 | hard | 3.33, 7.24, 15.73, 34.16, 74.21, 161.21 | 29.43%, 45.99%, 46.03%, 46.05%, 46.03%, 46.03% | 0.6079% | 98.00% |
| 7 | easy | 1.65, 2.11, 2.71, 3.46, 4.43, 5.66, 7.25 | 59.39%, 78.20%, 77.86%, 78.32%, 78.10%, 78.27%, 78.07% | 13.5172% | 98.00% |
| 7 | medium | 2.42, 3.97, 6.52, 10.69, 17.53, 28.76, 47.18 | 40.50%, 60.96%, 60.89%, 60.99%, 60.98%, 60.95%, 60.96% | 2.0772% | 98.00% |
| 7 | hard | 3.55, 7.46, 15.70, 33.01, 69.44, 146.05, 307.20 | 27.61%, 47.59%, 47.52%, 47.56%, 47.54%, 47.55%, 47.54% | 0.3190% | 98.00% |
| 8 | easy | 1.76, 2.25, 2.88, 3.68, 4.71, 6.03, 7.72, 9.87 | 55.68%, 78.22%, 78.12%, 78.26%, 78.13%, 78.11%, 78.11%, 78.22% | 9.9291% | 98.00% |
| 8 | medium | 2.58, 4.16, 6.72, 10.84, 17.50, 28.25, 45.60, 73.60 | 37.98%, 62.02%, 61.90%, 61.99%, 61.94%, 61.95%, 61.95%, 61.96% | 1.3315% | 98.00% |
| 8 | hard | 3.78, 7.69, 15.67, 31.90, 64.97, 132.32, 269.47, 548.80 | 25.93%, 49.15%, 49.07%, 49.12%, 49.10%, 49.10%, 49.10%, 49.10% | 0.1786% | 98.00% |

## 5. Monte Carlo Plan

Run at least `N = 100,000` rounds per combo, but do not use that as the only gate for high-volatility configurations.

Recommended verification tiers:

| Tier | Purpose | Gate |
| --- | --- | --- |
| Exact RTP | Primary correctness check. | Every combo must be 98% by formula. |
| Stratified simulation | Deterministic convergence check using quantile/stratified sampling. | Every combo should land in 97.9%-98.1%. |
| Naive Monte Carlo N >= 100k | Reality-style smoke for random variance. | Report deviations, do not auto-fail hard/high-row outliers without confidence interval. |
| Naive Monte Carlo N >= 1M for volatile rows | Optional audit for hard 7/8 rows. | Expected to remain noisy because top hit count is small. |

Strategies:

| Strategy | Meaning |
| --- | --- |
| Top/optimal continue | Player continues to the final row. |
| Typical mid cashout | Player cashes out at `min(3, rows)` after reaching that row. |
| Early cashout | Optional smoke at first successful row. |

Because each cashout depth is designed to 98% expected value, no strategy should be advantaged in exact math. Observed strategy differences in naive simulation are variance unless exact/stratified checks disagree.

## 6. Simulation Snapshot

Naive Monte Carlo with `N = 1,000,000` per combo produced the following directional outliers:

| Combo | Strategy | Observed RTP | Verdict |
| --- | --- | --- | --- |
| 7 hard | top continue | 99.69% | Above 99%, explained by rare top hit variance. Needs confidence interval note, not math fix. |
| 8 hard | top continue | 92.97% | Below 97%, explained by rare top hit variance. Expected top hits are about 1,786 per 1M rounds. |
| 6 medium | top continue | 97.18% | In range but close to lower edge. |
| 4 hard | top/typical | 97.67%-97.69% | In range, low-side variance. |

Stratified simulation at `N = 1,000,000` converged to 98.00% for all typical/top strategies, with only minor rounding drift (`8 hard top` around 98.02%).

## 7. Discrepancy Policy

| Finding | Classification |
| --- | --- |
| Exact RTP not 98% for any combo | Engine bug, fix required. |
| Stratified simulation outside 97.9%-98.1% | Engine/math implementation bug, fix required. |
| Naive Monte Carlo outside 97%-99% only on high-volatility hard rows | Report with confidence interval; no immediate math fix. |
| Naive Monte Carlo outside 97%-99% on easy/medium low rows | Investigate RNG/evaluation service, not necessarily math.py. |

## 8. Recommendation

No immediate `math.py` fix is recommended from Parte A. The exact formula and stratified simulation support the 98% target for all 15 configurations.

Parte B should add a reproducible verification tool/gate:

1. Exact matrix assertion for every rows/difficulty combo.
2. Stratified simulation gate for deterministic CI.
3. Naive Monte Carlo report artifact, clearly labelled as volatile for hard/high-row configurations.
4. Confidence interval output so product does not mistake sampling variance for RTP drift.

## 9. Parte B Granularity

| Sub-WP | Scope | Estimate |
| --- | --- | --- |
| RTP-B1 exact matrix contract | Unit/contract test over 15 combos. | 1-2 prompts |
| RTP-B2 deterministic simulator | Promote/refine stratified simulator into a repeatable tool. | 2-3 prompts |
| RTP-B3 report artifact | Generate markdown/JSON report with observed RTP and confidence intervals. | 2-3 prompts |
| RTP-B4 CI integration | Add opt-in stress gate and lightweight default gate. | 1-2 prompts |

Total expected effort: 6-10 prompts.

## 10. Stop-and-Ask

| Trigger | Category | Ask |
| --- | --- | --- |
| Product wants naive Monte Carlo N=100k to be a hard 97%-99% gate for hard 7/8 rows. | D | Stop: that gate will false-fail because variance is too high. |
| Exact RTP and empirical service outcomes disagree. | C | Stop with the service path that differs from `math.py`. |
| Max-win cap is applied before advertised multiplier payout in a way that changes RTP. | C/D | Stop and request cap policy confirmation. |

## 11. 12-Surface Impact

| Surface | Impact |
| --- | --- |
| 7 Gameplay shell | Indirect: payout ladder correctness. |
| 10 Backoffice editor | Indirect: rows/difficulty settings must not create invalid RTP combos. |
| 11 Replay | Indirect: replay must show multiplier/outcome consistent with engine math. |
| 12 Resume/disconnect | Indirect: resumed sessions must preserve the original ladder. |
