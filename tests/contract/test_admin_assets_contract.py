from __future__ import annotations


TITLE_CODE = "mines_classic"


def test_admin_assets_upload_list_and_delete_contract(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    _delete_title_assets(db_connection)
    admin_user = create_admin_user(prefix="contract-admin-assets")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)

    upload_response = client.post(
        f"/admin/titles/{TITLE_CODE}/assets",
        headers=headers,
        data={"asset_kind": "symbol_safe"},
        files={
            "file": (
                "safe.png",
                _png_bytes(),
                "image/png",
            )
        },
    )

    assert upload_response.status_code == 200, upload_response.text
    uploaded = upload_response.json()["data"]
    assert uploaded["title_code"] == TITLE_CODE
    assert uploaded["asset_kind"] == "symbol_safe"
    assert uploaded["mime"] == "image/png"
    assert uploaded["status"] == "active"
    assert uploaded["public_url"].startswith("/static/games/mines_classic/symbol_safe/")

    api_base_url = str(client.base_url).rstrip("/")
    static_base_url = api_base_url.removesuffix("/api/v1")
    static_response = client.get(f"{static_base_url}{uploaded['public_url']}")
    assert static_response.status_code == 200
    assert static_response.content == _png_bytes()

    list_response = client.get(
        f"/admin/titles/{TITLE_CODE}/assets",
        headers=headers,
    )

    assert list_response.status_code == 200, list_response.text
    assets = list_response.json()["data"]
    assert len(assets) == 1
    assert assets[0]["id"] == uploaded["id"]

    delete_response = client.delete(
        f"/admin/titles/{TITLE_CODE}/assets/symbol_safe",
        headers=headers,
    )

    assert delete_response.status_code == 200, delete_response.text
    deleted = delete_response.json()["data"]
    assert deleted["id"] == uploaded["id"]
    assert deleted["status"] == "deleted"


def test_admin_assets_reject_player_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-assets-player")

    response = client.get(
        f"/admin/titles/{TITLE_CODE}/assets",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _delete_title_assets(db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM title_assets WHERE title_code = %s",
            (TITLE_CODE,),
        )
