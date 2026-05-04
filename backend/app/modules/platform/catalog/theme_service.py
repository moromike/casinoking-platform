from __future__ import annotations

import hashlib
import json

from app.db.connection import db_connection
from app.modules.platform.catalog.title_config_service import load_generic_row
from app.modules.platform.asset_registry.service import list_title_assets
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_title_catalog_entry,
)


DEFAULT_THEME_TOKENS = {
    "--ck-bg": "#09090f",
    "--ck-surface": "#181924",
    "--ck-surface-strong": "#252752",
    "--ck-fg": "#f0f4f7",
    "--ck-muted": "#d8e2eb",
    "--ck-accent": "#56dc49",
    "--ck-accent-strong": "#8ef59b",
    "--ck-good": "#3de7d1",
    "--ck-danger": "#ff764e",
    "--ck-border": "rgba(96, 224, 124, 0.14)",
    "--ck-radius-panel": "20px",
    "--ck-radius-cell": "16px",
    "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.34)",
    "--ck-font-family": "inherit",
}

ALLOWED_THEME_TOKENS = frozenset(DEFAULT_THEME_TOKENS)
MAX_TOKEN_VALUE_LENGTH = 160


class ThemeValidationError(Exception):
    pass


class ThemeNotFoundError(Exception):
    pass


def resolve_title_theme(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    theme_tokens = DEFAULT_THEME_TOKENS.copy()
    stored_tokens = _load_published_theme_tokens(title_code=normalized_title_code)
    if stored_tokens is not None:
        theme_tokens.update(validate_theme_tokens(stored_tokens))

    assets = {
        str(asset["asset_kind"]): str(asset["public_url"])
        for asset in list_title_assets(title_code=normalized_title_code)
    }
    payload = {
        "title_code": normalized_title_code,
        "tokens": theme_tokens,
        "assets": assets,
    }
    etag = _build_etag(payload)
    return {**payload, "etag": etag}


def get_admin_title_theme(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = load_generic_row(cursor=cursor, title_code=normalized_title_code)

    published_tokens = DEFAULT_THEME_TOKENS.copy()
    draft_tokens = DEFAULT_THEME_TOKENS.copy()
    if row is not None and row["theme_tokens_json"] is not None:
        published_tokens.update(validate_theme_tokens(row["theme_tokens_json"]))
    if row is not None and row["draft_theme_tokens_json"] is not None:
        draft_tokens.update(validate_theme_tokens(row["draft_theme_tokens_json"]))
    else:
        draft_tokens = dict(published_tokens)

    return {
        "title_code": normalized_title_code,
        "published": {"tokens": published_tokens},
        "draft": {"tokens": draft_tokens},
        "has_unpublished_changes": draft_tokens != published_tokens,
        "published_updated_by_admin_user_id": (
            str(row["updated_by_admin_user_id"])
            if row is not None and row["updated_by_admin_user_id"] is not None
            else None
        ),
        "draft_updated_by_admin_user_id": (
            str(row["draft_updated_by_admin_user_id"])
            if row is not None and row["draft_updated_by_admin_user_id"] is not None
            else None
        ),
        "draft_updated_at": (
            row["draft_updated_at"].isoformat()
            if row is not None and row["draft_updated_at"] is not None
            else None
        ),
        "published_at": (
            row["published_at"].isoformat()
            if row is not None and row["published_at"] is not None
            else None
        ),
    }


def update_admin_title_theme_draft(
    *,
    title_code: str,
    tokens: dict[str, object],
    admin_user_id: str,
) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    validated_tokens = validate_theme_tokens(tokens)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE title_configs
                SET
                    draft_theme_tokens_json = %s::jsonb,
                    draft_updated_by_admin_user_id = %s,
                    draft_updated_at = NOW(),
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (json.dumps(validated_tokens), admin_user_id, normalized_title_code),
            )
            if cursor.rowcount != 1:
                raise ThemeNotFoundError("Title config not found")
    return get_admin_title_theme(title_code=normalized_title_code)


def publish_admin_title_theme(
    *,
    title_code: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = load_generic_row(cursor=cursor, title_code=normalized_title_code)
            if row is None:
                raise ThemeNotFoundError("Title config not found")
            draft_tokens = row["draft_theme_tokens_json"]
            if draft_tokens is None:
                draft_tokens = row["theme_tokens_json"] or DEFAULT_THEME_TOKENS
            validated_tokens = validate_theme_tokens(draft_tokens)
            cursor.execute(
                """
                UPDATE title_configs
                SET
                    theme_tokens_json = %s::jsonb,
                    draft_theme_tokens_json = %s::jsonb,
                    updated_by_admin_user_id = %s,
                    draft_updated_by_admin_user_id = %s,
                    published_at = NOW(),
                    draft_updated_at = NOW(),
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (
                    json.dumps(validated_tokens),
                    json.dumps(validated_tokens),
                    admin_user_id,
                    admin_user_id,
                    normalized_title_code,
                ),
            )
    return get_admin_title_theme(title_code=normalized_title_code)


def _resolve_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise ThemeValidationError("Title code is required")
    try:
        get_title_catalog_entry(title_code=normalized_title_code)
    except CatalogNotFoundError as exc:
        raise ThemeNotFoundError("Title not found") from exc
    except CatalogValidationError as exc:
        raise ThemeValidationError(str(exc)) from exc
    return normalized_title_code


def _load_published_theme_tokens(*, title_code: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT theme_tokens_json
                FROM title_configs
                WHERE title_code = %s
                """,
                (title_code,),
            )
            row = cursor.fetchone()
    if row is None:
        return None
    theme_tokens = row["theme_tokens_json"]
    if theme_tokens is None:
        return None
    if not isinstance(theme_tokens, dict):
        raise ThemeValidationError("Theme tokens must be an object")
    return theme_tokens


def validate_theme_tokens(tokens: dict[str, object]) -> dict[str, str]:
    validated: dict[str, str] = {}
    for key, value in tokens.items():
        if key not in ALLOWED_THEME_TOKENS:
            raise ThemeValidationError(f"Unsupported theme token: {key}")
        if not isinstance(value, str):
            raise ThemeValidationError(f"Theme token {key} must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            raise ThemeValidationError(f"Theme token {key} cannot be empty")
        if len(normalized_value) > MAX_TOKEN_VALUE_LENGTH:
            raise ThemeValidationError(f"Theme token {key} is too long")
        if any(character in normalized_value for character in (";", "{", "}")):
            raise ThemeValidationError(f"Theme token {key} contains unsupported characters")
        validated[key] = normalized_value
    return validated


def _build_etag(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
