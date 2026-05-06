from __future__ import annotations

import json
import re

from app.db.connection import db_connection
from app.modules.games.mines.backoffice_config import get_admin_backoffice_config
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
)


MINES_ENGINE_CODE = "mines"
TITLE_CODE_PATTERN = re.compile(r"^[a-z0-9_]{3,64}$")
ALLOWED_STATUSES = frozenset({"active", "inactive"})
ALLOWED_LOBBY_VISIBILITIES = frozenset({"hidden", "visible"})
DEFAULT_BOARD_ASSETS = {
    "safe_icon_data_url": None,
    "mine_icon_data_url": None,
}


class TitleCreationConflictError(Exception):
    pass


def update_site_title_publication(
    *,
    site_code: str,
    title_code: str,
    lobby_visibility: str,
    demo_enabled: bool,
    real_enabled: bool,
    lobby_display_name: str | None,
    lobby_description: str | None,
    featured: bool,
    position: int,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    normalized_lobby_visibility = _normalize_lobby_visibility(lobby_visibility)
    normalized_lobby_display_name = _normalize_optional_display_name(lobby_display_name)
    normalized_lobby_description = _normalize_optional_description(lobby_description)
    normalized_position = _normalize_position(position)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            title = _load_title(cursor=cursor, title_code=normalized_title_code)
            if title is None:
                raise CatalogNotFoundError("Title not found")
            if title["is_master"] is True:
                raise CatalogValidationError("Master titles cannot be published in the player library")

            cursor.execute(
                """
                SELECT site_code
                FROM site_titles
                WHERE site_code = %s
                  AND title_code = %s
                """,
                (normalized_site_code, normalized_title_code),
            )
            if cursor.fetchone() is None:
                raise CatalogNotFoundError("Title is not published on this site")

            cursor.execute(
                """
                UPDATE site_titles
                SET
                    lobby_visibility = %s,
                    demo_enabled = %s,
                    real_enabled = %s,
                    lobby_display_name = %s,
                    lobby_description = %s,
                    featured = %s,
                    position = %s,
                    updated_at = NOW()
                WHERE site_code = %s
                  AND title_code = %s
                """,
                (
                    normalized_lobby_visibility,
                    demo_enabled,
                    real_enabled,
                    normalized_lobby_display_name,
                    normalized_lobby_description,
                    featured,
                    normalized_position,
                    normalized_site_code,
                    normalized_title_code,
                ),
            )

            return _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )


