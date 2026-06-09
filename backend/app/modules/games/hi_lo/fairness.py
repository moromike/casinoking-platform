from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from app.modules.games.hi_lo.math import FAIRNESS_VERSION, GAME_CODE
from app.modules.games.hi_lo.randomness import (
    CardDraw,
    build_server_seed_hash,
    draw_card,
)

RANDOM_SOURCE = "internal_seed_engine"


@dataclass(frozen=True)
class DrawRequest:
    draw_index: int
    draw_purpose: str


def create_fairness_artifacts(
    *,
    server_seed: str,
    client_seed: str,
    round_nonce: int,
    draw_requests: list[DrawRequest],
    fairness_version: str = FAIRNESS_VERSION,
) -> dict[str, object]:
    draws = [
        draw_card(
            server_seed=server_seed,
            client_seed=client_seed,
            round_nonce=round_nonce,
            draw_index=request.draw_index,
            draw_purpose=request.draw_purpose,
            fairness_version=fairness_version,
        )
        for request in draw_requests
    ]
    return {
        "game_code": GAME_CODE,
        "fairness_version": fairness_version,
        "random_source": RANDOM_SOURCE,
        "round_nonce": round_nonce,
        "server_seed_hash": build_server_seed_hash(server_seed),
        "client_seed": client_seed,
        "draw_sequence_hash": build_draw_sequence_hash(
            draws=draws,
            round_nonce=round_nonce,
            fairness_version=fairness_version,
        ),
        "draws": [_serialize_draw(draw) for draw in draws],
        "user_verifiable": False,
    }


def verify_fairness_artifacts(
    *,
    artifacts: dict[str, object],
    server_seed: str,
    client_seed: str,
    round_nonce: int,
    draw_requests: list[DrawRequest],
    fairness_version: str = FAIRNESS_VERSION,
) -> dict[str, object]:
    recomputed = create_fairness_artifacts(
        server_seed=server_seed,
        client_seed=client_seed,
        round_nonce=round_nonce,
        draw_requests=draw_requests,
        fairness_version=fairness_version,
    )
    server_seed_hash_match = artifacts.get("server_seed_hash") == recomputed["server_seed_hash"]
    draw_sequence_hash_match = (
        artifacts.get("draw_sequence_hash") == recomputed["draw_sequence_hash"]
    )
    return {
        "server_seed_hash_match": server_seed_hash_match,
        "draw_sequence_hash_match": draw_sequence_hash_match,
        "verified": server_seed_hash_match and draw_sequence_hash_match,
        "computed": recomputed,
    }


def build_draw_sequence_hash(
    *,
    draws: list[CardDraw],
    round_nonce: int,
    fairness_version: str = FAIRNESS_VERSION,
) -> str:
    payload = {
        "fairness_version": fairness_version,
        "game_code": GAME_CODE,
        "round_nonce": round_nonce,
        "draws": [
            {
                "card_index": draw.card_index,
                "rank": draw.card.rank,
                "suit": draw.card.suit,
                "rng_material": draw.rng_material,
                "digest": draw.digest,
                "rejection_counter": draw.rejection_counter,
            }
            for draw in draws
        ],
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _serialize_draw(draw: CardDraw) -> dict[str, object]:
    return {
        "card_index": draw.card_index,
        "rank": draw.card.rank,
        "rank_label": draw.card.rank_label,
        "suit": draw.card.suit,
        "color": draw.card.color,
        "rng_material": draw.rng_material,
        "digest": draw.digest,
        "rejection_counter": draw.rejection_counter,
    }
