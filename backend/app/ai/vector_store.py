"""
Mongo-backed vector store (Atlas Vector Search compatible).

Stored doc shape:
{
  "source_id": "INT00012",
  "source_type": "crm_note",
  "text": "...",
  "hcp_id": "HCP0001",
  "product_id": null,
  "date": "2025-05-12",
  "extra": { ... },
  "embedding": [0.012, -0.34, ...]   # EMBED_DIM=256
}

Search behavior:
- If `USE_ATLAS_VECTOR_SEARCH=1`, uses Mongo Atlas `$vectorSearch` aggregation stage.
- Otherwise, loads embedding matrix in memory and does cosine similarity in numpy.

This dual-mode keeps demo runnable on local Mongo while being one-flag away from Atlas.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Optional

import numpy as np

from app.ai.embeddings import LocalSVDEmbeddings, get_embeddings_provider
from app.data.mongo import get_db
from app.data.store import DataStore

logger = logging.getLogger("app.vector_store")
USE_ATLAS = os.environ.get("USE_ATLAS_VECTOR_SEARCH", "0") == "1"


class VectorStore:
    _instance: Optional["VectorStore"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.provider = get_embeddings_provider()
        self.ids: list[str] = []
        self.matrix: Optional[np.ndarray] = None
        self.meta: list[dict] = []
        self._built = False

    @classmethod
    def instance(cls) -> "VectorStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = VectorStore()
        return cls._instance

    async def build(self) -> int:
        """Materialize chunks → embeddings → Mongo + in-memory matrix."""
        store = DataStore.instance()
        if not store.loaded:
            store.load_all()
        docs: list[dict] = []

        fi = store.df("field_interactions_source")
        for _, r in fi.iterrows():
            note = f"{r.get('crm_note_raw', '')} {r.get('next_step_raw', '')}".strip()
            if not note:
                continue
            docs.append({
                "source_id": r["interaction_id"], "source_type": "crm_note", "text": note,
                "hcp_id": r.get("hcp_id"), "product_id": r.get("product_id"),
                "date": str(r.get("interaction_datetime"))[:10],
                "extra": {"channel": r.get("channel"), "topic": r.get("discussion_topic"),
                          "outcome": r.get("call_outcome"), "rep_id": r.get("rep_id")},
            })
        for _, r in store.df("publication_source").iterrows():
            docs.append({
                "source_id": r["publication_id"], "source_type": "publication",
                "text": f"{r.get('publication_title', '')} {r.get('key_finding_summary', '')}",
                "hcp_id": r.get("hcp_id"), "product_id": None, "date": str(r.get("publication_date"))[:10],
                "extra": {"journal": r.get("journal_name"), "topic": r.get("topic_tag"),
                          "sentiment": r.get("topic_sentiment"), "relevance": r.get("relevance_score")},
            })
        for _, r in store.df("event_source").iterrows():
            docs.append({
                "source_id": r["event_id"], "source_type": "event",
                "text": f"{r.get('event_type', '')} {r.get('topic', '')} {r.get('note_raw', '')}",
                "hcp_id": r.get("hcp_id"), "product_id": None, "date": str(r.get("event_date"))[:10],
                "extra": {"event_type": r.get("event_type"), "engagement": r.get("engagement_score")},
            })
        for _, r in store.df("market_events_source").iterrows():
            docs.append({
                "source_id": r["market_event_id"], "source_type": "market_event",
                "text": f"{r.get('event_type', '')} {r.get('summary_raw', '')}",
                "hcp_id": None, "product_id": r.get("product_id"), "date": str(r.get("event_date"))[:10],
                "extra": {"region": r.get("region"), "severity": r.get("event_severity")},
            })

        if not docs:
            self._built = True
            return 0

        # Fit local embedder if needed
        if isinstance(self.provider, LocalSVDEmbeddings):
            self.provider.fit([d["text"] for d in docs])

        vecs = self.provider.embed([d["text"] for d in docs])
        for d, v in zip(docs, vecs):
            d["embedding"] = v.astype(float).tolist()

        db = get_db()
        await db.rag_chunks.delete_many({})
        await db.rag_chunks.insert_many(docs)
        # in-memory cache
        self.ids = [d["source_id"] for d in docs]
        self.matrix = vecs.astype(np.float32)
        self.meta = [{k: v for k, v in d.items() if k != "embedding"} for d in docs]
        self._built = True
        logger.info("VectorStore built: %s chunks (provider=%s, dim=%s)",
                    len(docs), self.provider.name, vecs.shape[1])
        return len(docs)

    async def search(self, query: str, k: int = 6, filters: Optional[dict] = None) -> list[dict]:
        if not self._built:
            return []
        qv = self.provider.embed([query])[0].astype(np.float32)
        if USE_ATLAS:
            return await self._atlas_search(qv.tolist(), k=k, filters=filters)
        return self._inmem_search(qv, k=k, filters=filters)

    def _inmem_search(self, qv: np.ndarray, k: int, filters: Optional[dict]) -> list[dict]:
        if self.matrix is None or self.matrix.shape[0] == 0:
            return []
        sims = self.matrix @ qv
        order = np.argsort(-sims)
        out = []
        for idx in order:
            m = self.meta[idx]
            if filters:
                if filters.get("hcp_id") and m.get("hcp_id") != filters["hcp_id"]:
                    continue
                if filters.get("source_type") and m.get("source_type") != filters["source_type"]:
                    continue
                if filters.get("product_id") and m.get("product_id") and m.get("product_id") != filters["product_id"]:
                    continue
            out.append({
                "source_id": m["source_id"], "source_type": m["source_type"],
                "text": (m.get("text") or "")[:500], "hcp_id": m.get("hcp_id"),
                "product_id": m.get("product_id"), "date": m.get("date"),
                "score": float(sims[idx]), **(m.get("extra") or {}),
            })
            if len(out) >= k:
                break
        return out

    async def _atlas_search(self, qv: list, k: int, filters: Optional[dict]) -> list[dict]:
        db = get_db()
        pipeline = [
            {"$vectorSearch": {
                "index": "rag_chunks_vector",
                "path": "embedding",
                "queryVector": qv,
                "numCandidates": k * 10,
                "limit": k,
                **({"filter": {fk: fv for fk, fv in filters.items() if fv}} if filters else {}),
            }},
            {"$project": {"_id": 0, "embedding": 0, "score": {"$meta": "vectorSearchScore"}}},
        ]
        return [doc async for doc in db.rag_chunks.aggregate(pipeline)]
