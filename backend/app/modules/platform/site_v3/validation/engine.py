from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import re
from typing import Any

from app.modules.platform.site_v3.manifests.modules import (
    ModuleField,
    ModuleManifest,
    get_module_manifest,
)


BLOCKING_SEVERITIES = frozenset({"error"})
SUPPORTED_LOCALES = frozenset({"it", "en", "de", "es"})
PAGE_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SLOT_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

ALLOWED_HTML_TAGS = frozenset(
    {
        "a",
        "b",
        "br",
        "em",
        "h2",
        "h3",
        "li",
        "ol",
        "p",
        "span",
        "strong",
        "ul",
    }
)
ALLOWED_HTML_ATTRS = {
    "a": frozenset({"href", "target", "rel"}),
    "span": frozenset({"class"}),
}
ALLOWED_URL_SCHEMES = ("https://", "http://", "/", "#", "mailto:")
ALLOWED_ASSET_URL_PREFIXES = ("https://", "http://", "/static/", "/uploads/")


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    module_id: str | None
    field: str
    code: str
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "module_id": self.module_id,
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


def validate_page_payload(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    title: str,
    modules: list[dict[str, Any]],
    title_exists: Callable[[str], bool],
    module_manifest_resolver: Callable[[str, int], ModuleManifest | None] | None = None,
) -> dict[str, object]:
    issues: list[ValidationIssue] = []
    normalized_site_code = str(site_code or "").strip()
    normalized_page_code = str(page_code or "").strip().lower()
    normalized_locale = str(locale or "").strip().lower()
    normalized_title = str(title or "").strip()

    if not normalized_site_code:
        issues.append(_issue(None, "site_code", "SITEV3.VALIDATION.REQUIRED", "Site code is required"))
    if not PAGE_CODE_PATTERN.fullmatch(normalized_page_code):
        issues.append(_issue(None, "page_code", "SITEV3.VALIDATION.REQUIRED", "Page code is required"))
    if normalized_locale not in SUPPORTED_LOCALES:
        issues.append(_issue(None, "locale", "SITEV3.VALIDATION.REQUIRED", "Locale is not supported"))
    if not normalized_title:
        issues.append(_issue(None, "title", "SITEV3.VALIDATION.REQUIRED", "Title is required"))
    elif len(normalized_title) > 160:
        issues.append(_issue(None, "title", "SITEV3.VALIDATION.REQUIRED", "Title is too long"))

    if not isinstance(modules, list):
        modules = []
        issues.append(_issue(None, "modules", "SITEV3.VALIDATION.REQUIRED", "Modules must be a list"))

    seen_positions: set[tuple[str, int]] = set()
    for index, raw_module in enumerate(modules):
        if not isinstance(raw_module, dict):
            issues.append(_issue(None, f"modules[{index}]", "SITEV3.VALIDATION.REQUIRED", "Module must be an object"))
            continue
        issues.extend(
            _validate_module(
                raw_module=raw_module,
                index=index,
                page_code=normalized_page_code,
                title_exists=title_exists,
                module_manifest_resolver=module_manifest_resolver,
                seen_positions=seen_positions,
            )
        )

    rendered_issues = [issue.to_dict() for issue in issues]
    return {
        "status": "invalid" if validation_has_blockers({"issues": rendered_issues}) else "valid",
        "issues": rendered_issues,
    }


def validation_has_blockers(validation_json: dict[str, object]) -> bool:
    raw_issues = validation_json.get("issues")
    if not isinstance(raw_issues, list):
        return True
    return any(
        isinstance(issue, dict) and issue.get("severity") in BLOCKING_SEVERITIES
        for issue in raw_issues
    )


def sanitize_rich_text_html(raw_html: str) -> str:
    parser = _SanitizingHtmlParser()
    parser.feed(raw_html)
    parser.close()
    if parser.unsafe:
        raise UnsafeHtmlError
    return "".join(parser.output)


class UnsafeHtmlError(Exception):
    pass


