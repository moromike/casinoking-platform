from __future__ import annotations

from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from app.db.connection import db_connection
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.catalog import title_config_service

GAME_CODE = "hi_lo"
DEFAULT_TITLE_CODE = "hilo001"
DEFAULT_LOCALE = "it"
ALLOWED_LOCALES = ("it", "en", "de", "es")
AUDIT_ACTION_TITLE_CONFIG_PUBLISH = "title_config_publish"
AUDIT_RESOURCE_TITLE = "title"

COPY_DEFINITIONS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("game.title", 80, ()),
    ("how_to_play.title", 80, ()),
    ("how_to_play.intro", 180, ()),
    ("how_to_play.card_1_title", 48, ()),
    ("how_to_play.card_1_text", 180, ()),
    ("how_to_play.card_2_title", 48, ()),
    ("how_to_play.card_2_text", 180, ()),
    ("how_to_play.card_3_title", 48, ()),
    ("how_to_play.card_3_text", 180, ()),
    ("how_to_play.continue", 48, ()),
    ("rules.dialog_aria", 80, ("gameTitle",)),
    ("rules.header_title", 80, ("gameTitle",)),
    ("rules.intro", 180, ()),
    ("rules.close_aria", 80, ()),
    ("rules.rules_tab", 32, ()),
    ("rules.replay_tab", 32, ()),
    ("rules.replay_loading", 80, ()),
    ("rules.replay_unavailable", 120, ()),
    ("rules.bet_predict_collect", 180, ()),
    ("rules.bet_predict_collect_heading", 64, ()),
    ("rules.probability_display", 64, ()),
    ("rules.payout_rules", 64, ()),
    ("rules.fairness_explain", 64, ()),
    ("rules.card_deck_mechanics", 64, ()),
    ("rules.skip_semantics", 64, ()),
    ("rules.edge_rank_behavior", 64, ()),
)
COPY_KEYS = tuple(key for key, _max_length, _placeholders in COPY_DEFINITIONS)
RULE_SECTION_KEYS = (
    "bet_predict_collect",
    "probability_display",
    "payout_rules",
    "fairness_explain",
    "card_deck_mechanics",
    "skip_semantics",
    "edge_rank_behavior",
)


class HiLoAdminConfigValidationError(Exception):
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
            str(stored_row["updated_by_admin_user_id"])
            if stored_row and stored_row.get("updated_by_admin_user_id")
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
            title_config_service.upsert_generic_draft(
                cursor=cursor,
                title_code=title_code,
                admin_user_id=admin_user_id,
                published_rules_sections=_store_rules(published),
                published_ui_labels=_store_copy(published),
                draft_rules_sections=_store_rules(draft),
                draft_ui_labels=_store_copy(draft),
            )

    return get_admin_config(title_code=title_code)


