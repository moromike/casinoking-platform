from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from uuid import UUID

from psycopg import errors
from psycopg.rows import DictRow

from app.core.config import settings
from app.db.connection import db_connection
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.asset_registry.storage import (
    AssetStorage,
    FilesystemAssetStorage,
)


class SiteCmsValidationError(Exception):
    pass


class SiteCmsNotFoundError(Exception):
    pass


class SiteCmsConflictError(Exception):
    pass


ALLOWED_TARGET_TYPES = frozenset({"none", "title_demo", "title_real"})
ALLOWED_STATUSES = frozenset({"draft", "published", "archived"})
SITE_ASSET_KIND_HOMEPAGE_BANNER = "homepage_banner"
ALLOWED_SITE_ASSET_KINDS = frozenset({SITE_ASSET_KIND_HOMEPAGE_BANNER})
SITE_IMAGE_MIME_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}
MAX_SITE_IMAGE_BYTES = 2 * 1024 * 1024
AUDIT_RESOURCE_SITE_HOME_SLOT = "site_home_slot"
AUDIT_ACTION_SITE_HOME_SLOT_UPDATE = "site_home_slot_update"
AUDIT_ACTION_SITE_HOME_SLOT_PUBLISH = "site_home_slot_publish"
AUDIT_RESOURCE_SITE_ASSET = "site_asset"
AUDIT_ACTION_SITE_ASSET_UPLOAD = "site_asset_upload"
AUDIT_ACTION_SITE_ASSET_DELETE = "site_asset_delete"
SLOT_AUDIT_FIELDS = (
    "title",
    "subtitle",
    "cta_label",
    "cta_target_type",
    "cta_target_ref",
    "media_asset_id",
    "sort_order",
    "status",
    "starts_at",
    "ends_at",
)


@dataclass(frozen=True)
class SiteAssetUpload:
    site_code: str
    asset_kind: str
    mime: str
    content: bytes
    uploaded_by_admin_user_id: str | None


