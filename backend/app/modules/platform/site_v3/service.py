from __future__ import annotations

from collections.abc import Callable
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
from app.modules.platform.site_v3.manifests import ModuleField, ModuleManifest, get_module_manifest, list_module_manifests
from app.modules.platform.site_v3.validation import (
    UnsafeHtmlError,
    sanitize_rich_text_html,
    validate_page_payload,
    validation_has_blockers,
)


ALLOWED_PAGE_STATUSES = frozenset({"draft", "published", "archived", "all"})
ALLOWED_LOCALES = frozenset({"it", "en", "de", "es"})
AUDIT_RESOURCE_KIND = "site_v3_page"


def list_admin_pages(
    *,
    site_code: str,
    locale: str = "it",
    status_filter: str = "all",
    page: int = 1,
    limit: int = 50,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_locale = _normalize_locale(locale)
    normalized_status = _normalize_status_filter(status_filter)
    normalized_page = _normalize_positive_int(page, "Page must be a positive integer")
    normalized_limit = min(_normalize_positive_int(limit, "Limit must be a positive integer"), 100)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            result = repository.list_pages(
                cursor=cursor,
                site_code=normalized_site_code,
                locale=normalized_locale,
                status_filter=normalized_status,
                page=normalized_page,
                limit=normalized_limit,
            )

    return {
        "site_code": normalized_site_code,
        "locale": normalized_locale,
        "pages": [_serialize_admin_page(row) for row in result["pages"]],
        "pagination": result["pagination"],
    }


def get_admin_page(
    *,
    site_code: str,
    page_code: str,
    locale: str = "it",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
            )
            if page is None:
                raise AppError("SITEV3.PAGE.NOT_FOUND")
            modules = repository.list_modules(cursor=cursor, page_id=str(page["id"]))
            versions = repository.list_versions(cursor=cursor, page_id=str(page["id"]))

    return {
        "page": _serialize_admin_page(page),
        "modules": [_serialize_module(row) for row in modules],
        "published": _published_summary(page=page, versions=versions),
    }


def save_draft(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    title: str,
    modules: list[dict[str, Any]],
    expected_draft_version: int | None,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    normalized_title = _normalize_title(title)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    normalized_expected_version = _normalize_optional_non_negative_int(expected_draft_version)
    normalized_modules = _normalize_modules(modules)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
                for_update=True,
            )
            created = False
            if page is None:
                page = repository.create_page(
                    cursor=cursor,
                    site_code=normalized_site_code,
                    page_code=normalized_page_code,
                    locale=normalized_locale,
                    title=normalized_title,
                    admin_user_id=normalized_admin_user_id,
                )
                created = True

            _check_expected_version(page=page, expected_draft_version=normalized_expected_version)
            manifest_resolver = _build_module_manifest_resolver(cursor=cursor, site_code=normalized_site_code)
            normalized_modules = _sanitize_module_html_fields(
                modules=normalized_modules,
                module_manifest_resolver=manifest_resolver,
            )
            saved_page = repository.update_page_draft(
                cursor=cursor,
                page_id=str(page["id"]),
                title=normalized_title,
                admin_user_id=normalized_admin_user_id,
            )
            repository.replace_modules(
                cursor=cursor,
                page_id=str(saved_page["id"]),
                modules=normalized_modules,
                admin_user_id=normalized_admin_user_id,
            )
            saved_modules = repository.list_modules(cursor=cursor, page_id=str(saved_page["id"]))
            if created:
                _record_page_audit(
                    cursor=cursor,
                    admin_user_id=normalized_admin_user_id,
                    action_kind="site_v3.page_create",
                    page=saved_page,
                    payload_extra={"draft_version": saved_page["draft_version"]},
                )
            _record_page_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.save_draft",
                page=saved_page,
                payload_extra={
                    "draft_version": saved_page["draft_version"],
                    "module_count": len(saved_modules),
                },
            )

    return {
        "page": _serialize_admin_page(saved_page),
        "modules": [_serialize_module(row) for row in saved_modules],
    }


