from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import require_admin_area
from app.api.responses import envelope
from app.modules.platform.site_v3.service import (
    archive_page,
    get_admin_page,
    list_admin_pages,
    list_page_versions,
    publish_page,
    save_draft,
    validate_draft_payload,
)
from app.modules.platform.site_v3.module_definitions import (
    archive_custom_module_definition,
    create_custom_module_definition,
    get_custom_module_definition,
    list_custom_module_definitions,
    publish_custom_module_definition,
    update_custom_module_definition_draft,
    validate_custom_module_definition_payload,
)
from app.modules.platform.site_v3.preview_service import issue_draft_preview_token


router = APIRouter(prefix="/admin/site-v3", tags=["site-v3-admin"])


class SiteV3ModulePayload(BaseModel):
    id: str | None = None
    client_id: str | None = None
    module_code: str
    schema_version: int = 1
    slot_key: str = "main"
    sort_order: int = 0
    config_json: dict[str, Any] = Field(default_factory=dict)


class SiteV3DraftPayload(BaseModel):
    locale: str = "it"
    title: str
    expected_draft_version: int | None = None
    modules: list[SiteV3ModulePayload] = Field(default_factory=list)


class SiteV3ValidatePayload(BaseModel):
    locale: str = "it"
    title: str
    modules: list[SiteV3ModulePayload] = Field(default_factory=list)


class SiteV3PublishPayload(BaseModel):
    locale: str = "it"
    expected_draft_version: int | None = None


class SiteV3ArchivePayload(BaseModel):
    locale: str = "it"


class SiteV3ModuleDefinitionFieldPayload(BaseModel):
    key: str
    label: str
    type: str
    group: str | None = None
    required: bool = False
    max_length: int | None = None
    max_items: int | None = None
    help: str | None = None


class SiteV3ModuleDefinitionPayload(BaseModel):
    module_code: str
    label: str
    category: str
    renderer_template: str
    field_schema_json: list[SiteV3ModuleDefinitionFieldPayload] = Field(default_factory=list)
    default_config_json: dict[str, Any] = Field(default_factory=dict)


@router.get("/sites/{site_code}/pages")
def get_site_v3_pages(
    site_code: str,
    locale: str = Query(default="it"),
    status: str = Query(default="all"),
    page: int = Query(default=1),
    limit: int = Query(default=50),
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        list_admin_pages(
            site_code=site_code,
            locale=locale,
            status_filter=status,
            page=page,
            limit=limit,
        )
    )


@router.get("/sites/{site_code}/pages/{page_code}")
def get_site_v3_page(
    site_code: str,
    page_code: str,
    locale: str = Query(default="it"),
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(get_admin_page(site_code=site_code, page_code=page_code, locale=locale))


@router.put("/sites/{site_code}/pages/{page_code}/draft")
def put_site_v3_page_draft(
    site_code: str,
    page_code: str,
    payload: SiteV3DraftPayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        save_draft(
            site_code=site_code,
            page_code=page_code,
            locale=payload.locale,
            title=payload.title,
            expected_draft_version=payload.expected_draft_version,
            modules=[module.model_dump() for module in payload.modules],
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.post("/sites/{site_code}/pages/{page_code}/validate")
def post_site_v3_page_validate(
    site_code: str,
    page_code: str,
    payload: SiteV3ValidatePayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        validate_draft_payload(
            site_code=site_code,
            page_code=page_code,
            locale=payload.locale,
            title=payload.title,
            modules=[module.model_dump() for module in payload.modules],
            admin_user_id=str(current_admin["id"]),
            record_audit=True,
        )
    )


@router.post("/sites/{site_code}/pages/{page_code}/publish")
def post_site_v3_page_publish(
    site_code: str,
    page_code: str,
    payload: SiteV3PublishPayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        publish_page(
            site_code=site_code,
            page_code=page_code,
            locale=payload.locale,
            expected_draft_version=payload.expected_draft_version,
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.post("/sites/{site_code}/pages/{page_code}/archive")
def post_site_v3_page_archive(
    site_code: str,
    page_code: str,
    payload: SiteV3ArchivePayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        archive_page(
            site_code=site_code,
            page_code=page_code,
            locale=payload.locale,
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.get("/sites/{site_code}/pages/{page_code}/versions")
def get_site_v3_page_versions(
    site_code: str,
    page_code: str,
    locale: str = Query(default="it"),
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(list_page_versions(site_code=site_code, page_code=page_code, locale=locale))


@router.get("/sites/{site_code}/module-definitions")
def get_site_v3_module_definitions(
    site_code: str,
    status: str = Query(default="all"),
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(list_custom_module_definitions(site_code=site_code, status_filter=status))


@router.post("/sites/{site_code}/module-definitions")
def post_site_v3_module_definition(
    site_code: str,
    payload: SiteV3ModuleDefinitionPayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        create_custom_module_definition(
            site_code=site_code,
            payload=payload.model_dump(),
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.get("/sites/{site_code}/module-definitions/{module_code}")
def get_site_v3_module_definition(
    site_code: str,
    module_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(get_custom_module_definition(site_code=site_code, module_code=module_code))


@router.put("/sites/{site_code}/module-definitions/{module_code}/draft")
def put_site_v3_module_definition_draft(
    site_code: str,
    module_code: str,
    payload: SiteV3ModuleDefinitionPayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        update_custom_module_definition_draft(
            site_code=site_code,
            module_code=module_code,
            payload=payload.model_dump(),
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.post("/sites/{site_code}/module-definitions/{module_code}/validate")
def post_site_v3_module_definition_validate(
    site_code: str,
    module_code: str,
    payload: SiteV3ModuleDefinitionPayload,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    del site_code
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(validate_custom_module_definition_payload(payload={**payload.model_dump(), "module_code": module_code}))


@router.post("/sites/{site_code}/module-definitions/{module_code}/publish")
def post_site_v3_module_definition_publish(
    site_code: str,
    module_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        publish_custom_module_definition(
            site_code=site_code,
            module_code=module_code,
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.post("/sites/{site_code}/module-definitions/{module_code}/archive")
def post_site_v3_module_definition_archive(
    site_code: str,
    module_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        archive_custom_module_definition(
            site_code=site_code,
            module_code=module_code,
            admin_user_id=str(current_admin["id"]),
        )
    )


@router.post("/sites/{site_code}/pages/{page_code}/draft-preview-token")
def post_site_v3_draft_preview_token(
    site_code: str,
    page_code: str,
    locale: str = Query(default="it"),
    current_admin: dict[str, object] | object = Depends(require_admin_area("games")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    return envelope(
        issue_draft_preview_token(
            site_code=site_code,
            page_code=page_code,
            locale=locale,
            admin_user_id=str(current_admin["id"]),
        )
    )
