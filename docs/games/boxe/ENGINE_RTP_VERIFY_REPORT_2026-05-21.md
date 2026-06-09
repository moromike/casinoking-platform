Status: ACTIVE
Last meaningful update: 2026-05-21

# BOXE Engine RTP Verification Report

Wave 4 Parte B verification artifact. Production `backend/app/modules/games/boxe/math.py` was not modified.

## Gate Result

- Exact analytical gate: PASS
- Variance-reduced importance-sampling gate: PASS
- Naive Monte Carlo: report-only, never a hard gate for high-volatility rows.
- CTO recommendation: NO FIX: current math.py formula verifies at 98% RTP; naive Monte Carlo remains report-only.

## Primary 15-Combo Matrix

| Rows | Difficulty | Multipliers | Top P(success) | Theoretical RTP | Importance observed RTP | >2pp discrepancy |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 4 | easy | `1.37, 1.75, 2.24, 2.87` | 34.15% | 98.00% | 98.00% | NO |
| 4 | medium | `2.01, 3.46, 5.95, 10.24` | 9.57% | 98.00% | 98.00% | NO |
| 4 | hard | `2.94, 6.81, 15.79, 36.58` | 2.68% | 98.00% | 98.00% | NO |
| 5 | easy | `1.46, 1.87, 2.39, 3.05, 3.91` | 25.06% | 98.00% | 98.00% | NO |
| 5 | medium | `2.14, 3.62, 6.13, 10.39, 17.60` | 5.57% | 98.00% | 98.00% | NO |
| 5 | hard | `3.13, 7.02, 15.76, 35.35, 79.31` | 1.24% | 98.00% | 98.00% | NO |
| 6 | easy | `1.55, 1.99, 2.54, 3.25, 4.16, 5.32` | 18.42% | 98.00% | 98.00% | NO |
| 6 | medium | `2.27, 3.79, 6.32, 10.54, 17.57, 29.29` | 3.35% | 98.00% | 98.00% | NO |
| 6 | hard | `3.33, 7.24, 15.73, 34.16, 74.21, 161.21` | 0.61% | 98.00% | 98.00% | NO |
| 7 | easy | `1.65, 2.11, 2.71, 3.46, 4.43, 5.66, 7.25` | 13.52% | 98.00% | 98.00% | NO |
| 7 | medium | `2.42, 3.97, 6.52, 10.69, 17.53, 28.76, 47.18` | 2.08% | 98.00% | 98.00% | NO |
| 7 | hard | `3.55, 7.46, 15.70, 33.01, 69.44, 146.05, 307.20` | 0.32% | 98.00% | 98.00% | NO |
| 8 | easy | `1.76, 2.25, 2.88, 3.68, 4.71, 6.03, 7.72, 9.87` | 9.93% | 98.00% | 98.00% | NO |
| 8 | medium | `2.58, 4.16, 6.72, 10.84, 17.50, 28.25, 45.60, 73.60` | 1.33% | 98.00% | 98.00% | NO |
| 8 | hard | `3.78, 7.69, 15.67, 31.90, 64.97, 132.32, 269.47, 548.80` | 0.18% | 98.00% | 98.00% | NO |

## Strategy Matrix

| Rows | Difficulty | Strategy | Cashout step | P(success) | Multiplier | Theoretical RTP | Importance observed RTP | Delta | Gate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4 | easy | early | 1 | 71.53% | 1.37x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | easy | typical | 3 | 43.75% | 2.24x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | easy | top | 4 | 34.15% | 2.87x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | medium | early | 1 | 48.76% | 2.01x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | medium | typical | 3 | 16.47% | 5.95x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | medium | top | 4 | 9.57% | 10.24x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | hard | early | 1 | 33.33% | 2.94x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | hard | typical | 3 | 6.21% | 15.79x | 98.00% | 98.00% | +0.00% | PASS |
| 4 | hard | top | 4 | 2.68% | 36.58x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | easy | early | 1 | 67.12% | 1.46x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | easy | typical | 3 | 41.00% | 2.39x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | easy | top | 5 | 25.06% | 3.91x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | medium | early | 1 | 45.79% | 2.14x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | medium | typical | 3 | 15.99% | 6.13x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | medium | top | 5 | 5.57% | 17.60x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | hard | early | 1 | 31.31% | 3.13x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | hard | typical | 3 | 6.22% | 15.76x | 98.00% | 98.00% | +0.00% | PASS |
| 5 | hard | top | 5 | 1.24% | 79.31x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | easy | early | 1 | 63.23% | 1.55x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | easy | typical | 3 | 38.58% | 2.54x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | easy | top | 6 | 18.42% | 5.32x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | medium | early | 1 | 43.17% | 2.27x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | medium | typical | 3 | 15.51% | 6.32x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | medium | top | 6 | 3.35% | 29.29x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | hard | early | 1 | 29.43% | 3.33x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | hard | typical | 3 | 6.23% | 15.73x | 98.00% | 98.00% | +0.00% | PASS |
| 6 | hard | top | 6 | 0.61% | 161.21x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | easy | early | 1 | 59.39% | 1.65x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | easy | typical | 3 | 36.16% | 2.71x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | easy | top | 7 | 13.52% | 7.25x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | medium | early | 1 | 40.50% | 2.42x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | medium | typical | 3 | 15.03% | 6.52x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | medium | top | 7 | 2.08% | 47.18x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | hard | early | 1 | 27.61% | 3.55x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | hard | typical | 3 | 6.24% | 15.70x | 98.00% | 98.00% | +0.00% | PASS |
| 7 | hard | top | 7 | 0.32% | 307.20x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | easy | early | 1 | 55.68% | 1.76x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | easy | typical | 3 | 34.03% | 2.88x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | easy | top | 8 | 9.93% | 9.87x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | medium | early | 1 | 37.98% | 2.58x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | medium | typical | 3 | 14.58% | 6.72x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | medium | top | 8 | 1.33% | 73.60x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | hard | early | 1 | 25.93% | 3.78x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | hard | typical | 3 | 6.25% | 15.67x | 98.00% | 98.00% | +0.00% | PASS |
| 8 | hard | top | 8 | 0.18% | 548.80x | 98.00% | 98.00% | +0.00% | PASS |