def update_title_profile(
    *,
    title_code: str,
    display_name: str,
    site_code: str = "casinoking",
) -> dict[str, object]:
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_display_name = _normalize_display_name(display_name)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            title = _load_title(cursor=cursor, title_code=normalized_title_code)
            if title is None:
                raise CatalogNotFoundError("Title not found")
            if title["is_master"] is True:
                raise CatalogValidationError("Master titles cannot be renamed")

            cursor.execute(
                """
                SELECT site_code
                FROM site_titles
                WHERE site_code = %s
                  AND title_code = %s
                """,
                (normalized_site_code, normalized_title_code),
            )
            if cursor.fetchone() is None:
                raise CatalogNotFoundError("Title is not published on this site")

            cursor.execute(
                """
                UPDATE game_titles
                SET display_name = %s,
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (normalized_display_name, normalized_title_code),
            )

            return _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )


def duplicate_mines_title(
    *,
    source_title_code: str,
    title_code: str,
    display_name: str,
    site_code: str,
    status: str = "active",
    site_title_status: str = "active",
    admin_user_id: str | None = None,
) -> dict[str, object]:
    normalized_source_title_code = _normalize_code(source_title_code, "Source title code is required")
    normalized_title_code = _normalize_new_title_code(title_code)
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_display_name = _normalize_display_name(display_name)
    normalized_status = _normalize_status(status, "Title status is invalid")
    normalized_site_title_status = _normalize_status(
        site_title_status,
        "Site title status is invalid",
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            source_title = _load_title(cursor=cursor, title_code=normalized_source_title_code)
            if source_title is None:
                raise CatalogNotFoundError("Source title not found")
            if source_title["engine_code"] != MINES_ENGINE_CODE:
                raise CatalogValidationError("Only Mines titles can be duplicated by this endpoint")
            if source_title["is_master"] is not True:
                raise CatalogValidationError("Only a Mines master title can be duplicated")

            target_title = _load_title(cursor=cursor, title_code=normalized_title_code)
            if target_title is not None:
                raise TitleCreationConflictError("Title code already exists")

            cursor.execute(
                """
                SELECT site_code
                FROM sites
                WHERE site_code = %s
                """,
                (normalized_site_code,),
            )
            if cursor.fetchone() is None:
                raise CatalogNotFoundError("Site not found")

            source_generic = _load_generic_config(
                cursor=cursor,
                title_code=normalized_source_title_code,
            )
            source_mines = _load_mines_config(
                cursor=cursor,
                title_code=normalized_source_title_code,
            )
            if source_generic is None or source_mines is None:
                default_snapshot = get_admin_backoffice_config(
                    title_code=normalized_source_title_code,
                )["published"]
                source_generic = source_generic or _default_generic_config(default_snapshot)
                source_mines = source_mines or _default_mines_config(default_snapshot)

            cursor.execute(
                """
                INSERT INTO game_titles (
                    title_code,
                    engine_code,
                    display_name,
                    status,
                    is_master,
                    source_title_code
                )
                VALUES (%s, %s, %s, %s, false, %s)
                """,
                (
                    normalized_title_code,
                    MINES_ENGINE_CODE,
                    normalized_display_name,
                    normalized_status,
                    normalized_source_title_code,
                ),
            )
            cursor.execute(
                """
                INSERT INTO site_titles (site_code, title_code, position, status)
                VALUES (
                    %s,
                    %s,
                    (
                        SELECT COALESCE(MAX(position), 0) + 1
                        FROM site_titles
                        WHERE site_code = %s
                    ),
                    %s
                )
                """,
                (
                    normalized_site_code,
                    normalized_title_code,
                    normalized_site_code,
                    normalized_site_title_status,
                ),
            )

            _insert_generic_config(
                cursor=cursor,
                title_code=normalized_title_code,
                source=source_generic,
                admin_user_id=admin_user_id,
            )
            _insert_mines_config(
                cursor=cursor,
                title_code=normalized_title_code,
                source=source_mines,
            )

            return _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )


def _load_title(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT title_code, engine_code, display_name, status, is_master, source_title_code
        FROM game_titles
        WHERE title_code = %s
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _load_generic_config(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            published_at
        FROM title_configs
        WHERE title_code = %s
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _load_mines_config(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json
        FROM mines_title_configs
        WHERE title_code = %s
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _insert_generic_config(
    *,
    cursor,
    title_code: str,
    source: dict[str, object],
    admin_user_id: str | None,
) -> None:
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_bet_limits_json,
            draft_demo_labels_json,
            draft_theme_tokens_json,
            published_at,
            updated_by_admin_user_id,
            draft_updated_by_admin_user_id,
            draft_updated_at
        )
        VALUES (
            %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            COALESCE(%s, NOW()),
            %s,
            %s,
            NOW()
        )
        """,
        (
            title_code,
            _dump_json(source["rules_sections_json"]),
            _dump_json(source["ui_labels_json"]),
            _dump_json(source["bet_limits_json"]),
            _dump_json(source["demo_labels_json"]),
            _dump_json(source["theme_tokens_json"]),
            _dump_json(source["rules_sections_json"]),
            _dump_json(source["ui_labels_json"]),
            _dump_json(source["bet_limits_json"]),
            _dump_json(source["demo_labels_json"]),
            _dump_json(source["theme_tokens_json"]),
            source.get("published_at"),
            admin_user_id,
            admin_user_id,
        ),
    )


def _insert_mines_config(*, cursor, title_code: str, source: dict[str, object]) -> None:
    cursor.execute(
        """
        INSERT INTO mines_title_configs (
            title_code,
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json,
            published_board_assets_json,
            draft_grid_sizes_json,
            draft_mine_counts_json,
            draft_default_mine_counts_json,
            draft_board_assets_json
        )
        VALUES (
            %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb
        )
        """,
        (
            title_code,
            _dump_json(source["published_grid_sizes_json"]),
            _dump_json(source["published_mine_counts_json"]),
            _dump_json(source["default_mine_counts_json"]),
            _dump_json(DEFAULT_BOARD_ASSETS),
            _dump_json(source["published_grid_sizes_json"]),
            _dump_json(source["published_mine_counts_json"]),
            _dump_json(source["default_mine_counts_json"]),
            _dump_json(DEFAULT_BOARD_ASSETS),
        ),
    )