def validate_draft_payload(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    title: str,
    modules: list[dict[str, Any]],
    admin_user_id: str | None = None,
    record_audit: bool = False,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    normalized_title = _normalize_title(title)
    normalized_modules = _normalize_modules(modules, sanitize_html=False)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid") if admin_user_id else None

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)

            def _title_exists(title_code: str) -> bool:
                return repository.title_is_available_for_site(
                    cursor=cursor,
                    site_code=normalized_site_code,
                    title_code=title_code,
                )
            manifest_resolver = _build_module_manifest_resolver(cursor=cursor, site_code=normalized_site_code)

            validation = validate_page_payload(
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
                title=normalized_title,
                modules=normalized_modules,
                title_exists=_title_exists,
                module_manifest_resolver=manifest_resolver,
            )
            if record_audit and normalized_admin_user_id:
                page = repository.load_page(
                    cursor=cursor,
                    site_code=normalized_site_code,
                    page_code=normalized_page_code,
                    locale=normalized_locale,
                )
                _record_page_audit(
                    cursor=cursor,
                    admin_user_id=normalized_admin_user_id,
                    action_kind="site_v3.validate",
                    page=page,
                    identity={
                        "site_code": normalized_site_code,
                        "page_code": normalized_page_code,
                        "locale": normalized_locale,
                    },
                    payload_extra={"validation": validation},
                )

    return validation


def publish_page(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    expected_draft_version: int | None,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")
    normalized_expected_version = _normalize_optional_non_negative_int(expected_draft_version)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
                for_update=True,
            )
            if page is None:
                raise AppError("SITEV3.PAGE.NOT_FOUND")
            _check_expected_version(page=page, expected_draft_version=normalized_expected_version)
            modules = repository.list_modules(cursor=cursor, page_id=str(page["id"]))

            def _title_exists(title_code: str) -> bool:
                return repository.title_is_available_for_site(
                    cursor=cursor,
                    site_code=normalized_site_code,
                    title_code=title_code,
                )
            manifest_resolver = _build_module_manifest_resolver(cursor=cursor, site_code=normalized_site_code)

            validation = validate_page_payload(
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
                title=str(page["title"]),
                modules=[_module_for_validation(row) for row in modules],
                title_exists=_title_exists,
                module_manifest_resolver=manifest_resolver,
            )
            if validation_has_blockers(validation):
                raise AppError(
                    "SITEV3.PUBLISH.VALIDATION_FAILED",
                    details=validation,
                )

            published_version = int(page["draft_version"])
            snapshot = build_snapshot_from_modules(
                page=page,
                modules=modules,
                version_key="published_version",
                version=published_version,
                custom_definition_resolver=_build_custom_definition_version_resolver(
                    cursor=cursor,
                    site_code=normalized_site_code,
                ),
            )
            version_row = repository.create_page_version(
                cursor=cursor,
                page_id=str(page["id"]),
                version=published_version,
                status="published",
                snapshot_json=snapshot,
                validation_json=validation,
                created_by=normalized_admin_user_id,
                published_by=normalized_admin_user_id,
            )
            published_page = repository.mark_page_published(
                cursor=cursor,
                page_id=str(page["id"]),
                version=published_version,
                admin_user_id=normalized_admin_user_id,
            )
            _record_page_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.publish",
                page=published_page,
                payload_extra={
                    "draft_version": published_page["draft_version"],
                    "published_version": published_version,
                    "version_id": str(version_row["id"]),
                    "validation": validation,
                },
            )

    return {
        "page": _serialize_admin_page(published_page),
        "version": _serialize_version(version_row, include_snapshot=True),
    }


def archive_page(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
                for_update=True,
            )
            if page is None:
                raise AppError("SITEV3.PAGE.NOT_FOUND")
            archived_page = repository.mark_page_archived(
                cursor=cursor,
                page_id=str(page["id"]),
                admin_user_id=normalized_admin_user_id,
            )
            _record_page_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.archive",
                page=archived_page,
                payload_extra={
                    "draft_version": archived_page["draft_version"],
                    "published_version": archived_page["published_version"],
                },
            )

    return {"page": _serialize_admin_page(archived_page)}


