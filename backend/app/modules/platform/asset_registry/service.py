from __future__ import annotations

from dataclasses import dataclass
import hashlib

from psycopg.rows import DictRow

from app.core.config import settings
from app.db.connection import db_connection
from app.modules.platform.asset_registry.storage import (
    AssetStorage,
    FilesystemAssetStorage,
)
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_title_catalog_entry,
)


IMAGE_MIME_EXTENSIONS = {
    "image/png": "png",
    "image/svg+xml": "svg",
}
IMAGE_ASSET_KINDS = {"logo", "background", "symbol_safe", "symbol_mine"}
MAX_IMAGE_BYTES = 512 * 1024
AUDIO_MIME_EXTENSIONS = {
    "audio/mpeg": "mp3",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/webm": "webm",
}
AUDIO_ASSET_KINDS = {
    "audio_safe_reveal",
    "audio_mine_hit",
    "audio_collect",
    "audio_win",
}
MAX_AUDIO_BYTES = 1024 * 1024
AUDIT_ACTION_TITLE_ASSET_UPLOAD = "title_asset_upload"
AUDIT_ACTION_TITLE_ASSET_DELETE = "title_asset_delete"
AUDIT_RESOURCE_TITLE_ASSET = "title_asset"
ALL_ASSET_KINDS = {
    "logo",
    "background",
    "symbol_safe",
    "symbol_mine",
    "audio_safe_reveal",
    "audio_mine_hit",
    "audio_collect",
    "audio_win",
    "audio_lose",
    "audio_click",
    "font",
}


class AssetRegistryValidationError(Exception):
    pass


class AssetRegistryNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class AssetUpload:
    title_code: str
    asset_kind: str
    mime: str
    content: bytes
    uploaded_by_admin_user_id: str | None


