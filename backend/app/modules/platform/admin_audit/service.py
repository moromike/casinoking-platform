from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, date, datetime, time
import json
from hashlib import sha256
from typing import Iterator

import psycopg

from app.db.connection import db_connection


class AdminAuditValidationError(Exception):
    pass


ADMIN_AUDIT_LOG_MAX_LIMIT = 100


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


def list_audit_entries(
    *,
    action_kind: str | None = None,
    resource_kind: str | None = None,
    resource_id: str | None = None,
    admin_user_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: str | int = 1,
    limit: str | int = 50,
) -> dict[str, object]:
    normalized_action_kind = _normalize_optional_text(
        action_kind,
        field_name="action_kind",
        max_length=64,
    )
    normalized_resource_kind = _normalize_optional_text(
        resource_kind,
        field_name="resource_kind",
        max_length=32,
    )
    normalized_resource_id = _normalize_optional_text(
        resource_id,
        field_name="resource_id",
        max_length=128,
    )
    normalized_admin_user_id = _normalize_optional_text(
        admin_user_id,
        field_name="admin_user_id",
        max_length=36,
    )
    parsed_date_from = _parse_audit_datetime(
        date_from,
        field_name="date_from",
        end_of_day=False,
    )
    parsed_date_to = _parse_audit_datetime(
        date_to,
        field_name="date_to",
        end_of_day=True,
    )
    if parsed_date_from is not None and parsed_date_to is not None and parsed_date_from > parsed_date_to:
        raise AdminAuditValidationError("date_from must be earlier than or equal to date_to")

    normalized_page = _parse_positive_int(page, field_name="page")
    normalized_limit = _parse_positive_int(limit, field_name="limit")
    if normalized_limit > ADMIN_AUDIT_LOG_MAX_LIMIT:
        raise AdminAuditValidationError(f"limit must be less than or equal to {ADMIN_AUDIT_LOG_MAX_LIMIT}")

    conditions: list[str] = []
    params: list[object] = []
    if normalized_action_kind is not None:
        conditions.append("action_kind = %s")
        params.append(normalized_action_kind)
    if normalized_resource_kind is not None:
        conditions.append("resource_kind = %s")
        params.append(normalized_resource_kind)
    if normalized_resource_id is not None:
        conditions.append("resource_id = %s")
        params.append(normalized_resource_id)
    if normalized_admin_user_id is not None:
        conditions.append("admin_user_id = %s")
        params.append(normalized_admin_user_id)
    if parsed_date_from is not None:
        conditions.append("created_at >= %s")
        params.append(parsed_date_from)
    if parsed_date_to is not None:
        conditions.append("created_at <= %s")
        params.append(parsed_date_to)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (normalized_page - 1) * normalized_limit

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total_items
                FROM admin_audit_log
                {where_clause}
                """,
                params,
            )
            total_items = int(cursor.fetchone()["total_items"])

            cursor.execute(
                f"""
                SELECT
                    id,
                    admin_user_id,
                    action_kind,
                    resource_kind,
                    resource_id,
                    payload_json,
                    request_fingerprint,
                    created_at
                FROM admin_audit_log
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, normalized_limit, offset],
            )
            rows = cursor.fetchall()

    total_pages = 0 if total_items == 0 else (total_items + normalized_limit - 1) // normalized_limit
    return {
        "events": [
            {
                "id": str(row["id"]),
                "admin_user_id": str(row["admin_user_id"]),
                "action_kind": row["action_kind"],
                "resource_kind": row["resource_kind"],
                "resource_id": row["resource_id"],
                "payload_json": row["payload_json"],
                "request_fingerprint": row["request_fingerprint"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ],
        "pagination": {
            "page": normalized_page,
            "limit": normalized_limit,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


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


def _normalize_optional_text(
    value: str | None,
    *,
    field_name: str,
    max_length: int,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        raise AdminAuditValidationError(f"{field_name} is not valid")
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


def _parse_positive_int(value: str | int, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AdminAuditValidationError(f"{field_name} must be a positive integer") from exc
    if parsed < 1:
        raise AdminAuditValidationError(f"{field_name} must be greater than or equal to 1")
    return parsed


def _parse_audit_datetime(
    value: str | None,
    *,
    field_name: str,
    end_of_day: bool,
) -> datetime | None:
    if value is None:
        return None

    normalized_value = value.strip()
    if not normalized_value:
        raise AdminAuditValidationError(f"{field_name} is not valid")

    try:
        if len(normalized_value) == 10:
            parsed_date = date.fromisoformat(normalized_value)
            return datetime.combine(
                parsed_date,
                time.max if end_of_day else time.min,
                tzinfo=UTC,
            )

        parsed_datetime = datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdminAuditValidationError(f"{field_name} is not valid") from exc

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=UTC)
    return parsed_datetime.astimezone(UTC)