def list_public_home_slots(*, site_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")
            if site["status"] != "active":
                raise SiteCmsValidationError("Site is not active")

            cursor.execute(
                """
                SELECT
                    shs.id,
                    shs.site_code,
                    shs.slot_key,
                    shs.title,
                    shs.subtitle,
                    shs.cta_label,
                    shs.cta_target_type,
                    shs.cta_target_ref,
                    shs.media_asset_id,
                    shs.sort_order,
                    shs.status,
                    shs.starts_at,
                    shs.ends_at,
                    shs.created_by,
                    shs.updated_by,
                    shs.created_at,
                    shs.updated_at,
                    sa.asset_kind AS media_asset_kind,
                    sa.public_url AS media_asset_public_url,
                    sa.mime AS media_asset_mime,
                    sa.byte_size AS media_asset_byte_size,
                    sa.checksum_sha256 AS media_asset_checksum_sha256,
                    sa.created_at AS media_asset_created_at,
                    sa.status AS media_asset_status
                FROM site_home_slots shs
                LEFT JOIN site_assets sa
                  ON sa.id = shs.media_asset_id
                 AND sa.status = 'active'
                WHERE shs.site_code = %s
                  AND shs.status = 'published'
                  AND (shs.starts_at IS NULL OR shs.starts_at <= NOW())
                  AND (shs.ends_at IS NULL OR shs.ends_at > NOW())
                ORDER BY shs.sort_order ASC, shs.created_at ASC, shs.slot_key ASC
                """,
                (normalized_site_code,),
            )
            rows = list(cursor.fetchall())

    return {
        "site": _serialize_site(site),
        "slots": [_serialize_public_slot(row) for row in rows],
    }


def list_admin_home_slots(*, site_code: str) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")

            cursor.execute(
                """
                SELECT
                    shs.id,
                    shs.site_code,
                    shs.slot_key,
                    shs.title,
                    shs.subtitle,
                    shs.cta_label,
                    shs.cta_target_type,
                    shs.cta_target_ref,
                    shs.media_asset_id,
                    shs.sort_order,
                    shs.status,
                    shs.starts_at,
                    shs.ends_at,
                    shs.created_by,
                    shs.updated_by,
                    shs.created_at,
                    shs.updated_at,
                    sa.asset_kind AS media_asset_kind,
                    sa.public_url AS media_asset_public_url,
                    sa.mime AS media_asset_mime,
                    sa.byte_size AS media_asset_byte_size,
                    sa.checksum_sha256 AS media_asset_checksum_sha256,
                    sa.created_at AS media_asset_created_at,
                    sa.status AS media_asset_status
                FROM site_home_slots shs
                LEFT JOIN site_assets sa
                  ON sa.id = shs.media_asset_id
                 AND sa.status = 'active'
                WHERE shs.site_code = %s
                ORDER BY shs.sort_order ASC, shs.slot_key ASC
                """,
                (normalized_site_code,),
            )
            rows = list(cursor.fetchall())

    return {
        "site": _serialize_site(site),
        "slots": [_serialize_slot(row) for row in rows],
    }


def create_home_slot(
    *,
    admin_user_id: str,
    site_code: str,
    slot_key: str,
    title: str,
    subtitle: str | None = None,
    cta_label: str | None = None,
    cta_target_type: str = "none",
    cta_target_ref: str | None = None,
    media_asset_id: str | None = None,
    sort_order: int = 0,
    status: str = "draft",
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_payload = _normalize_slot_payload(
        slot_key=slot_key,
        title=title,
        subtitle=subtitle,
        cta_label=cta_label,
        cta_target_type=cta_target_type,
        cta_target_ref=cta_target_ref,
        media_asset_id=media_asset_id,
        sort_order=sort_order,
        status=status,
        starts_at=starts_at,
        ends_at=ends_at,
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")
            _validate_media_asset(
                cursor=cursor,
                site_code=normalized_site_code,
                media_asset_id=normalized_payload["media_asset_id"],
            )
            _validate_target(
                cursor=cursor,
                site_code=normalized_site_code,
                target_type=str(normalized_payload["cta_target_type"]),
                target_ref=normalized_payload["cta_target_ref"],
            )

            try:
                cursor.execute(
                    """
                    INSERT INTO site_home_slots (
                        site_code,
                        slot_key,
                        title,
                        subtitle,
                        cta_label,
                        cta_target_type,
                        cta_target_ref,
                        media_asset_id,
                        sort_order,
                        status,
                        starts_at,
                        ends_at,
                        created_by,
                        updated_by
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING
                        id,
                        site_code,
                        slot_key,
                        title,
                        subtitle,
                        cta_label,
                        cta_target_type,
                        cta_target_ref,
                        media_asset_id,
                        sort_order,
                        status,
                        starts_at,
                        ends_at,
                        created_by,
                        updated_by,
                        created_at,
                        updated_at
                    """,
                    (
                        normalized_site_code,
                        normalized_payload["slot_key"],
                        normalized_payload["title"],
                        normalized_payload["subtitle"],
                        normalized_payload["cta_label"],
                        normalized_payload["cta_target_type"],
                        normalized_payload["cta_target_ref"],
                        normalized_payload["media_asset_id"],
                        normalized_payload["sort_order"],
                        normalized_payload["status"],
                        normalized_payload["starts_at"],
                        normalized_payload["ends_at"],
                        admin_user_id,
                        admin_user_id,
                    ),
                )
            except errors.UniqueViolation as exc:
                raise SiteCmsConflictError("Home slot already exists") from exc
            row = cursor.fetchone()

            before = _empty_slot_audit_state()
            after = _slot_audit_state(row)
            _record_slot_audit_entries(
                cursor=cursor,
                admin_user_id=admin_user_id,
                before=before,
                after=after,
            )

    return _serialize_slot(row)


def update_home_slot(
    *,
    admin_user_id: str,
    site_code: str,
    slot_key: str,
    updates: dict[str, object],
) -> dict[str, object]:
    if not updates:
        raise SiteCmsValidationError("At least one field is required")

    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_slot_key = _normalize_slot_key(slot_key)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            before_row = _load_slot(
                cursor=cursor,
                site_code=normalized_site_code,
                slot_key=normalized_slot_key,
            )
            if before_row is None:
                if _load_site(cursor=cursor, site_code=normalized_site_code) is None:
                    raise SiteCmsNotFoundError("Site not found")
                raise SiteCmsNotFoundError("Home slot not found")

            merged = {
                "slot_key": normalized_slot_key,
                "title": before_row["title"],
                "subtitle": before_row["subtitle"],
                "cta_label": before_row["cta_label"],
                "cta_target_type": before_row["cta_target_type"],
                "cta_target_ref": before_row["cta_target_ref"],
                "media_asset_id": before_row["media_asset_id"],
                "sort_order": before_row["sort_order"],
                "status": before_row["status"],
                "starts_at": before_row["starts_at"],
                "ends_at": before_row["ends_at"],
            }
            merged.update(updates)
            if "cta_target_type" in updates and str(updates["cta_target_type"]).strip().lower() == "none":
                merged["cta_target_ref"] = None

            normalized_payload = _normalize_slot_payload(**merged)
            _validate_media_asset(
                cursor=cursor,
                site_code=normalized_site_code,
                media_asset_id=normalized_payload["media_asset_id"],
            )
            _validate_target(
                cursor=cursor,
                site_code=normalized_site_code,
                target_type=str(normalized_payload["cta_target_type"]),
                target_ref=normalized_payload["cta_target_ref"],
            )

            cursor.execute(
                """
                UPDATE site_home_slots
                SET
                    title = %s,
                    subtitle = %s,
                    cta_label = %s,
                    cta_target_type = %s,
                    cta_target_ref = %s,
                    media_asset_id = %s,
                    sort_order = %s,
                    status = %s,
                    starts_at = %s,
                    ends_at = %s,
                    updated_by = %s,
                    updated_at = NOW()
                WHERE site_code = %s
                  AND slot_key = %s
                RETURNING
                    id,
                    site_code,
                    slot_key,
                    title,
                    subtitle,
                    cta_label,
                    cta_target_type,
                    cta_target_ref,
                    media_asset_id,
                    sort_order,
                    status,
                    starts_at,
                    ends_at,
                    created_by,
                    updated_by,
                    created_at,
                    updated_at
                """,
                (
                    normalized_payload["title"],
                    normalized_payload["subtitle"],
                    normalized_payload["cta_label"],
                    normalized_payload["cta_target_type"],
                    normalized_payload["cta_target_ref"],
                    normalized_payload["media_asset_id"],
                    normalized_payload["sort_order"],
                    normalized_payload["status"],
                    normalized_payload["starts_at"],
                    normalized_payload["ends_at"],
                    admin_user_id,
                    normalized_site_code,
                    normalized_slot_key,
                ),
            )
            after_row = cursor.fetchone()
            before = _slot_audit_state(before_row)
            after = _slot_audit_state(after_row)
            _record_slot_audit_entries(
                cursor=cursor,
                admin_user_id=admin_user_id,
                before=before,
                after=after,
            )

    return _serialize_slot(after_row)


def list_site_assets(
    *,
    site_code: str,
    asset_kind: str = SITE_ASSET_KIND_HOMEPAGE_BANNER,
) -> list[dict[str, object]]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_asset_kind = _normalize_site_asset_kind(asset_kind)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")

            cursor.execute(
                """
                SELECT
                    id,
                    site_code,
                    asset_kind,
                    file_path,
                    public_url,
                    mime,
                    byte_size,
                    checksum_sha256,
                    uploaded_by_admin_user_id,
                    created_at,
                    status
                FROM site_assets
                WHERE site_code = %s
                  AND asset_kind = %s
                  AND status = 'active'
                ORDER BY created_at DESC, id DESC
                """,
                (normalized_site_code, normalized_asset_kind),
            )
            rows = list(cursor.fetchall())

    return [_serialize_site_asset(row) for row in rows]


def upload_site_asset(
    upload: SiteAssetUpload,
    *,
    storage: AssetStorage | None = None,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(upload.site_code, "Site code is required")
    normalized_asset_kind = _normalize_site_asset_kind(upload.asset_kind)
    mime = _normalize_site_asset_mime(upload.mime)
    _validate_site_asset_payload(
        asset_kind=normalized_asset_kind,
        mime=mime,
        content=upload.content,
    )
    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")

    checksum = hashlib.sha256(upload.content).hexdigest()
    extension = _site_asset_extension_for_mime(mime)
    relative_path = _build_site_asset_relative_path(
        site_code=normalized_site_code,
        asset_kind=normalized_asset_kind,
        checksum=checksum,
        extension=extension,
    )
    public_url = _build_site_asset_public_url(
        site_code=normalized_site_code,
        asset_kind=normalized_asset_kind,
        checksum=checksum,
        extension=extension,
    )
    asset_storage = storage or FilesystemAssetStorage(settings.asset_storage_root)
    asset_storage.write_if_missing(relative_path=relative_path, content=upload.content)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM site_assets
                WHERE site_code = %s
                  AND asset_kind = %s
                  AND checksum_sha256 = %s
                """,
                (normalized_site_code, normalized_asset_kind, checksum),
            )
            existing_row = cursor.fetchone()
            if existing_row is not None:
                cursor.execute(
                    """
                    UPDATE site_assets
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
                        site_code,
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
                        existing_row["id"],
                    ),
                )
                row = cursor.fetchone()
            else:
                cursor.execute(
                    """
                    INSERT INTO site_assets (
                        site_code,
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
                        site_code,
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
                        normalized_site_code,
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
                _record_site_asset_audit_entry(
                    cursor=cursor,
                    admin_user_id=upload.uploaded_by_admin_user_id,
                    action_kind=AUDIT_ACTION_SITE_ASSET_UPLOAD,
                    row=row,
                )

    if row is None:
        raise SiteCmsValidationError("Site asset upload failed")
    return _serialize_site_asset(row)


def delete_site_asset(
    *,
    site_code: str,
    asset_id: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required")
    normalized_asset_id = _normalize_uuid(asset_id, "Site asset id is invalid")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            site = _load_site(cursor=cursor, site_code=normalized_site_code)
            if site is None:
                raise SiteCmsNotFoundError("Site not found")

            cursor.execute(
                """
                UPDATE site_assets
                SET status = 'deleted'
                WHERE id = %s
                  AND site_code = %s
                  AND status = 'active'
                RETURNING
                    id,
                    site_code,
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
                (normalized_asset_id, normalized_site_code),
            )
            row = cursor.fetchone()
            if row is None:
                raise SiteCmsNotFoundError("Active site asset not found")

            cursor.execute(
                """
                UPDATE site_home_slots
                SET media_asset_id = NULL,
                    updated_by = %s,
                    updated_at = NOW()
                WHERE site_code = %s
                  AND media_asset_id = %s
                """,
                (admin_user_id, normalized_site_code, normalized_asset_id),
            )
            _record_site_asset_audit_entry(
                cursor=cursor,
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_SITE_ASSET_DELETE,
                row=row,
            )

    return _serialize_site_asset(row)


def _load_site(*, cursor, site_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT site_code, display_name, status, created_at, updated_at
        FROM sites
        WHERE site_code = %s
        """,
        (site_code,),
    )
    return cursor.fetchone()


def _load_slot(*, cursor, site_code: str, slot_key: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            shs.id,
            shs.site_code,
            shs.slot_key,
            shs.title,
            shs.subtitle,
            shs.cta_label,
            shs.cta_target_type,
            shs.cta_target_ref,
            shs.media_asset_id,
            shs.sort_order,
            shs.status,
            shs.starts_at,
            shs.ends_at,
            shs.created_by,
            shs.updated_by,
            shs.created_at,
            shs.updated_at,
            sa.asset_kind AS media_asset_kind,
            sa.public_url AS media_asset_public_url,
            sa.mime AS media_asset_mime,
            sa.byte_size AS media_asset_byte_size,
            sa.checksum_sha256 AS media_asset_checksum_sha256,
            sa.created_at AS media_asset_created_at,
            sa.status AS media_asset_status
        FROM site_home_slots shs
        LEFT JOIN site_assets sa
          ON sa.id = shs.media_asset_id
         AND sa.status = 'active'
        WHERE shs.site_code = %s
          AND shs.slot_key = %s
        """,
        (site_code, slot_key),
    )
    return cursor.fetchone()


def _validate_media_asset(*, cursor, site_code: str, media_asset_id: object) -> None:
    if media_asset_id is None:
        return
    normalized_media_asset_id = _normalize_uuid(media_asset_id, "Media asset id is invalid")
    cursor.execute(
        """
        SELECT id
        FROM site_assets
        WHERE id = %s
          AND site_code = %s
          AND asset_kind = %s
          AND status = 'active'
        """,
        (normalized_media_asset_id, site_code, SITE_ASSET_KIND_HOMEPAGE_BANNER),
    )
    if cursor.fetchone() is None:
        raise SiteCmsValidationError("Media asset is not active")


def _validate_target(
    *,
    cursor,
    site_code: str,
    target_type: str,
    target_ref: object,
) -> None:
    if target_type == "none":
        if target_ref is not None:
            raise SiteCmsValidationError("Target ref must be empty when target type is none")
        return

    normalized_target_ref = _normalize_code(str(target_ref or ""), "Target title is required")
    cursor.execute(
        """
        SELECT
            s.status AS site_status,
            gt.status AS title_status,
            gt.is_master,
            ge.status AS engine_status,
            st.status AS site_title_status,
            st.lobby_visibility,
            st.demo_enabled,
            st.real_enabled
        FROM site_titles st
        JOIN sites s ON s.site_code = st.site_code
        JOIN game_titles gt ON gt.title_code = st.title_code
        JOIN game_engines ge ON ge.engine_code = gt.engine_code
        WHERE st.site_code = %s
          AND st.title_code = %s
        """,
        (site_code, normalized_target_ref),
    )
    row = cursor.fetchone()
    if row is None:
        raise SiteCmsValidationError("Target title is not published on this site")
    if row["site_status"] != "active":
        raise SiteCmsValidationError("Site is not active")
    if row["title_status"] != "active":
        raise SiteCmsValidationError("Target title is not active")
    if row["is_master"] is True:
        raise SiteCmsValidationError("Target title cannot be a master title")
    if row["engine_status"] != "active":
        raise SiteCmsValidationError("Target title engine is not active")
    if row["site_title_status"] != "active":
        raise SiteCmsValidationError("Target title is not active on this site")
    if row["lobby_visibility"] != "visible":
        raise SiteCmsValidationError("Target title is not visible in the site lobby")
    if target_type == "title_demo" and row["demo_enabled"] is not True:
        raise SiteCmsValidationError("Target title is not demo-enabled")
    if target_type == "title_real" and row["real_enabled"] is not True:
        raise SiteCmsValidationError("Target title is not real-enabled")


def _normalize_slot_payload(
    *,
    slot_key: str,
    title: str,
    subtitle: str | None,
    cta_label: str | None,
    cta_target_type: str,
    cta_target_ref: object,
    media_asset_id: object,
    sort_order: int,
    status: str,
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> dict[str, object]:
    normalized_target_type = _normalize_choice(
        cta_target_type,
        allowed=ALLOWED_TARGET_TYPES,
        message="Target type is invalid",
    )
    normalized_target_ref = (
        None
        if normalized_target_type == "none"
        else _normalize_code(str(cta_target_ref or ""), "Target title is required")
    )
    normalized_starts_at = _normalize_datetime(starts_at, "Starts at is invalid")
    normalized_ends_at = _normalize_datetime(ends_at, "Ends at is invalid")
    if (
        normalized_starts_at is not None
        and normalized_ends_at is not None
        and normalized_starts_at >= normalized_ends_at
    ):
        raise SiteCmsValidationError("Starts at must be earlier than ends at")

    return {
        "slot_key": _normalize_slot_key(slot_key),
        "title": _normalize_text(title, "Title is required", 160),
        "subtitle": _normalize_optional_text(subtitle, "Subtitle is too long", 500),
        "cta_label": _normalize_optional_text(cta_label, "CTA label is too long", 80),
        "cta_target_type": normalized_target_type,
        "cta_target_ref": normalized_target_ref,
        "media_asset_id": (
            None
            if media_asset_id is None
            else _normalize_uuid(media_asset_id, "Media asset id is invalid")
        ),
        "sort_order": _normalize_non_negative_int(sort_order, "Sort order must be greater than or equal to zero"),
        "status": _normalize_choice(status, allowed=ALLOWED_STATUSES, message="Status is invalid"),
        "starts_at": normalized_starts_at,
        "ends_at": normalized_ends_at,
    }


def _normalize_code(raw_value: str, message: str) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError(message)
    normalized = raw_value.strip().lower()
    if not normalized:
        raise SiteCmsValidationError(message)
    return normalized


def _normalize_slot_key(raw_value: str) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError("Slot key is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise SiteCmsValidationError("Slot key is required")
    if len(normalized) > 64:
        raise SiteCmsValidationError("Slot key is too long")
    if not normalized[0].isalnum() or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in normalized):
        raise SiteCmsValidationError("Slot key must use lowercase letters, numbers, underscores or dashes")
    if len(normalized) < 2:
        raise SiteCmsValidationError("Slot key is too short")
    return normalized


def _normalize_text(raw_value: str, message: str, max_length: int) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError(message)
    normalized = raw_value.strip()
    if not normalized:
        raise SiteCmsValidationError(message)
    if len(normalized) > max_length:
        raise SiteCmsValidationError(message if "too long" in message else "Title is too long")
    return normalized


def _normalize_optional_text(raw_value: str | None, message: str, max_length: int) -> str | None:
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError(message)
    normalized = raw_value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise SiteCmsValidationError(message)
    return normalized


def _normalize_choice(raw_value: str, *, allowed: frozenset[str], message: str) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError(message)
    normalized = raw_value.strip().lower()
    if normalized not in allowed:
        raise SiteCmsValidationError(message)
    return normalized


def _normalize_non_negative_int(raw_value: int, message: str) -> int:
    try:
        normalized = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise SiteCmsValidationError("Sort order must be an integer") from exc
    if normalized < 0:
        raise SiteCmsValidationError(message)
    return normalized


def _normalize_uuid(raw_value: object, message: str) -> str:
    try:
        return str(UUID(str(raw_value)))
    except (TypeError, ValueError) as exc:
        raise SiteCmsValidationError(message) from exc


def _normalize_datetime(raw_value: datetime | None, message: str) -> datetime | None:
    if raw_value is None:
        return None
    if not isinstance(raw_value, datetime):
        raise SiteCmsValidationError(message)
    if raw_value.tzinfo is None:
        return raw_value.replace(tzinfo=UTC)
    return raw_value.astimezone(UTC)


def _normalize_site_asset_kind(raw_value: str) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError("Site asset kind is invalid")
    normalized = raw_value.strip().lower()
    if normalized not in ALLOWED_SITE_ASSET_KINDS:
        raise SiteCmsValidationError("Unsupported site asset kind")
    return normalized


def _normalize_site_asset_mime(raw_value: str) -> str:
    if not isinstance(raw_value, str):
        raise SiteCmsValidationError("Site asset MIME type is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise SiteCmsValidationError("Site asset MIME type is required")
    return normalized


def _validate_site_asset_payload(*, asset_kind: str, mime: str, content: bytes) -> None:
    if not content:
        raise SiteCmsValidationError("Site asset file is empty")
    if asset_kind != SITE_ASSET_KIND_HOMEPAGE_BANNER:
        raise SiteCmsValidationError("Site asset kind is not uploadable")
    if mime not in SITE_IMAGE_MIME_EXTENSIONS:
        raise SiteCmsValidationError("Site asset MIME type is not supported")
    if len(content) > MAX_SITE_IMAGE_BYTES:
        raise SiteCmsValidationError("Site asset file is too large")


def _site_asset_extension_for_mime(mime: str) -> str:
    try:
        return SITE_IMAGE_MIME_EXTENSIONS[mime]
    except KeyError as exc:
        raise SiteCmsValidationError("Site asset MIME type is not supported") from exc


def _build_site_asset_relative_path(
    *,
    site_code: str,
    asset_kind: str,
    checksum: str,
    extension: str,
) -> str:
    return f"sites/{site_code}/{asset_kind}/{checksum[:8]}.{extension}"


def _build_site_asset_public_url(
    *,
    site_code: str,
    asset_kind: str,
    checksum: str,
    extension: str,
) -> str:
    return f"/static/sites/{site_code}/{asset_kind}/{checksum[:8]}.{extension}"


def _serialize_site(row: dict[str, object]) -> dict[str, object]:
    return {
        "site_code": row["site_code"],
        "display_name": row["display_name"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _serialize_site_asset(row: DictRow | dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "site_code": row["site_code"],
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


def _serialize_slot_media_asset(row: DictRow | dict[str, object]) -> dict[str, object] | None:
    if row["media_asset_id"] is None:
        return None
    if not _row_has_key(row, "media_asset_public_url") or row["media_asset_public_url"] is None:
        return None
    return {
        "id": str(row["media_asset_id"]),
        "site_code": row["site_code"],
        "asset_kind": row["media_asset_kind"],
        "public_url": row["media_asset_public_url"],
        "mime": row["media_asset_mime"],
        "byte_size": row["media_asset_byte_size"],
        "checksum_sha256": row["media_asset_checksum_sha256"],
        "created_at": row["media_asset_created_at"].isoformat(),
        "status": row["media_asset_status"],
    }


def _row_has_key(row: DictRow | dict[str, object], key: str) -> bool:
    try:
        row[key]
    except KeyError:
        return False
    return True


def _serialize_slot(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "site_code": row["site_code"],
        "slot_key": row["slot_key"],
        "title": row["title"],
        "subtitle": row["subtitle"],
        "cta_label": row["cta_label"],
        "cta_target_type": row["cta_target_type"],
        "cta_target_ref": row["cta_target_ref"],
        "media_asset_id": str(row["media_asset_id"]) if row["media_asset_id"] is not None else None,
        "sort_order": row["sort_order"],
        "status": row["status"],
        "starts_at": row["starts_at"].isoformat() if row["starts_at"] is not None else None,
        "ends_at": row["ends_at"].isoformat() if row["ends_at"] is not None else None,
        "created_by": str(row["created_by"]) if row["created_by"] is not None else None,
        "updated_by": str(row["updated_by"]) if row["updated_by"] is not None else None,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "media_asset": _serialize_slot_media_asset(row),
    }


def _serialize_public_slot(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "site_code": row["site_code"],
        "slot_key": row["slot_key"],
        "title": row["title"],
        "subtitle": row["subtitle"],
        "cta_label": row["cta_label"],
        "cta_target_type": row["cta_target_type"],
        "cta_target_ref": row["cta_target_ref"],
        "media_asset_id": str(row["media_asset_id"]) if row["media_asset_id"] is not None else None,
        "media_asset": _serialize_slot_media_asset(row),
        "sort_order": row["sort_order"],
    }


def _empty_slot_audit_state() -> dict[str, object]:
    return {
        "site_code": None,
        "slot_key": None,
        **{field_name: None for field_name in SLOT_AUDIT_FIELDS},
    }


def _slot_audit_state(row: dict[str, object]) -> dict[str, object]:
    serialized = _serialize_slot(row)
    return {
        "site_code": serialized["site_code"],
        "slot_key": serialized["slot_key"],
        **{field_name: serialized[field_name] for field_name in SLOT_AUDIT_FIELDS},
    }


def _record_slot_audit_entries(
    *,
    cursor,
    admin_user_id: str,
    before: dict[str, object],
    after: dict[str, object],
) -> None:
    changed_fields = [
        field_name
        for field_name in SLOT_AUDIT_FIELDS
        if before.get(field_name) != after.get(field_name)
    ]
    if not changed_fields:
        return

    site_code = str(after["site_code"])
    slot_key = str(after["slot_key"])
    resource_id = _build_slot_resource_id(site_code=site_code, slot_key=slot_key)
    payload = _build_slot_audit_payload(
        site_code=site_code,
        slot_key=slot_key,
        changed_fields=changed_fields,
        before=before,
        after=after,
    )
    _record_slot_audit_entry(
        cursor=cursor,
        admin_user_id=admin_user_id,
        action_kind=AUDIT_ACTION_SITE_HOME_SLOT_UPDATE,
        resource_id=resource_id,
        payload=payload,
    )
    if before.get("status") != "published" and after.get("status") == "published":
        _record_slot_audit_entry(
            cursor=cursor,
            admin_user_id=admin_user_id,
            action_kind=AUDIT_ACTION_SITE_HOME_SLOT_PUBLISH,
            resource_id=resource_id,
            payload=payload,
        )


def _record_slot_audit_entry(
    *,
    cursor,
    admin_user_id: str,
    action_kind: str,
    resource_id: str,
    payload: dict[str, object],
) -> None:
    record_audit_entry(
        admin_user_id=admin_user_id,
        action_kind=action_kind,
        resource_kind=AUDIT_RESOURCE_SITE_HOME_SLOT,
        resource_id=resource_id,
        payload=payload,
        request_fingerprint=build_audit_request_fingerprint(
            action_kind=action_kind,
            resource_kind=AUDIT_RESOURCE_SITE_HOME_SLOT,
            resource_id=resource_id,
            payload=payload,
        ),
        cursor=cursor,
    )


def _record_site_asset_audit_entry(
    *,
    cursor,
    admin_user_id: str,
    action_kind: str,
    row: DictRow | dict[str, object],
) -> None:
    compact_asset = _compact_site_asset_for_audit(row)
    resource_id = _build_site_asset_resource_id(
        site_code=str(row["site_code"]),
        asset_id=str(row["id"]),
    )
    payload = {
        "site_code": row["site_code"],
        "asset_kind": row["asset_kind"],
        "asset": compact_asset,
    }
    record_audit_entry(
        admin_user_id=admin_user_id,
        action_kind=action_kind,
        resource_kind=AUDIT_RESOURCE_SITE_ASSET,
        resource_id=resource_id,
        payload=payload,
        request_fingerprint=build_audit_request_fingerprint(
            action_kind=action_kind,
            resource_kind=AUDIT_RESOURCE_SITE_ASSET,
            resource_id=resource_id,
            payload=payload,
        ),
        cursor=cursor,
    )


def _build_site_asset_resource_id(*, site_code: str, asset_id: str) -> str:
    return f"{site_code}:{asset_id}"


def _compact_site_asset_for_audit(row: DictRow | dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "asset_kind": row["asset_kind"],
        "mime": row["mime"],
        "byte_size": row["byte_size"],
        "checksum_sha256": row["checksum_sha256"],
        "public_url": row["public_url"],
        "status": row["status"],
    }


def _build_slot_audit_payload(
    *,
    site_code: str,
    slot_key: str,
    changed_fields: list[str],
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        "site_code": site_code,
        "slot_key": slot_key,
        "changed_fields": changed_fields,
        "before": {field_name: before.get(field_name) for field_name in SLOT_AUDIT_FIELDS},
        "after": {field_name: after.get(field_name) for field_name in SLOT_AUDIT_FIELDS},
    }


def _build_slot_resource_id(*, site_code: str, slot_key: str) -> str:
    return f"{site_code}:{slot_key}"
