Status: ACTIVE
Last meaningful update: 2026-05-22

# BOXE Safe-Path Stress Result

Command:

```powershell
$env:PYTHONPATH='backend'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:RUN_BOXE_STRESS='1'
$env:BOXE_SAFE_PATH_STRESS_BOARDS='100000'
python -m pytest tests/stress/boxe_math/test_boxe_safe_path_stress.py -q
```

Result:

```text
...............                                                          [100%]
15 passed in 407.01s (0:06:47)
```

Coverage:

- 15 `rows x difficulty` combinations.
- 100,000 seed-derived boards per combination.
- Every generated row verified with at least one safe cell and one mine.
- Every generated row verified against `safe_count_for_row` and its mine complement.
