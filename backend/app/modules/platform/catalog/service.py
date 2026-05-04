from __future__ import annotations

from app.db.connection import db_connection


class CatalogValidationError(Exception):
    pass


class CatalogNotFoundError(Exception):
    pass


def get_title_catalog_entry(*, title_code: str) -> dict[str, object]:
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    gt.title_code,
                    gt.engine_code,
                    gt.display_name,
                    gt.status,
                    gt.created_at,
                    gt.updated_at,
                    ge.display_name AS engine_display_name,
                    ge.status AS engine_status
                FROM game_titles gt
                JOIN game_engines ge ON ge.engine_code = gt.engine_code
                WHERE gt.title_code = %s
                """,
                (normalized_title_code,),
            )
            row = cursor.fetchone()

    if row is None:
        raise CatalogNotFoundError("Title not found")
    return _serialize_title(row)


def list_site_titles(*, site_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    site_code,
                    display_name,
                    status,
                    created_at,
                    updated_at
                FROM sites
                WHERE site_code = %s
                """,
                (normalized_site_code,),
            )
            site_row = cursor.fetchone()
            if site_row is None:
                raise CatalogNotFoundError("Site not found")

            cursor.execute(
                """
                SELECT
                    gt.title_code,
                    gt.engine_code,
                    gt.display_name,
                    gt.status,
                    gt.created_at,
                    gt.updated_at,
                    ge.display_name AS engine_display_name,
                    ge.status AS engine_status,
                    st.status AS site_title_status
                FROM site_titles st
                JOIN game_titles gt ON gt.title_code = st.title_code
                JOIN game_engines ge ON ge.engine_code = gt.engine_code
                WHERE st.site_code = %s
                ORDER BY gt.display_name, gt.title_code
                """,
                (normalized_site_code,),
            )
            title_rows = list(cursor.fetchall())

    return {
        "site": _serialize_site(site_row),
        "titles": [
            {
                **_serialize_title(row),
                "site_title_status": row["site_title_status"],
            }
            for row in title_rows
        ],
    }


def get_published_title_for_launch(*, site_code: str, title_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_title_code = _normalize_code(title_code, "Title code is required")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    gt.title_code,
                    gt.engine_code,
                    gt.display_name,
                    gt.status,
                    gt.created_at,
                    gt.updated_at,
                    ge.display_name AS engine_display_name,
                    ge.status AS engine_status,
                    s.status AS site_status,
                    st.status AS site_title_status
                FROM site_titles st
                JOIN sites s ON s.site_code = st.site_code
                JOIN game_titles gt ON gt.title_code = st.title_code
                JOIN game_engines ge ON ge.engine_code = gt.engine_code
                WHERE st.site_code = %s
                  AND st.title_code = %s
                """,
                (normalized_site_code, normalized_title_code),
            )
            row = cursor.fetchone()

    if row is None:
        raise CatalogNotFoundError("Title is not published on this site")
    if row["site_status"] != "active":
        raise CatalogValidationError("Site is not active")
    if row["site_title_status"] != "active":
        raise CatalogValidationError("Title is not active on this site")
    if row["status"] != "active":
        raise CatalogValidationError("Title is not active")
    if row["engine_status"] != "active":
        raise CatalogValidationError("Engine is not active")
    return _serialize_title(row)


def _serialize_title(row: dict[str, object]) -> dict[str, object]:
    return {
        "title_code": row["title_code"],
        "engine_code": row["engine_code"],
        "display_name": row["display_name"],
        "status": row["status"],
        "engine": {
            "engine_code": row["engine_code"],
            "display_name": row["engine_display_name"],
            "status": row["engine_status"],
        },
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _serialize_site(row: dict[str, object]) -> dict[str, object]:
    return {
        "site_code": row["site_code"],
        "display_name": row["display_name"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _normalize_code(raw_value: str, message: str) -> str:
    normalized = raw_value.strip().lower()
    if not normalized:
        raise CatalogValidationError(message)
    return normalized
