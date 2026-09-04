from __future__ import annotations

from copy import deepcopy
from html import escape
from html.parser import HTMLParser
import json
from urllib.parse import urlparse

from app.db.connection import db_connection
from app.modules.games.boxe.i18n_manifest import (
    ALLOWED_LOCALES,
    BOXE_COPY_MANIFEST,
    BOXE_DEFAULT_COPY,
    BOXE_DEFAULT_RULES_HTML,
    BOXE_RULE_SECTION_KEYS,
    DEFAULT_LOCALE,
)
from app.modules.games.boxe.math import DIFFICULTIES, SUPPORTED_ROWS
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)

GAME_CODE = "boxe"
DEFAULT_TITLE_CODE = "boxe001"
AUDIT_ACTION_TITLE_CONFIG_PUBLISH = "title_config_publish"
AUDIT_RESOURCE_TITLE = "title"
RULE_SECTION_KEYS = BOXE_RULE_SECTION_KEYS


class BoxeAdminConfigValidationError(Exception):
    pass


def get_public_admin_config(*, title_code: str = DEFAULT_TITLE_CODE) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    return _build_published_payload(stored_row=stored_row)


def get_admin_config(*, title_code: str = DEFAULT_TITLE_CODE) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    published = _build_published_payload(stored_row=stored_row)
    draft = _build_draft_payload(stored_row=stored_row, published_payload=published)
    return {
        "game_code": GAME_CODE,
        "title_code": title_code,
        "published": published,
        "draft": draft,
        "has_unpublished_changes": draft != published,
        "draft_updated_by_admin_user_id": (
            str(stored_row["draft_updated_by_admin_user_id"])
            if stored_row and stored_row.get("draft_updated_by_admin_user_id")
            else None
        ),
        "draft_updated_at": (
            stored_row["draft_updated_at"].isoformat()
            if stored_row and stored_row.get("draft_updated_at") is not None
            else None
        ),
        "published_updated_by_admin_user_id": (
            str(stored_row["published_updated_by_admin_user_id"])
            if stored_row and stored_row.get("published_updated_by_admin_user_id")
            else None
        ),
        "published_at": (
            stored_row["published_at"].isoformat()
            if stored_row and stored_row.get("published_at") is not None
            else None
        ),
    }


def update_admin_config_draft(
    *,
    admin_user_id: str,
    title_code: str,
    payload: dict[str, object],
) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    published = _build_published_payload(stored_row=stored_row)
    draft = _normalize_payload(payload)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)
            cursor.execute(
                """
                INSERT INTO boxe_admin_config (
                    title_code,
                    rows_enabled_json,
                    default_rows,
                    difficulty_enabled_json,
                    default_difficulty,
                    draft_payload_json,
                    published_payload_json,
                    draft_updated_by_admin_user_id,
                    draft_updated_at
                )
                VALUES (
                    %s,
                    %s::jsonb,
                    %s,
                    %s::jsonb,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s,
                    NOW()
                )
                ON CONFLICT (title_code)
                DO UPDATE
                SET draft_payload_json = EXCLUDED.draft_payload_json,
                    draft_updated_by_admin_user_id = EXCLUDED.draft_updated_by_admin_user_id,
                    draft_updated_at = NOW(),
                    updated_at = NOW()
                """,
                (
                    title_code,
                    json.dumps(published["rows_enabled"]),
                    published["default_rows"],
                    json.dumps(published["difficulty_enabled"]),
                    published["default_difficulty"],
                    json.dumps(draft),
                    json.dumps(published),
                    admin_user_id,
                ),
            )

    return get_admin_config(title_code=title_code)


