from __future__ import annotations

from uuid import uuid4

import pytest

from app.api.errors import AppError
from app.modules.platform.site_v3.service import (
    public_get_manifest,
    public_get_published_page,
    save_draft,
)


def test_site_v3_service_direct_public_get_does_not_expose_draft(
    create_admin_user,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-contract-admin")
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_contract_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Contract Target",
    )
    page_code = f"contract-{uuid4().hex[:8]}"

    try:
        save_draft(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            title="Contract Draft",
            expected_draft_version=None,
            admin_user_id=str(admin["user_id"]),
            modules=[
                {
                    "module_code": "featured_game",
                    "slot_key": "main",
                    "sort_order": 0,
                    "config_json": {"title_code": title["title_code"]},
                }
            ],
        )

        with pytest.raises(AppError) as exc_info:
            public_get_published_page(site_code="casinoking", page_code=page_code, locale="it")
        assert exc_info.value.code == "SITEV3.PAGE.NOT_PUBLISHED"
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def test_site_v3_public_manifest_is_published_only(
    create_admin_user,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-manifest-admin")
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_manifest_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Manifest Target",
    )
    page_code = f"manifest-{uuid4().hex[:8]}"

    try:
        save_draft(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            title="Manifest Draft",
            expected_draft_version=None,
            admin_user_id=str(admin["user_id"]),
            modules=[
                {
                    "module_code": "featured_game",
                    "slot_key": "main",
                    "sort_order": 0,
                    "config_json": {"title_code": title["title_code"]},
                }
            ],
        )

        manifest = public_get_manifest(site_code="casinoking", locale="it")
        assert all(page["page_code"] != page_code for page in manifest["pages"])
        assert {module["module_code"] for module in manifest["modules"]} >= {
            "global_header",
            "hero_banner",
            "game_grid",
            "featured_game",
            "promo_band",
            "rich_text_safe",
            "global_footer",
        }
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def _cleanup_site_v3_page(*, db_connection, page_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_kind = 'site_v3_page'
              AND resource_id LIKE %s
            """,
            (f"casinoking:{page_code}:%",),
        )
        cursor.execute(
            """
            DELETE FROM site_v3_pages
            WHERE site_code = 'casinoking'
              AND page_code = %s
            """,
            (page_code,),
        )
