from __future__ import annotations

from psycopg.types.json import Jsonb

from app.modules.auth.service import ensure_local_admin
from app.modules.platform.asset_registry.service import (
    AssetRegistryNotFoundError,
    AssetRegistryValidationError,
    AssetUpload,
    delete_title_asset,
    list_title_assets,
    upload_title_asset,
)
from app.modules.platform.asset_registry.storage import FilesystemAssetStorage
from app.tools.migrate_mines_board_asset_data_urls import (
    migrate_mines_board_asset_data_urls,
)


TITLE_CODE = "mines_classic"


def test_title_asset_upload_is_checksum_idempotent_and_serves_versioned_url(
    db_connection,
    tmp_path,
) -> None:
    admin = ensure_local_admin(
        email="asset-registry-idempotent@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)
    content = _png_bytes()

    _delete_title_assets(db_connection)

    first = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="symbol_safe",
            mime="image/png",
            content=content,
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )
    second = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="symbol_safe",
            mime="image/png",
            content=content,
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )

    assert second["id"] == first["id"]
    assert second["checksum_sha256"] == first["checksum_sha256"]
    assert second["public_url"].startswith("/static/games/mines_classic/symbol_safe/")
    assert second["public_url"].endswith(".png")
    assert storage.exists(relative_path=str(second["file_path"])) is True

    active_assets = list_title_assets(title_code=TITLE_CODE)
    assert [asset["asset_kind"] for asset in active_assets] == ["symbol_safe"]

    active_count = _count_assets(
        db_connection,
        asset_kind="symbol_safe",
        status="active",
    )
    assert active_count == 1


def test_title_asset_upload_replaces_active_asset_for_same_kind(
    db_connection,
    tmp_path,
) -> None:
    admin = ensure_local_admin(
        email="asset-registry-replace@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)

    _delete_title_assets(db_connection)

    first = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="symbol_mine",
            mime="image/png",
            content=_png_bytes(),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )
    second = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="symbol_mine",
            mime="image/svg+xml",
            content=b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )

    assert second["id"] != first["id"]
    assert second["public_url"].endswith(".svg")
    assert _count_assets(db_connection, asset_kind="symbol_mine", status="active") == 1
    assert _count_assets(db_connection, asset_kind="symbol_mine", status="deleted") == 1


def test_title_asset_delete_marks_active_asset_deleted(db_connection, tmp_path) -> None:
    admin = ensure_local_admin(
        email="asset-registry-delete@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)

    _delete_title_assets(db_connection)

    uploaded = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="symbol_safe",
            mime="image/png",
            content=_png_bytes(),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )
    deleted = delete_title_asset(title_code=TITLE_CODE, asset_kind="symbol_safe")

    assert deleted["id"] == uploaded["id"]
    assert deleted["status"] == "deleted"
    assert list_title_assets(title_code=TITLE_CODE) == []


def test_title_asset_upload_rejects_invalid_payload(db_connection, tmp_path) -> None:
    admin = ensure_local_admin(
        email="asset-registry-invalid@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)
    _delete_title_assets(db_connection)

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="audio_win",
                mime="audio/mpeg",
                content=b"audio",
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Asset kind is not uploadable in Phase 4"
    else:
        raise AssertionError("Expected validation error for unsupported Phase 4 kind")

    try:
        delete_title_asset(title_code=TITLE_CODE, asset_kind="symbol_safe")
    except AssetRegistryNotFoundError as exc:
        assert str(exc) == "Active asset not found"
    else:
        raise AssertionError("Expected not found for missing active asset")


def test_mines_board_data_url_migration_rewrites_config_to_static_urls(
    db_connection,
    tmp_path,
) -> None:
    storage = FilesystemAssetStorage(tmp_path)
    _delete_title_assets(db_connection)
    data_url = "data:image/png;base64," + "iVBORw0KGgo="

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE mines_title_configs
            SET
                published_board_assets_json = %s::jsonb,
                draft_board_assets_json = %s::jsonb
            WHERE title_code = %s
            """,
            (
                Jsonb(
                    {
                        "safe_icon_data_url": data_url,
                        "mine_icon_data_url": None,
                    }
                ),
                Jsonb(
                    {
                        "safe_icon_data_url": None,
                        "mine_icon_data_url": data_url,
                    }
                ),
                TITLE_CODE,
            ),
        )

    migrated = migrate_mines_board_asset_data_urls(storage=storage)

    assert {
        (asset.config_column, asset.board_asset_field)
        for asset in migrated
    } == {
        ("published_board_assets_json", "safe_icon_data_url"),
        ("draft_board_assets_json", "mine_icon_data_url"),
    }

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                published_board_assets_json,
                draft_board_assets_json
            FROM mines_title_configs
            WHERE title_code = %s
            """,
            (TITLE_CODE,),
        )
        row = cursor.fetchone()

    published_assets = row["published_board_assets_json"]
    draft_assets = row["draft_board_assets_json"]
    assert published_assets["safe_icon_data_url"].startswith("/static/games/")
    assert draft_assets["mine_icon_data_url"].startswith("/static/games/")
    assert storage.exists(
        relative_path=published_assets["safe_icon_data_url"].removeprefix("/static/games/")
    )
    assert storage.exists(
        relative_path=draft_assets["mine_icon_data_url"].removeprefix("/static/games/")
    )


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


def _count_assets(db_connection, *, asset_kind: str, status: str) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM title_assets
            WHERE title_code = %s
              AND asset_kind = %s
              AND status = %s
            """,
            (TITLE_CODE, asset_kind, status),
        )
        row = cursor.fetchone()
    return int(row["count"])
