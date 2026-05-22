"""
MongoDB async client + persistence helpers.

Collections:
- ai_outputs: every AI response (briefing, narrative, chat) with full context
- audit_logs: structured audit events (conversion attribution snapshots, user actions)
- rag_chunks: vector store backing the RAG layer (Atlas Vector Search compatible)

Atlas Vector Search compatibility:
The rag_chunks documents follow the schema Atlas expects, with a top-level `embedding`
array. On Atlas, create an index:

    {
      "fields": [
        {"type": "vector", "path": "embedding", "numDimensions": 256, "similarity": "cosine"}
      ]
    }

Locally we cosine-search in Python over a Mongo cursor — same API, same data layout.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger("app.mongo")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def get_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is None:
        url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        name = os.environ.get("DB_NAME", "commercial_analytics")
        _client = AsyncIOMotorClient(url)
        _db = _client[name]
        logger.info("Connected to Mongo db=%s", name)
    return _db


async def ensure_indexes() -> None:
    db = get_db()
    await db.ai_outputs.create_index([("type", 1), ("created_at", -1)])
    await db.ai_outputs.create_index([("hcp_id", 1)])
    # TTL: auto-expire AI outputs after 90 days (created_at is ISO string — Mongo's TTL needs Date,
    # so we add a parallel `created_at_dt` BSON date for the TTL only)
    await db.ai_outputs.create_index([("created_at_dt", 1)], expireAfterSeconds=90 * 24 * 3600)
    await db.audit_logs.create_index([("category", 1), ("created_at", -1)])
    await db.audit_logs.create_index([("subject_id", 1)])
    await db.audit_logs.create_index([("created_at_dt", 1)], expireAfterSeconds=365 * 24 * 3600)
    await db.rag_chunks.create_index([("source_type", 1), ("hcp_id", 1)])
    await db.rag_chunks.create_index([("source_id", 1)], unique=False)
    logger.info("Mongo indexes ensured.")


# ---------------- AI output persistence ----------------
async def log_ai_output(
    type_: str,
    payload: dict,
    *,
    hcp_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    latency_ms: Optional[int] = None,
    fallback_used: Optional[bool] = None,
    question: Optional[str] = None,
    citations: Optional[list] = None,
) -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    doc = {
        "type": type_,
        "hcp_id": hcp_id,
        "question": question,
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "fallback_used": fallback_used,
        "citations": citations or [],
        "payload": payload,
        "created_at": now.isoformat(),
        "created_at_dt": now,  # for TTL index
    }
    db = get_db()
    res = await db.ai_outputs.insert_one(doc)
    return str(res.inserted_id)


async def log_audit(category: str, subject_id: str, action: str, detail: dict) -> str:
    from datetime import datetime, timezone
    db = get_db()
    res = await db.audit_logs.insert_one({
        "category": category,
        "subject_id": subject_id,
        "action": action,
        "detail": detail,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return str(res.inserted_id)


async def list_ai_outputs(type_: Optional[str] = None, hcp_id: Optional[str] = None, limit: int = 50,
                          include_payload: bool = False) -> list:
    """List AI outputs. Payload is omitted by default to keep responses small;
    set include_payload=True to fetch full markdown bodies."""
    db = get_db()
    q: dict = {}
    if type_:
        q["type"] = type_
    if hcp_id:
        q["hcp_id"] = hcp_id
    projection = {"_id": 0, "created_at_dt": 0}
    if not include_payload:
        projection["payload"] = 0
    cur = db.ai_outputs.find(q, projection).sort("created_at", -1).limit(limit)
    items = [doc async for doc in cur]
    if not include_payload:
        # Attach a short answer preview from payload without re-hydrating it.
        # We re-query just the small text snippets when needed.
        ids = []
        full_cur = db.ai_outputs.find(q, {"_id": 0, "payload.answer_markdown": 1,
                                          "payload.brief_markdown": 1,
                                          "payload.narrative_markdown": 1,
                                          "created_at": 1}).sort("created_at", -1).limit(limit)
        async for d in full_cur:
            p = d.get("payload") or {}
            snippet = (p.get("answer_markdown") or p.get("brief_markdown") or p.get("narrative_markdown") or "")
            ids.append((d.get("created_at"), snippet[:280]))
        # zip by created_at to attach
        snippets = {ca: s for ca, s in ids}
        for it in items:
            it["preview"] = snippets.get(it.get("created_at"), "")
    return items


async def list_audit_logs(category: Optional[str] = None, subject_id: Optional[str] = None, limit: int = 100) -> list:
    db = get_db()
    q: dict = {}
    if category:
        q["category"] = category
    if subject_id:
        q["subject_id"] = subject_id
    cur = db.audit_logs.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cur]