def _load_site_title_entry(*, cursor, site_code: str, title_code: str) -> dict[str, object]:
    cursor.execute(
        """
        SELECT
            gt.title_code,
            gt.engine_code,
            gt.display_name,
            gt.status,
            gt.is_master,
            gt.source_title_code,
            gt.created_at,
            gt.updated_at,
            ge.display_name AS engine_display_name,
            ge.status AS engine_status,
            st.status AS site_title_status,
            st.lobby_visibility,
            st.demo_enabled,
            st.real_enabled,
            st.lobby_display_name,
            st.lobby_description,
            st.featured,
            st.position
        FROM site_titles st
        JOIN game_titles gt ON gt.title_code = st.title_code
        JOIN game_engines ge ON ge.engine_code = gt.engine_code
        WHERE st.site_code = %s
          AND st.title_code = %s
        """,
        (site_code, title_code),
    )
    row = cursor.fetchone()
    if row is None:
        raise CatalogNotFoundError("Title is not published on this site")
    return {
        "title_code": row["title_code"],
        "engine_code": row["engine_code"],
        "display_name": row["display_name"],
        "status": row["status"],
        "is_master": row["is_master"],
        "source_title_code": row["source_title_code"],
        "site_title_status": row["site_title_status"],
        "publication": {
            "site_title_status": row["site_title_status"],
            "lobby_visibility": row["lobby_visibility"],
            "demo_enabled": row["demo_enabled"],
            "real_enabled": row["real_enabled"],
            "lobby_display_name": row["lobby_display_name"],
            "lobby_description": row["lobby_description"],
            "featured": row["featured"],
            "position": row["position"],
        },
        "engine": {
            "engine_code": row["engine_code"],
            "display_name": row["engine_display_name"],
            "status": row["engine_status"],
        },
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _default_generic_config(default_snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "rules_sections_json": default_snapshot["rules_sections"],
        "ui_labels_json": default_snapshot["ui_labels"],
        "bet_limits_json": None,
        "demo_labels_json": None,
        "theme_tokens_json": None,
        "published_at": None,
    }


def _default_mines_config(default_snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "published_grid_sizes_json": default_snapshot["published_grid_sizes"],
        "published_mine_counts_json": default_snapshot["published_mine_counts"],
        "default_mine_counts_json": default_snapshot["default_mine_counts"],
    }


def _normalize_new_title_code(raw_value: str) -> str:
    normalized = _normalize_code(raw_value, "Title code is required")
    if not TITLE_CODE_PATTERN.fullmatch(normalized):
        raise CatalogValidationError(
            "Title code must be 3-64 characters and use only lowercase letters, numbers and underscores"
        )
    return normalized


def _normalize_code(raw_value: str, message: str) -> str:
    normalized = raw_value.strip().lower()
    if not normalized:
        raise CatalogValidationError(message)
    return normalized


def _normalize_display_name(raw_value: str) -> str:
    normalized = raw_value.strip()
    if not normalized:
        raise CatalogValidationError("Display name is required")
    if len(normalized) > 160:
        raise CatalogValidationError("Display name is too long")
    return normalized


def _normalize_optional_display_name(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    if len(normalized) > 160:
        raise CatalogValidationError("Lobby display name is too long")
    return normalized


def _normalize_optional_description(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    if len(normalized) > 500:
        raise CatalogValidationError("Lobby description is too long")
    return normalized


def _normalize_position(raw_value: int) -> int:
    try:
        normalized = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise CatalogValidationError("Position must be an integer") from exc
    if normalized < 0:
        raise CatalogValidationError("Position must be greater than or equal to zero")
    return normalized


def _normalize_lobby_visibility(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    if normalized not in ALLOWED_LOBBY_VISIBILITIES:
        raise CatalogValidationError("Lobby visibility is invalid")
    return normalized


def _normalize_status(raw_value: str, message: str) -> str:
    normalized = raw_value.strip().lower()
    if normalized not in ALLOWED_STATUSES:
        raise CatalogValidationError(message)
    return normalized


def _dump_json(value: object) -> str | None:
    if value is None:
        return None
    return json.dumps(value)
