from __future__ import annotations

from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb


def load_site(*, cursor: Cursor, site_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT site_code, display_name, status, created_at, updated_at
        FROM sites
        WHERE site_code = %s
        """,
        (site_code,),
    )
    return cursor.fetchone()


def title_is_available_for_site(*, cursor: Cursor, site_code: str, title_code: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM site_titles st
        JOIN sites s ON s.site_code = st.site_code
        JOIN game_titles gt ON gt.title_code = st.title_code
        JOIN game_engines ge ON ge.engine_code = gt.engine_code
        WHERE st.site_code = %s
          AND st.title_code = %s
          AND s.status = 'active'
          AND gt.status = 'active'
          AND gt.archived_at IS NULL
          AND gt.is_master = false
          AND ge.status = 'active'
          AND st.status = 'active'
          AND st.lobby_visibility = 'visible'
        """,
        (site_code, title_code),
    )
    return cursor.fetchone() is not None


def list_pages(
    *,
    cursor: Cursor,
    site_code: str,
    locale: str,
    status_filter: str,
    page: int,
    limit: int,
) -> dict[str, object]:
    conditions = ["site_code = %s", "locale = %s"]
    params: list[object] = [site_code, locale]
    if status_filter != "all":
        conditions.append("status = %s")
        params.append(status_filter)

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit
    cursor.execute(
        f"""
        SELECT COUNT(*) AS total_items
        FROM site_v3_pages
        WHERE {where_clause}
        """,
        params,
    )
    total_items = int(cursor.fetchone()["total_items"])
    cursor.execute(
        f"""
        SELECT
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        FROM site_v3_pages
        WHERE {where_clause}
        ORDER BY updated_at DESC, page_code ASC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    )
    rows = list(cursor.fetchall())
    total_pages = 0 if total_items == 0 else (total_items + limit - 1) // limit
    return {
        "pages": rows,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


def load_page(
    *,
    cursor: Cursor,
    site_code: str,
    page_code: str,
    locale: str,
    for_update: bool = False,
) -> dict[str, object] | None:
    lock_clause = " FOR UPDATE" if for_update else ""
    cursor.execute(
        f"""
        SELECT
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        FROM site_v3_pages
        WHERE site_code = %s
          AND page_code = %s
          AND locale = %s
        {lock_clause}
        """,
        (site_code, page_code, locale),
    )
    return cursor.fetchone()


def create_page(
    *,
    cursor: Cursor,
    site_code: str,
    page_code: str,
    locale: str,
    title: str,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        INSERT INTO site_v3_pages (
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            created_by,
            updated_by
        )
        VALUES (%s, %s, %s, %s, 'draft', 0, %s, %s)
        RETURNING
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        """,
        (site_code, page_code, locale, title, admin_user_id, admin_user_id),
    )
    return cursor.fetchone()


