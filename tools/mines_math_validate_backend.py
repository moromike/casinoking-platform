from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for path in (ROOT, BACKEND):
    path_string = str(path)
    if path_string not in sys.path:
        sys.path.insert(0, path_string)

from app.modules.games.mines.randomness import generate_board as backend_generate_board
from app.modules.games.mines.runtime import (
    FAIRNESS_VERSION,
    get_multiplier as backend_get_multiplier,
    get_payout_table as backend_get_payout_table,
)
from tools.mines_math_simulator import (
    generate_board as simulator_generate_board,
    get_multiplier as simulator_get_multiplier,
    load_payout_table,
)


def validate() -> dict[str, object]:
    simulator_table = load_payout_table()
    backend_table = backend_get_payout_table()
    multiplier_checks = 0

    if simulator_table.keys() != backend_table.keys():
        raise AssertionError("Simulator/backend grid keys differ")

    for grid_size, mine_map in backend_table.items():
        if simulator_table[grid_size].keys() != mine_map.keys():
            raise AssertionError(f"Simulator/backend mine keys differ for grid {grid_size}")
        for mine_count, backend_ladder in mine_map.items():
            if simulator_table[grid_size][mine_count] != backend_ladder:
                raise AssertionError(
                    f"Simulator/backend ladder differs for grid={grid_size}, mines={mine_count}"
                )
            for step, expected_multiplier in enumerate(backend_ladder, start=1):
                simulator_multiplier = simulator_get_multiplier(grid_size, mine_count, step)
                backend_multiplier = backend_get_multiplier(
                    grid_size=grid_size,
                    mine_count=mine_count,
                    safe_reveals_count=step,
                )
                if simulator_multiplier != backend_multiplier:
                    raise AssertionError(
                        "Simulator/backend multiplier differs for "
                        f"grid={grid_size}, mines={mine_count}, step={step}"
                    )
                if expected_multiplier != backend_multiplier:
                    raise AssertionError(
                        "Backend ladder/get_multiplier mismatch for "
                        f"grid={grid_size}, mines={mine_count}, step={step}"
                    )
                multiplier_checks += 1

    rng_checks = 0
    seeds = ("mines-cert-a", "mines-cert-b", "mines-cert-c")
    configs = ((9, 1), (16, 4), (25, 3), (36, 12), (49, 24))
    for seed_index, seed in enumerate(seeds, start=1):
        for grid_size, mine_count in configs:
            nonce = seed_index * 1000 + grid_size + mine_count
            simulator_result = simulator_generate_board(
                grid_size=grid_size,
                mine_count=mine_count,
                fairness_version=FAIRNESS_VERSION,
                server_seed=seed,
                nonce=nonce,
            )
            backend_result = backend_generate_board(
                grid_size=grid_size,
                mine_count=mine_count,
                fairness_version=FAIRNESS_VERSION,
                server_seed=seed,
                nonce=nonce,
            )
            if simulator_result != backend_result:
                raise AssertionError(
                    "Simulator/backend RNG differs for "
                    f"grid={grid_size}, mines={mine_count}, seed={seed}, nonce={nonce}"
                )
            rng_checks += 1

    return {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "fairness_version": FAIRNESS_VERSION,
        "grid_configs": sum(len(mine_map) for mine_map in backend_table.values()),
        "multiplier_checks": multiplier_checks,
        "rng_checks": rng_checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate independent Mines simulator against backend runtime"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("var/audit/mines_math_backend_parity.json"),
        help="Audit JSON output path.",
    )
    args = parser.parse_args()

    result = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print(f"audit_log={args.output}")


if __name__ == "__main__":
    main()