def publish_admin_config(*, admin_user_id: str, title_code: str) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    before = _build_published_payload(stored_row=stored_row)
    draft = _build_draft_payload(stored_row=stored_row, published_payload=before)
    after = _normalize_payload(draft)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)
            title_config_service.upsert_generic_published(
                cursor=cursor,
                title_code=title_code,
                admin_user_id=admin_user_id,
                rules_sections=_store_rules(after),
                ui_labels=_store_copy(after),
            )
            audit_payload = _build_publish_audit_payload(
                title_code=title_code,
                before=before,
                after=after,
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


def _load_stored_row(*, title_code: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return title_config_service.load_generic_row(cursor=cursor, title_code=title_code)


def _build_published_payload(*, stored_row: dict[str, object] | None) -> dict[str, object]:
    if stored_row is None:
        return _empty_payload()
    return _hydrate_payload(
        rules_store=_as_dict(stored_row.get("rules_sections_json")),
        copy_store=_as_dict(stored_row.get("ui_labels_json")),
    )


def _build_draft_payload(
    *,
    stored_row: dict[str, object] | None,
    published_payload: dict[str, object],
) -> dict[str, object]:
    if stored_row is None:
        return deepcopy(published_payload)
    draft_rules = _as_dict(stored_row.get("draft_rules_sections_json"))
    draft_copy = _as_dict(stored_row.get("draft_ui_labels_json"))
    if not draft_rules and not draft_copy:
        return deepcopy(published_payload)
    return _hydrate_payload(rules_store=draft_rules, copy_store=draft_copy)


def _empty_payload() -> dict[str, object]:
    return {
        "default_locale": DEFAULT_LOCALE,
        "copy": {locale: {} for locale in ALLOWED_LOCALES},
        "rules_html": {locale: {} for locale in ALLOWED_LOCALES},
    }


def _hydrate_payload(
    *,
    rules_store: dict[str, object],
    copy_store: dict[str, object],
) -> dict[str, object]:
    default_locale = _normalize_default_locale(copy_store.get("default_locale"))
    raw_copy = _as_dict(copy_store.get("copy"))
    raw_rules = _as_dict(rules_store.get("rules_html"))
    copy: dict[str, dict[str, str]] = {}
    rules_html: dict[str, dict[str, str]] = {}

    for locale in ALLOWED_LOCALES:
        locale_copy = _as_dict(raw_copy.get(locale))
        copy[locale] = {
            key: value
            for key in COPY_KEYS
            if isinstance((value := locale_copy.get(key)), str) and value.strip()
        }

        locale_rules = _as_dict(raw_rules.get(locale))
        rules_html[locale] = {
            key: value
            for key in RULE_SECTION_KEYS
            if isinstance((value := locale_rules.get(key)), str) and value.strip()
        }

    return {
        "default_locale": default_locale,
        "copy": copy,
        "rules_html": rules_html,
    }


def _normalize_payload(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise HiLoAdminConfigValidationError("payload must be an object")
    return {
        "default_locale": _normalize_default_locale(payload.get("default_locale")),
        "copy": _normalize_copy(payload.get("copy")),
        "rules_html": _normalize_rules_html(payload.get("rules_html")),
    }


def _normalize_default_locale(raw_default: object) -> str:
    default_locale = str(raw_default or DEFAULT_LOCALE).strip().lower()
    if default_locale not in ALLOWED_LOCALES:
        raise HiLoAdminConfigValidationError("default_locale must be a supported HI-LO locale")
    return default_locale


def _normalize_copy(raw_copy: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_copy, dict):
        raise HiLoAdminConfigValidationError("copy must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_payload = raw_copy.get(locale)
        if not isinstance(locale_payload, dict):
            raise HiLoAdminConfigValidationError(f"copy.{locale} must be an object")
        normalized[locale] = {}
        for key, max_length, required_placeholders in COPY_DEFINITIONS:
            raw_value = locale_payload.get(key)
            if not isinstance(raw_value, str):
                raise HiLoAdminConfigValidationError(f"copy.{locale}.{key} must be a string")
            value = raw_value.strip()
            if not value:
                raise HiLoAdminConfigValidationError(f"copy.{locale}.{key} is required")
            if len(value) > max_length:
                raise HiLoAdminConfigValidationError(
                    f"copy.{locale}.{key} exceeds {max_length} characters"
                )
            placeholders = _extract_placeholders(value)
            for placeholder in placeholders:
                if placeholder not in required_placeholders:
                    raise HiLoAdminConfigValidationError(
                        f"copy.{locale}.{key} contains unknown placeholder {placeholder}"
                    )
            for placeholder in required_placeholders:
                if placeholder not in placeholders:
                    raise HiLoAdminConfigValidationError(
                        f"copy.{locale}.{key} is missing placeholder {placeholder}"
                    )
            normalized[locale][key] = value
    return normalized


def _normalize_rules_html(raw_rules: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_rules, dict):
        raise HiLoAdminConfigValidationError("rules_html must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_rules = raw_rules.get(locale)
        if not isinstance(locale_rules, dict):
            raise HiLoAdminConfigValidationError(f"rules_html.{locale} must be an object")
        normalized[locale] = {}
        for key in RULE_SECTION_KEYS:
            raw_value = locale_rules.get(key)
            if not isinstance(raw_value, str):
                raise HiLoAdminConfigValidationError(f"rules_html.{locale}.{key} must be a string")
            value = _sanitize_html(raw_value)
            if not value:
                raise HiLoAdminConfigValidationError(f"rules_html.{locale}.{key} is required")
            normalized[locale][key] = value
    return normalized


def _store_copy(payload: dict[str, object]) -> dict[str, object]:
    return {
        "default_locale": payload["default_locale"],
        "copy": payload["copy"],
    }


def _store_rules(payload: dict[str, object]) -> dict[str, object]:
    return {"rules_html": payload["rules_html"]}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


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
        raise HiLoAdminConfigValidationError("Admin user not found")


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
    copy = _as_dict(snapshot.get("copy"))
    rules_html = _as_dict(snapshot.get("rules_html"))
    return {
        "default_locale": snapshot.get("default_locale"),
        "copy_locales": sorted(copy.keys()),
        "rules_locales": sorted(rules_html.keys()),
    }
