from __future__ import annotations

from contextlib import contextmanager
import json
from hashlib import sha256
from typing import Iterator

import psycopg

from app.db.connection import db_connection


class AdminAuditValidationError(Exception):
    pass


@contextmanager
def _managed_cursor(
    cursor: psycopg.Cursor | None,
) -> Iterator[psycopg.Cursor]:
    if cursor is not None:
        yield cursor
        return

    with db_connection() as connection:
        with connection.cursor() as managed:
            yield managed


def record_audit_entry(
    *,
    admin_user_id: str,
    action_kind: str,
    resource_kind: str,
    resource_id: str,
    payload: dict,
    request_fingerprint: str,
    cursor: psycopg.Cursor | None = None,
) -> None:
    normalized_action_kind = _normalize_text(
        action_kind,
        field_name="action_kind",
        max_length=64,
    )
    normalized_resource_kind = _normalize_text(
        resource_kind,
        field_name="resource_kind",
        max_length=32,
    )
    normalized_resource_id = _normalize_text(
        resource_id,
        field_name="resource_id",
        max_length=128,
    )
    normalized_request_fingerprint = _normalize_request_fingerprint(request_fingerprint)
    payload_json = _canonical_payload(payload)

    with _managed_cursor(cursor) as active_cursor:
        active_cursor.execute(
            """
            INSERT INTO admin_audit_log (
                admin_user_id,
                action_kind,
                resource_kind,
                resource_id,
                payload_json,
                request_fingerprint
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                admin_user_id,
                normalized_action_kind,
                normalized_resource_kind,
                normalized_resource_id,
                payload_json,
                normalized_request_fingerprint,
            ),
        )


def build_audit_request_fingerprint(
    *,
    action_kind: str,
    resource_kind: str,
    resource_id: str,
    payload: dict,
) -> str:
    serialized = json.dumps(
        {
            "action_kind": action_kind,
            "payload": payload,
            "resource_id": resource_id,
            "resource_kind": resource_kind,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _normalize_text(value: str, *, field_name: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise AdminAuditValidationError(f"{field_name} is required")
    if len(normalized) > max_length:
        raise AdminAuditValidationError(f"{field_name} is too long")
    return normalized


def _normalize_request_fingerprint(value: str) -> str:
    normalized = value.strip()
    if len(normalized) != 64:
        raise AdminAuditValidationError("request_fingerprint must be a 64-character digest")
    return normalized


def _canonical_payload(payload: dict) -> str:
    if not isinstance(payload, dict):
        raise AdminAuditValidationError("payload must be an object")
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)