def list_title_assets(*, title_code: str) -> list[dict[str, object]]:
    normalized_title_code = _resolve_title_code(title_code)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title_code,
                    asset_kind,
                    file_path,
                    public_url,
                    mime,
                    byte_size,
                    checksum_sha256,
                    uploaded_by_admin_user_id,
                    created_at,
                    status
                FROM title_assets
                WHERE title_code = %s
                  AND status = 'active'
                ORDER BY asset_kind
                """,
                (normalized_title_code,),
            )
            rows = cursor.fetchall()
    return [_serialize_asset(row) for row in rows]


def upload_title_asset(
    upload: AssetUpload,
    *,
    storage: AssetStorage | None = None,
) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(upload.title_code)
    normalized_asset_kind = _normalize_asset_kind(upload.asset_kind)
    mime = _normalize_mime(upload.mime)
    _validate_asset_payload(
        asset_kind=normalized_asset_kind,
        mime=mime,
        content=upload.content,
    )

    checksum = hashlib.sha256(upload.content).hexdigest()
    extension = _extension_for_mime(mime)
    relative_path = _build_relative_path(
        title_code=normalized_title_code,
        asset_kind=normalized_asset_kind,
        checksum=checksum,
        extension=extension,
    )
    public_url = _build_public_url(relative_path)
    asset_storage = storage or FilesystemAssetStorage(settings.asset_storage_root)
    asset_storage.write_if_missing(relative_path=relative_path, content=upload.content)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            before_active_assets = _load_active_assets_for_kind(
                cursor=cursor,
                title_code=normalized_title_code,
                asset_kind=normalized_asset_kind,
            )
            cursor.execute(
                """
                SELECT id
                FROM title_assets
                WHERE title_code = %s
                  AND asset_kind = %s
                  AND checksum_sha256 = %s
                """,
                (normalized_title_code, normalized_asset_kind, checksum),
            )
            existing_row = cursor.fetchone()
            if existing_row is not None:
                asset_id = existing_row["id"]
                cursor.execute(
                    """
                    UPDATE title_assets
                    SET status = 'deleted'
                    WHERE title_code = %s
                      AND asset_kind = %s
                      AND id <> %s
                      AND status = 'active'
                    """,
                    (normalized_title_code, normalized_asset_kind, asset_id),
                )
                cursor.execute(
                    """
                    UPDATE title_assets
                    SET
                        file_path = %s,
                        public_url = %s,
                        mime = %s,
                        byte_size = %s,
                        uploaded_by_admin_user_id = %s,
                        status = 'active'
                    WHERE id = %s
                    RETURNING
                        id,
                        title_code,
                        asset_kind,
                        file_path,
                        public_url,
                        mime,
                        byte_size,
                        checksum_sha256,
                        uploaded_by_admin_user_id,
                        created_at,
                        status
                    """,
                    (
                        relative_path,
                        public_url,
                        mime,
                        len(upload.content),
                        upload.uploaded_by_admin_user_id,
                        asset_id,
                    ),
                )
                row = cursor.fetchone()
            else:
                cursor.execute(
                    """
                    UPDATE title_assets
                    SET status = 'deleted'
                    WHERE title_code = %s
                      AND asset_kind = %s
                      AND status = 'active'
                    """,
                    (normalized_title_code, normalized_asset_kind),
                )
                cursor.execute(
                    """
                    INSERT INTO title_assets (
                        title_code,
                        asset_kind,
                        file_path,
                        public_url,
                        mime,
                        byte_size,
                        checksum_sha256,
                        uploaded_by_admin_user_id,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
                    RETURNING
                        id,
                        title_code,
                        asset_kind,
                        file_path,
                        public_url,
                        mime,
                        byte_size,
                        checksum_sha256,
                        uploaded_by_admin_user_id,
                        created_at,
                        status
                    """,
                    (
                        normalized_title_code,
                        normalized_asset_kind,
                        relative_path,
                        public_url,
                        mime,
                        len(upload.content),
                        checksum,
                        upload.uploaded_by_admin_user_id,
                    ),
                )
                row = cursor.fetchone()

            if upload.uploaded_by_admin_user_id is not None:
                audit_payload = _build_title_asset_upload_audit_payload(
                    title_code=normalized_title_code,
                    asset_kind=normalized_asset_kind,
                    before=before_active_assets,
                    after=row,
                )
                resource_id = _build_title_asset_resource_id(
                    title_code=normalized_title_code,
                    asset_kind=normalized_asset_kind,
                )
                record_audit_entry(
                    admin_user_id=upload.uploaded_by_admin_user_id,
                    action_kind=AUDIT_ACTION_TITLE_ASSET_UPLOAD,
                    resource_kind=AUDIT_RESOURCE_TITLE_ASSET,
                    resource_id=resource_id,
                    payload=audit_payload,
                    request_fingerprint=build_audit_request_fingerprint(
                        action_kind=AUDIT_ACTION_TITLE_ASSET_UPLOAD,
                        resource_kind=AUDIT_RESOURCE_TITLE_ASSET,
                        resource_id=resource_id,
                        payload=audit_payload,
                    ),
                    cursor=cursor,
                )

    if row is None:
        raise AssetRegistryValidationError("Asset upload failed")
    return _serialize_asset(row)


def delete_title_asset(
    *,
    title_code: str,
    asset_kind: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_title_code = _resolve_title_code(title_code)
    normalized_asset_kind = _normalize_asset_kind(asset_kind)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE title_assets
                SET status = 'deleted'
                WHERE title_code = %s
                  AND asset_kind = %s
                  AND status = 'active'
                RETURNING
                    id,
                    title_code,
                    asset_kind,
                    file_path,
                    public_url,
                    mime,
                    byte_size,
                    checksum_sha256,
                    uploaded_by_admin_user_id,
                    created_at,
                    status
                """,
                (normalized_title_code, normalized_asset_kind),
            )
            row = cursor.fetchone()
            if row is not None:
                audit_payload = _build_title_asset_delete_audit_payload(
                    title_code=normalized_title_code,
                    asset_kind=normalized_asset_kind,
                    deleted=row,
                )
                resource_id = _build_title_asset_resource_id(
                    title_code=normalized_title_code,
                    asset_kind=normalized_asset_kind,
                )
                record_audit_entry(
                    admin_user_id=admin_user_id,
                    action_kind=AUDIT_ACTION_TITLE_ASSET_DELETE,
                    resource_kind=AUDIT_RESOURCE_TITLE_ASSET,
                    resource_id=resource_id,
                    payload=audit_payload,
                    request_fingerprint=build_audit_request_fingerprint(
                        action_kind=AUDIT_ACTION_TITLE_ASSET_DELETE,
                        resource_kind=AUDIT_RESOURCE_TITLE_ASSET,
                        resource_id=resource_id,
                        payload=audit_payload,
                    ),
                    cursor=cursor,
                )
    if row is None:
        raise AssetRegistryNotFoundError("Active asset not found")
    return _serialize_asset(row)


def _resolve_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise AssetRegistryValidationError("Title code is required")
    try:
        get_title_catalog_entry(title_code=normalized_title_code)
    except CatalogNotFoundError as exc:
        raise AssetRegistryNotFoundError("Title not found") from exc
    except CatalogValidationError as exc:
        raise AssetRegistryValidationError(str(exc)) from exc
    return normalized_title_code


