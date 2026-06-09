from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_admin
from app.db.connection import db_connection
from app.modules.platform.cms_v2.service import CMSV2Service, PageDraft
from app.api.responses import envelope

router = APIRouter(prefix="/admin/cms-v2", tags=["cms-v2"])

@router.get("/sites/{site_code}/pages")
async def list_pages(site_code: str, admin = Depends(get_current_admin)):
    pages = await CMSV2Service.list_pages(site_code)
    return envelope(pages)

@router.get("/sites/{site_code}/pages/{page_code}")
async def get_page(site_code: str, page_code: str, admin = Depends(get_current_admin)):
    page = await CMSV2Service.get_page_by_code(site_code, page_code)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return envelope(page.model_dump())

@router.put("/sites/{site_code}/pages/{page_code}")
async def save_page(site_code: str, page_code: str, draft: PageDraft, admin = Depends(get_current_admin)):
    if draft.site_code != site_code or draft.page_code != page_code:
        raise HTTPException(status_code=400, detail="Mismatched site or page code")
    
    page_id = await CMSV2Service.upsert_page_draft(draft, admin["id"])
    return envelope({"id": str(page_id), "status": "saved"})

@router.post("/sites/{site_code}/pages/{page_code}/publish")
async def publish_page(site_code: str, page_code: str, admin = Depends(get_current_admin)):
    # 1. Verify page exists
    page = await CMSV2Service.get_page_by_code(site_code, page_code)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # 2. Update status to 'published'
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE cms_v2_pages SET status = 'published', updated_by = %s, updated_at = NOW() WHERE id = %s",
                (admin["id"], page.id)
            )
    
    return envelope({"id": str(page.id), "status": "published"})

@router.delete("/sites/{site_code}/pages/{page_id}")
async def delete_page(site_code: str, page_id: UUID, admin = Depends(get_current_admin)):
    await CMSV2Service.delete_page(page_id)
    return envelope({"status": "deleted"})

@router.get("/sites/{site_code}/pages/{page_code}/public")
async def get_public_page(site_code: str, page_code: str):
    # Public endpoint for the player site
    # For now, it just returns the page if it's published.
    # In the lab phase, we might allow reading drafts for preview.
    page = await CMSV2Service.get_page_by_code(site_code, page_code)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Optional: logic to only show 'published' status to real players
    return envelope(page)
