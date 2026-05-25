from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from app.modules.platform.game_codes import (
    GAME_CODE_BOXE,
    GAME_CODE_HI_LO,
    GAME_CODE_MINES,
)


REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class GameRuntimeDescriptor:
    game_code: str
    display_name: str
    payout_runtime_source: str
    math_source: str
    rtp_source: str
    replay_verification_source: str
    spec_paths: tuple[str, ...]


GAME_RUNTIME_DESCRIPTORS: dict[str, GameRuntimeDescriptor] = {
    GAME_CODE_MINES: GameRuntimeDescriptor(
        game_code=GAME_CODE_MINES,
        display_name="Mines",
        payout_runtime_source="docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json",
        math_source="backend/app/modules/games/mines/runtime.py",
        rtp_source="docs/games/mines/MATH_SPEC.md#11",
        replay_verification_source="backend/app/modules/games/mines/service.py:_replay_payload",
        spec_paths=("docs/games/mines/MATH_SPEC.md",),
    ),
    GAME_CODE_BOXE: GameRuntimeDescriptor(
        game_code=GAME_CODE_BOXE,
        display_name="BOXE",
        payout_runtime_source="backend/app/modules/games/boxe/math.py",
        math_source="backend/app/modules/games/boxe/math.py",
        rtp_source="docs/games/boxe/MATH_SPEC.md",
        replay_verification_source="backend/app/modules/games/boxe/service.py:_replay_payload",
        spec_paths=("docs/games/boxe/SPEC.md", "docs/games/boxe/MATH_SPEC.md"),
    ),
    GAME_CODE_HI_LO: GameRuntimeDescriptor(
        game_code=GAME_CODE_HI_LO,
        display_name="HI-LO",
        payout_runtime_source="backend/app/modules/games/hi_lo/math.py",
        math_source="backend/app/modules/games/hi_lo/math.py",
        rtp_source="docs/games/hi-lo/MATH_SPEC.md",
        replay_verification_source="backend/app/modules/games/hi_lo/service.py:get_round_replay",
        spec_paths=("docs/games/hi-lo/SPEC.md", "docs/games/hi-lo/MATH_SPEC.md"),
    ),
}


def read_game_runtime_descriptor(game_code: str) -> GameRuntimeDescriptor | None:
    return GAME_RUNTIME_DESCRIPTORS.get(game_code)


def format_game_runtime_descriptor_value(game_code: str) -> str:
    descriptor = GAME_RUNTIME_DESCRIPTORS[game_code]
    spec_count = len(descriptor.spec_paths)
    return (
        f"runtime descriptor v1: payout/RTP/replay/spec hash present "
        f"({spec_count} spec file{'s' if spec_count != 1 else ''})"
    )


def build_game_runtime_descriptor_notes(game_code: str) -> tuple[str, ...]:
    descriptor = GAME_RUNTIME_DESCRIPTORS[game_code]
    return (
        f"payout_runtime_source: {descriptor.payout_runtime_source}",
        f"math_source: {descriptor.math_source}",
        f"rtp_source: {descriptor.rtp_source}",
        f"replay_verification_source: {descriptor.replay_verification_source}",
        "spec_hashes: "
        + ", ".join(
            f"{path}={_hash_repo_file(path)[:12]}"
            for path in descriptor.spec_paths
        ),
    )


def serialize_game_runtime_descriptor(game_code: str) -> dict[str, object]:
    descriptor = GAME_RUNTIME_DESCRIPTORS[game_code]
    return {
        "game_code": descriptor.game_code,
        "display_name": descriptor.display_name,
        "payout_runtime_source": descriptor.payout_runtime_source,
        "math_source": descriptor.math_source,
        "rtp_source": descriptor.rtp_source,
        "replay_verification_source": descriptor.replay_verification_source,
        "spec_files": [
            {
                "path": path,
                "sha256": _hash_repo_file(path),
            }
            for path in descriptor.spec_paths
        ],
    }


def _hash_repo_file(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    if not path.exists():
        return f"unavailable:{relative_path}"
    return sha256(path.read_bytes()).hexdigest()
