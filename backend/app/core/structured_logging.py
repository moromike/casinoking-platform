from __future__ import annotations

from datetime import UTC, datetime
import json
from collections.abc import Mapping
import sys
from typing import Any, Literal

from app.api.request_context import get_request_id


LogLevel = Literal["debug", "info", "warning", "error", "critical"]

REDACTED_VALUE = "[REDACTED]"
TRUNCATED_CONTAINER = {"...truncated...": True}
TRUNCATED_SUFFIX = "\u2026[truncated]"
MAX_STRING_LENGTH = 256
MAX_NESTING_DEPTH = 3
MAX_PAYLOAD_BYTES = 8 * 1024

EXACT_SENSITIVE_KEYS = {
    "authorization",
    "token",
    "jwt",
    "secret",
    "password",
    "pwd",
    "server_seed",
    "private_key",
    "database_url",
    "redis_url",
    "reset_token",
    "access_token",
    "launch_token",
}

SENSITIVE_KEY_SUFFIXES = (
    "_token",
    "_secret",
    "_password",
    "_pwd",
    "_key",
    "_seed",
    "_credential",
    "_authorization",
)

SENSITIVE_KEY_SUBSTRINGS = (
    "secret",
    "password",
    "token",
    "seed",
    "credential",
    "authorization",
    "bearer",
    "authheader",
)

LOG_EVENT_NAMES = {
    "system.unhandled_exception",
    "system.validation_error",
    "system.http_exception_normalized",
    "access_session.timeout_sweep_failed",
    "access_session.auto_settlement_failed",
    "ledger.idempotency_conflict",
    "log.missing_request_id",
    "log.payload_truncated",
    "log.serialization_fallback",
}

_VALID_LEVELS = {"debug", "info", "warning", "error", "critical"}


def log_event(
    level: str,
    event_name: str,
    details: Mapping[str, Any] | None = None,
    *,
    job_id: str | None = None,
) -> None:
    """Emit one structured JSON line to stdout.

    MVP policy: `critical` is only a level label for filtering; it does not
    trigger paging or alerting.
    """

    try:
        normalized_level = _normalize_level(level)
        request_id = get_request_id()
        context_fields, missing_request_context = _context_fields(
            request_id=request_id,
            job_id=job_id,
        )
        sanitized_details, used_serialization_fallback = sanitize_log_details(details or {})
        record = _build_record(
            level=normalized_level,
            event_name=event_name,
            context_fields=context_fields,
            details=sanitized_details,
        )

        if used_serialization_fallback:
            _emit_internal_event(
                level="warning",
                event_name="log.serialization_fallback",
                details={"original_event_name": event_name},
                context_fields=context_fields,
            )
        if missing_request_context:
            _emit_internal_event(
                level="warning",
                event_name="log.missing_request_id",
                details={"original_event_name": event_name},
                context_fields=context_fields,
            )

        json_line = _serialize_record(record)
        if len(json_line.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            _emit_internal_event(
                level="warning",
                event_name="log.payload_truncated",
                details={
                    "original_event_name": event_name,
                    "payload_bytes": len(json_line.encode("utf-8")),
                    "max_payload_bytes": MAX_PAYLOAD_BYTES,
                },
                context_fields=context_fields,
            )
            record.pop("details", None)
            json_line = _serialize_record(record)

        _write_stdout_line(json_line)
    except Exception:
        return


def sanitize_log_details(details: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    sanitized, used_fallback = _sanitize_value(details, depth=0)
    if isinstance(sanitized, dict):
        return sanitized, used_fallback
    return {}, True


def is_sensitive_key(key: str) -> bool:
    normalized_key = key.lower()
    compact_key = "".join(char for char in normalized_key if char.isalnum())
    if normalized_key in EXACT_SENSITIVE_KEYS:
        return True
    if any(normalized_key.endswith(suffix) for suffix in SENSITIVE_KEY_SUFFIXES):
        return True
    if any(fragment in normalized_key for fragment in SENSITIVE_KEY_SUBSTRINGS):
        return True
    return any(compact_key.endswith(suffix.strip("_")) for suffix in SENSITIVE_KEY_SUFFIXES)


def _sanitize_value(value: Any, *, depth: int) -> tuple[Any, bool]:
    if depth > MAX_NESTING_DEPTH:
        return dict(TRUNCATED_CONTAINER), False

    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        used_fallback = False
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if is_sensitive_key(key):
                sanitized[key] = REDACTED_VALUE
                continue
            nested_value, nested_fallback = _sanitize_value(raw_value, depth=depth + 1)
            sanitized[key] = nested_value
            used_fallback = used_fallback or nested_fallback or not isinstance(raw_key, str)
        return sanitized, used_fallback

    if isinstance(value, (list, tuple)):
        sanitized_items: list[Any] = []
        used_fallback = False
        for item in value:
            sanitized_item, nested_fallback = _sanitize_value(item, depth=depth + 1)
            sanitized_items.append(sanitized_item)
            used_fallback = used_fallback or nested_fallback
        return sanitized_items, used_fallback

    if isinstance(value, str):
        return _truncate_string(value), False
    if isinstance(value, (int, float, bool)) or value is None:
        return value, False

    return _truncate_string(str(value)), True


def _truncate_string(value: str) -> str:
    if len(value) <= MAX_STRING_LENGTH:
        return value
    return value[: MAX_STRING_LENGTH - len(TRUNCATED_SUFFIX)] + TRUNCATED_SUFFIX


def _context_fields(
    *,
    request_id: str | None,
    job_id: str | None,
) -> tuple[dict[str, str], bool]:
    if job_id:
        return {"job_id": job_id}, False
    if request_id:
        return {"request_id": request_id}, False
    return {"request_id": "-"}, True


def _build_record(
    *,
    level: str,
    event_name: str,
    context_fields: Mapping[str, str],
    details: Mapping[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": level,
        "event_name": event_name,
        "event_schema_version": 1,
        **context_fields,
    }
    if details:
        record["details"] = dict(details)
    return record


def _emit_internal_event(
    *,
    level: str,
    event_name: str,
    details: Mapping[str, Any],
    context_fields: Mapping[str, str],
) -> None:
    record = _build_record(
        level=level,
        event_name=event_name,
        context_fields=context_fields,
        details=details,
    )
    _write_stdout_line(_serialize_record(record))


def _serialize_record(record: Mapping[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _write_stdout_line(line: str) -> None:
    sys.stdout.write(f"{line}\n")
    sys.stdout.flush()


def _normalize_level(level: str) -> str:
    normalized = level.lower()
    if normalized in _VALID_LEVELS:
        return normalized
    return "info"