def list_page_versions(
    *,
    site_code: str,
    page_code: str,
    locale: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
            )
            if page is None:
                raise AppError("SITEV3.PAGE.NOT_FOUND")
            versions = repository.list_versions(cursor=cursor, page_id=str(page["id"]))

    return {
        "page": _serialize_admin_page(page),
        "versions": [_serialize_version(row, include_snapshot=False) for row in versions],
    }


def public_get_published_page(
    *,
    site_code: str,
    page_code: str,
    locale: str = "it",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
            )
            if page is None:
                raise AppError("SITEV3.PAGE.NOT_FOUND")
            if page["status"] != "published" or page["published_version"] is None:
                raise AppError("SITEV3.PAGE.NOT_PUBLISHED")
            version = repository.load_published_version(
                cursor=cursor,
                page_id=str(page["id"]),
                version=int(page["published_version"]),
            )
            if version is None:
                raise AppError("SITEV3.PAGE.NOT_PUBLISHED")

    snapshot = dict(version["snapshot_json"])
    snapshot["version_id"] = str(version["id"])
    snapshot["published_at"] = version["published_at"].isoformat() if version["published_at"] else None
    return snapshot


def public_get_navigation(
    *,
    site_code: str,
    locale: str = "it",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_locale = _normalize_locale(locale)
    header = None
    footer = None

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            for row in repository.list_published_pages(
                cursor=cursor,
                site_code=normalized_site_code,
                locale=normalized_locale,
            ):
                snapshot = dict(row["snapshot_json"])
                for module in snapshot.get("modules", []):
                    if not isinstance(module, dict):
                        continue
                    if module.get("module_code") == "global_header" and header is None:
                        header = module
                    if module.get("module_code") == "global_footer" and footer is None:
                        footer = module

    return {
        "site_code": normalized_site_code,
        "locale": normalized_locale,
        "status": "ready" if header or footer else "partial",
        "header": header,
        "footer": footer,
    }


def public_get_manifest(
    *,
    site_code: str,
    locale: str = "it",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_locale = _normalize_locale(locale)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            rows = repository.list_published_pages(
                cursor=cursor,
                site_code=normalized_site_code,
                locale=normalized_locale,
            )

    return {
        "site_code": normalized_site_code,
        "locales": [normalized_locale],
        "default_locale": "it",
        "modules": [_serialize_manifest_module(manifest) for manifest in list_module_manifests()],
        "pages": [
            {
                "page_code": row["page_code"],
                "locale": row["locale"],
                "title": row["title"],
                "published_version": row["published_version"],
                "published_at": row["published_at"].isoformat() if row["published_at"] else None,
            }
            for row in rows
        ],
    }


def _require_site(*, cursor, site_code: str) -> dict[str, object]:
    site = repository.load_site(cursor=cursor, site_code=site_code)
    if site is None:
        raise AppError("SITEV3.PAGE.NOT_FOUND", message="Site not found")
    if site["status"] != "active":
        raise AppError("SITEV3.PAGE.NOT_FOUND", message="Site is not active")
    return site


def _normalize_modules(modules: list[dict[str, Any]], *, sanitize_html: bool = True) -> list[dict[str, Any]]:
    if not isinstance(modules, list):
        raise AppError(
            "SITEV3.VALIDATION.REQUIRED",
            details={"field": "modules", "message": "Modules must be a list"},
        )
    normalized: list[dict[str, Any]] = []
    for index, raw_module in enumerate(modules):
        if not isinstance(raw_module, dict):
            raise AppError(
                "SITEV3.VALIDATION.REQUIRED",
                details={"field": f"modules[{index}]", "message": "Module must be an object"},
            )
        module_code = _normalize_code(str(raw_module.get("module_code", "")), "Module code is required", max_length=64, allow_underscore=True)
        slot_key = _normalize_code(str(raw_module.get("slot_key", "main")), "Slot key is required", max_length=64)
        schema_version = _normalize_positive_int(raw_module.get("schema_version", 1), "Schema version must be positive")
        sort_order = _normalize_non_negative_int(raw_module.get("sort_order", index), "Sort order must be greater than or equal to zero")
        config_json = raw_module.get("config_json", raw_module.get("config", {}))
        if not isinstance(config_json, dict):
            raise AppError(
                "SITEV3.VALIDATION.REQUIRED",
                details={"field": "config_json", "message": "Module config must be an object"},
            )
        if sanitize_html and module_code == "rich_text_safe" and isinstance(config_json.get("html"), str):
            try:
                config_json = {
                    **config_json,
                    "html": sanitize_rich_text_html(str(config_json["html"])),
                }
            except UnsafeHtmlError as exc:
                raise AppError(
                    "SITEV3.VALIDATION.UNSAFE_HTML",
                    details={"field": "html", "module_id": str(raw_module.get("id") or raw_module.get("client_id") or index)},
                ) from exc
        normalized.append(
            {
                "id": raw_module.get("id"),
                "client_id": raw_module.get("client_id"),
                "module_code": module_code,
                "schema_version": schema_version,
                "slot_key": slot_key,
                "sort_order": sort_order,
                "config_json": dict(config_json),
            }
        )
    return normalized


def _module_for_validation(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "module_code": row["module_code"],
        "schema_version": row["schema_version"],
        "slot_key": row["slot_key"],
        "sort_order": row["sort_order"],
        "config_json": row["config_json"],
    }


def _build_module_manifest_resolver(*, cursor, site_code: str) -> Callable[[str, int], ModuleManifest | None]:
    custom_cache: dict[tuple[str, int], ModuleManifest | None] = {}

    def _resolve(module_code: str, schema_version: int) -> ModuleManifest | None:
        built_in = get_module_manifest(module_code)
        if built_in is not None:
            return built_in
        if not module_code.startswith("custom_"):
            return None
        cache_key = (module_code, schema_version)
        if cache_key not in custom_cache:
            version_row = repository.load_module_definition_version(
                cursor=cursor,
                site_code=site_code,
                module_code=module_code,
                version=schema_version,
            )
            custom_cache[cache_key] = (
                _custom_definition_version_to_manifest(version_row)
                if version_row is not None
                else None
            )
        return custom_cache[cache_key]

    return _resolve


def _build_custom_definition_version_resolver(*, cursor, site_code: str) -> Callable[[str, int], dict[str, object] | None]:
    cache: dict[tuple[str, int], dict[str, object] | None] = {}

    def _resolve(module_code: str, schema_version: int) -> dict[str, object] | None:
        if not module_code.startswith("custom_"):
            return None
        cache_key = (module_code, schema_version)
        if cache_key not in cache:
            row = repository.load_module_definition_version(
                cursor=cursor,
                site_code=site_code,
                module_code=module_code,
                version=schema_version,
            )
            cache[cache_key] = _serialize_custom_definition_version(row) if row is not None else None
        return cache[cache_key]

    return _resolve


def _custom_definition_version_to_manifest(row: dict[str, object] | None) -> ModuleManifest | None:
    if row is None:
        return None
    return ModuleManifest(
        module_code=str(row["module_code"]),
        schema_version=int(row["version"]),
        slot_keys=_slot_keys_for_custom_category(str(row["category"])),
        fields=tuple(_custom_field_to_manifest_field(field) for field in row["field_schema_json"] if isinstance(field, dict)),
        description=str(row["label"]),
    )


def _custom_field_to_manifest_field(field: dict[str, object]) -> ModuleField:
    field_type = str(field.get("type") or "string")
    return ModuleField(
        key=str(field.get("key") or ""),
        field_type=field_type,  # type: ignore[arg-type]
        required=bool(field.get("required", False)),
        max_length=int(field["max_length"]) if field.get("max_length") is not None else None,
        max_items=int(field["max_items"]) if field.get("max_items") is not None else None,
    )


def _slot_keys_for_custom_category(category: str) -> tuple[str, ...]:
    if category == "hero":
        return ("hero", "main")
    if category == "catalog":
        return ("games", "main")
    if category == "promo":
        return ("promo", "main")
    if category == "text_legal":
        return ("content", "footer", "main")
    return ("main",)


def _sanitize_module_html_fields(
    *,
    modules: list[dict[str, Any]],
    module_manifest_resolver: Callable[[str, int], ModuleManifest | None],
) -> list[dict[str, Any]]:
    sanitized_modules: list[dict[str, Any]] = []
    for index, module in enumerate(modules):
        config_json = dict(module["config_json"])
        manifest = module_manifest_resolver(str(module["module_code"]), int(module["schema_version"]))
        if manifest is not None:
            for field in manifest.fields:
                if field.field_type != "html" or not isinstance(config_json.get(field.key), str):
                    continue
                try:
                    config_json[field.key] = sanitize_rich_text_html(str(config_json[field.key]))
                except UnsafeHtmlError as exc:
                    raise AppError(
                        "SITEV3.VALIDATION.UNSAFE_HTML",
                        details={"field": field.key, "module_id": str(module.get("id") or module.get("client_id") or index)},
                    ) from exc
        sanitized_modules.append({**module, "config_json": config_json})
    return sanitized_modules


def build_snapshot_from_modules(
    *,
    page: dict[str, object],
    modules: list[dict[str, object]],
    version_key: str,
    version: int,
    is_preview: bool = False,
    custom_definition_resolver: Callable[[str, int], dict[str, object] | None] | None = None,
) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "site_code": page["site_code"],
        "page_code": page["page_code"],
        "locale": page["locale"],
        "title": page["title"],
        version_key: version,
        "modules": [
            _serialize_public_module(row, custom_definition_resolver=custom_definition_resolver)
            for row in modules
        ],
    }
    if is_preview:
        snapshot["is_preview"] = True
        snapshot["published_at"] = None
    return snapshot


def _record_page_audit(
    *,
    cursor,
    admin_user_id: str,
    action_kind: str,
    page: dict[str, object] | None,
    payload_extra: dict[str, object] | None = None,
    identity: dict[str, str] | None = None,
) -> None:
    if page is not None:
        site_code = str(page["site_code"])
        page_code = str(page["page_code"])
        locale = str(page["locale"])
    elif identity is not None:
        site_code = identity["site_code"]
        page_code = identity["page_code"]
        locale = identity["locale"]
    else:
        raise ValueError("page or identity is required")

    request_id = get_or_create_request_id()
    resource_id = f"{site_code}:{page_code}:{locale}"
    payload: dict[str, object] = {
        "source": "site_v3",
        "actor": {"admin_user_id": admin_user_id},
        "request_id": request_id,
        "support_id": request_id,
        "site_code": site_code,
        "page_code": page_code,
        "locale": locale,
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


def _check_expected_version(*, page: dict[str, object], expected_draft_version: int | None) -> None:
    if expected_draft_version is None:
        return
    current_version = int(page["draft_version"])
    if current_version != expected_draft_version:
        raise AppError(
            "SITEV3.PAGE.DUPLICATE_CODE",
            message="Draft version conflict",
            status_code=409,
            details={
                "field": "expected_draft_version",
                "draft_version": current_version,
            },
        )


def _published_summary(*, page: dict[str, object], versions: list[dict[str, object]]) -> dict[str, object] | None:
    published_version = page.get("published_version")
    if published_version is None:
        return None
    for version in versions:
        if int(version["version"]) == int(published_version) and version["status"] == "published":
            return _serialize_version(version, include_snapshot=False)
    return None


def _serialize_admin_page(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "site_code": row["site_code"],
        "page_code": row["page_code"],
        "locale": row["locale"],
        "title": row["title"],
        "status": row["status"],
        "draft_version": row["draft_version"],
        "published_version": row["published_version"],
        "created_by": str(row["created_by"]),
        "updated_by": str(row["updated_by"]),
        "archived_by": str(row["archived_by"]) if row["archived_by"] is not None else None,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "archived_at": row["archived_at"].isoformat() if row["archived_at"] is not None else None,
    }


def _serialize_module(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "page_id": str(row["page_id"]),
        "module_code": row["module_code"],
        "schema_version": row["schema_version"],
        "slot_key": row["slot_key"],
        "sort_order": row["sort_order"],
        "config_json": row["config_json"],
        "created_by": str(row["created_by"]),
        "updated_by": str(row["updated_by"]),
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _serialize_public_module(
    row: dict[str, object],
    *,
    custom_definition_resolver: Callable[[str, int], dict[str, object] | None] | None = None,
) -> dict[str, object]:
    module_code = str(row["module_code"])
    schema_version = int(row["schema_version"])
    module = {
        "id": str(row["id"]),
        "module_code": module_code,
        "schema_version": schema_version,
        "slot_key": row["slot_key"],
        "sort_order": row["sort_order"],
        "config_json": row["config_json"],
    }
    if custom_definition_resolver is not None and module_code.startswith("custom_"):
        definition_snapshot = custom_definition_resolver(module_code, schema_version)
        if definition_snapshot is not None:
            module["definition_snapshot"] = definition_snapshot
    return module


def _serialize_version(row: dict[str, object], *, include_snapshot: bool) -> dict[str, object]:
    version = {
        "id": str(row["id"]),
        "page_id": str(row["page_id"]),
        "version": row["version"],
        "status": row["status"],
        "validation_json": row["validation_json"],
        "created_by": str(row["created_by"]),
        "published_by": str(row["published_by"]) if row["published_by"] is not None else None,
        "created_at": row["created_at"].isoformat(),
        "published_at": row["published_at"].isoformat() if row["published_at"] is not None else None,
    }
    if include_snapshot:
        version["snapshot_json"] = row["snapshot_json"]
    return version


def _serialize_custom_definition_version(row: dict[str, object]) -> dict[str, object]:
    return {
        "module_code": row["module_code"],
        "label": row["label"],
        "category": row["category"],
        "renderer_template": row["renderer_template"],
        "definition_version": row["version"],
        "definition_version_id": str(row["id"]),
        "schema_version": row["schema_version"],
        "field_schema_json": row["field_schema_json"],
        "default_config_json": row["default_config_json"],
        "published_at": row["published_at"].isoformat() if row["published_at"] is not None else None,
    }


def _serialize_manifest_module(manifest) -> dict[str, object]:
    return {
        "module_code": manifest.module_code,
        "schema_version": manifest.schema_version,
        "slot_keys": list(manifest.slot_keys),
        "description": manifest.description,
    }


def _normalize_code(raw_value: str, message: str, *, max_length: int, allow_underscore: bool = False) -> str:
    if not isinstance(raw_value, str):
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    normalized = raw_value.strip().lower()
    if not normalized or len(normalized) > max_length:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if not allow_underscore:
        allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if not normalized[0].isalnum() or any(character not in allowed_chars for character in normalized):
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    return normalized


def _normalize_locale(raw_value: str) -> str:
    normalized = str(raw_value or "").strip().lower()
    if normalized not in ALLOWED_LOCALES:
        raise AppError(
            "SITEV3.VALIDATION.REQUIRED",
            details={"field": "locale", "message": "Locale is not supported"},
        )
    return normalized


def _normalize_title(raw_value: str) -> str:
    if not isinstance(raw_value, str):
        raise AppError("SITEV3.VALIDATION.REQUIRED", details={"field": "title"})
    normalized = raw_value.strip()
    if not normalized or len(normalized) > 160:
        raise AppError("SITEV3.VALIDATION.REQUIRED", details={"field": "title"})
    return normalized


def _normalize_status_filter(raw_value: str) -> str:
    normalized = str(raw_value or "all").strip().lower()
    if normalized not in ALLOWED_PAGE_STATUSES:
        raise AppError("SITEV3.VALIDATION.REQUIRED", details={"field": "status"})
    return normalized


def _normalize_positive_int(raw_value: object, message: str) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message) from exc
    if parsed < 1:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    return parsed


def _normalize_non_negative_int(raw_value: object, message: str) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message) from exc
    if parsed < 0:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message)
    return parsed


def _normalize_optional_non_negative_int(raw_value: int | None) -> int | None:
    if raw_value is None:
        return None
    return _normalize_non_negative_int(raw_value, "Expected draft version must be non-negative")


def _normalize_uuid(raw_value: str | None, message: str) -> str:
    try:
        return str(UUID(str(raw_value)))
    except (TypeError, ValueError) as exc:
        raise AppError("SITEV3.VALIDATION.REQUIRED", message=message) from exc
