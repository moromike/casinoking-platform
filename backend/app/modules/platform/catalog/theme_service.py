from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from app.db.connection import db_connection
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
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
THEME_SKIN_KEY = "skin"
DEFAULT_SKIN_CONFIG = {
    "title_render_mode": "text",
    "button_density": "default",
    "button_radius": "rounded",
    "button_style": "raised",
    "button_emphasis": "primary",
    "game_area_background_fit": "cover",
    "game_area_background_position": "center",
    "game_area_overlay": "medium",
    "closed_cell_background_dominance": "balanced",
}
ALLOWED_SKIN_VALUES = {
    "title_render_mode": frozenset({"text", "image"}),
    "button_density": frozenset({"compact", "default", "large"}),
    "button_radius": frozenset({"square", "soft", "rounded"}),
    "button_style": frozenset({"flat", "outlined", "raised"}),
    "button_emphasis": frozenset({"primary", "secondary", "danger", "neutral"}),
    "game_area_background_fit": frozenset({"cover", "contain"}),
    "game_area_background_position": frozenset(
        {"center", "top", "bottom", "left", "right"}
    ),
    "game_area_overlay": frozenset({"none", "light", "medium", "strong"}),
    "closed_cell_background_dominance": frozenset(
        {"subtle", "balanced", "strong", "solid"}
    ),
}
GAME_AREA_OVERLAY_ALPHA = {
    "none": 0.0,
    "light": 0.18,
    "medium": 0.42,
    "strong": 0.62,
}
NORMAL_TEXT_MIN_CONTRAST = 4.5
UI_TEXT_MIN_CONTRAST = 3.0
AUDIT_ACTION_THEME_PUBLISH = "theme_publish"
AUDIT_RESOURCE_TITLE = "title"


class ThemeValidationError(Exception):
    pass


class ThemeNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ValidatedThemePayload:
    tokens: dict[str, str]
    skin: dict[str, str] | None
    storage: dict[str, object]


