"""
Lightweight RAG: TF-IDF over text-bearing source records.
Indexes: CRM notes, publication abstracts, event notes, market events.
Each doc carries source_id, source_type, hcp_id (optional), product_id (optional), date.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from app.data.store import DataStore


@dataclass
class Doc:
    source_id: str
    source_type: str
    text: str
    hcp_id: Optional[str] = None
    product_id: Optional[str] = None
    date: Optional[str] = None
    extra: dict = field(default_factory=dict)


class RAGIndex:
    _instance: Optional["RAGIndex"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.docs: list[Doc] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None

    @classmethod
    def instance(cls) -> "RAGIndex":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = RAGIndex()
                    cls._instance.build()
        return cls._instance

    def build(self) -> None:
        store = DataStore.instance()
        if not store.loaded:
            store.load_all()
        docs: list[Doc] = []

        fi = store.df("field_interactions_source")
        for _, r in fi.iterrows():
            note = str(r.get("crm_note_raw", "")) + " " + str(r.get("next_step_raw", ""))
            if not note.strip():
                continue
            docs.append(Doc(
                source_id=r["interaction_id"],
                source_type="crm_note",
                text=note,
                hcp_id=r.get("hcp_id"),
                product_id=r.get("product_id"),
                date=str(r.get("interaction_datetime"))[:10],
                extra={"channel": r.get("channel"), "topic": r.get("discussion_topic"),
                       "outcome": r.get("call_outcome"), "rep_id": r.get("rep_id")},
            ))

        pubs = store.df("publication_source")
        for _, r in pubs.iterrows():
            text = f"{r.get('publication_title', '')} {r.get('key_finding_summary', '')}"
            docs.append(Doc(
                source_id=r["publication_id"],
                source_type="publication",
                text=text,
                hcp_id=r.get("hcp_id"),
                date=str(r.get("publication_date"))[:10],
                extra={"journal": r.get("journal_name"), "topic": r.get("topic_tag"),
                       "sentiment": r.get("topic_sentiment"), "relevance": r.get("relevance_score")},
            ))

        events = store.df("event_source")
        for _, r in events.iterrows():
            docs.append(Doc(
                source_id=r["event_id"],
                source_type="event",
                text=f"{r.get('event_type', '')} {r.get('topic', '')} {r.get('note_raw', '')}",
                hcp_id=r.get("hcp_id"),
                date=str(r.get("event_date"))[:10],
                extra={"event_type": r.get("event_type"), "engagement": r.get("engagement_score")},
            ))

        mkt = store.df("market_events_source")
        for _, r in mkt.iterrows():
            docs.append(Doc(
                source_id=r["market_event_id"],
                source_type="market_event",
                text=f"{r.get('event_type', '')} {r.get('summary_raw', '')}",
                product_id=r.get("product_id"),
                date=str(r.get("event_date"))[:10],
                extra={"region": r.get("region"), "severity": r.get("event_severity")},
            ))

        self.docs = docs
        if not docs:
            return
        corpus = [d.text or " " for d in docs]
        self.vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, k: int = 6, filters: Optional[dict] = None) -> list[dict]:
        if not self.docs or self.vectorizer is None:
            return []
        q = self.vectorizer.transform([query])
        sims = (self.matrix @ q.T).toarray().ravel()
        order = np.argsort(-sims)
        out = []
        for idx in order:
            d = self.docs[idx]
            if filters:
                if "hcp_id" in filters and filters["hcp_id"] and d.hcp_id != filters["hcp_id"]:
                    continue
                if "source_type" in filters and filters["source_type"] and d.source_type != filters["source_type"]:
                    continue
                if "product_id" in filters and filters["product_id"] and d.product_id and d.product_id != filters["product_id"]:
                    continue
            out.append({
                "source_id": d.source_id,
                "source_type": d.source_type,
                "text": d.text[:500],
                "hcp_id": d.hcp_id,
                "product_id": d.product_id,
                "date": d.date,
                "score": float(sims[idx]),
                **d.extra,
            })
            if len(out) >= k:
                break
        return out
