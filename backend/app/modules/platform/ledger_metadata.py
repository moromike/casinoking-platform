from __future__ import annotations

from hashlib import sha256
from typing import Any

LEDGER_METADATA_SCHEMA_VERSION = 2

METADATA_COMPLETENESS_COMPLETE = "complete"
METADATA_COMPLETENESS_PARTIAL = "partial"
METADATA_COMPLETENESS_LEGACY = "legacy"

FORWARD_LEDGER_METADATA_FIELDS = frozenset(
    {
        "game_code",
        "title_code",
        "site_code",
        "wallet_type",
        "platform_round_id",
        "game_round_id",
        "access_session_id",
        "settlement_kind",
        "idempotency_key_hash",
        "replay_ref",
        "metadata_schema_version",
    }
)


def build_forward_ledger_metadata(
    *,
    game_code: str,
    title_code: str,
    site_code: str,
    wallet_type: str,
    platform_round_id: str,
    game_round_id: str | None,
    access_session_id: str | None,
    settlement_kind: str | None,
    idempotency_key: str | None,
    replay_ref: dict[str, Any] | None = None,
    game_config_payload: dict[str, Any] | None = None,
    progress_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "game_code": game_code,
        "title_code": title_code,
        "site_code": site_code,
        "wallet_type": wallet_type,
        "platform_round_id": platform_round_id,
        "game_round_id": game_round_id or platform_round_id,
        "access_session_id": access_session_id,
        "settlement_kind": settlement_kind,
        "idempotency_key_hash": _hash_idempotency_key(idempotency_key),
        "replay_ref": replay_ref,
        "metadata_schema_version": LEDGER_METADATA_SCHEMA_VERSION,
    }
    if game_config_payload is not None:
        metadata["game_config_payload"] = game_config_payload
    if progress_payload is not None:
        metadata["progress_payload"] = progress_payload
    metadata["metadata_completeness"] = classify_metadata_completeness(metadata)
    return metadata


def classify_metadata_completeness(metadata: object) -> str:
    if not isinstance(metadata, dict):
        return METADATA_COMPLETENESS_LEGACY
    if "metadata_schema_version" not in metadata:
        return METADATA_COMPLETENESS_LEGACY
    if not FORWARD_LEDGER_METADATA_FIELDS.issubset(metadata):
        return METADATA_COMPLETENESS_PARTIAL
    if metadata.get("settlement_kind") is None:
        return METADATA_COMPLETENESS_PARTIAL
    if metadata.get("idempotency_key_hash") is None:
        return METADATA_COMPLETENESS_PARTIAL
    if metadata.get("replay_ref") is None:
        return METADATA_COMPLETENESS_PARTIAL
    return METADATA_COMPLETENESS_COMPLETE


def _hash_idempotency_key(idempotency_key: str | None) -> str | None:
    if not idempotency_key:
        return None
    return sha256(idempotency_key.encode("utf-8")).hexdigest()
