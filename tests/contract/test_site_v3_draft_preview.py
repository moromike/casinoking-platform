from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.core.config import settings


def test_site_v3_draft_preview_token_and_snapshot_flow(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-admin")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_preview_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Preview Target",
    )
    page_code = f"preview-{uuid4().hex[:8]}"

    try:
        draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Preview Draft",
                "modules": _valid_modules(title["title_code"], headline="Draft headline"),
            },
        )
        assert draft_response.status_code == 200, draft_response.text
        assert _version_count(db_connection=db_connection, page_code=page_code) == 0

        token_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
            headers=headers,
        )
        assert token_response.status_code == 200, token_response.text
        token_payload = token_response.json()["data"]
        assert token_payload["preview_url"].endswith(f"/preview/{token_payload['token']}")
        assert token_payload["draft_version"] == 1

        preview_response = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": token_payload["token"]},
        )
        assert preview_response.status_code == 200, preview_response.text
        assert preview_response.headers["cache-control"] == "no-store"
        preview = preview_response.json()["data"]
        assert preview["title"] == "Preview Draft"
        assert preview["draft_version"] == 1
        assert preview["is_preview"] is True
        assert "published_version" not in preview
        assert _version_count(db_connection=db_connection, page_code=page_code) == 0

        actions = _fetch_site_v3_audit_actions(
            db_connection=db_connection,
            admin_user_id=str(admin["user_id"]),
            resource_id=f"casinoking:{page_code}:it",
        )
        assert "site_v3.preview_token.issue" in actions
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def test_site_v3_draft_preview_missing_expired_scope_and_stale_tokens(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-errors")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_preview_errors_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Preview Errors Target",
    )
    page_code = f"preview-errors-{uuid4().hex[:8]}"
    other_page_code = f"preview-other-{uuid4().hex[:8]}"

    try:
        _save_draft(client=client, headers=headers, page_code=page_code, title_code=title["title_code"], headline="First")
        _save_draft(client=client, headers=headers, page_code=other_page_code, title_code=title["title_code"], headline="Other")

        missing = client.get(f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it")
        assert missing.status_code == 401
        assert missing.json()["error"]["code"] == "SITEV3.PREVIEW.TOKEN_MISSING"

        expired_token = _make_preview_token(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            draft_version=1,
            admin_id=str(admin["user_id"]),
            expires_delta=timedelta(minutes=-1),
        )
        expired = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": expired_token},
        )
        assert expired.status_code == 401
        assert expired.json()["error"]["code"] == "SITEV3.PREVIEW.TOKEN_EXPIRED"

        token = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
            headers=headers,
        ).json()["data"]["token"]
        scope_mismatch = client.get(
            f"/site-v3/sites/casinoking/pages/{other_page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": token},
        )
        assert scope_mismatch.status_code == 403
        assert scope_mismatch.json()["error"]["code"] == "SITEV3.PREVIEW.TOKEN_SCOPE_MISMATCH"

        _save_draft(
            client=client,
            headers=headers,
            page_code=page_code,
            title_code=title["title_code"],
            headline="Second",
            expected_draft_version=1,
        )
        stale = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": token},
        )
        assert stale.status_code == 409
        error = stale.json()["error"]
        assert error["code"] == "SITEV3.PREVIEW.TOKEN_STALE"
        assert error["details"]["draft_version"] == 2
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)
        _cleanup_site_v3_page(db_connection=db_connection, page_code=other_page_code)


def test_site_v3_draft_preview_page_not_found_and_auth_required(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-missing")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    page_code = f"missing-{uuid4().hex[:8]}"

    unauthenticated = client.post(
        f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
    )
    assert unauthenticated.status_code == 401

    missing = client.post(
        f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
        headers=headers,
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "SITEV3.PREVIEW.PAGE_NOT_FOUND"


def test_site_v3_draft_preview_preserves_composition_order(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-preview-order")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_preview_order_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Preview Order Target",
    )
    page_code = f"preview-order-{uuid4().hex[:8]}"

    try:
        response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Preview Order",
                "modules": [
                    {
                        "module_code": "global_header",
                        "slot_key": "header",
                        "sort_order": 0,
                        "config_json": {"brand_label": "CasinoKing"},
                    },
                    {
                        "module_code": "game_grid",
                        "slot_key": "games",
                        "sort_order": 1,
                        "config_json": {"heading": "Games first", "title_codes": [title["title_code"]]},
                    },
                    {
                        "module_code": "hero_banner",
                        "slot_key": "hero",
                        "sort_order": 2,
                        "config_json": {
                            "headline": "Hero second",
                            "body": "Body",
                            "cta_label": "Play",
                            "cta_title_code": title["title_code"],
                        },
                    },
                    {
                        "module_code": "global_footer",
                        "slot_key": "footer",
                        "sort_order": 3,
                        "config_json": {"legal_text": "18+"},
                    },
                ],
            },
        )
        assert response.status_code == 200, response.text

        token = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
            headers=headers,
        ).json()["data"]["token"]
        preview_response = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": token},
        )
        assert preview_response.status_code == 200, preview_response.text
        module_codes = [module["module_code"] for module in preview_response.json()["data"]["modules"]]
        assert module_codes == ["global_header", "game_grid", "hero_banner", "global_footer"]
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def _save_draft(
    *,
    client,
    headers: dict[str, str],
    page_code: str,
    title_code: str,
    headline: str,
    expected_draft_version: int | None = None,
) -> None:
    body: dict[str, object] = {
        "locale": "it",
        "title": f"{headline} page",
        "modules": _valid_modules(title_code, headline=headline),
    }
    if expected_draft_version is not None:
        body["expected_draft_version"] = expected_draft_version
    response = client.put(
        f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
        headers=headers,
        json=body,
    )
    assert response.status_code == 200, response.text


def _valid_modules(title_code: str, *, headline: str) -> list[dict[str, object]]:
    return [
        {
            "module_code": "hero_banner",
            "slot_key": "hero",
            "sort_order": 0,
            "config_json": {
                "headline": headline,
                "body": "Preview body",
                "cta_label": "Play demo",
                "cta_title_code": title_code,
            },
        },
        {
            "module_code": "rich_text_safe",
            "slot_key": "content",
            "sort_order": 1,
            "config_json": {"html": "<p><strong>Safe</strong> preview.</p>"},
        },
    ]


def _make_preview_token(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    draft_version: int,
    admin_id: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "typ": "site_v3_draft_preview",
            "site_code": site_code,
            "page_code": page_code,
            "locale": locale,
            "draft_version": draft_version,
            "admin_id": admin_id,
            "iat": now,
            "exp": now + expires_delta,
            "jti": uuid4().hex,
        },
        settings.site_v3_draft_preview_secret,
        algorithm="HS256",
    )


def _version_count(*, db_connection, page_code: str) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS version_count
            FROM site_v3_page_versions version
            JOIN site_v3_pages page ON page.id = version.page_id
            WHERE page.page_code = %s
            """,
            (page_code,),
        )
        return int(cursor.fetchone()["version_count"])


def _fetch_site_v3_audit_actions(
    *,
    db_connection,
    admin_user_id: str,
    resource_id: str,
) -> set[str]:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT action_kind, payload_json
            FROM admin_audit_log
            WHERE admin_user_id = %s
              AND resource_kind = 'site_v3_page'
              AND resource_id = %s
            """,
            (admin_user_id, resource_id),
        )
        rows = cursor.fetchall()
    assert all(row["payload_json"]["source"] == "site_v3" for row in rows)
    return {row["action_kind"] for row in rows}


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
