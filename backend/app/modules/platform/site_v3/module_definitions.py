from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from app.api.errors import AppError
from app.api.request_context import get_or_create_request_id
from app.db.connection import db_connection
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.site_v3 import repository
from app.modules.platform.site_v3.manifests.modules import MODULE_MANIFESTS


ALLOWED_DEFINITION_STATUSES = frozenset({"draft", "published", "archived", "all"})
ALLOWED_DEFINITION_CATEGORIES = frozenset({"hero", "catalog", "promo", "text_legal"})
ALLOWED_RENDERER_TEMPLATES = frozenset(
    {"image_banner", "game_grid", "editorial_panel", "rich_text", "feature_card"}
)
ALLOWED_FIELD_TYPES = frozenset(
    {"asset_ref", "boolean", "html", "string", "title_code", "title_code_list", "url"}
)
ALLOWED_FIELD_GROUPS = frozenset({"assets", "catalog", "content", "links", "rules"})
MODULE_CODE_PATTERN = re.compile(r"^custom_[a-z0-9][a-z0-9_]{1,56}$")
FIELD_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
AUDIT_RESOURCE_KIND = "site_v3_module_definition"


def list_custom_module_definitions(
    *,
    site_code: str,
    status_filter: str = "all",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_status = _normalize_status_filter(status_filter)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            definitions = repository.list_module_definitions(
                cursor=cursor,
                site_code=normalized_site_code,
                status_filter=normalized_status,
            )
    return {
        "site_code": normalized_site_code,
        "definitions": [_serialize_definition(row) for row in definitions],
    }


def get_custom_module_definition(*, site_code: str, module_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_module_code = _normalize_module_code(module_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            definition = repository.load_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=normalized_module_code,
            )
            if definition is None:
                raise AppError("SITEV3.MODULE_DEFINITION.NOT_FOUND")
    return {"definition": _serialize_definition(definition)}


def create_custom_module_definition(
    *,
    site_code: str,
    payload: dict[str, Any],
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    normalized_payload = _normalize_definition_payload(payload)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            existing = repository.load_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=normalized_payload["module_code"],
            )
            if existing is not None:
                raise AppError(
                    "SITEV3.MODULE_DEFINITION.DUPLICATE_CODE",
                    details={"field": "module_code"},
                )
            definition = repository.create_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=str(normalized_payload["module_code"]),
                label=str(normalized_payload["label"]),
                category=str(normalized_payload["category"]),
                renderer_template=str(normalized_payload["renderer_template"]),
                field_schema_json=list(normalized_payload["field_schema_json"]),
                default_config_json=dict(normalized_payload["default_config_json"]),
                admin_user_id=normalized_admin_user_id,
            )
            _record_definition_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.module_definition_create",
                definition=definition,
                payload_extra={"status": definition["status"]},
            )
    return {"definition": _serialize_definition(definition)}


def update_custom_module_definition_draft(
    *,
    site_code: str,
    module_code: str,
    payload: dict[str, Any],
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_module_code = _normalize_module_code(module_code)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    normalized_payload = _normalize_definition_payload({**payload, "module_code": normalized_module_code})
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            definition = repository.load_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=normalized_module_code,
                for_update=True,
            )
            if definition is None:
                raise AppError("SITEV3.MODULE_DEFINITION.NOT_FOUND")
            if definition["status"] == "archived":
                raise AppError(
                    "SITEV3.MODULE_DEFINITION.INVALID_STATE",
                    details={"field": "status", "status": "archived"},
                )
            updated_definition = repository.update_module_definition_draft(
                cursor=cursor,
                definition_id=str(definition["id"]),
                label=str(normalized_payload["label"]),
                category=str(normalized_payload["category"]),
                renderer_template=str(normalized_payload["renderer_template"]),
                field_schema_json=list(normalized_payload["field_schema_json"]),
                default_config_json=dict(normalized_payload["default_config_json"]),
                admin_user_id=normalized_admin_user_id,
            )
            _record_definition_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.module_definition_update_draft",
                definition=updated_definition,
                payload_extra={"draft_schema_version": updated_definition["draft_schema_version"]},
            )
    return {"definition": _serialize_definition(updated_definition)}


