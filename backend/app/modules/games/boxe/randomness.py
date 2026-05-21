from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Iterable

from app.modules.games.boxe.math import (
    FAIRNESS_VERSION,
    GAME_CODE,
    cells_for_row,
    get_row_success_probability,
    get_safe_count_for_row,
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


@dataclass(frozen=True)
class BoardCell:
    row: int
    position: int
    safe: bool
    unit_interval: Decimal
    rng_material: str


@dataclass(frozen=True)
class BoardRow:
    row: int
    cells: tuple[BoardCell, ...]

    @property
    def safe_count(self) -> int:
        return sum(1 for cell in self.cells if cell.safe)

    @property
    def mine_count(self) -> int:
        return len(self.cells) - self.safe_count


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
    row = step - 1
    cell_count = cells_for_row(row, rows)
    if selected_box_index < 0 or selected_box_index >= cell_count:
        raise ValueError(
            f"selected_box_index must be between 0 and {cell_count - 1} for row={row}"
        )

    board = derive_boxe_board(
        rows=rows,
        difficulty=difficulty,
        server_seed=server_seed,
        client_seed=client_seed,
        nonce=nonce,
        fairness_version=fairness_version,
    )
    cell = board[row].cells[selected_box_index]
    return StepOutcome(
        rows=rows,
        difficulty=difficulty,
        step=step,
        selected_box_index=selected_box_index,
        safe=cell.safe,
        unit_interval=cell.unit_interval,
        success_probability=get_row_success_probability(
            row=row,
            rows=rows,
            difficulty=difficulty,
        ),
        rng_material=cell.rng_material,
    )


def derive_boxe_board(
    *,
    rows: int,
    difficulty: str,
    server_seed: str,
    client_seed: str,
    nonce: int,
    fairness_version: str = FAIRNESS_VERSION,
) -> tuple[BoardRow, ...]:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    board_rows: list[BoardRow] = []
    for row in range(rows):
        cell_count = cells_for_row(row, rows)
        safe_count = get_safe_count_for_row(row=row, rows=rows, difficulty=difficulty)
        scored_positions = [
            (
                _build_board_cell_rng_material(
                    rows=rows,
                    difficulty=difficulty,
                    row=row,
                    position=position,
                    server_seed=server_seed,
                    client_seed=client_seed,
                    nonce=nonce,
                    fairness_version=fairness_version,
                ),
                position,
            )
            for position in range(cell_count)
        ]
        safe_positions = {
            position
            for _rng_material, position in sorted(scored_positions, key=lambda item: item[0])[
                :safe_count
            ]
        }
        cells = tuple(
            BoardCell(
                row=row,
                position=position,
                safe=position in safe_positions,
                unit_interval=_hex_to_unit_interval(rng_material),
                rng_material=rng_material,
            )
            for rng_material, position in sorted(scored_positions, key=lambda item: item[1])
        )
        board_rows.append(BoardRow(row=row, cells=cells))
    return tuple(board_rows)


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
    board = derive_boxe_board(
        rows=rows,
        difficulty=difficulty,
        server_seed=server_seed,
        client_seed=client_seed,
        nonce=nonce,
        fairness_version=fairness_version,
    )
    reveal: list[dict[str, object]] = []
    for board_row in board:
        row = board_row.row
        cells: list[dict[str, object]] = []
        for cell in board_row.cells:
            is_picked = (row, cell.position) in picked
            cells.append(
                {
                    "position": cell.position,
                    "state": "safe" if cell.safe else "mine",
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


def _build_board_cell_rng_material(
    *,
    rows: int,
    difficulty: str,
    row: int,
    position: int,
    server_seed: str,
    client_seed: str,
    nonce: int,
    fairness_version: str,
) -> str:
    material = "|".join(
        (
            _field("client_seed", client_seed),
            _field("difficulty", difficulty),
            _field("fairness_version", fairness_version),
            _field("game_code", GAME_CODE),
            _field("nonce", str(nonce)),
            _field("position", str(position)),
            _field("row", str(row)),
            _field("rows", str(rows)),
            _field("server_seed", server_seed),
            _field("source", "safe_count_board"),
        )
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _field(name: str, value: str) -> str:
    return f"{name}:{len(value)}:{value}"


def _hex_to_unit_interval(hex_digest: str) -> Decimal:
    sample = int(hex_digest[:16], 16)
    return Decimal(sample) / Decimal(16**16)
