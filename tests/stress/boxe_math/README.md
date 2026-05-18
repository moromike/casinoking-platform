Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE Math Stress Tests

These tests are on-demand only. They are not part of normal CI because 1M to
10M+ rounds per configuration are intentionally expensive.

## Run

```powershell
$env:RUN_BOXE_STRESS='1'
python -m pytest tests/stress/boxe_math -q
```

Optional:

```powershell
$env:BOXE_STRESS_ROUNDS='10000000'
python -m pytest tests/stress/boxe_math -q
```

## Interpretation

The stress suite runs all 15 supported configurations: 5 row counts times 3
difficulties. The default target is 1,000,000 rounds per configuration.

Expected RTP band:

```text
97.9% <= empirical RTP <= 98.1%
```

The simulator uses the deterministic stratified validation mode documented in
`docs/games/boxe/MATH_SPEC.md`, so results should be stable across machines.