def validate_custom_module_definition_payload(*, payload: dict[str, Any]) -> dict[str, object]:
    try:
        _normalize_definition_payload(payload)
    except AppError as exc:
        details = exc.details if isinstance(exc.details, dict) else {}
        issues = details.get("issues") if isinstance(details.get("issues"), list) else []
        return {"status": "invalid", "issues": issues}
    return {"status": "valid", "issues": []}


def publish_custom_module_definition(
    *,
    site_code: str,
    module_code: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_module_code = _normalize_module_code(module_code)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            definition = repository.load_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=normalized_module_code,
                for_update=True,
            )
            if definition is None:
                raise AppError("SITEV3.MODULE_DEFINITION.NOT_FOUND")
            if definition["status"] == "archived":
                raise AppError(
                    "SITEV3.MODULE_DEFINITION.INVALID_STATE",
                    details={"field": "status", "status": "archived"},
                )
            _normalize_definition_payload(_payload_from_definition_row(definition))
            version = int(definition["published_version"] or 0) + 1
            version_row = repository.create_module_definition_version(
                cursor=cursor,
                definition_id=str(definition["id"]),
                version=version,
                label=str(definition["label"]),
                category=str(definition["category"]),
                renderer_template=str(definition["renderer_template"]),
                schema_version=int(definition["draft_schema_version"]),
                field_schema_json=list(definition["draft_field_schema_json"]),
                default_config_json=dict(definition["draft_default_config_json"]),
                created_by=str(definition["updated_by"]),
                published_by=normalized_admin_user_id,
            )
            published_definition = repository.mark_module_definition_published(
                cursor=cursor,
                definition_id=str(definition["id"]),
                version=version,
                admin_user_id=normalized_admin_user_id,
            )
            _record_definition_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.module_definition_publish",
                definition=published_definition,
                payload_extra={"published_version": version},
            )
    return {
        "definition": _serialize_definition(published_definition),
        "version": _serialize_definition_version(version_row),
    }


def archive_custom_module_definition(
    *,
    site_code: str,
    module_code: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_module_code = _normalize_module_code(module_code)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            definition = repository.load_module_definition(
                cursor=cursor,
                site_code=normalized_site_code,
                module_code=normalized_module_code,
                for_update=True,
            )
            if definition is None:
                raise AppError("SITEV3.MODULE_DEFINITION.NOT_FOUND")
            archived_definition = repository.mark_module_definition_archived(
                cursor=cursor,
                definition_id=str(definition["id"]),
                admin_user_id=normalized_admin_user_id,
            )
            _record_definition_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.module_definition_archive",
                definition=archived_definition,
                payload_extra={"published_version": archived_definition["published_version"]},
            )
    return {"definition": _serialize_definition(archived_definition)}


def _normalize_definition_payload(payload: dict[str, Any]) -> dict[str, object]:
    if not isinstance(payload, dict):
        _raise_definition_invalid([
            _issue("payload", "SITEV3.MODULE_DEFINITION.INVALID", "Definition payload must be an object")
        ])
    module_code = _normalize_module_code(payload.get("module_code"))
    label = _normalize_label(payload.get("label"))
    category = str(payload.get("category") or "").strip().lower()
    renderer_template = str(payload.get("renderer_template") or "").strip().lower()
    raw_field_schema = payload.get("field_schema_json", payload.get("field_schema", []))
    raw_default_config = payload.get("default_config_json", payload.get("default_config", {}))
    issues: list[dict[str, object]] = []

    if module_code in MODULE_MANIFESTS:
        issues.append(_issue("module_code", "SITEV3.MODULE_DEFINITION.RESERVED_CODE", "Module code collides with a built-in module"))
    if category not in ALLOWED_DEFINITION_CATEGORIES:
        issues.append(_issue("category", "SITEV3.MODULE_DEFINITION.INVALID_CATEGORY", "Category is not supported for custom modules"))
    if renderer_template not in ALLOWED_RENDERER_TEMPLATES:
        issues.append(_issue("renderer_template", "SITEV3.MODULE_DEFINITION.INVALID_TEMPLATE", "Renderer template is not supported"))

    field_schema = _normalize_field_schema(raw_field_schema, issues=issues)
    default_config = _normalize_default_config(raw_default_config, field_schema=field_schema, issues=issues)
    if issues:
        _raise_definition_invalid(issues)
    return {
        "module_code": module_code,
        "label": label,
        "category": category,
        "renderer_template": renderer_template,
        "field_schema_json": field_schema,
        "default_config_json": default_config,
    }


