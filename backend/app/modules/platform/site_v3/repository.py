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


def list_module_definitions(
    *,
    cursor: Cursor,
    site_code: str,
    status_filter: str = "all",
) -> list[dict[str, object]]:
    conditions = ["d.site_code = %s"]
    params: list[object] = [site_code]
    if status_filter != "all":
        conditions.append("d.status = %s")
        params.append(status_filter)
    where_clause = " AND ".join(conditions)
    cursor.execute(
        f"""
        SELECT
            d.id,
            d.site_code,
            d.module_code,
            d.label,
            d.category,
            d.renderer_template,
            d.draft_schema_version,
            d.draft_field_schema_json,
            d.draft_default_config_json,
            d.status,
            d.published_version,
            d.created_by,
            d.updated_by,
            d.published_by,
            d.archived_by,
            d.created_at,
            d.updated_at,
            d.published_at,
            d.archived_at,
            pv.label AS published_label,
            pv.category AS published_category,
            pv.renderer_template AS published_renderer_template,
            pv.schema_version AS published_schema_version,
            pv.field_schema_json AS published_field_schema_json,
            pv.default_config_json AS published_default_config_json
        FROM site_v3_module_definitions d
        LEFT JOIN LATERAL (
            SELECT
                label,
                category,
                renderer_template,
                schema_version,
                field_schema_json,
                default_config_json
            FROM site_v3_module_definition_versions
            WHERE definition_id = d.id
              AND version = d.published_version
        ) pv ON TRUE
        WHERE {where_clause}
        ORDER BY d.updated_at DESC, d.module_code ASC
        """,
        params,
    )
    return list(cursor.fetchall())


def load_module_definition(
    *,
    cursor: Cursor,
    site_code: str,
    module_code: str,
    for_update: bool = False,
) -> dict[str, object] | None:
    lock_clause = " FOR UPDATE OF d" if for_update else ""
    cursor.execute(
        f"""
        SELECT
            d.id,
            d.site_code,
            d.module_code,
            d.label,
            d.category,
            d.renderer_template,
            d.draft_schema_version,
            d.draft_field_schema_json,
            d.draft_default_config_json,
            d.status,
            d.published_version,
            d.created_by,
            d.updated_by,
            d.published_by,
            d.archived_by,
            d.created_at,
            d.updated_at,
            d.published_at,
            d.archived_at,
            pv.label AS published_label,
            pv.category AS published_category,
            pv.renderer_template AS published_renderer_template,
            pv.schema_version AS published_schema_version,
            pv.field_schema_json AS published_field_schema_json,
            pv.default_config_json AS published_default_config_json
        FROM site_v3_module_definitions d
        LEFT JOIN LATERAL (
            SELECT
                label,
                category,
                renderer_template,
                schema_version,
                field_schema_json,
                default_config_json
            FROM site_v3_module_definition_versions
            WHERE definition_id = d.id
              AND version = d.published_version
        ) pv ON TRUE
        WHERE d.site_code = %s
          AND d.module_code = %s
        {lock_clause}
        """,
        (site_code, module_code),
    )
    return cursor.fetchone()


def create_module_definition(
    *,
    cursor: Cursor,
    site_code: str,
    module_code: str,
    label: str,
    category: str,
    renderer_template: str,
    field_schema_json: list[dict[str, object]],
    default_config_json: dict[str, object],
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        INSERT INTO site_v3_module_definitions (
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            draft_schema_version,
            draft_field_schema_json,
            draft_default_config_json,
            status,
            created_by,
            updated_by
        )
        VALUES (%s, %s, %s, %s, %s, 1, %s::jsonb, %s::jsonb, 'draft', %s, %s)
        RETURNING
            id,
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            draft_schema_version,
            draft_field_schema_json,
            draft_default_config_json,
            status,
            published_version,
            created_by,
            updated_by,
            published_by,
            archived_by,
            created_at,
            updated_at,
            published_at,
            archived_at
        """,
        (
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            Jsonb(field_schema_json),
            Jsonb(default_config_json),
            admin_user_id,
            admin_user_id,
        ),
    )
    return cursor.fetchone()


def update_module_definition_draft(
    *,
    cursor: Cursor,
    definition_id: str,
    label: str,
    category: str,
    renderer_template: str,
    field_schema_json: list[dict[str, object]],
    default_config_json: dict[str, object],
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_module_definitions
        SET
            label = %s,
            category = %s,
            renderer_template = %s,
            draft_schema_version = draft_schema_version + 1,
            draft_field_schema_json = %s::jsonb,
            draft_default_config_json = %s::jsonb,
            status = CASE WHEN status = 'archived' THEN 'draft' ELSE status END,
            updated_by = %s,
            updated_at = NOW(),
            archived_by = NULL,
            archived_at = NULL
        WHERE id = %s
        RETURNING
            id,
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            draft_schema_version,
            draft_field_schema_json,
            draft_default_config_json,
            status,
            published_version,
            created_by,
            updated_by,
            published_by,
            archived_by,
            created_at,
            updated_at,
            published_at,
            archived_at
        """,
        (
            label,
            category,
            renderer_template,
            Jsonb(field_schema_json),
            Jsonb(default_config_json),
            admin_user_id,
            definition_id,
        ),
    )
    return cursor.fetchone()