def publish_admin_config(*, admin_user_id: str, title_code: str) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    published = _build_published_payload(stored_row=stored_row)
    draft = _build_draft_payload(stored_row=stored_row, published_payload=published)
    normalized_draft = _normalize_payload(draft)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)
            cursor.execute(
                """
                INSERT INTO boxe_admin_config (
                    title_code,
                    rows_enabled_json,
                    default_rows,
                    difficulty_enabled_json,
                    default_difficulty,
                    draft_payload_json,
                    published_payload_json,
                    draft_updated_by_admin_user_id,
                    published_updated_by_admin_user_id,
                    draft_updated_at,
                    published_at
                )
                VALUES (
                    %s,
                    %s::jsonb,
                    %s,
                    %s::jsonb,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s,
                    %s,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (title_code)
                DO UPDATE
                SET rows_enabled_json = EXCLUDED.rows_enabled_json,
                    default_rows = EXCLUDED.default_rows,
                    difficulty_enabled_json = EXCLUDED.difficulty_enabled_json,
                    default_difficulty = EXCLUDED.default_difficulty,
                    draft_payload_json = EXCLUDED.draft_payload_json,
                    published_payload_json = EXCLUDED.published_payload_json,
                    draft_updated_by_admin_user_id = EXCLUDED.draft_updated_by_admin_user_id,
                    published_updated_by_admin_user_id = EXCLUDED.published_updated_by_admin_user_id,
                    draft_updated_at = NOW(),
                    published_at = NOW(),
                    updated_at = NOW()
                """,
                (
                    title_code,
                    json.dumps(normalized_draft["rows_enabled"]),
                    normalized_draft["default_rows"],
                    json.dumps(normalized_draft["difficulty_enabled"]),
                    normalized_draft["default_difficulty"],
                    json.dumps(normalized_draft),
                    json.dumps(normalized_draft),
                    admin_user_id,
                    admin_user_id,
                ),
            )
            audit_payload = _build_publish_audit_payload(
                title_code=title_code,
                before=published,
                after=normalized_draft,
            )
            record_audit_entry(
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_TITLE_CONFIG_PUBLISH,
                resource_kind=AUDIT_RESOURCE_TITLE,
                resource_id=title_code,
                payload=audit_payload,
                request_fingerprint=build_audit_request_fingerprint(
                    action_kind=AUDIT_ACTION_TITLE_CONFIG_PUBLISH,
                    resource_kind=AUDIT_RESOURCE_TITLE,
                    resource_id=title_code,
                    payload=audit_payload,
                ),
                cursor=cursor,
            )

    return get_admin_config(title_code=title_code)


def is_published_configuration_supported(
    *,
    rows: int,
    difficulty: str,
    title_code: str = DEFAULT_TITLE_CODE,
) -> bool:
    config = get_public_admin_config(title_code=title_code)
    return rows in config["rows_enabled"] and difficulty.strip().lower() in config["difficulty_enabled"]