def _normalize_module_code(raw_value: object) -> str:
    normalized = str(raw_value or "").strip().lower().replace("-", "_")
    if not MODULE_CODE_PATTERN.fullmatch(normalized):
        _raise_definition_invalid([
            _issue("module_code", "SITEV3.MODULE_DEFINITION.INVALID_CODE", "Module code must start with custom_ and use lowercase letters, numbers or underscores")
        ])
    return normalized


def _normalize_label(raw_value: object) -> str:
    if not isinstance(raw_value, str):
        _raise_definition_invalid([
            _issue("label", "SITEV3.MODULE_DEFINITION.INVALID_LABEL", "Label is required")
        ])
    normalized = raw_value.strip()
    if not normalized or len(normalized) > 120:
        _raise_definition_invalid([
            _issue("label", "SITEV3.MODULE_DEFINITION.INVALID_LABEL", "Label must be between 1 and 120 characters")
        ])
    return normalized


def _normalize_field_schema(raw_value: object, *, issues: list[dict[str, object]]) -> list[dict[str, object]]:
    if not isinstance(raw_value, list):
        issues.append(_issue("field_schema_json", "SITEV3.MODULE_DEFINITION.INVALID_FIELDS", "Field schema must be a list"))
        return []
    if not raw_value:
        issues.append(_issue("field_schema_json", "SITEV3.MODULE_DEFINITION.INVALID_FIELDS", "At least one field is required"))
        return []
    if len(raw_value) > 20:
        issues.append(_issue("field_schema_json", "SITEV3.MODULE_DEFINITION.INVALID_FIELDS", "A custom module can have at most 20 fields"))

    field_keys: set[str] = set()
    normalized_fields: list[dict[str, object]] = []
    for index, raw_field in enumerate(raw_value[:20]):
        field_path = f"field_schema_json[{index}]"
        if not isinstance(raw_field, dict):
            issues.append(_issue(field_path, "SITEV3.MODULE_DEFINITION.INVALID_FIELD", "Field must be an object"))
            continue
        key = str(raw_field.get("key") or "").strip().lower()
        label = str(raw_field.get("label") or "").strip()
        field_type = str(raw_field.get("type") or raw_field.get("field_type") or "").strip().lower()
        group = str(raw_field.get("group") or _default_group_for_field_type(field_type)).strip().lower()
        required = bool(raw_field.get("required", False))
        help_text = str(raw_field.get("help") or "").strip()
        max_length = _normalize_optional_int(raw_field.get("max_length", raw_field.get("maxLength")), minimum=1, maximum=12000)
        max_items = _normalize_optional_int(raw_field.get("max_items", raw_field.get("maxItems")), minimum=1, maximum=50)

        if not FIELD_KEY_PATTERN.fullmatch(key):
            issues.append(_issue(f"{field_path}.key", "SITEV3.MODULE_DEFINITION.INVALID_FIELD_KEY", "Field key must be snake_case and start with a letter"))
        if key in field_keys:
            issues.append(_issue(f"{field_path}.key", "SITEV3.MODULE_DEFINITION.DUPLICATE_FIELD_KEY", "Field key is duplicated"))
        field_keys.add(key)
        if not label or len(label) > 80:
            issues.append(_issue(f"{field_path}.label", "SITEV3.MODULE_DEFINITION.INVALID_FIELD_LABEL", "Field label must be between 1 and 80 characters"))
        if field_type not in ALLOWED_FIELD_TYPES:
            issues.append(_issue(f"{field_path}.type", "SITEV3.MODULE_DEFINITION.INVALID_FIELD_TYPE", "Field type is not supported"))
        if group not in ALLOWED_FIELD_GROUPS:
            issues.append(_issue(f"{field_path}.group", "SITEV3.MODULE_DEFINITION.INVALID_FIELD_GROUP", "Field group is not supported"))
        if help_text and len(help_text) > 240:
            issues.append(_issue(f"{field_path}.help", "SITEV3.MODULE_DEFINITION.INVALID_FIELD_HELP", "Field help is too long"))
        if max_length is None and field_type in {"string", "url"}:
            max_length = 300 if field_type == "url" else 160
        if max_length is None and field_type == "html":
            max_length = 12000
        if max_items is None and field_type == "title_code_list":
            max_items = 24

        normalized_fields.append(
            {
                "key": key,
                "label": label,
                "type": field_type,
                "group": group,
                "required": required,
                **({"max_length": max_length} if max_length is not None else {}),
                **({"max_items": max_items} if max_items is not None else {}),
                **({"help": help_text} if help_text else {}),
            }
        )
    return normalized_fields


