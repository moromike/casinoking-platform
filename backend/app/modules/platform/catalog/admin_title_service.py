from __future__ import annotations

import json
import re

from app.db.connection import db_connection
from app.modules.games.mines.backoffice_config import get_admin_backoffice_config
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
)


MINES_ENGINE_CODE = "mines"
TITLE_CODE_PATTERN = re.compile(r"^[a-z0-9_]{3,64}$")
ALLOWED_STATUSES = frozenset({"active", "inactive"})
ALLOWED_LOBBY_VISIBILITIES = frozenset({"hidden", "visible"})
AUDIT_ACTION_LOBBY_PUBLICATION_CHANGE = "lobby_publication_change"
AUDIT_ACTION_TITLE_ARCHIVE = "title_archive"
AUDIT_ACTION_TITLE_RESTORE = "title_restore"
AUDIT_RESOURCE_SITE_TITLE = "site_title"
AUDIT_RESOURCE_GAME_TITLE = "game_title"
DEFAULT_BOARD_ASSETS = {
    "safe_icon_data_url": None,
    "mine_icon_data_url": None,
}


class TitleCreationConflictError(Exception):
    pass


class TitleArchiveBlockedError(Exception):
    pass


def archive_title(
    *,
    admin_user_id: str,
    title_code: str,
    reason: str | None = None,
    site_code: str = "casinoking",
) -> dict[str, object]:
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_reason = _normalize_optional_archive_reason(reason)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            title = _load_title_for_update(cursor=cursor, title_code=normalized_title_code)
            if title is None:
                raise CatalogNotFoundError("Title not found")
            if title["is_master"] is True:
                raise CatalogValidationError("Master titles cannot be archived")
            if title["archived_at"] is not None:
                raise CatalogValidationError("Title is already archived")
            _ensure_title_has_no_active_runtime_refs(cursor=cursor, title_code=normalized_title_code)

            before_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            homepage_cta_neutralized = _neutralize_homepage_cta_targets(
                cursor=cursor,
                admin_user_id=admin_user_id,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            cursor.execute(
                """
                UPDATE game_titles
                SET status = 'inactive',
                    archived_at = NOW(),
                    archived_by_admin_user_id = %s,
                    archive_reason = %s,
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (admin_user_id, normalized_reason, normalized_title_code),
            )
            cursor.execute(
                """
                UPDATE site_titles
                SET status = 'inactive',
                    lobby_visibility = 'hidden',
                    demo_enabled = false,
                    real_enabled = false,
                    updated_at = NOW()
                WHERE site_code = %s
                  AND title_code = %s
                """,
                (normalized_site_code, normalized_title_code),
            )
            after_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            audit_payload = {
                "title_code": normalized_title_code,
                "site_code": normalized_site_code,
                "before": {
                    "status": title["status"],
                    "archived": False,
                    "is_test": title["is_test"],
                    "site_publication": before_entry["publication"],
                },
                "after": {
                    "status": after_entry["status"],
                    "archived": True,
                    "archived_at": after_entry["archived_at"],
                    "is_test": after_entry["is_test"],
                    "site_publication": after_entry["publication"],
                },
                "homepage_cta_neutralized": homepage_cta_neutralized,
                "blocked_launch": True,
                "reason": normalized_reason,
            }
            _record_title_audit(
                cursor=cursor,
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_TITLE_ARCHIVE,
                title_code=normalized_title_code,
                payload=audit_payload,
            )
            return after_entry


def restore_title(
    *,
    admin_user_id: str,
    title_code: str,
    site_code: str = "casinoking",
) -> dict[str, object]:
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    normalized_site_code = _normalize_code(site_code, "Site code is required")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            title = _load_title_for_update(cursor=cursor, title_code=normalized_title_code)
            if title is None:
                raise CatalogNotFoundError("Title not found")
            if title["is_master"] is True:
                raise CatalogValidationError("Master titles cannot be restored")
            if title["archived_at"] is None:
                raise CatalogValidationError("Title is not archived")

            before_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            cursor.execute(
                """
                UPDATE game_titles
                SET status = 'inactive',
                    archived_at = NULL,
                    archived_by_admin_user_id = NULL,
                    archive_reason = NULL,
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (normalized_title_code,),
            )
            cursor.execute(
                """
                UPDATE site_titles
                SET status = 'inactive',
                    lobby_visibility = 'hidden',
                    demo_enabled = false,
                    real_enabled = false,
                    updated_at = NOW()
                WHERE site_code = %s
                  AND title_code = %s
                """,
                (normalized_site_code, normalized_title_code),
            )
            after_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            audit_payload = {
                "title_code": normalized_title_code,
                "site_code": normalized_site_code,
                "before": {
                    "status": before_entry["status"],
                    "archived": True,
                    "archived_at": before_entry["archived_at"],
                    "is_test": before_entry["is_test"],
                    "site_publication": before_entry["publication"],
                },
                "after": {
                    "status": after_entry["status"],
                    "archived": False,
                    "archived_at": None,
                    "is_test": after_entry["is_test"],
                    "site_publication": after_entry["publication"],
                },
            }
            _record_title_audit(
                cursor=cursor,
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_TITLE_RESTORE,
                title_code=normalized_title_code,
                payload=audit_payload,
            )
            return after_entry


def update_site_title_publication(
    *,
    admin_user_id: str,
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
            if title["archived_at"] is not None:
                raise CatalogValidationError("Archived titles cannot be published in the player library")
            if title["is_master"] is True:
                raise CatalogValidationError("Master titles cannot be published in the player library")

            before_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            if _publication_requires_live_config(
                lobby_visibility=normalized_lobby_visibility,
                demo_enabled=demo_enabled,
                real_enabled=real_enabled,
            ):
                _validate_title_is_launchable_with_live_config(
                    cursor=cursor,
                    site_code=normalized_site_code,
                    title=title,
                    site_title_entry=before_entry,
                )

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

            after_entry = _load_site_title_entry(
                cursor=cursor,
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            audit_payload = _build_lobby_publication_audit_payload(
                site_code=normalized_site_code,
                title_code=normalized_title_code,
                before=before_entry["publication"],
                after=after_entry["publication"],
            )
            resource_id = _build_site_title_resource_id(
                site_code=normalized_site_code,
                title_code=normalized_title_code,
            )
            record_audit_entry(
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_LOBBY_PUBLICATION_CHANGE,
                resource_kind=AUDIT_RESOURCE_SITE_TITLE,
                resource_id=resource_id,
                payload=audit_payload,
                request_fingerprint=build_audit_request_fingerprint(
                    action_kind=AUDIT_ACTION_LOBBY_PUBLICATION_CHANGE,
                    resource_kind=AUDIT_RESOURCE_SITE_TITLE,
                    resource_id=resource_id,
                    payload=audit_payload,
                ),
                cursor=cursor,
            )

            return after_entry


def update_title_profile(
    *,
    title_code: str,
    display_name: str,
    is_test: bool | None = None,
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
            if title["archived_at"] is not None:
                raise CatalogValidationError("Archived titles cannot be updated")
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
                    is_test = COALESCE(%s, is_test),
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (normalized_display_name, is_test, normalized_title_code),
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
    is_test: bool = False,
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
            if source_title["archived_at"] is not None:
                raise CatalogValidationError("Archived master titles cannot be duplicated")
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
                    is_test,
                    source_title_code
                )
                VALUES (%s, %s, %s, %s, false, %s, %s)
                """,
                (
                    normalized_title_code,
                    MINES_ENGINE_CODE,
                    normalized_display_name,
                    normalized_status,
                    bool(is_test),
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
        SELECT
            title_code,
            engine_code,
            display_name,
            status,
            archived_at,
            archived_by_admin_user_id,
            archive_reason,
            is_test,
            is_master,
            source_title_code
        FROM game_titles
        WHERE title_code = %s
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _load_title_for_update(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            title_code,
            engine_code,
            display_name,
            status,
            archived_at,
            archived_by_admin_user_id,
            archive_reason,
            is_test,
            is_master,
            source_title_code
        FROM game_titles
        WHERE title_code = %s
        FOR UPDATE
        """,
        (title_code,),
    )
    return cursor.fetchone()


def _ensure_title_has_no_active_runtime_refs(*, cursor, title_code: str) -> None:
    cursor.execute(
        """
        SELECT 1
        FROM game_access_sessions
        WHERE title_code = %s
          AND status = 'active'
        LIMIT 1
        """,
        (title_code,),
    )
    if cursor.fetchone() is not None:
        raise TitleArchiveBlockedError("Title has active access sessions")

    cursor.execute(
        """
        SELECT 1
        FROM game_table_sessions
        WHERE title_code = %s
          AND status = 'active'
        LIMIT 1
        """,
        (title_code,),
    )
    if cursor.fetchone() is not None:
        raise TitleArchiveBlockedError("Title has active table sessions")

    cursor.execute(
        """
        SELECT 1
        FROM platform_rounds
        WHERE title_code = %s
          AND status IN ('created', 'active')
        LIMIT 1
        """,
        (title_code,),
    )
    if cursor.fetchone() is not None:
        raise TitleArchiveBlockedError("Title has open platform rounds")


def _neutralize_homepage_cta_targets(
    *,
    cursor,
    admin_user_id: str,
    site_code: str,
    title_code: str,
) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT
            slot_key,
            cta_target_type,
            cta_target_ref
        FROM site_home_slots
        WHERE site_code = %s
          AND cta_target_ref = %s
          AND cta_target_type <> 'none'
        FOR UPDATE
        """,
        (site_code, title_code),
    )
    rows = cursor.fetchall()
    if not rows:
        return []

    cursor.execute(
        """
        UPDATE site_home_slots
        SET cta_target_type = 'none',
            cta_target_ref = NULL,
            updated_by = %s,
            updated_at = NOW()
        WHERE site_code = %s
          AND cta_target_ref = %s
          AND cta_target_type <> 'none'
        """,
        (admin_user_id, site_code, title_code),
    )
    return [
        {
            "slot_key": row["slot_key"],
            "before": {
                "cta_target_type": row["cta_target_type"],
                "cta_target_ref": row["cta_target_ref"],
            },
            "after": {
                "cta_target_type": "none",
                "cta_target_ref": None,
            },
        }
        for row in rows
    ]


def _record_title_audit(
    *,
    cursor,
    admin_user_id: str,
    action_kind: str,
    title_code: str,
    payload: dict[str, object],
) -> None:
    request_fingerprint = build_audit_request_fingerprint(
        action_kind=action_kind,
        resource_kind=AUDIT_RESOURCE_GAME_TITLE,
        resource_id=title_code,
        payload=payload,
    )
    record_audit_entry(
        admin_user_id=admin_user_id,
        action_kind=action_kind,
        resource_kind=AUDIT_RESOURCE_GAME_TITLE,
        resource_id=title_code,
        payload=payload,
        request_fingerprint=request_fingerprint,
        cursor=cursor,
    )


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


def _publication_requires_live_config(
    *,
    lobby_visibility: str,
    demo_enabled: bool,
    real_enabled: bool,
) -> bool:
    return lobby_visibility == "visible" or demo_enabled is True or real_enabled is True


def _validate_title_is_launchable_with_live_config(
    *,
    cursor,
    site_code: str,
    title: dict[str, object],
    site_title_entry: dict[str, object],
) -> None:
    if _load_site_status(cursor=cursor, site_code=site_code) != "active":
        raise CatalogValidationError("Site is not active")
    if site_title_entry["site_title_status"] != "active":
        raise CatalogValidationError("Title is not active on this site")
    if title["status"] != "active":
        raise CatalogValidationError("Title is not active")
    if title["archived_at"] is not None:
        raise CatalogValidationError("Title is archived")

    engine = site_title_entry["engine"]
    if not isinstance(engine, dict) or engine["status"] != "active":
        raise CatalogValidationError("Engine is not active")

    if title["engine_code"] == MINES_ENGINE_CODE:
        _validate_mines_live_config(
            cursor=cursor,
            title_code=str(title["title_code"]),
        )
        return

    raise CatalogValidationError("Title live config validation is not available for this engine")


def _load_site_status(*, cursor, site_code: str) -> str | None:
    cursor.execute(
        """
        SELECT status
        FROM sites
        WHERE site_code = %s
        """,
        (site_code,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return str(row["status"])


def _validate_mines_live_config(*, cursor, title_code: str) -> None:
    generic_config = _load_generic_config(cursor=cursor, title_code=title_code)
    if generic_config is None or generic_config["published_at"] is None:
        raise CatalogValidationError("Title requires a published live config before lobby publication")

    mines_config = _load_mines_config(cursor=cursor, title_code=title_code)
    if mines_config is None:
        raise CatalogValidationError("Title requires a published live config before lobby publication")

    if not _has_non_empty_list(mines_config["published_grid_sizes_json"]):
        raise CatalogValidationError("Title requires published Mines grid sizes before lobby publication")
    if not _has_non_empty_dict(mines_config["published_mine_counts_json"]):
        raise CatalogValidationError("Title requires published Mines mine counts before lobby publication")
    if not _has_non_empty_dict(mines_config["default_mine_counts_json"]):
        raise CatalogValidationError("Title requires published Mines defaults before lobby publication")


def _has_non_empty_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0


def _has_non_empty_dict(value: object) -> bool:
    return isinstance(value, dict) and len(value) > 0


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
            gt.archived_at,
            gt.archived_by_admin_user_id,
            gt.archive_reason,
            gt.is_test,
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
        "archived_at": row["archived_at"].isoformat() if row["archived_at"] is not None else None,
        "archived_by_admin_user_id": (
            str(row["archived_by_admin_user_id"]) if row["archived_by_admin_user_id"] is not None else None
        ),
        "archive_reason": row["archive_reason"],
        "is_archived": row["archived_at"] is not None,
        "is_test": row["is_test"],
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


def _normalize_optional_archive_reason(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    if len(normalized) > 500:
        raise CatalogValidationError("Archive reason is too long")
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


def _build_site_title_resource_id(*, site_code: str, title_code: str) -> str:
    return f"{site_code}:{title_code}"


def _build_lobby_publication_audit_payload(
    *,
    site_code: str,
    title_code: str,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    tracked_fields = (
        "lobby_visibility",
        "demo_enabled",
        "real_enabled",
        "lobby_display_name",
        "lobby_description",
        "featured",
        "position",
    )
    changed_fields = [
        field_name
        for field_name in tracked_fields
        if before[field_name] != after[field_name]
    ]
    return {
        "site_code": site_code,
        "title_code": title_code,
        "changed_fields": changed_fields,
        "before": {field_name: before[field_name] for field_name in tracked_fields},
        "after": {field_name: after[field_name] for field_name in tracked_fields},
    }