def _normalize_asset_kind(asset_kind: str) -> str:
    normalized = asset_kind.strip().lower()
    if normalized not in ALL_ASSET_KINDS:
        raise AssetRegistryValidationError("Unsupported asset kind")
    return normalized


def _normalize_mime(mime: str) -> str:
    normalized = mime.strip().lower()
    if not normalized:
        raise AssetRegistryValidationError("Asset MIME type is required")
    return normalized


def _validate_asset_payload(*, asset_kind: str, mime: str, content: bytes) -> None:
    if not content:
        raise AssetRegistryValidationError("Asset file is empty")
    if asset_kind in IMAGE_ASSET_KINDS:
        if mime not in IMAGE_MIME_EXTENSIONS:
            raise AssetRegistryValidationError("Asset MIME type is not supported")
        if len(content) > MAX_IMAGE_BYTES:
            raise AssetRegistryValidationError("Asset file is too large")
        return
    if asset_kind in AUDIO_ASSET_KINDS:
        if mime not in AUDIO_MIME_EXTENSIONS:
            raise AssetRegistryValidationError("Asset MIME type is not supported")
        if len(content) > MAX_AUDIO_BYTES:
            raise AssetRegistryValidationError("Asset file is too large")
        return
    raise AssetRegistryValidationError("Asset kind is not uploadable")


def _extension_for_mime(mime: str) -> str:
    extension = IMAGE_MIME_EXTENSIONS.get(mime) or AUDIO_MIME_EXTENSIONS.get(mime)
    if extension is None:
        raise AssetRegistryValidationError("Asset MIME type is not supported")
    return extension


def _build_relative_path(
    *,
    title_code: str,
    asset_kind: str,
    checksum: str,
    extension: str,
) -> str:
    return f"{title_code}/{asset_kind}/{checksum[:8]}.{extension}"


def _build_public_url(relative_path: str) -> str:
    normalized_path = relative_path.replace("\\", "/")
    return f"{settings.asset_public_base_url}/{normalized_path}"


def _serialize_asset(row: DictRow | dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "title_code": row["title_code"],
        "asset_kind": row["asset_kind"],
        "file_path": row["file_path"],
        "public_url": row["public_url"],
        "mime": row["mime"],
        "byte_size": row["byte_size"],
        "checksum_sha256": row["checksum_sha256"],
        "uploaded_by_admin_user_id": (
            str(row["uploaded_by_admin_user_id"])
            if row["uploaded_by_admin_user_id"] is not None
            else None
        ),
        "created_at": row["created_at"].isoformat(),
        "status": row["status"],
    }


def _load_active_assets_for_kind(
    *,
    cursor,
    title_code: str,
    asset_kind: str,
) -> list[DictRow]:
    cursor.execute(
        """
        SELECT
            id,
            title_code,
            asset_kind,
            file_path,
            public_url,
            mime,
            byte_size,
            checksum_sha256,
            uploaded_by_admin_user_id,
            created_at,
            status
        FROM title_assets
        WHERE title_code = %s
          AND asset_kind = %s
          AND status = 'active'
        ORDER BY created_at DESC
        """,
        (title_code, asset_kind),
    )
    return list(cursor.fetchall())


def _build_title_asset_resource_id(*, title_code: str, asset_kind: str) -> str:
    return f"{title_code}:{asset_kind}"


def _build_title_asset_upload_audit_payload(
    *,
    title_code: str,
    asset_kind: str,
    before: list[DictRow],
    after: DictRow | dict[str, object] | None,
) -> dict[str, object]:
    return {
        "title_code": title_code,
        "asset_kind": asset_kind,
        "before": {
            "active_assets": [
                _compact_asset_for_audit(asset)
                for asset in before
            ],
        },
        "after": {
            "active_asset": (
                _compact_asset_for_audit(after)
                if after is not None
                else None
            ),
        },
    }


def _build_title_asset_delete_audit_payload(
    *,
    title_code: str,
    asset_kind: str,
    deleted: DictRow | dict[str, object],
) -> dict[str, object]:
    return {
        "title_code": title_code,
        "asset_kind": asset_kind,
        "before": {
            "active_asset": _compact_asset_for_audit(
                deleted,
                status_override="active",
            ),
        },
        "after": {
            "deleted_asset": _compact_asset_for_audit(deleted),
        },
    }


def _compact_asset_for_audit(
    row: DictRow | dict[str, object],
    *,
    status_override: str | None = None,
) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "asset_kind": row["asset_kind"],
        "mime": row["mime"],
        "byte_size": row["byte_size"],
        "checksum_sha256": row["checksum_sha256"],
        "public_url": row["public_url"],
        "status": status_override or row["status"],
    }