def _validate_module(
    *,
    raw_module: dict[str, Any],
    index: int,
    page_code: str,
    title_exists: Callable[[str], bool],
    module_manifest_resolver: Callable[[str, int], ModuleManifest | None] | None,
    seen_positions: set[tuple[str, int]],
) -> list[ValidationIssue]:
    module_id = _module_identifier(raw_module, index=index)
    module_code = str(raw_module.get("module_code") or "").strip().lower()
    schema_version = _parse_positive_int(raw_module.get("schema_version", 1))
    slot_key = str(raw_module.get("slot_key") or "main").strip().lower()
    sort_order = _parse_non_negative_int(raw_module.get("sort_order", index))
    config = raw_module.get("config_json", raw_module.get("config", {}))
    issues: list[ValidationIssue] = []

    manifest = (
        module_manifest_resolver(module_code, schema_version or 1)
        if module_manifest_resolver is not None
        else get_module_manifest(module_code)
    )
    if manifest is None:
        return [
            _issue(
                module_id,
                "module_code",
                "SITEV3.VALIDATION.UNKNOWN_MODULE",
                f"Unknown module: {module_code or '<empty>'}",
            )
        ]
    if module_code == "system_registration_form" and page_code != "register":
        issues.append(
            _issue(
                module_id,
                "module_code",
                "SITEV3.VALIDATION.SYSTEM_MODULE_PAGE",
                "Registration system module can only be mounted on the register system page",
            )
        )
    if schema_version != manifest.schema_version:
        issues.append(_issue(module_id, "schema_version", "SITEV3.VALIDATION.REQUIRED", "Schema version is invalid"))
    if slot_key not in manifest.slot_keys or not SLOT_KEY_PATTERN.fullmatch(slot_key):
        issues.append(_issue(module_id, "slot_key", "SITEV3.VALIDATION.REQUIRED", "Slot key is invalid"))
    if sort_order is None:
        issues.append(_issue(module_id, "sort_order", "SITEV3.VALIDATION.REQUIRED", "Sort order is invalid"))
    else:
        position_key = (slot_key, sort_order)
        if position_key in seen_positions:
            issues.append(_issue(module_id, "sort_order", "SITEV3.VALIDATION.REQUIRED", "Sort order is duplicated"))
        seen_positions.add(position_key)

    if not isinstance(config, dict):
        config = {}
        issues.append(_issue(module_id, "config_json", "SITEV3.VALIDATION.REQUIRED", "Module config must be an object"))

    for field in manifest.fields:
        issues.extend(_validate_field(module_id=module_id, field=field, config=config, title_exists=title_exists))
    return issues


def _validate_field(
    *,
    module_id: str | None,
    field: ModuleField,
    config: dict[str, Any],
    title_exists: Callable[[str], bool],
) -> list[ValidationIssue]:
    value = config.get(field.key)
    issues: list[ValidationIssue] = []
    if field.required and _is_empty(value):
        return [_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} is required")]
    if _is_empty(value):
        return []

    if field.field_type == "string":
        if not isinstance(value, str):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be text"))
        elif field.max_length is not None and len(value.strip()) > field.max_length:
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} is too long"))
    elif field.field_type == "url":
        if not isinstance(value, str):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be a URL or path"))
        elif field.max_length is not None and len(value.strip()) > field.max_length:
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} is too long"))
        elif not value.strip().startswith(ALLOWED_URL_SCHEMES):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be http(s), /, # or mailto"))
    elif field.field_type == "html":
        if not isinstance(value, str):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be HTML text"))
        elif field.max_length is not None and len(value) > field.max_length:
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} is too long"))
        else:
            try:
                sanitize_rich_text_html(value)
            except UnsafeHtmlError:
                issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.UNSAFE_HTML", "HTML contains unsafe tags or attributes"))
    elif field.field_type == "title_code":
        issues.extend(_validate_title_code(module_id=module_id, field_key=field.key, value=value, title_exists=title_exists))
    elif field.field_type == "title_code_list":
        if not isinstance(value, list) or not value:
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be a non-empty list"))
        else:
            if field.max_items is not None and len(value) > field.max_items:
                issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} has too many entries"))
            for title_code in value:
                issues.extend(_validate_title_code(module_id=module_id, field_key=field.key, value=title_code, title_exists=title_exists))
    elif field.field_type == "nav_items":
        issues.extend(_validate_nav_items(module_id=module_id, field=field, value=value, title_exists=title_exists))
    elif field.field_type == "asset_ref":
        if not isinstance(value, dict):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be an object"))
        elif not value.get("asset_id") and not value.get("public_url"):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} needs asset_id or public_url"))
        else:
            public_url = value.get("public_url")
            if public_url is not None and not _is_allowed_asset_public_url(public_url):
                issues.append(
                    _issue(
                        module_id,
                        field.key,
                        "SITEV3.VALIDATION.INVALID_ASSET_URL",
                        f"{field.key} public_url must be http(s), /static/ or /uploads/",
                    )
                )
    elif field.field_type == "boolean":
        if not isinstance(value, bool):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be true or false"))
    return issues