def _load_stored_row(*, title_code: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    title_code,
                    rows_enabled_json,
                    default_rows,
                    difficulty_enabled_json,
                    default_difficulty,
                    draft_payload_json,
                    published_payload_json,
                    draft_updated_by_admin_user_id,
                    published_updated_by_admin_user_id,
                    draft_updated_at,
                    published_at
                FROM boxe_admin_config
                WHERE title_code = %s
                """,
                (title_code,),
            )
            row = cursor.fetchone()
    return dict(row) if row is not None else None


def _build_published_payload(*, stored_row: dict[str, object] | None) -> dict[str, object]:
    if stored_row is None:
        return _default_payload()
    return _normalize_payload(stored_row["published_payload_json"])


def _build_draft_payload(
    *,
    stored_row: dict[str, object] | None,
    published_payload: dict[str, object],
) -> dict[str, object]:
    if stored_row is None:
        return deepcopy(published_payload)
    return _normalize_payload(stored_row["draft_payload_json"])


def _default_payload() -> dict[str, object]:
    copy_by_locale = deepcopy(BOXE_DEFAULT_COPY)
    rules_html = deepcopy(BOXE_DEFAULT_RULES_HTML)
    return {
        "rows_enabled": list(SUPPORTED_ROWS),
        "default_rows": 8,
        "difficulty_enabled": list(DIFFICULTIES),
        "default_difficulty": "easy",
        "default_locale": DEFAULT_LOCALE,
        "copy": copy_by_locale,
        "rules_html": rules_html,
    }


def _normalize_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise BoxeAdminConfigValidationError("payload must be an object")

    rows_enabled = _normalize_rows(payload.get("rows_enabled"))
    default_rows = _normalize_default_rows(payload.get("default_rows"), rows_enabled=rows_enabled)
    difficulty_enabled = _normalize_difficulties(payload.get("difficulty_enabled"))
    default_difficulty = _normalize_default_difficulty(
        payload.get("default_difficulty"),
        difficulty_enabled=difficulty_enabled,
    )
    copy_payload = _normalize_copy(payload.get("copy"))
    rules_html = _normalize_rules_html(payload.get("rules_html"))
    default_locale = _normalize_default_locale(payload.get("default_locale"))

    return {
        "rows_enabled": rows_enabled,
        "default_rows": default_rows,
        "difficulty_enabled": difficulty_enabled,
        "default_difficulty": default_difficulty,
        "default_locale": default_locale,
        "copy": copy_payload,
        "rules_html": rules_html,
    }


def _normalize_rows(raw_rows: object) -> list[int]:
    if not isinstance(raw_rows, list):
        raise BoxeAdminConfigValidationError("rows_enabled must be a list")
    try:
        rows = [int(value) for value in raw_rows]
    except (TypeError, ValueError) as exc:
        raise BoxeAdminConfigValidationError("rows_enabled must contain integers") from exc
    if not rows:
        raise BoxeAdminConfigValidationError("rows_enabled must contain at least one row")
    if len(rows) != len(set(rows)):
        raise BoxeAdminConfigValidationError("rows_enabled must contain unique rows")
    if not set(rows).issubset(set(SUPPORTED_ROWS)):
        raise BoxeAdminConfigValidationError("rows_enabled must be a subset of supported BOXE rows")
    return sorted(rows)


def _normalize_default_rows(raw_default: object, *, rows_enabled: list[int]) -> int:
    try:
        default_rows = int(raw_default)
    except (TypeError, ValueError) as exc:
        raise BoxeAdminConfigValidationError("default_rows must be an integer") from exc
    if default_rows not in rows_enabled:
        raise BoxeAdminConfigValidationError("default_rows must belong to rows_enabled")
    return default_rows


def _normalize_difficulties(raw_difficulties: object) -> list[str]:
    if not isinstance(raw_difficulties, list):
        raise BoxeAdminConfigValidationError("difficulty_enabled must be a list")
    difficulties = [
        str(value).strip().lower()
        for value in raw_difficulties
        if str(value).strip()
    ]
    if not difficulties:
        raise BoxeAdminConfigValidationError("difficulty_enabled must contain at least one difficulty")
    if len(difficulties) != len(set(difficulties)):
        raise BoxeAdminConfigValidationError("difficulty_enabled must contain unique difficulties")
    if not set(difficulties).issubset(set(DIFFICULTIES)):
        raise BoxeAdminConfigValidationError("difficulty_enabled must be a subset of supported BOXE difficulties")
    return [difficulty for difficulty in DIFFICULTIES if difficulty in difficulties]


def _normalize_default_difficulty(
    raw_default: object,
    *,
    difficulty_enabled: list[str],
) -> str:
    default_difficulty = str(raw_default or "").strip().lower()
    if default_difficulty not in difficulty_enabled:
        raise BoxeAdminConfigValidationError("default_difficulty must belong to difficulty_enabled")
    return default_difficulty


def _normalize_default_locale(raw_default: object) -> str:
    default_locale = str(raw_default or DEFAULT_LOCALE).strip().lower()
    if default_locale not in ALLOWED_LOCALES:
        raise BoxeAdminConfigValidationError("default_locale must be a supported BOXE locale")
    return default_locale


def _normalize_copy(raw_copy: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_copy, dict):
        raise BoxeAdminConfigValidationError("copy must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_payload = raw_copy.get(locale)
        if not isinstance(locale_payload, dict):
            raise BoxeAdminConfigValidationError(f"copy.{locale} must be an object")
        normalized[locale] = {}
        for raw_key, raw_value in locale_payload.items():
            if not isinstance(raw_key, str):
                raise BoxeAdminConfigValidationError(f"copy.{locale} keys must be strings")
            if not isinstance(raw_value, str):
                raise BoxeAdminConfigValidationError(f"copy.{locale}.{raw_key} must be a string")
            normalized[locale][raw_key] = raw_value.strip()
        for definition in BOXE_COPY_MANIFEST:
            raw_value = locale_payload.get(definition.key)
            if not isinstance(raw_value, str):
                raise BoxeAdminConfigValidationError(f"copy.{locale}.{definition.key} must be a string")
            value = normalized[locale][definition.key]
            if definition.required and not value:
                raise BoxeAdminConfigValidationError(f"copy.{locale}.{definition.key} is required")
            if len(value) > definition.max_length:
                raise BoxeAdminConfigValidationError(
                    f"copy.{locale}.{definition.key} exceeds {definition.max_length} characters"
                )
            placeholders = _extract_placeholders(value)
            for placeholder in placeholders:
                if placeholder not in definition.placeholders:
                    raise BoxeAdminConfigValidationError(
                        f"copy.{locale}.{definition.key} contains unknown placeholder {placeholder}"
                    )
            for placeholder in definition.placeholders:
                if placeholder not in placeholders:
                    raise BoxeAdminConfigValidationError(
                        f"copy.{locale}.{definition.key} is missing placeholder {placeholder}"
                    )
            normalized[locale][definition.key] = value
    return normalized


def _normalize_rules_html(raw_rules: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_rules, dict):
        raise BoxeAdminConfigValidationError("rules_html must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_rules = raw_rules.get(locale)
        if not isinstance(locale_rules, dict):
            raise BoxeAdminConfigValidationError(f"rules_html.{locale} must be an object")
        normalized[locale] = {}
        for key in RULE_SECTION_KEYS:
            raw_value = locale_rules.get(key)
            if not isinstance(raw_value, str):
                raise BoxeAdminConfigValidationError(f"rules_html.{locale}.{key} must be a string")
            value = _sanitize_html(raw_value)
            if not value:
                raise BoxeAdminConfigValidationError(f"rules_html.{locale}.{key} is required")
            normalized[locale][key] = value
    return normalized


def _sanitize_html(value: str) -> str:
    sanitizer = _SafeHtmlSanitizer()
    sanitizer.feed(value.strip())
    sanitizer.close()
    return sanitizer.get_html().strip()


class _SafeHtmlSanitizer(HTMLParser):
    allowed_tags = {
        "p",
        "br",
        "strong",
        "em",
        "ul",
        "ol",
        "li",
        "code",
        "a",
    }
    self_closing_tags = {"br"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed_tags:
            return
        if tag == "a":
            href = None
            for key, value in attrs:
                if key == "href" and value and _is_safe_href(value):
                    href = value
                    break
            if href:
                self.parts.append(
                    f'<a href="{escape(href, quote=True)}" rel="noopener noreferrer">'
                )
                self.open_tags.append(tag)
            return
        self.parts.append(f"<{tag}>")
        if tag not in self.self_closing_tags:
            self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.allowed_tags or tag in self.self_closing_tags:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.parts.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))

    def get_html(self) -> str:
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")
        return "".join(self.parts)


def _is_safe_href(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto"} and not value.lower().startswith("javascript:")


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


def _ensure_admin_user_exists(*, cursor, admin_user_id: str) -> None:
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'admin'
        """,
        (admin_user_id,),
    )
    if cursor.fetchone() is None:
        raise BoxeAdminConfigValidationError("Admin user not found")


def _build_publish_audit_payload(
    *,
    title_code: str,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        "engine_code": GAME_CODE,
        "title_code": title_code,
        "before": _compact_audit_snapshot(before),
        "after": _compact_audit_snapshot(after),
    }


def _compact_audit_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "rows_enabled": snapshot["rows_enabled"],
        "default_rows": snapshot["default_rows"],
        "difficulty_enabled": snapshot["difficulty_enabled"],
        "default_difficulty": snapshot["default_difficulty"],
        "default_locale": snapshot["default_locale"],
    }
