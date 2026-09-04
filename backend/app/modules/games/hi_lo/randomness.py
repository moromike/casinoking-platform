from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from app.modules.games.hi_lo.math import (
    FAIRNESS_VERSION,
    GAME_CODE,
    Card,
    card_from_index,
)

CARD_COUNT = 52
_UINT256_SIZE = 1 << 256
_REJECTION_LIMIT = _UINT256_SIZE - (_UINT256_SIZE % CARD_COUNT)


@dataclass(frozen=True)
class CardDraw:
    card: Card
    card_index: int
    unit_interval: Decimal
    rng_material: str
    digest: str
    rejection_counter: int


def build_server_seed_hash(server_seed: str) -> str:
    return sha256(server_seed.encode("utf-8")).hexdigest()


def draw_card(
    *,
    server_seed: str,
    client_seed: str,
    round_nonce: int,
    draw_index: int,
    draw_purpose: str,
    fairness_version: str = FAIRNESS_VERSION,
) -> CardDraw:
    if round_nonce < 0:
        raise ValueError("round_nonce must be non-negative")
    if draw_index < 0:
        raise ValueError("draw_index must be non-negative")
    normalized_draw_purpose = _normalize_non_empty(draw_purpose, "draw_purpose")
    rng_material = build_draw_rng_material(
        server_seed=server_seed,
        client_seed=client_seed,
        round_nonce=round_nonce,
        draw_index=draw_index,
        draw_purpose=normalized_draw_purpose,
        fairness_version=fairness_version,
    )
    card_index, digest, rejection_counter = _digest_to_card_index(rng_material)
    return CardDraw(
        card=card_from_index(card_index),
        card_index=card_index,
        unit_interval=_digest_to_unit_interval(digest),
        rng_material=rng_material,
        digest=digest,
        rejection_counter=rejection_counter,
    )


def build_draw_rng_material(
    *,
    server_seed: str,
    client_seed: str,
    round_nonce: int,
    draw_index: int,
    draw_purpose: str,
    fairness_version: str = FAIRNESS_VERSION,
) -> str:
    return "|".join(
        (
            _field("client_seed", _normalize_non_empty(client_seed, "client_seed")),
            _field("draw_index", str(draw_index)),
            _field("draw_purpose", _normalize_non_empty(draw_purpose, "draw_purpose")),
            _field("fairness_version", _normalize_non_empty(fairness_version, "fairness_version")),
            _field("game_code", GAME_CODE),
            _field("round_nonce", str(round_nonce)),
            _field("server_seed", _normalize_non_empty(server_seed, "server_seed")),
        )
    )


def _digest_to_card_index(rng_material: str) -> tuple[int, str, int]:
    counter = 0
    while True:
        digest = sha256(f"{rng_material}|rejection_counter:{counter}".encode("utf-8")).hexdigest()
        candidate = int(digest, 16)
        if candidate < _REJECTION_LIMIT:
            return candidate % CARD_COUNT, digest, counter
        counter += 1


def _digest_to_unit_interval(hex_digest: str) -> Decimal:
    return Decimal(int(hex_digest, 16)) / Decimal(_UINT256_SIZE)


def _field(name: str, value: str) -> str:
    return f"{name}:{len(value)}:{value}"


def _normalize_non_empty(raw_value: str, field_name: str) -> str:
    value = raw_value.strip()
    if not value:
        raise ValueError(f"{field_name} is required")
    return value