def _is_allowed_asset_public_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    return bool(normalized) and normalized.startswith(ALLOWED_ASSET_URL_PREFIXES)


def _validate_nav_items(
    *,
    module_id: str | None,
    field: ModuleField,
    value: Any,
    title_exists: Callable[[str], bool],
) -> list[ValidationIssue]:
    if not isinstance(value, list):
        return [_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} must be a list")]
    issues: list[ValidationIssue] = []
    if field.max_items is not None and len(value) > field.max_items:
        issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", f"{field.key} has too many entries"))
    for item in value:
        if not isinstance(item, dict):
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", "Navigation item must be an object"))
            continue
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            issues.append(_issue(module_id, field.key, "SITEV3.VALIDATION.REQUIRED", "Navigation item label is required"))
        title_code = item.get("title_code")
        if title_code:
            issues.extend(_validate_title_code(module_id=module_id, field_key=field.key, value=title_code, title_exists=title_exists))
    return issues


def _validate_title_code(
    *,
    module_id: str | None,
    field_key: str,
    value: Any,
    title_exists: Callable[[str], bool],
) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.strip():
        return [_issue(module_id, field_key, "SITEV3.VALIDATION.REQUIRED", f"{field_key} is required")]
    title_code = value.strip().lower()
    if not title_exists(title_code):
        return [_issue(module_id, field_key, "SITEV3.VALIDATION.UNKNOWN_TITLE", f"Unknown or unavailable title: {title_code}")]
    return []


def _issue(module_id: str | None, field: str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        severity="error",
        module_id=module_id,
        field=field,
        code=code,
        message=message,
    )


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _parse_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_non_negative_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _module_identifier(raw_module: dict[str, Any], *, index: int) -> str:
    module_id = raw_module.get("id") or raw_module.get("client_id")
    if isinstance(module_id, str) and module_id.strip():
        return module_id.strip()
    return f"module:{index}"


class _SanitizingHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.unsafe = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag not in ALLOWED_HTML_TAGS:
            self.unsafe = True
            return

        safe_attrs: list[str] = []
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            value = raw_value or ""
            if name.startswith("on"):
                self.unsafe = True
                return
            if name not in ALLOWED_HTML_ATTRS.get(normalized_tag, frozenset()):
                self.unsafe = True
                return
            if name in {"href"} and not value.lower().startswith(ALLOWED_URL_SCHEMES):
                self.unsafe = True
                return
            safe_attrs.append(f'{name}="{escape(value, quote=True)}"')

        suffix = f" {' '.join(safe_attrs)}" if safe_attrs else ""
        self.output.append(f"<{normalized_tag}{suffix}>")

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag not in ALLOWED_HTML_TAGS:
            self.unsafe = True
            return
        if normalized_tag == "br":
            return
        self.output.append(f"</{normalized_tag}>")

    def handle_data(self, data: str) -> None:
        self.output.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&#{name};")