## Discrepancies Over 2pp From 98%

- None in exact analytical or variance-reduced importance-sampling verification.

## Naive Monte Carlo Appendix

Naive top-strategy rounds per combo: `1000000`. These results are not pass/fail gates.

| Rows | Difficulty | Wins | Observed RTP | Delta | 95% CI | >2pp from 98% |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 4 | easy | 340708 | 97.78% | -0.22% | 97.52% - 98.05% | NO |
| 4 | medium | 95333 | 97.62% | -0.38% | 97.03% - 98.21% | NO |
| 4 | hard | 26910 | 98.44% | +0.44% | 97.28% - 99.59% | NO |
| 5 | easy | 250968 | 98.13% | +0.13% | 97.80% - 98.46% | NO |
| 5 | medium | 55930 | 98.44% | +0.44% | 97.65% - 99.23% | NO |
| 5 | hard | 12292 | 97.49% | -0.51% | 95.77% - 99.21% | NO |
| 6 | easy | 184276 | 98.03% | +0.03% | 97.63% - 98.44% | NO |
| 6 | medium | 33695 | 98.69% | +0.69% | 97.66% - 99.73% | NO |
| 6 | hard | 6091 | 98.19% | +0.19% | 95.74% - 100.65% | NO |
| 7 | easy | 135321 | 98.11% | +0.11% | 97.62% - 98.59% | NO |
| 7 | medium | 20794 | 98.11% | +0.11% | 96.79% - 99.42% | NO |
| 7 | hard | 3082 | 94.68% | -3.32% | 91.28% - 98.07% | YES |
| 8 | easy | 99332 | 98.04% | +0.04% | 97.46% - 98.62% | NO |
| 8 | medium | 13243 | 97.47% | -0.53% | 95.82% - 99.12% | NO |
| 8 | hard | 1712 | 93.95% | -4.05% | 89.41% - 98.50% | YES |

Naive discrepancies over 2pp:
- 7 hard: 94.68% (-3.32%), report-only.
- 8 hard: 93.95% (-4.05%), report-only.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE RTP exact matrix | N/A | Read-only `math.py` import | N/A | N/A | N/A | N/A | Unit/tool gate covers 15 combos | This report + approach doc | PASS | No production engine behavior changed. |
| BOXE variance-reduced observed RTP | N/A | Read-only probability/multiplier model | N/A | N/A | N/A | N/A | Importance-sampling gate covers early/typical/top strategies | This report | PASS | Naive Monte Carlo is explicitly report-only. |
| CTO fix/no-fix decision | N/A | No fix recommended | N/A | N/A | N/A | N/A | Exact + importance gates pass | This report | COMPLETE | No `math.py` patch is recommended. |

## Commands

```powershell
python tools/boxe_rtp_verify.py --write-report docs/games/boxe/ENGINE_RTP_VERIFY_REPORT_2026-05-21.md
python -m pytest backend/tests/unit/test_boxe_rtp_verify.py backend/tests/unit/test_boxe_math.py -q
```

## Documents Read

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` sections 6.3, 13.1, 14, and the 12-surface Rule-12 material
- `docs/games/boxe/ENGINE_RTP_VERIFY_APPROACH_2026-05-21.md`
- `docs/games/boxe/MATH_SPEC.md`
- `docs/games/boxe/BOXE_BRIEF.md` implementation log section
