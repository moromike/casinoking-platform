from __future__ import annotations

from uuid import uuid4


def test_site_v3_preview_token_does_not_unlock_published_or_admin_routes(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-security")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_security_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Security Target",
    )
    page_code = f"security-{uuid4().hex[:8]}"

    try:
        draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Security Draft",
                "modules": [
                    {
                        "module_code": "featured_game",
                        "slot_key": "main",
                        "sort_order": 0,
                        "config_json": {"title_code": title["title_code"]},
                    }
                ],
            },
        )
        assert draft_response.status_code == 200, draft_response.text
        token = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
            headers=headers,
        ).json()["data"]["token"]

        published_with_preview_token = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}",
            headers={"Authorization": f"Bearer {token}", "X-Draft-Preview-Token": token},
        )
        assert published_with_preview_token.status_code == 404
        assert published_with_preview_token.json()["error"]["code"] == "SITEV3.PAGE.NOT_PUBLISHED"

        admin_with_preview_token = client.get(
            "/admin/site-v3/sites/casinoking/pages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert admin_with_preview_token.status_code in {401, 403}
        assert admin_with_preview_token.json()["error"]["code"] in {
            "CK.AUTH.INVALID_TOKEN",
            "CK.AUTH.UNAUTHORIZED",
            "CK.AUTH.FORBIDDEN",
            "UNAUTHORIZED",
        }
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def test_site_v3_preview_token_is_never_used_in_public_query_contract() -> None:
    source = _read("backend/app/api/routes/site_v3_public.py")
    assert "X-Draft-Preview-Token" in source
    assert "draft_preview_token: str | None = Header" in source
    assert "preview_token: str | None = Query" not in source
    assert "token: str | None = Query" not in source


def test_site_v3_preview_applies_rich_text_sanitization_on_draft(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-sanitize")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    page_code = f"sanitize-{uuid4().hex[:8]}"

    try:
        unsafe_draft = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Unsafe Draft",
                "modules": [
                    {
                        "module_code": "rich_text_safe",
                        "slot_key": "content",
                        "sort_order": 0,
                        "config_json": {"html": "<p onclick=\"alert(1)\">Unsafe</p>"},
                    }
                ],
            },
        )
        assert unsafe_draft.status_code == 422
        assert unsafe_draft.json()["error"]["code"] == "SITEV3.VALIDATION.UNSAFE_HTML"
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def _read(relative_path: str) -> str:
    from pathlib import Path

    return Path(relative_path).read_text(encoding="utf-8")


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
