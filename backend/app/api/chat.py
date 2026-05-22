"""Conversational Analytics API — Ask Data."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ask_data_service import AskDataService

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    history: Optional[list] = None


@router.post("/ask")
async def ask(req: AskRequest):
    svc = AskDataService()
    try:
        return await svc.ask(req.question, session_id=req.session_id, history=req.history)
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")


@router.get("/suggested")
def suggested():
    return [
        "Why did conversion rates change in oncology last quarter?",
        "Which reps improved conversion most QoQ?",
        "Show the top KOL-driven oncology opportunities.",
        "Which territories are under-performing this month?",
        "What are the most common objections in cardiology calls?",
        "Which HCPs should I prioritize this week?",
    ]