def update_page_draft(
    *,
    cursor: Cursor,
    page_id: str,
    title: str,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_pages
        SET
            title = %s,
            status = CASE WHEN status = 'published' THEN 'published' ELSE 'draft' END,
            draft_version = draft_version + 1,
            updated_by = %s,
            updated_at = NOW(),
            archived_by = NULL,
            archived_at = NULL
        WHERE id = %s
        RETURNING
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        """,
        (title, admin_user_id, page_id),
    )
    return cursor.fetchone()


def replace_modules(
    *,
    cursor: Cursor,
    page_id: str,
    modules: list[dict[str, Any]],
    admin_user_id: str,
) -> None:
    cursor.execute("DELETE FROM site_v3_modules WHERE page_id = %s", (page_id,))
    for index, module in enumerate(modules):
        cursor.execute(
            """
            INSERT INTO site_v3_modules (
                page_id,
                module_code,
                schema_version,
                slot_key,
                sort_order,
                config_json,
                created_by,
                updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            """,
            (
                page_id,
                module["module_code"],
                module["schema_version"],
                module["slot_key"],
                module.get("sort_order", index),
                Jsonb(module["config_json"]),
                admin_user_id,
                admin_user_id,
            ),
        )


def list_modules(*, cursor: Cursor, page_id: str) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT
            id,
            page_id,
            module_code,
            schema_version,
            slot_key,
            sort_order,
            config_json,
            created_by,
            updated_by,
            created_at,
            updated_at
        FROM site_v3_modules
        WHERE page_id = %s
        ORDER BY slot_key ASC, sort_order ASC, created_at ASC, id ASC
        """,
        (page_id,),
    )
    return list(cursor.fetchall())


def create_page_version(
    *,
    cursor: Cursor,
    page_id: str,
    version: int,
    status: str,
    snapshot_json: dict[str, object],
    validation_json: dict[str, object],
    created_by: str,
    published_by: str | None = None,
) -> dict[str, object]:
    cursor.execute(
        """
        INSERT INTO site_v3_page_versions (
            page_id,
            version,
            status,
            snapshot_json,
            validation_json,
            created_by,
            published_by,
            published_at
        )
        VALUES (
            %s,
            %s,
            %s,
            %s::jsonb,
            %s::jsonb,
            %s,
            %s,
            CASE WHEN %s = 'published' THEN NOW() ELSE NULL END
        )
        RETURNING
            id,
            page_id,
            version,
            status,
            snapshot_json,
            validation_json,
            created_by,
            published_by,
            created_at,
            published_at
        """,
        (
            page_id,
            version,
            status,
            Jsonb(snapshot_json),
            Jsonb(validation_json),
            created_by,
            published_by,
            status,
        ),
    )
    return cursor.fetchone()


def mark_page_published(
    *,
    cursor: Cursor,
    page_id: str,
    version: int,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_pages
        SET
            status = 'published',
            published_version = %s,
            updated_by = %s,
            updated_at = NOW(),
            archived_by = NULL,
            archived_at = NULL
        WHERE id = %s
        RETURNING
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        """,
        (version, admin_user_id, page_id),
    )
    return cursor.fetchone()


def mark_page_archived(
    *,
    cursor: Cursor,
    page_id: str,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_pages
        SET
            status = 'archived',
            updated_by = %s,
            archived_by = %s,
            updated_at = NOW(),
            archived_at = NOW()
        WHERE id = %s
        RETURNING
            id,
            site_code,
            page_code,
            locale,
            title,
            status,
            draft_version,
            published_version,
            created_by,
            updated_by,
            archived_by,
            created_at,
            updated_at,
            archived_at
        """,
        (admin_user_id, admin_user_id, page_id),
    )
    return cursor.fetchone()


def list_versions(
    *,
    cursor: Cursor,
    page_id: str,
) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT
            id,
            page_id,
            version,
            status,
            snapshot_json,
            validation_json,
            created_by,
            published_by,
            created_at,
            published_at
        FROM site_v3_page_versions
        WHERE page_id = %s
        ORDER BY version DESC
        """,
        (page_id,),
    )
    return list(cursor.fetchall())


def load_published_version(
    *,
    cursor: Cursor,
    page_id: str,
    version: int,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            id,
            page_id,
            version,
            status,
            snapshot_json,
            validation_json,
            created_by,
            published_by,
            created_at,
            published_at
        FROM site_v3_page_versions
        WHERE page_id = %s
          AND version = %s
          AND status = 'published'
        """,
        (page_id, version),
    )
    return cursor.fetchone()


def list_published_pages(
    *,
    cursor: Cursor,
    site_code: str,
    locale: str,
) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT
            p.id,
            p.site_code,
            p.page_code,
            p.locale,
            p.title,
            p.published_version,
            v.id AS version_id,
            v.snapshot_json,
            v.published_at
        FROM site_v3_pages p
        JOIN site_v3_page_versions v
          ON v.page_id = p.id
         AND v.version = p.published_version
         AND v.status = 'published'
        WHERE p.site_code = %s
          AND p.locale = %s
          AND p.status = 'published'
          AND p.published_version IS NOT NULL
        ORDER BY p.page_code ASC
        """,
        (site_code, locale),
    )
    return list(cursor.fetchall())


def row_to_dict(row: DictRow | dict[str, object] | None) -> dict[str, object] | None:
    if row is None:
        return None
    return dict(row)
