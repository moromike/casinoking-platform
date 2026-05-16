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


def test_title_audio_asset_upload_supports_runtime_sound_kind(
    db_connection,
    tmp_path,
) -> None:
    admin = ensure_local_admin(
        email="asset-registry-audio@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)

    _delete_title_assets(db_connection)

    uploaded = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="audio_safe_reveal",
            mime="audio/mpeg",
            content=b"ID3\x00\x00\x00\x00\x00\x00\x00",
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )

    assert uploaded["asset_kind"] == "audio_safe_reveal"
    assert uploaded["mime"] == "audio/mpeg"
    assert uploaded["public_url"].startswith("/static/games/mines_classic/audio_safe_reveal/")
    assert uploaded["public_url"].endswith(".mp3")
    assert storage.exists(relative_path=str(uploaded["file_path"])) is True


def test_title_game_card_upload_requires_square_small_image(db_connection, tmp_path) -> None:
    admin = ensure_local_admin(
        email="asset-registry-game-card@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)

    _delete_title_assets(db_connection)

    uploaded = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="game_card",
            mime="image/png",
            content=_png_bytes_with_size(width=512, height=512),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )

    assert uploaded["asset_kind"] == "game_card"
    assert uploaded["mime"] == "image/png"
    assert uploaded["public_url"].startswith("/static/games/mines_classic/game_card/")
    assert uploaded["public_url"].endswith(".png")
    assert storage.exists(relative_path=str(uploaded["file_path"])) is True

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="game_card",
                mime="image/png",
                content=_png_bytes_with_size(width=512, height=384),
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Game card asset must be square"
    else:
        raise AssertionError("Expected validation error for non-square game card")

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="game_card",
                mime="image/png",
                content=_png_bytes_with_size(width=512, height=512)
                + (b"x" * (301 * 1024)),
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Game card asset file is too large"
    else:
        raise AssertionError("Expected validation error for oversized game card")


def test_title_skin_assets_use_explicit_png_webp_kinds_and_caps(
    db_connection,
    tmp_path,
) -> None:
    admin = ensure_local_admin(
        email="asset-registry-skin@example.com",
        password="StrongPass-asset-registry",
    )
    storage = FilesystemAssetStorage(tmp_path)

    _delete_title_assets(db_connection)

    title_logo = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="title_logo",
            mime="image/webp",
            content=_webp_vp8x_bytes(width=720, height=180),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )
    game_area_background = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="game_area_background",
            mime="image/png",
            content=_png_bytes_with_size(width=1280, height=720),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )
    cell_texture = upload_title_asset(
        AssetUpload(
            title_code=TITLE_CODE,
            asset_kind="cell_face_down_background",
            mime="image/png",
            content=_png_bytes_with_size(width=256, height=256),
            uploaded_by_admin_user_id=str(admin["user_id"]),
        ),
        storage=storage,
    )

    assert title_logo["public_url"].endswith(".webp")
    assert game_area_background["public_url"].endswith(".png")
    assert cell_texture["public_url"].endswith(".png")
    assert storage.exists(relative_path=str(title_logo["file_path"])) is True

    active_kinds = {asset["asset_kind"] for asset in list_title_assets(title_code=TITLE_CODE)}
    assert active_kinds == {
        "title_logo",
        "game_area_background",
        "cell_face_down_background",
    }

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="title_logo",
                mime="image/svg+xml",
                content=b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Asset MIME type is not supported"
    else:
        raise AssertionError("Expected validation error for SVG skin asset")

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="game_area_background",
                mime="image/png",
                content=_png_bytes_with_size(width=1280, height=720)
                + (b"x" * (401 * 1024)),
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Skin asset file is too large"
    else:
        raise AssertionError("Expected validation error for oversized skin asset")


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
    deleted = delete_title_asset(
        title_code=TITLE_CODE,
        asset_kind="symbol_safe",
        admin_user_id=str(admin["user_id"]),
    )

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
                mime="application/octet-stream",
                content=b"audio",
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Asset MIME type is not supported"
    else:
        raise AssertionError("Expected validation error for unsupported MIME type")

    try:
        upload_title_asset(
            AssetUpload(
                title_code=TITLE_CODE,
                asset_kind="audio_lose",
                mime="audio/mpeg",
                content=b"audio",
                uploaded_by_admin_user_id=str(admin["user_id"]),
            ),
            storage=storage,
        )
    except AssetRegistryValidationError as exc:
        assert str(exc) == "Asset kind is not uploadable"
    else:
        raise AssertionError("Expected validation error for legacy audio kind")

    try:
        delete_title_asset(
            title_code=TITLE_CODE,
            asset_kind="symbol_safe",
            admin_user_id=str(admin["user_id"]),
        )
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


def _png_bytes_with_size(*, width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _webp_vp8x_bytes(*, width: int, height: int) -> bytes:
    content = bytearray(30)
    content[0:4] = b"RIFF"
    content[4:8] = (22).to_bytes(4, "little")
    content[8:12] = b"WEBP"
    content[12:16] = b"VP8X"
    content[24:27] = (width - 1).to_bytes(3, "little")
    content[27:30] = (height - 1).to_bytes(3, "little")
    return bytes(content)


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
