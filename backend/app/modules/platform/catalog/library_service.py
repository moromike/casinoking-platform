from __future__ import annotations

from app.db.connection import db_connection
from app.modules.platform.catalog.service import CatalogNotFoundError, CatalogValidationError


def get_site_game_library(*, site_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT site_code, display_name, status, created_at, updated_at
                FROM sites
                WHERE site_code = %s
                """,
                (normalized_site_code,),
            )
            site_row = cursor.fetchone()
            if site_row is None:
                raise CatalogNotFoundError("Site not found")
            if site_row["status"] != "active":
                raise CatalogValidationError("Site is not active")

            cursor.execute(
                """
                SELECT
                    gt.title_code,
                    gt.engine_code,
                    gt.display_name,
                    gt.status,
                    gt.is_master,
                    ge.display_name AS engine_display_name,
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
                  AND st.status = 'active'
                  AND st.lobby_visibility = 'visible'
                  AND gt.status = 'active'
                  AND gt.is_master = false
                  AND ge.status = 'active'
                  AND (st.demo_enabled = true OR st.real_enabled = true)
                ORDER BY st.featured DESC, st.position ASC, gt.display_name ASC, gt.title_code ASC
                """,
                (normalized_site_code,),
            )
            rows = list(cursor.fetchall())

    return {
        "site": {
            "site_code": site_row["site_code"],
            "display_name": site_row["display_name"],
            "status": site_row["status"],
        },
        "titles": [_serialize_library_title(row) for row in rows],
    }


def _serialize_library_title(row: dict[str, object]) -> dict[str, object]:
    return {
        "title_code": row["title_code"],
        "engine_code": row["engine_code"],
        "engine_display_name": row["engine_display_name"],
        "display_name": row["lobby_display_name"] or row["display_name"],
        "catalog_display_name": row["display_name"],
        "description": row["lobby_description"],
        "demo_enabled": row["demo_enabled"],
        "real_enabled": row["real_enabled"],
        "featured": row["featured"],
        "position": row["position"],
    }


def _normalize_code(raw_value: str, message: str) -> str:
    normalized = raw_value.strip().lower()
    if not normalized:
        raise CatalogValidationError(message)
    return normalized