def _normalize_default_config(
    raw_value: object,
    *,
    field_schema: list[dict[str, object]],
    issues: list[dict[str, object]],
) -> dict[str, object]:
    if not isinstance(raw_value, dict):
        issues.append(_issue("default_config_json", "SITEV3.MODULE_DEFINITION.INVALID_DEFAULTS", "Default config must be an object"))
        return {}
    try:
        if len(json.dumps(raw_value, sort_keys=True)) > 20000:
            issues.append(_issue("default_config_json", "SITEV3.MODULE_DEFINITION.INVALID_DEFAULTS", "Default config is too large"))
    except TypeError:
        issues.append(_issue("default_config_json", "SITEV3.MODULE_DEFINITION.INVALID_DEFAULTS", "Default config must be JSON serializable"))
        return {}

    known_fields = {str(field["key"]): field for field in field_schema if "key" in field}
    for key in raw_value:
        if key not in known_fields:
            issues.append(_issue(f"default_config_json.{key}", "SITEV3.MODULE_DEFINITION.UNKNOWN_DEFAULT_FIELD", "Default config contains an unknown field"))

    normalized_defaults: dict[str, object] = {}
    for key, field in known_fields.items():
        value = raw_value.get(key, _empty_default_for_type(str(field["type"])))
        if not _default_value_matches_type(value, str(field["type"])):
            issues.append(_issue(f"default_config_json.{key}", "SITEV3.MODULE_DEFINITION.INVALID_DEFAULT_VALUE", "Default value does not match the field type"))
            value = _empty_default_for_type(str(field["type"]))
        normalized_defaults[key] = value
    return normalized_defaults


def _empty_default_for_type(field_type: str) -> object:
    if field_type == "boolean":
        return False
    if field_type == "asset_ref":
        return {}
    if field_type == "title_code_list":
        return []
    return ""


def _default_value_matches_type(value: object, field_type: str) -> bool:
    if field_type in {"string", "html", "title_code", "url"}:
        return isinstance(value, str)
    if field_type == "boolean":
        return isinstance(value, bool)
    if field_type == "asset_ref":
        return isinstance(value, dict)
    if field_type == "title_code_list":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    return False


def _default_group_for_field_type(field_type: str) -> str:
    if field_type == "asset_ref":
        return "assets"
    if field_type in {"title_code", "title_code_list"}:
        return "catalog"
    if field_type in {"url"}:
        return "links"
    if field_type == "html":
        return "rules"
    return "content"


def _normalize_optional_int(raw_value: object, *, minimum: int, maximum: int) -> int | None:
    if raw_value is None or raw_value == "":
        return None
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return None
    if parsed < minimum or parsed > maximum:
        return None
    return parsed


def _payload_from_definition_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "module_code": row["module_code"],
        "label": row["label"],
        "category": row["category"],
        "renderer_template": row["renderer_template"],
        "field_schema_json": row["draft_field_schema_json"],
        "default_config_json": row["draft_default_config_json"],
    }


