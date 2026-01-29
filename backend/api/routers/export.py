from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from mdcore.exporters.notion.exporter import NotionExporter
from api.services.notion import NotionClient

router = APIRouter()

class ExportNotionRequest(BaseModel):
    markdown: str
    token: str
    page_id: str

@router.post("/notion")
async def export_to_notion(request: ExportNotionRequest):
    """
    Export Markdown content to a Notion Page.
    """
    # 1. Convert Markdown to Blocks
    exporter = NotionExporter()
    try:
        blocks = exporter.export(request.markdown)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse markdown: {str(e)}")

    if not blocks:
        raise HTTPException(status_code=400, detail="No content to export")

    # 2. Send to Notion
    client = NotionClient(token=request.token)
    
    # Validate page first? (Optional, skip for speed)
    # await client.validate_page(request.page_id)
    
    try:
        result = await client.append_blocks(request.page_id, blocks)
        return {"success": True, "count": len(blocks)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Notion API Error: {str(e)}")
