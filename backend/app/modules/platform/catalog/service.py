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
                    gt.archived_at,
                    gt.is_test,
                    gt.is_master,
                    gt.source_title_code,
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


def list_site_titles(
    *,
    site_code: str,
    status_filter: str = "all",
    test_filter: str = "all",
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_status_filter = _normalize_status_filter(status_filter)
    normalized_test_filter = _normalize_test_filter(test_filter)
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

            where_clauses = ["st.site_code = %s"]
            params: list[object] = [normalized_site_code]
            if normalized_status_filter == "active":
                where_clauses.extend([
                    "gt.archived_at IS NULL",
                    "gt.status = 'active'",
                    "st.status = 'active'",
                ])
            elif normalized_status_filter == "inactive":
                where_clauses.extend([
                    "gt.archived_at IS NULL",
                    "(gt.status <> 'active' OR st.status <> 'active')",
                ])
            elif normalized_status_filter == "archived":
                where_clauses.append("gt.archived_at IS NOT NULL")
            if normalized_test_filter == "only":
                where_clauses.append("gt.is_test = true")
            elif normalized_test_filter == "exclude":
                where_clauses.append("gt.is_test = false")

            cursor.execute(
                f"""
                SELECT
                    gt.title_code,
                    gt.engine_code,
                    gt.display_name,
                    gt.status,
                    gt.archived_at,
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
                WHERE {" AND ".join(where_clauses)}
                ORDER BY gt.display_name, gt.title_code
                """,
                params,
            )
            title_rows = list(cursor.fetchall())

    return {
        "site": _serialize_site(site_row),
        "titles": [
            {
                **_serialize_title(row),
                "site_title_status": row["site_title_status"],
                "publication": _serialize_site_title_publication(row),
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
                    gt.archived_at,
                    gt.is_test,
                    gt.is_master,
                    gt.source_title_code,
                    gt.created_at,
                    gt.updated_at,
                    ge.display_name AS engine_display_name,
                    ge.status AS engine_status,
                    s.status AS site_status,
                    st.status AS site_title_status,
                    st.lobby_visibility,
                    st.demo_enabled,
                    st.real_enabled,
                    st.lobby_display_name,
                    st.lobby_description,
                    st.featured,
                    st.position
                FROM site_titles st
                JOIN sites s ON s.site_code = st.site_code
                JOIN game_titles gt ON gt.title_code = st.title_code
                JOIN game_engines ge ON ge.engine_code = gt.engine_code
                WHERE st.site_code = %s
                  AND st.title_code = %s
                  AND gt.archived_at IS NULL
                FOR UPDATE OF gt
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
    if row["archived_at"] is not None:
        raise CatalogValidationError("Title is not available")
    if row["engine_status"] != "active":
        raise CatalogValidationError("Engine is not active")
    return {
        **_serialize_title(row),
        "publication": _serialize_site_title_publication(row),
    }


def _serialize_title(row: dict[str, object]) -> dict[str, object]:
    return {
        "title_code": row["title_code"],
        "engine_code": row["engine_code"],
        "display_name": row["display_name"],
        "status": row["status"],
        "archived_at": row.get("archived_at").isoformat() if row.get("archived_at") is not None else None,
        "is_archived": row.get("archived_at") is not None,
        "is_test": row.get("is_test", False),
        "is_master": row.get("is_master", False),
        "source_title_code": row.get("source_title_code"),
        "engine": {
            "engine_code": row["engine_code"],
            "display_name": row["engine_display_name"],
            "status": row["engine_status"],
        },
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _serialize_site_title_publication(row: dict[str, object]) -> dict[str, object]:
    return {
        "site_title_status": row.get("site_title_status"),
        "lobby_visibility": row.get("lobby_visibility", "hidden"),
        "demo_enabled": row.get("demo_enabled", False),
        "real_enabled": row.get("real_enabled", False),
        "lobby_display_name": row.get("lobby_display_name"),
        "lobby_description": row.get("lobby_description"),
        "featured": row.get("featured", False),
        "position": row.get("position", 0),
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


def _normalize_status_filter(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    if normalized not in {"active", "inactive", "archived", "all"}:
        raise CatalogValidationError("Status filter is invalid")
    return normalized


def _normalize_test_filter(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    if normalized not in {"only", "exclude", "all"}:
        raise CatalogValidationError("Test filter is invalid")
    return normalized


def ensure_title_is_mutable(*, title_code: str) -> dict[str, object]:
    title = get_title_catalog_entry(title_code=title_code)
    if title["is_master"] is True:
        raise CatalogValidationError("Master titles are read-only")
    if title.get("is_archived") is True:
        raise CatalogValidationError("Archived titles are read-only")
    return title
