from __future__ import annotations

from dataclasses import asdict
import re

from app.modules.platform.game_codes import (
    GAME_CODE_BOXE,
    GAME_CODE_HI_LO,
    GAME_CODE_MINES,
)
from app.modules.platform.game_modules.adapter import (
    GameEmbedDescriptor,
    GameLaunchDescriptor,
    GameReplayDescriptor,
    GameStorageDescriptor,
)


EMBED_PROTOCOL_V1 = "ck-game-embed-v1"
STORAGE_ALLOWED_USES = (
    "ui_preferences",
    "audio_preferences",
    "safe_resume_hints",
    "demo_anonymous_convenience",
)

_REPLAY_DESCRIPTORS = {
    GAME_CODE_MINES: {
        "player_replay_endpoint": "/games/mines/session/{roundRef}/replay",
        "admin_replay_endpoint": "/games/mines/admin/session/{roundRef}/replay",
        "replay_payload_schema": "mines.replay.v1",
        "viewer": "module-owned",
        "account_summary_fields": ("grid_size", "mine_count", "outcome", "payout_amount"),
        "finance_summary_fields": ("bet_amount", "payout_amount", "wallet_type"),
    },
    GAME_CODE_BOXE: {
        "player_replay_endpoint": "/games/boxe/round/{roundRef}/replay",
        "admin_replay_endpoint": "/games/boxe/admin/round/{roundRef}/replay",
        "replay_payload_schema": "boxe.replay.v1",
        "viewer": "module-owned",
        "account_summary_fields": ("rows", "difficulty", "outcome", "payout_amount"),
        "finance_summary_fields": ("bet_amount", "payout_amount", "wallet_source"),
    },
    GAME_CODE_HI_LO: {
        "player_replay_endpoint": "/games/hi-lo/round/{roundRef}/replay",
        "admin_replay_endpoint": "/games/hi-lo/admin/round/{roundRef}/replay",
        "replay_payload_schema": "hi_lo.replay.v1",
        "viewer": "module-owned",
        "account_summary_fields": ("deck", "step", "outcome", "payout_amount"),
        "finance_summary_fields": ("bet_amount", "payout_amount", "wallet_source"),
    },
}


def build_game_module_descriptor_payload(
    *,
    game_code: str,
    title_code: str,
    site_code: str,
    mode: str,
    player_ref: str,
    wallet_source: str,
    launch_ref: str,
    host_code: str | None = None,
    brand_code: str | None = None,
    return_url: str | None = None,
    locale: str | None = None,
    embed_origin: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, object]:
    storage_descriptor = build_storage_descriptor(
        game_code=game_code,
        title_code=title_code,
        site_code=site_code,
    )
    launch_descriptor = GameLaunchDescriptor(
        game_code=game_code,
        title_code=title_code,
        site_code=site_code,
        mode=mode,
        player_ref=player_ref,
        wallet_source=wallet_source,
        launch_ref=launch_ref,
        host_code=host_code or site_code,
        brand_code=brand_code or site_code,
        return_url=return_url,
        locale=locale or "it",
        embed_origin=embed_origin,
        storage_namespace=storage_descriptor.namespace,
        correlation_id=correlation_id,
    )
    embed_descriptor = GameEmbedDescriptor(
        protocol=EMBED_PROTOCOL_V1,
        game_code=game_code,
        launch_ref=launch_ref,
        embed_origin=embed_origin,
    )
    replay_descriptor = build_replay_descriptor(game_code=game_code)
    return {
        "launch_descriptor": asdict(launch_descriptor),
        "storage_descriptor": asdict(storage_descriptor),
        "embed_descriptor": asdict(embed_descriptor),
        "replay_descriptor": asdict(replay_descriptor),
    }


def build_storage_descriptor(
    *,
    game_code: str,
    title_code: str,
    site_code: str,
) -> GameStorageDescriptor:
    return GameStorageDescriptor(
        namespace=build_storage_namespace(site_code=site_code, game_code=game_code),
        game_code=game_code,
        title_code=title_code,
        site_code=site_code,
        allowed_uses=STORAGE_ALLOWED_USES,
    )


def build_storage_namespace(*, site_code: str, game_code: str) -> str:
    return f"host.{_storage_component(site_code)}.game.{_storage_component(game_code)}"


def build_replay_descriptor(*, game_code: str) -> GameReplayDescriptor:
    descriptor = _REPLAY_DESCRIPTORS[game_code]
    return GameReplayDescriptor(
        game_code=game_code,
        player_replay_endpoint=str(descriptor["player_replay_endpoint"]),
        admin_replay_endpoint=str(descriptor["admin_replay_endpoint"]),
        replay_payload_schema=str(descriptor["replay_payload_schema"]),
        viewer=str(descriptor["viewer"]),
        account_summary_fields=tuple(descriptor["account_summary_fields"]),
        finance_summary_fields=tuple(descriptor["finance_summary_fields"]),
    )


def _storage_component(raw_value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", raw_value.strip().lower()).strip("-")
    return normalized or "unknown"
