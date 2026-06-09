import json
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.db.connection import db_connection

class ModuleInstance(BaseModel):
    id: Optional[UUID] = None
    slot_key: str
    module_code: str
    config: dict = Field(default_factory=dict)
    sort_order: int = 0

class PageDraft(BaseModel):
    id: Optional[UUID] = None
    site_code: str
    page_code: str
    title: str
    status: str = "draft"
    modules: List[ModuleInstance] = Field(default_factory=list)

class CMSV2Service:
    @staticmethod
    async def get_page_by_code(site_code: str, page_code: str) -> Optional[PageDraft]:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                # Get page
                cursor.execute(
                    """
                    SELECT id, site_code, page_code, title, status
                    FROM cms_v2_pages
                    WHERE site_code = %s AND page_code = %s
                    """,
                    (site_code, page_code),
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                page_id = row["id"]
                page = PageDraft(
                    id=page_id,
                    site_code=row["site_code"],
                    page_code=row["page_code"],
                    title=row["title"],
                    status=row["status"]
                )
                
                # Get modules
                cursor.execute(
                    """
                    SELECT id, slot_key, module_code, config, sort_order
                    FROM cms_v2_modules
                    WHERE page_id = %s
                    ORDER BY sort_order ASC
                    """,
                    (page_id,),
                )
                for m_row in cursor.fetchall():
                    page.modules.append(ModuleInstance(
                        id=m_row["id"],
                        slot_key=m_row["slot_key"],
                        module_code=m_row["module_code"],
                        config=m_row["config"] if isinstance(m_row["config"], dict) else json.loads(m_row["config"]),
                        sort_order=m_row["sort_order"]
                    ))
                
                return page

    @staticmethod
    async def upsert_page_draft(draft: PageDraft, user_id: UUID) -> UUID:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                # Check if page exists
                cursor.execute(
                    "SELECT id FROM cms_v2_pages WHERE site_code = %s AND page_code = %s",
                    (draft.site_code, draft.page_code),
                )
                existing_page = cursor.fetchone()
                
                if existing_page:
                    page_id = existing_page["id"]
                    # Update page
                    cursor.execute(
                        """
                        UPDATE cms_v2_pages
                        SET title = %s, updated_by = %s, updated_at = NOW()
                        WHERE id = %s
                        RETURNING id
                        """,
                        (draft.title, user_id, page_id),
                    )
                else:
                    # Create page
                    cursor.execute(
                        """
                        INSERT INTO cms_v2_pages (site_code, page_code, title, status, created_by, updated_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (draft.site_code, draft.page_code, draft.title, draft.status, user_id, user_id),
                    )
                    page_id = cursor.fetchone()["id"]
                
                # Sync modules
                cursor.execute("DELETE FROM cms_v2_modules WHERE page_id = %s", (page_id,))
                
                if draft.modules:
                    for i, mod in enumerate(draft.modules):
                        cursor.execute(
                            """
                            INSERT INTO cms_v2_modules (page_id, slot_key, module_code, config, sort_order)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (page_id, mod.slot_key, mod.module_code, json.dumps(mod.config), i),
                        )
                
                return page_id

    @staticmethod
    async def upsert_page(site_code: str, page_code: str, title: str, status: str, user_id: UUID) -> UUID:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM cms_v2_pages WHERE site_code = %s AND page_code = %s",
                    (site_code, page_code),
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE cms_v2_pages SET title = %s, status = %s, updated_by = %s, updated_at = NOW() WHERE id = %s RETURNING id",
                        (title, status, user_id, existing["id"])
                    )
                    return existing["id"]
                else:
                    cursor.execute(
                        "INSERT INTO cms_v2_pages (site_code, page_code, title, status, created_by, updated_by) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                        (site_code, page_code, title, status, user_id, user_id)
                    )
                    return cursor.fetchone()["id"]

    @staticmethod
    async def delete_page(page_id: UUID):
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM cms_v2_modules WHERE page_id = %s", (page_id,))
                cursor.execute("DELETE FROM cms_v2_pages WHERE id = %s", (page_id,))

    @staticmethod
    async def list_pages(site_code: str) -> List[dict]:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, page_code, title, status, updated_at
                    FROM cms_v2_pages
                    WHERE site_code = %s
                    ORDER BY updated_at DESC
                    """,
                    (site_code,),
                )
                return cursor.fetchall()
