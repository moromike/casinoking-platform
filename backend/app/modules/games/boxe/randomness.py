from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Iterable

from app.modules.games.boxe.math import (
    FAIRNESS_VERSION,
    get_step_success_probability,
    normalize_difficulty,
    validate_rows,
)


@dataclass(frozen=True)
class StepOutcome:
    rows: int
    difficulty: str
    step: int
    selected_box_index: int
    safe: bool
    unit_interval: Decimal
    success_probability: Decimal
    rng_material: str


PickedCell = tuple[int, int]


def build_server_seed_hash(server_seed: str) -> str:
    return sha256(server_seed.encode("utf-8")).hexdigest()


def generate_step_outcome(
    *,
    rows: int,
    difficulty: str,
    step: int,
    selected_box_index: int,
    server_seed: str,
    client_seed: str,
    nonce: int,
    fairness_version: str = FAIRNESS_VERSION,
) -> StepOutcome:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    if step < 1 or step > rows:
        raise ValueError(f"Unsupported BOXE step {step} for rows={rows}")
    if selected_box_index < 0:
        raise ValueError("selected_box_index must be non-negative")

    rng_material = _build_step_rng_material(
        rows=rows,
        difficulty=difficulty,
        step=step,
        selected_box_index=selected_box_index,
        server_seed=server_seed,
        client_seed=client_seed,
        nonce=nonce,
        fairness_version=fairness_version,
    )
    unit_interval = _hex_to_unit_interval(rng_material)
    success_probability = get_step_success_probability(
        rows=rows,
        difficulty=difficulty,
        step=step,
    )
    return StepOutcome(
        rows=rows,
        difficulty=difficulty,
        step=step,
        selected_box_index=selected_box_index,
        safe=unit_interval < success_probability,
        unit_interval=unit_interval,
        success_probability=success_probability,
        rng_material=rng_material,
    )


def generate_pyramid_full_reveal(
    *,
    rows: int,
    difficulty: str,
    server_seed: str,
    client_seed: str,
    nonce: int,
    picked_cells: Iterable[PickedCell] = (),
    fairness_version: str = FAIRNESS_VERSION,
) -> list[dict[str, object]]:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    picked = set(picked_cells)
    reveal: list[dict[str, object]] = []
    for row in range(rows):
        step = row + 1
        cell_count = rows - row + 1
        cells: list[dict[str, object]] = []
        for position in range(cell_count):
            outcome = generate_step_outcome(
                rows=rows,
                difficulty=difficulty,
                step=step,
                selected_box_index=position,
                server_seed=server_seed,
                client_seed=client_seed,
                nonce=nonce,
                fairness_version=fairness_version,
            )
            is_picked = (row, position) in picked
            cells.append(
                {
                    "position": position,
                    "state": "safe" if outcome.safe else "mine",
                    "picked": is_picked,
                    "reveal_scope": "picked_path" if is_picked else "terminal_full_reveal",
                }
            )
        reveal.append({"row": row, "cells": cells})
    return reveal


def build_round_path_hash(*, outcomes: list[StepOutcome], nonce: int) -> str:
    payload = {
        "fairness_version": FAIRNESS_VERSION,
        "nonce": nonce,
        "outcomes": [
            {
                "step": outcome.step,
                "selected_box_index": outcome.selected_box_index,
                "safe": outcome.safe,
                "rng_material": outcome.rng_material,
            }
            for outcome in outcomes
        ],
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _build_step_rng_material(
    *,
    rows: int,
    difficulty: str,
    step: int,
    selected_box_index: int,
    server_seed: str,
    client_seed: str,
    nonce: int,
    fairness_version: str,
) -> str:
    payload = {
        "client_seed": client_seed,
        "difficulty": difficulty,
        "fairness_version": fairness_version,
        "game_code": "boxe",
        "nonce": nonce,
        "rows": rows,
        "selected_box_index": selected_box_index,
        "server_seed": server_seed,
        "step": step,
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _hex_to_unit_interval(hex_digest: str) -> Decimal:
    sample = int(hex_digest[:16], 16)
    return Decimal(sample) / Decimal(16**16)