def resolve_title_theme(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    theme_tokens = DEFAULT_THEME_TOKENS.copy()
    skin: dict[str, str] | None = None
    stored_tokens = _load_published_theme_tokens(title_code=normalized_title_code)
    if stored_tokens is not None:
        validated_payload = validate_theme_payload(stored_tokens)
        theme_tokens.update(validated_payload.tokens)
        skin = validated_payload.skin

    assets = {
        str(asset["asset_kind"]): str(asset["public_url"])
        for asset in list_title_assets(title_code=normalized_title_code)
    }
    payload = {
        "title_code": normalized_title_code,
        "tokens": theme_tokens,
        "assets": assets,
    }
    if skin is not None:
        payload["skin"] = skin
    etag = _build_etag(payload)
    return {**payload, "etag": etag}


def get_admin_title_theme(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = load_generic_row(cursor=cursor, title_code=normalized_title_code)

    published_config = _build_effective_theme_payload(
        row["theme_tokens_json"] if row is not None else None
    )
    if row is not None and row["draft_theme_tokens_json"] is not None:
        draft_config = _build_effective_theme_payload(row["draft_theme_tokens_json"])
    else:
        draft_config = published_config

    return {
        "title_code": normalized_title_code,
        "published": {
            "tokens": published_config.tokens,
            "skin": published_config.skin,
        },
        "draft": {
            "tokens": draft_config.tokens,
            "skin": draft_config.skin,
        },
        "has_unpublished_changes": draft_config.storage != published_config.storage,
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
    validated_payload = validate_theme_payload(tokens)
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
                (json.dumps(validated_payload.storage), admin_user_id, normalized_title_code),
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
            before_config = _build_effective_theme_payload_for_audit(row["theme_tokens_json"])
            validated_payload = validate_theme_payload(draft_tokens)
            after_config = _build_effective_theme_payload(validated_payload.storage)
            _validate_theme_contrast_for_publish(after_config)
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
                    json.dumps(validated_payload.storage),
                    json.dumps(validated_payload.storage),
                    admin_user_id,
                    admin_user_id,
                    normalized_title_code,
                ),
            )

            audit_payload = _build_theme_publish_audit_payload(
                title_code=normalized_title_code,
                before=before_config,
                after=after_config,
            )
            record_audit_entry(
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_THEME_PUBLISH,
                resource_kind=AUDIT_RESOURCE_TITLE,
                resource_id=normalized_title_code,
                payload=audit_payload,
                request_fingerprint=build_audit_request_fingerprint(
                    action_kind=AUDIT_ACTION_THEME_PUBLISH,
                    resource_kind=AUDIT_RESOURCE_TITLE,
                    resource_id=normalized_title_code,
                    payload=audit_payload,
                ),
                cursor=cursor,
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


def validate_theme_payload(tokens: object) -> ValidatedThemePayload:
    if not isinstance(tokens, dict):
        raise ThemeValidationError("Theme tokens must be an object")
    validated: dict[str, str] = {}
    skin: dict[str, str] | None = None
    for raw_key, value in tokens.items():
        if not isinstance(raw_key, str):
            raise ThemeValidationError("Theme token keys must be strings")
        key = raw_key.strip()
        if key == THEME_SKIN_KEY:
            skin = _validate_theme_skin(value)
            continue
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

    storage: dict[str, object] = dict(validated)
    if skin is not None:
        storage[THEME_SKIN_KEY] = skin
    return ValidatedThemePayload(tokens=validated, skin=skin, storage=storage)


def validate_theme_tokens(tokens: dict[str, object]) -> dict[str, str]:
    return validate_theme_payload(tokens).tokens


def _validate_theme_skin(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ThemeValidationError("Theme skin must be an object")

    skin = DEFAULT_SKIN_CONFIG.copy()
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str):
            raise ThemeValidationError("Theme skin keys must be strings")
        key = raw_key.strip()
        allowed_values = ALLOWED_SKIN_VALUES.get(key)
        if allowed_values is None:
            raise ThemeValidationError(f"Unsupported theme skin field: {key}")
        if not isinstance(raw_value, str):
            raise ThemeValidationError(f"Theme skin field {key} must be a string")
        normalized_value = raw_value.strip()
        if normalized_value not in allowed_values:
            raise ThemeValidationError(
                f"Unsupported theme skin value for {key}: {normalized_value}"
            )
        skin[key] = normalized_value
    return skin


def _build_etag(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _build_effective_theme_payload(tokens: object) -> ValidatedThemePayload:
    effective_tokens = DEFAULT_THEME_TOKENS.copy()
    skin: dict[str, str] | None = None
    if tokens is not None:
        if not isinstance(tokens, dict):
            raise ThemeValidationError("Theme tokens must be an object")
        validated_payload = validate_theme_payload(tokens)
        effective_tokens.update(validated_payload.tokens)
        skin = validated_payload.skin
    storage: dict[str, object] = dict(effective_tokens)
    if skin is not None:
        storage[THEME_SKIN_KEY] = skin
    return ValidatedThemePayload(tokens=effective_tokens, skin=skin, storage=storage)


def _build_effective_theme_payload_for_audit(tokens: object) -> ValidatedThemePayload:
    try:
        return _build_effective_theme_payload(tokens)
    except ThemeValidationError:
        return _build_effective_theme_payload(None)


def _build_theme_publish_audit_payload(
    *,
    title_code: str,
    before: ValidatedThemePayload,
    after: ValidatedThemePayload,
) -> dict[str, object]:
    changed_token_keys = [
        token_key
        for token_key in sorted(ALLOWED_THEME_TOKENS)
        if before.tokens[token_key] != after.tokens[token_key]
    ]
    before_skin = before.skin or {}
    after_skin = after.skin or {}
    changed_skin_keys = [
        skin_key
        for skin_key in sorted(ALLOWED_SKIN_VALUES)
        if before_skin.get(skin_key) != after_skin.get(skin_key)
    ]
    return {
        "title_code": title_code,
        "changed_token_keys": changed_token_keys,
        "changed_skin_keys": changed_skin_keys,
        "before": {"tokens": before.tokens, "skin": before.skin},
        "after": {"tokens": after.tokens, "skin": after.skin},
    }


def _validate_theme_contrast_for_publish(config: ValidatedThemePayload) -> None:
    tokens = config.tokens
    foreground = _parse_css_color(tokens["--ck-fg"], token_key="--ck-fg")
    muted = _parse_css_color(tokens["--ck-muted"], token_key="--ck-muted")
    bg = _parse_css_color(tokens["--ck-bg"], token_key="--ck-bg")
    surface = _parse_css_color(tokens["--ck-surface"], token_key="--ck-surface")
    surface_strong = _parse_css_color(
        tokens["--ck-surface-strong"],
        token_key="--ck-surface-strong",
    )
    accent = _parse_css_color(tokens["--ck-accent"], token_key="--ck-accent")

    normal_pairs = [
        ("foreground on background", foreground, bg),
        ("foreground on surface", foreground, surface),
        ("foreground on board surface", foreground, surface_strong),
    ]
    ui_pairs = [
        ("muted text on surface", muted, surface),
        ("muted text on board surface", muted, surface_strong),
        ("primary button label on accent", (8, 17, 8), accent),
    ]

    if config.skin is not None:
        overlay_alpha = GAME_AREA_OVERLAY_ALPHA[config.skin["game_area_overlay"]]
        game_area_background = _blend_colors(
            foreground=(0, 0, 0),
            background=surface_strong,
            alpha=overlay_alpha,
        )
        normal_pairs.append(
            ("foreground on game area overlay", foreground, game_area_background)
        )
        ui_pairs.append(("muted text on game area overlay", muted, game_area_background))

    for label, text_color, background_color in normal_pairs:
        ratio = _contrast_ratio(text_color, background_color)
        if ratio < NORMAL_TEXT_MIN_CONTRAST:
            raise ThemeValidationError(
                f"Theme contrast is too low for {label}: {ratio:.2f}:1"
            )

    for label, text_color, background_color in ui_pairs:
        ratio = _contrast_ratio(text_color, background_color)
        if ratio < UI_TEXT_MIN_CONTRAST:
            raise ThemeValidationError(
                f"Theme UI contrast is too low for {label}: {ratio:.2f}:1"
            )


def _parse_css_color(value: str, *, token_key: str) -> tuple[int, int, int]:
    normalized = value.strip()
    if normalized.startswith("#"):
        return _parse_hex_color(normalized, token_key=token_key)
    rgb_match = re.fullmatch(
        r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*(0|1|0?\.\d+))?\s*\)",
        normalized,
    )
    if rgb_match:
        channels = tuple(int(rgb_match.group(index)) for index in range(1, 4))
        if all(0 <= channel <= 255 for channel in channels):
            return channels
    raise ThemeValidationError(
        f"Theme contrast check requires parseable color token: {token_key}"
    )


def _parse_hex_color(value: str, *, token_key: str) -> tuple[int, int, int]:
    raw = value.removeprefix("#")
    if len(raw) == 3:
        try:
            return tuple(int(character * 2, 16) for character in raw)  # type: ignore[return-value]
        except ValueError as exc:
            raise ThemeValidationError(
                f"Theme contrast check requires parseable color token: {token_key}"
            ) from exc
    if len(raw) == 6:
        try:
            return (
                int(raw[0:2], 16),
                int(raw[2:4], 16),
                int(raw[4:6], 16),
            )
        except ValueError as exc:
            raise ThemeValidationError(
                f"Theme contrast check requires parseable color token: {token_key}"
            ) from exc
    raise ThemeValidationError(
        f"Theme contrast check requires parseable color token: {token_key}"
    )


def _blend_colors(
    *,
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
    alpha: float,
) -> tuple[int, int, int]:
    return tuple(
        round(foreground[index] * alpha + background[index] * (1 - alpha))
        for index in range(3)
    )


def _contrast_ratio(
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: tuple[int, int, int]) -> float:
    channels = []
    for channel in color:
        normalized = channel / 255
        channels.append(
            normalized / 12.92
            if normalized <= 0.03928
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return (0.2126 * channels[0]) + (0.7152 * channels[1]) + (0.0722 * channels[2])
