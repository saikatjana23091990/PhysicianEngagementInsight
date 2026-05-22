"""Audit log + AI output history API."""
from typing import Optional
from fastapi import APIRouter, Query

from app.data.mongo import list_ai_outputs, list_audit_logs

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/ai_outputs")
async def ai_outputs(type: Optional[str] = None, hcp_id: Optional[str] = None, limit: int = 50):
    items = await list_ai_outputs(type_=type, hcp_id=hcp_id, limit=limit)
    return {"total": len(items), "items": items}


@router.get("/logs")
async def logs(category: Optional[str] = None, subject_id: Optional[str] = None, limit: int = 100):
    items = await list_audit_logs(category=category, subject_id=subject_id, limit=limit)
    return {"total": len(items), "items": items}
