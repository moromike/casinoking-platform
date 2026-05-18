Status: ACTIVE
Last meaningful update: 2026-05-18

# Mines Math Stress Tests

These tests are on-demand only. They are not part of normal CI because 1M to
10M+ rounds per configuration across all Mines runtime configurations are
intentionally expensive.

## Run

```powershell
$env:RUN_MINES_STRESS='1'
python -m pytest tests/stress/mines_math -q
```

Optional extensive run:

```powershell
$env:RUN_MINES_STRESS='1'
$env:MINES_STRESS_ROUNDS='10000000'
python -m pytest tests/stress/mines_math -q
```

## Interpretation

The stress suite covers all 130 supported Mines runtime configurations:

- 3x3: 8 mine-count configurations
- 4x4: 15 mine-count configurations
- 5x5: 24 mine-count configurations
- 6x6: 35 mine-count configurations
- 7x7: 48 mine-count configurations

The default target is 1,000,000 rounds per configuration. The simulated player
strategy is first safe reveal then cashout. This keeps every supported
configuration statistically observable at 1M rounds while validating the same
runtime multiplier table used by the backend.

Expected RTP band:

```text
97.9% <= empirical RTP <= 98.1%
```

The simulator uses deterministic stratified validation documented in
`docs/games/mines/MATH_SPEC.md`, so results should be stable across machines.
