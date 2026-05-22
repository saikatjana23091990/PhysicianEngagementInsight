from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.briefing_service import BriefingService

router = APIRouter(prefix="/briefing", tags=["briefing"])


class BriefRequest(BaseModel):
    hcp_id: str


@router.post("/generate")
async def generate(req: BriefRequest):
    svc = BriefingService()
    out = await svc.generate_brief(req.hcp_id)
    if out.get("error"):
        raise HTTPException(404, out["error"])
    return out


@router.get("/context/{hcp_id}")
def context(hcp_id: str):
    svc = BriefingService()
    ctx = svc.assemble_context(hcp_id)
    if not ctx:
        raise HTTPException(404, "HCP not found")
    return ctx