def _require_site(*, cursor, site_code: str) -> dict[str, object]:
    site = repository.load_site(cursor=cursor, site_code=site_code)
    if site is None:
        raise AppError("SITEV3.PAGE.NOT_FOUND", message="Site not found")
    if site["status"] != "active":
        raise AppError("SITEV3.PAGE.NOT_FOUND", message="Site is not active")
    return site


def _normalize_code(raw_value: str, message: str, *, max_length: int) -> str:
    if not isinstance(raw_value, str):
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    normalized = raw_value.strip().lower()
    if not normalized or len(normalized) > max_length:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if not normalized[0].isalnum() or any(character not in allowed_chars for character in normalized):
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    return normalized


def _normalize_status_filter(raw_value: str) -> str:
    normalized = str(raw_value or "all").strip().lower()
    if normalized not in ALLOWED_DEFINITION_STATUSES:
        raise AppError("SITEV3.VALIDATION.REQUIRED", details={"field": "status"})
    return normalized


def _normalize_uuid(raw_value: str | None, message: str) -> str:
    try:
        return str(UUID(str(raw_value)))
    except (TypeError, ValueError) as exc:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message) from exc


def _serialize_definition(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "site_code": row["site_code"],
        "module_code": row["module_code"],
        "label": row["label"],
        "category": row["category"],
        "renderer_template": row["renderer_template"],
        "draft_schema_version": row["draft_schema_version"],
        "field_schema_json": row["draft_field_schema_json"],
        "default_config_json": row["draft_default_config_json"],
        "status": row["status"],
        "published_version": row["published_version"],
        "created_by": str(row["created_by"]),
        "updated_by": str(row["updated_by"]),
        "published_by": str(row["published_by"]) if row["published_by"] is not None else None,
        "archived_by": str(row["archived_by"]) if row["archived_by"] is not None else None,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "published_at": row["published_at"].isoformat() if row["published_at"] is not None else None,
        "archived_at": row["archived_at"].isoformat() if row["archived_at"] is not None else None,
    }


def _serialize_definition_version(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "definition_id": str(row["definition_id"]),
        "version": row["version"],
        "label": row["label"],
        "category": row["category"],
        "renderer_template": row["renderer_template"],
        "schema_version": row["schema_version"],
        "field_schema_json": row["field_schema_json"],
        "default_config_json": row["default_config_json"],
        "created_by": str(row["created_by"]),
        "published_by": str(row["published_by"]),
        "created_at": row["created_at"].isoformat(),
        "published_at": row["published_at"].isoformat(),
    }


def _record_definition_audit(
    *,
    cursor,
    admin_user_id: str,
    action_kind: str,
    definition: dict[str, object],
    payload_extra: dict[str, object] | None = None,
) -> None:
    request_id = get_or_create_request_id()
    site_code = str(definition["site_code"])
    module_code = str(definition["module_code"])
    resource_id = f"{site_code}:{module_code}"
    payload: dict[str, object] = {
        "source": "site_v3",
        "actor": {"admin_user_id": admin_user_id},
        "request_id": request_id,
        "support_id": request_id,
        "site_code": site_code,
        "module_code": module_code,
    }
    if payload_extra:
        payload.update(payload_extra)
    record_audit_entry(
        admin_user_id=admin_user_id,
        action_kind=action_kind,
        resource_kind=AUDIT_RESOURCE_KIND,
        resource_id=resource_id,
        payload=payload,
        request_fingerprint=build_audit_request_fingerprint(
            action_kind=action_kind,
            resource_kind=AUDIT_RESOURCE_KIND,
            resource_id=resource_id,
            payload=payload,
        ),
        cursor=cursor,
    )


def _issue(field: str, code: str, message: str) -> dict[str, object]:
    return {
        "severity": "error",
        "field": field,
        "code": code,
        "message": message,
    }


def _raise_definition_invalid(issues: list[dict[str, object]]) -> None:
    raise AppError(
        "SITEV3.MODULE_DEFINITION.INVALID",
        details={"issues": issues},
    )