def create_module_definition_version(
    *,
    cursor: Cursor,
    definition_id: str,
    version: int,
    label: str,
    category: str,
    renderer_template: str,
    schema_version: int,
    field_schema_json: list[dict[str, object]],
    default_config_json: dict[str, object],
    created_by: str,
    published_by: str,
) -> dict[str, object]:
    cursor.execute(
        """
        INSERT INTO site_v3_module_definition_versions (
            definition_id,
            version,
            label,
            category,
            renderer_template,
            schema_version,
            field_schema_json,
            default_config_json,
            created_by,
            published_by
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
        RETURNING
            id,
            definition_id,
            version,
            label,
            category,
            renderer_template,
            schema_version,
            field_schema_json,
            default_config_json,
            created_by,
            published_by,
            created_at,
            published_at
        """,
        (
            definition_id,
            version,
            label,
            category,
            renderer_template,
            schema_version,
            Jsonb(field_schema_json),
            Jsonb(default_config_json),
            created_by,
            published_by,
        ),
    )
    return cursor.fetchone()


def load_module_definition_version(
    *,
    cursor: Cursor,
    site_code: str,
    module_code: str,
    version: int,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            dv.id,
            dv.definition_id,
            d.site_code,
            d.module_code,
            dv.version,
            dv.label,
            dv.category,
            dv.renderer_template,
            dv.schema_version,
            dv.field_schema_json,
            dv.default_config_json,
            dv.created_by,
            dv.published_by,
            dv.created_at,
            dv.published_at
        FROM site_v3_module_definition_versions dv
        JOIN site_v3_module_definitions d ON d.id = dv.definition_id
        WHERE d.site_code = %s
          AND d.module_code = %s
          AND dv.version = %s
        """,
        (site_code, module_code, version),
    )
    return cursor.fetchone()


def mark_module_definition_published(
    *,
    cursor: Cursor,
    definition_id: str,
    version: int,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_module_definitions
        SET
            status = 'published',
            published_version = %s,
            published_by = %s,
            published_at = NOW(),
            updated_by = %s,
            updated_at = NOW(),
            archived_by = NULL,
            archived_at = NULL
        WHERE id = %s
        RETURNING
            id,
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            draft_schema_version,
            draft_field_schema_json,
            draft_default_config_json,
            status,
            published_version,
            created_by,
            updated_by,
            published_by,
            archived_by,
            created_at,
            updated_at,
            published_at,
            archived_at
        """,
        (version, admin_user_id, admin_user_id, definition_id),
    )
    return cursor.fetchone()


def mark_module_definition_archived(
    *,
    cursor: Cursor,
    definition_id: str,
    admin_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        UPDATE site_v3_module_definitions
        SET
            status = 'archived',
            updated_by = %s,
            updated_at = NOW(),
            archived_by = %s,
            archived_at = NOW()
        WHERE id = %s
        RETURNING
            id,
            site_code,
            module_code,
            label,
            category,
            renderer_template,
            draft_schema_version,
            draft_field_schema_json,
            draft_default_config_json,
            status,
            published_version,
            created_by,
            updated_by,
            published_by,
            archived_by,
            created_at,
            updated_at,
            published_at,
            archived_at
        """,
        (admin_user_id, admin_user_id, definition_id),
    )
    return cursor.fetchone()


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
        ORDER BY sort_order ASC, created_at ASC, id ASC
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
