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
    await db.audit_logs.create_index([("category", 1), ("created_at", -1)])
    await db.audit_logs.create_index([("subject_id", 1)])
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
        "created_at": datetime.now(timezone.utc).isoformat(),
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


async def list_ai_outputs(type_: Optional[str] = None, hcp_id: Optional[str] = None, limit: int = 50) -> list:
    db = get_db()
    q: dict = {}
    if type_:
        q["type"] = type_
    if hcp_id:
        q["hcp_id"] = hcp_id
    cur = db.ai_outputs.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cur]


async def list_audit_logs(category: Optional[str] = None, subject_id: Optional[str] = None, limit: int = 100) -> list:
    db = get_db()
    q: dict = {}
    if category:
        q["category"] = category
    if subject_id:
        q["subject_id"] = subject_id
    cur = db.audit_logs.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [doc async for doc in cur]
