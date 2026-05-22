"""Conversational Analytics API — Ask Data (with streaming)."""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.ask_data_service import AskDataService
from app.ai.llm import llm_service
from app.data.mongo import log_ai_output

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


@router.post("/ask_stream")
async def ask_stream(req: AskRequest):
    """SSE streaming endpoint. Emits:
      event: meta   {retrieved: [...]}
      event: delta  {text}
      event: done   {provider, model, latency_ms, audit_id}
    """
    svc = AskDataService()
    payload = await svc.build_stream_payload(req.question, history=req.history)

    async def event_gen():
        import time
        yield f"event: meta\ndata: {json.dumps({'retrieved': payload['retrieved']})}\n\n"
        full = []
        t0 = time.time()
        used_provider = None
        try:
            async for chunk in llm_service.stream(messages=payload["messages"], system=payload["system"], max_tokens=1100):
                if chunk.get("type") == "delta":
                    full.append(chunk["text"])
                    used_provider = chunk.get("provider")
                    yield f"event: delta\ndata: {json.dumps({'text': chunk['text']})}\n\n"
                elif chunk.get("type") == "error":
                    yield f"event: error\ndata: {json.dumps({'message': chunk.get('text')})}\n\n"
                    return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            return

        full_text = "".join(full)
        latency_ms = int((time.time() - t0) * 1000)
        audit_id = None
        try:
            audit_id = await log_ai_output(
                "chat_stream", {"question": req.question, "answer_markdown": full_text,
                                "retrieved_sources": payload["retrieved"]},
                question=req.question, provider=used_provider, latency_ms=latency_ms,
                citations=[s["source_id"] for s in payload["retrieved"]],
            )
        except Exception:
            pass
        yield f"event: done\ndata: {json.dumps({'provider': used_provider, 'latency_ms': latency_ms, 'audit_id': audit_id, 'sources': len(payload['retrieved'])})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


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
