from __future__ import annotations

import copy
import hashlib
import json

from app.db.connection import db_connection
from app.modules.games.mines.i18n_manifest import (
    ALLOWED_LOCALES,
    DEFAULT_LOCALE,
    MINES_COPY_MANIFEST,
    MINES_DEFAULT_COPY,
    MINES_DEFAULT_RULE_SECTIONS,
    MINES_RULE_SECTION_MANIFEST,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_title_catalog_entry,
)


class TitleLocaleValidationError(Exception):
    pass


class TitleLocaleNotFoundError(Exception):
    pass


def get_admin_title_locale_state(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            published_row = _load_current_published_row_with_cursor(
                cursor=cursor,
                title_code=normalized_title_code,
            )
            draft_row = _load_draft_row_with_cursor(
                cursor=cursor,
                title_code=normalized_title_code,
            )

    published_map = _row_to_locale_map(published_row) if published_row is not None else build_default_locale_map()
    draft_map = (
        _row_to_locale_map(draft_row)
        if draft_row is not None
        else copy.deepcopy(published_map)
    )
    published = _resolve_bundle_from_map(
        title_code=normalized_title_code,
        locale_map=published_map,
        include_editorial_locales=True,
    )
    draft = _resolve_bundle_from_map(
        title_code=normalized_title_code,
        locale_map=draft_map,
        include_editorial_locales=True,
    )
    return {
        "published": published,
        "draft": draft,
        "has_unpublished_changes": draft["resolved_locale"] != published["resolved_locale"]
        or draft["content_hash_sha256"] != published["content_hash_sha256"],
    }


def build_default_locale_map(*, published_locale: str = DEFAULT_LOCALE) -> dict[str, object]:
    normalized_locale = _normalize_supported_locale(
        locale=published_locale,
        field_name="published_locale",
    )
    locales = {
        locale: {
            "copy": copy.deepcopy(MINES_DEFAULT_COPY[locale]),
            "rules_sections": copy.deepcopy(MINES_DEFAULT_RULE_SECTIONS[locale]),
        }
        for locale in ALLOWED_LOCALES
    }
    completeness = validate_locale_map(
        locales=locales,
        default_locale=normalized_locale,
        fallback_locale=normalized_locale,
    )
    return {
        "version": 1,
        "default_locale": normalized_locale,
        "fallback_locale": normalized_locale,
        "available_locales": list(ALLOWED_LOCALES),
        "locales": locales,
        "completeness": completeness,
        "content_hash_sha256": hash_locale_content(locales),
    }


def resolve_title_locale_bundle(
    *,
    title_code: str,
) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    row = _load_current_published_row(title_code=normalized_title_code)
    if row is None:
        default_map = build_default_locale_map()
        return _resolve_bundle_from_map(
            title_code=normalized_title_code,
            locale_map=default_map,
        )

    return _resolve_bundle_from_map(
        title_code=normalized_title_code,
        locale_map=_row_to_locale_map(row),
    )


def upsert_title_locale_draft(
    *,
    cursor,
    title_code: str,
    admin_user_id: str,
    published_locale_code: str | None,
    copy_payload: dict[str, str] | None = None,
    rules_sections_payload: dict[str, dict[str, str]] | None = None,
    locale_map_payload: dict[str, object] | None = None,
) -> None:
    if published_locale_code is None and locale_map_payload is None:
        return

    normalized_title_code = _resolve_title_code(title_code)
    draft_row = _load_draft_row_with_cursor(cursor=cursor, title_code=normalized_title_code)
    current_row = _load_current_published_row_with_cursor(
        cursor=cursor,
        title_code=normalized_title_code,
    )
    base_map = (
        _row_to_locale_map(draft_row)
        if draft_row is not None
        else _row_to_locale_map(current_row)
        if current_row is not None
        else build_default_locale_map()
    )
    locale_map = _apply_locale_draft_payload(
        base_map=base_map,
        published_locale_code=published_locale_code,
        copy_payload=copy_payload,
        rules_sections_payload=rules_sections_payload,
        locale_map_payload=locale_map_payload,
    )

    if draft_row is not None:
        cursor.execute(
            """
            UPDATE title_locale_maps
            SET default_locale_code = %s,
                fallback_locale_code = %s,
                locales_json = %s::jsonb,
                completeness_json = %s::jsonb,
                content_hash_sha256 = %s,
                created_by_admin_user_id = %s,
                created_at = NOW()
            WHERE id = %s
            """,
            (
                normalized_locale,
                normalized_locale,
                json.dumps(locale_map["locales"]),
                json.dumps(locale_map["completeness"]),
                locale_map["content_hash_sha256"],
                admin_user_id,
                draft_row["id"],
            ),
        )
        return

    version = _next_locale_map_version(cursor=cursor, title_code=normalized_title_code)
    cursor.execute(
        """
        INSERT INTO title_locale_maps (
            title_code,
            version,
            status,
            is_current,
            default_locale_code,
            fallback_locale_code,
            locales_json,
            completeness_json,
            content_hash_sha256,
            created_by_admin_user_id
        )
        VALUES (
            %s,
            %s,
            'draft',
            false,
            %s,
            %s,
            %s::jsonb,
            %s::jsonb,
            %s,
            %s
        )
        """,
        (
            normalized_title_code,
            version,
            locale_map["default_locale"],
            locale_map["fallback_locale"],
            json.dumps(locale_map["locales"]),
            json.dumps(locale_map["completeness"]),
            locale_map["content_hash_sha256"],
            admin_user_id,
        ),
    )


def publish_title_locale_draft(
    *,
    cursor,
    title_code: str,
    admin_user_id: str,
) -> None:
    normalized_title_code = _resolve_title_code(title_code)
    draft_row = _load_draft_row_with_cursor(cursor=cursor, title_code=normalized_title_code)
    current_row = _load_current_published_row_with_cursor(
        cursor=cursor,
        title_code=normalized_title_code,
    )
    if draft_row is None:
        if current_row is not None:
            return
        locale_map = build_default_locale_map()
        version = _next_locale_map_version(cursor=cursor, title_code=normalized_title_code)
        cursor.execute(
            """
            INSERT INTO title_locale_maps (
                title_code,
                version,
                status,
                is_current,
                default_locale_code,
                fallback_locale_code,
                locales_json,
                completeness_json,
                content_hash_sha256,
                created_by_admin_user_id,
                published_by_admin_user_id,
                published_at
            )
            VALUES (
                %s,
                %s,
                'published',
                true,
                %s,
                %s,
                %s::jsonb,
                %s::jsonb,
                %s,
                %s,
                %s,
                NOW()
            )
            """,
            (
                normalized_title_code,
                version,
                DEFAULT_LOCALE,
                DEFAULT_LOCALE,
                json.dumps(locale_map["locales"]),
                json.dumps(locale_map["completeness"]),
                locale_map["content_hash_sha256"],
                admin_user_id,
                admin_user_id,
            ),
        )
        return

    _resolve_bundle_from_map(
        title_code=normalized_title_code,
        locale_map=_row_to_locale_map(draft_row),
    )
    _assert_locale_map_publishable(locale_map=_row_to_locale_map(draft_row))
    cursor.execute(
        """
        UPDATE title_locale_maps
        SET is_current = false,
            status = 'archived'
        WHERE title_code = %s
          AND status = 'published'
          AND is_current = true
        """,
        (normalized_title_code,),
    )
    cursor.execute(
        """
        UPDATE title_locale_maps
        SET status = 'published',
            is_current = true,
            published_by_admin_user_id = %s,
            published_at = NOW()
        WHERE id = %s
        """,
        (admin_user_id, draft_row["id"]),
    )


def validate_locale_map(
    *,
    locales: object,
    default_locale: str,
    fallback_locale: str,
) -> dict[str, object]:
    if default_locale not in ALLOWED_LOCALES:
        raise TitleLocaleValidationError("default_locale is not supported")
    if fallback_locale not in ALLOWED_LOCALES:
        raise TitleLocaleValidationError("fallback_locale is not supported")
    if default_locale != fallback_locale:
        raise TitleLocaleValidationError("Mines supports one published locale per Title")
    if not isinstance(locales, dict):
        raise TitleLocaleValidationError("locales must be an object")
    if default_locale not in locales:
        raise TitleLocaleValidationError("published locale is missing")

    completeness: dict[str, object] = {}
    for locale, payload in locales.items():
        if locale not in ALLOWED_LOCALES:
            raise TitleLocaleValidationError(f"unsupported locale {locale}")
        if not isinstance(payload, dict):
            raise TitleLocaleValidationError(f"{locale} payload must be an object")
        copy_payload = payload.get("copy")
        if not isinstance(copy_payload, dict):
            raise TitleLocaleValidationError(f"{locale}.copy must be an object")
        rules_sections_payload = payload.get("rules_sections")
        if not isinstance(rules_sections_payload, dict):
            raise TitleLocaleValidationError(f"{locale}.rules_sections must be an object")
        copy_report = _validate_copy_payload(locale=locale, copy_payload=copy_payload)
        rules_report = _validate_rules_sections_payload(
            locale=locale,
            rules_sections_payload=rules_sections_payload,
        )
        locale_report = {
            **copy_report,
            "rules_sections": rules_report,
            "complete": bool(copy_report["complete"] and rules_report["complete"]),
        }
        completeness[locale] = locale_report

    return {
        "default_locale": default_locale,
        "fallback_locale": fallback_locale,
        "locales": completeness,
    }


def hash_locale_content(locales: object) -> str:
    serialized = json.dumps(locales, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _validate_copy_payload(*, locale: str, copy_payload: dict[object, object]) -> dict[str, object]:
    allowed_keys = {definition.key for definition in MINES_COPY_MANIFEST}
    missing_keys: list[str] = []
    empty_keys: list[str] = []
    too_long_keys: list[str] = []
    invalid_placeholder_keys: list[str] = []
    extra_keys = sorted(str(key) for key in copy_payload if str(key) not in allowed_keys)

    for definition in MINES_COPY_MANIFEST:
        raw_value = copy_payload.get(definition.key)
        if raw_value is None:
            if definition.required:
                missing_keys.append(definition.key)
            continue
        if not isinstance(raw_value, str):
            raise TitleLocaleValidationError(f"{locale}.{definition.key} must be a string")
        if definition.required and not raw_value.strip():
            empty_keys.append(definition.key)
        if definition.max_length is not None and len(raw_value) > definition.max_length:
            too_long_keys.append(definition.key)
        placeholders = _extract_placeholders(raw_value)
        if any(placeholder not in definition.placeholders for placeholder in placeholders):
            invalid_placeholder_keys.append(definition.key)
        for required_placeholder in definition.placeholders:
            if required_placeholder not in placeholders:
                invalid_placeholder_keys.append(definition.key)
                break

    return {
        "complete": not (
            missing_keys
            or empty_keys
            or too_long_keys
            or invalid_placeholder_keys
            or extra_keys
        ),
        "missing_keys": missing_keys,
        "empty_keys": empty_keys,
        "too_long_keys": too_long_keys,
        "invalid_placeholder_keys": sorted(set(invalid_placeholder_keys)),
        "extra_keys": extra_keys,
    }


def _assert_locale_map_publishable(*, locale_map: dict[str, object]) -> None:
    completeness = locale_map.get("completeness")
    if not isinstance(completeness, dict):
        raise TitleLocaleValidationError("locale completeness report is missing")
    locale_reports = completeness.get("locales")
    if not isinstance(locale_reports, dict):
        raise TitleLocaleValidationError("locale completeness report is invalid")
    resolved_locale = str(locale_map["default_locale"])
    report = locale_reports.get(resolved_locale)
    if not isinstance(report, dict):
        raise TitleLocaleValidationError("published locale completeness report is missing")
    if report.get("complete") is True:
        return

    blocking_fields = (
        "missing_keys",
        "empty_keys",
        "too_long_keys",
        "invalid_placeholder_keys",
        "extra_keys",
    )
    details: list[str] = []
    for field_name in blocking_fields:
        values = report.get(field_name)
        if isinstance(values, list) and values:
            details.append(f"{field_name}: {', '.join(str(value) for value in values[:8])}")
    rules_report = report.get("rules_sections")
    if isinstance(rules_report, dict):
        for field_name in (
            "missing_sections",
            "empty_sections",
            "too_long_sections",
            "invalid_sections",
            "extra_sections",
        ):
            values = rules_report.get(field_name)
            if isinstance(values, list) and values:
                details.append(f"{field_name}: {', '.join(str(value) for value in values[:8])}")
    suffix = "; ".join(details) if details else "coverage incomplete"
    raise TitleLocaleValidationError(f"Published locale is not complete: {suffix}")


def _resolve_bundle_from_map(
    *,
    title_code: str,
    locale_map: dict[str, object],
    include_editorial_locales: bool = False,
) -> dict[str, object]:
    locales = locale_map["locales"]
    if not isinstance(locales, dict):
        raise TitleLocaleValidationError("locales must be an object")
    default_locale = str(locale_map["default_locale"])
    fallback_locale = str(locale_map["fallback_locale"])
    if default_locale != fallback_locale:
        raise TitleLocaleValidationError("Mines supports one published locale per Title")
    if default_locale not in locales:
        raise TitleLocaleValidationError("published locale is missing")
    resolved_locale = default_locale
    locale_payload = locales[resolved_locale]
    if not isinstance(locale_payload, dict):
        raise TitleLocaleValidationError("resolved locale payload must be an object")
    copy_payload = locale_payload.get("copy")
    if not isinstance(copy_payload, dict):
        raise TitleLocaleValidationError("resolved locale copy must be an object")
    rules_sections = _merge_default_rules_sections(
        resolved_locale=resolved_locale,
        rules_sections=locale_payload.get("rules_sections", {}),
    )

    bundle = {
        "title_code": title_code,
        "resolved_locale": resolved_locale,
        "published_locale": resolved_locale,
        "default_locale": default_locale,
        "fallback_locale": fallback_locale,
        "editable_locales": list(ALLOWED_LOCALES),
        "available_locales": [resolved_locale],
        "locale_map_version": locale_map["version"],
        "content_hash_sha256": locale_map["content_hash_sha256"],
        "copy": copy_payload,
        "rules_sections": rules_sections,
    }
    if include_editorial_locales:
        bundle["available_locales"] = sorted(locales.keys())
        bundle["locales"] = copy.deepcopy(locales)
        bundle["completeness"] = copy.deepcopy(locale_map.get("completeness", {}))
    return bundle


def _load_current_published_row(*, title_code: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return _load_current_published_row_with_cursor(
                cursor=cursor,
                title_code=title_code,
            )


def _load_current_published_row_with_cursor(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            id,
            title_code,
            version,
            default_locale_code,
            fallback_locale_code,
            locales_json,
            completeness_json,
            content_hash_sha256
        FROM title_locale_maps
        WHERE title_code = %s
          AND status = 'published'
          AND is_current = true
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _load_draft_row_with_cursor(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            id,
            title_code,
            version,
            default_locale_code,
            fallback_locale_code,
            locales_json,
            completeness_json,
            content_hash_sha256
        FROM title_locale_maps
        WHERE title_code = %s
          AND status = 'draft'
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _next_locale_map_version(*, cursor, title_code: str) -> int:
    cursor.execute(
        """
        SELECT COALESCE(MAX(version), 0) + 1 AS next_version
        FROM title_locale_maps
        WHERE title_code = %s
        """,
        (title_code,),
    )
    row = cursor.fetchone()
    return int(row["next_version"])


def _row_to_locale_map(row: dict[str, object]) -> dict[str, object]:
    locales = row["locales_json"]
    if not isinstance(locales, dict):
        raise TitleLocaleValidationError("locales must be an object")
    return {
        "version": row["version"],
        "default_locale": row["default_locale_code"],
        "fallback_locale": row["fallback_locale_code"],
        "available_locales": sorted(locales.keys()),
        "locales": locales,
        "completeness": row["completeness_json"],
        "content_hash_sha256": row["content_hash_sha256"],
    }


def _bundle_to_locale_map(bundle: dict[str, object]) -> dict[str, object]:
    resolved_locale = str(bundle["resolved_locale"])
    return {
        "version": bundle["locale_map_version"],
        "default_locale": resolved_locale,
        "fallback_locale": resolved_locale,
        "available_locales": [resolved_locale],
        "locales": {
            resolved_locale: {
                "copy": bundle["copy"],
                "rules_sections": bundle.get("rules_sections", {}),
            }
        },
        "completeness": {},
        "content_hash_sha256": bundle["content_hash_sha256"],
    }


def _resolve_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise TitleLocaleValidationError("Title code is required")
    try:
        get_title_catalog_entry(title_code=normalized_title_code)
    except CatalogNotFoundError as exc:
        raise TitleLocaleNotFoundError("Title not found") from exc
    except CatalogValidationError as exc:
        raise TitleLocaleValidationError(str(exc)) from exc
    return normalized_title_code


def _normalize_supported_locale(*, locale: str, field_name: str) -> str:
    normalized = locale.strip().lower()
    if normalized not in ALLOWED_LOCALES:
        raise TitleLocaleValidationError(f"{field_name} is not supported")
    return normalized


def _apply_locale_draft_payload(
    *,
    base_map: dict[str, object],
    published_locale_code: str | None,
    copy_payload: dict[str, str] | None,
    rules_sections_payload: dict[str, dict[str, str]] | None,
    locale_map_payload: dict[str, object] | None,
) -> dict[str, object]:
    locale_map = copy.deepcopy(base_map)
    if locale_map_payload is not None:
        normalized_locale = _normalize_supported_locale(
            locale=str(
                locale_map_payload.get("published_locale")
                or locale_map_payload.get("published_locale_code")
                or locale_map_payload.get("default_locale")
                or locale_map["default_locale"],
            ),
            field_name="locale_map.published_locale",
        )
        raw_locales = locale_map_payload.get("locales")
        if not isinstance(raw_locales, dict):
            raise TitleLocaleValidationError("locale_map.locales must be an object")
        locales = _normalize_locale_payloads(raw_locales)
    else:
        assert published_locale_code is not None
        normalized_locale = _normalize_supported_locale(
            locale=published_locale_code,
            field_name="published_locale_code",
        )
        locales = locale_map["locales"]
        if not isinstance(locales, dict):
            raise TitleLocaleValidationError("locales must be an object")
        locales = _seed_missing_default_locales(copy.deepcopy(locales))
        locale_payload = locales.get(normalized_locale)
        if not isinstance(locale_payload, dict):
            locale_payload = {
                "copy": copy.deepcopy(MINES_DEFAULT_COPY[normalized_locale]),
                "rules_sections": copy.deepcopy(MINES_DEFAULT_RULE_SECTIONS[normalized_locale]),
            }
        if copy_payload is not None:
            locale_payload["copy"] = copy.deepcopy(copy_payload)
        if rules_sections_payload is not None:
            locale_payload["rules_sections"] = copy.deepcopy(rules_sections_payload)
        locales[normalized_locale] = locale_payload

    completeness = validate_locale_map(
        locales=locales,
        default_locale=normalized_locale,
        fallback_locale=normalized_locale,
    )
    return {
        **locale_map,
        "default_locale": normalized_locale,
        "fallback_locale": normalized_locale,
        "available_locales": sorted(locales.keys()),
        "locales": locales,
        "completeness": completeness,
        "content_hash_sha256": hash_locale_content(locales),
    }


def _normalize_locale_payloads(raw_locales: dict[object, object]) -> dict[str, object]:
    locales: dict[str, object] = {}
    for raw_locale, raw_payload in raw_locales.items():
        locale = _normalize_supported_locale(
            locale=str(raw_locale),
            field_name="locale_map.locales",
        )
        if not isinstance(raw_payload, dict):
            raise TitleLocaleValidationError(f"{locale} payload must be an object")
        copy_payload = raw_payload.get("copy")
        rules_sections_payload = raw_payload.get("rules_sections")
        if not isinstance(copy_payload, dict):
            raise TitleLocaleValidationError(f"{locale}.copy must be an object")
        if not isinstance(rules_sections_payload, dict):
            raise TitleLocaleValidationError(f"{locale}.rules_sections must be an object")
        locales[locale] = {
            "copy": copy.deepcopy(copy_payload),
            "rules_sections": copy.deepcopy(rules_sections_payload),
        }
    return _seed_missing_default_locales(locales)


def _seed_missing_default_locales(locales: dict[str, object]) -> dict[str, object]:
    for locale in ALLOWED_LOCALES:
        if locale not in locales:
            locales[locale] = {
                "copy": copy.deepcopy(MINES_DEFAULT_COPY[locale]),
                "rules_sections": copy.deepcopy(MINES_DEFAULT_RULE_SECTIONS[locale]),
            }
    return locales


def flatten_locale_rule_sections(rules_sections: object) -> dict[str, str]:
    if not isinstance(rules_sections, dict):
        return {}
    flattened: dict[str, str] = {}
    for definition in MINES_RULE_SECTION_MANIFEST:
        section_payload = rules_sections.get(definition.key)
        if isinstance(section_payload, dict):
            body_html = section_payload.get("body_html")
            if isinstance(body_html, str):
                flattened[definition.key] = body_html
    return flattened


def _merge_default_rules_sections(
    *,
    resolved_locale: str,
    rules_sections: object,
) -> dict[str, dict[str, str]]:
    defaults = copy.deepcopy(MINES_DEFAULT_RULE_SECTIONS[resolved_locale])
    if not isinstance(rules_sections, dict):
        return defaults
    for definition in MINES_RULE_SECTION_MANIFEST:
        section_payload = rules_sections.get(definition.key)
        if not isinstance(section_payload, dict):
            continue
        body_html = section_payload.get("body_html")
        if isinstance(body_html, str) and body_html.strip():
            defaults[definition.key] = {"body_html": body_html}
    return defaults


def _validate_rules_sections_payload(
    *,
    locale: str,
    rules_sections_payload: dict[object, object],
) -> dict[str, object]:
    allowed_keys = {definition.key for definition in MINES_RULE_SECTION_MANIFEST}
    missing_sections: list[str] = []
    empty_sections: list[str] = []
    too_long_sections: list[str] = []
    invalid_sections: list[str] = []
    extra_sections = sorted(str(key) for key in rules_sections_payload if str(key) not in allowed_keys)

    for definition in MINES_RULE_SECTION_MANIFEST:
        raw_section = rules_sections_payload.get(definition.key)
        if raw_section is None:
            if definition.required:
                missing_sections.append(definition.key)
            continue
        if not isinstance(raw_section, dict):
            invalid_sections.append(definition.key)
            continue
        body_html = raw_section.get("body_html")
        if not isinstance(body_html, str):
            invalid_sections.append(definition.key)
            continue
        if definition.required and not body_html.strip():
            empty_sections.append(definition.key)
        if len(body_html) > definition.body_soft_max_length:
            too_long_sections.append(definition.key)

    return {
        "complete": not (
            missing_sections
            or empty_sections
            or too_long_sections
            or invalid_sections
            or extra_sections
        ),
        "missing_sections": missing_sections,
        "empty_sections": empty_sections,
        "too_long_sections": too_long_sections,
        "invalid_sections": invalid_sections,
        "extra_sections": extra_sections,
    }


def _extract_placeholders(value: str) -> set[str]:
    placeholders: set[str] = set()
    cursor = 0
    while True:
        start = value.find("{{", cursor)
        if start == -1:
            return placeholders
        end = value.find("}}", start + 2)
        if end == -1:
            return placeholders
        placeholders.add(value[start + 2 : end].strip())
        cursor = end + 2
