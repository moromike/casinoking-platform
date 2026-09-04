from decimal import Decimal
from functools import lru_cache
import json
from pathlib import Path

RUNTIME_FILE_NAME = "CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json"
FAIRNESS_VERSION = "seed_internal_v2"


def get_runtime_config() -> dict[str, object]:
    table = get_payout_table()
    return {
        "game_code": "mines",
        "supported_grid_sizes": sorted(table.keys()),
        "supported_mine_counts": {
            str(grid_size): sorted(mine_map.keys())
            for grid_size, mine_map in sorted(table.items())
        },
        "payout_ladders": {
            str(grid_size): {
                str(mine_count): [str(multiplier) for multiplier in multipliers]
                for mine_count, multipliers in sorted(mine_map.items())
            }
            for grid_size, mine_map in sorted(table.items())
        },
        "payout_runtime_file": RUNTIME_FILE_NAME,
        "fairness_version": FAIRNESS_VERSION,
    }


def get_multiplier(
    *,
    grid_size: int,
    mine_count: int,
    safe_reveals_count: int,
) -> Decimal:
    table = get_payout_table()
    return table[grid_size][mine_count][safe_reveals_count - 1]


def supports_configuration(*, grid_size: int, mine_count: int) -> bool:
    table = get_payout_table()
    return grid_size in table and mine_count in table[grid_size]


@lru_cache(maxsize=1)
def get_payout_table() -> dict[int, dict[int, list[Decimal]]]:
    runtime_path = _resolve_runtime_path()
    raw_data = json.loads(
        runtime_path.read_text(),
        parse_float=Decimal,
    )
    return {
        int(grid_size): {
            int(mine_count): list(multipliers)
            for mine_count, multipliers in mine_map.items()
        }
        for grid_size, mine_map in raw_data.items()
    }


def _resolve_runtime_path() -> Path:
    candidates = [
        Path("/app/docs/runtime") / RUNTIME_FILE_NAME,
        Path(__file__).resolve().parents[5] / "docs" / "runtime" / RUNTIME_FILE_NAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Runtime payout file not found: {RUNTIME_FILE_NAME}")
