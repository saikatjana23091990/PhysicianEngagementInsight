"""Conversational analytics service ("Ask Data") backed by the LLM + structured tool calls."""
from __future__ import annotations

import json
from typing import Optional

from app.data.store import DataStore
from app.data.mongo import log_ai_output
from app.services.conversion_engine import ConversionEngine
from app.services.kol_engine import KOLEngine
from app.services.opportunity_engine import OpportunityEngine
from app.ai.guardrails import build_system_prompt, trim_context
from app.ai.llm import llm_service
from app.ai.vector_store import VectorStore


class AskDataService:
    """
    Strategy: structured-data-first.
    1. Compute a compact "data dossier" containing pre-aggregated KPIs and breakdowns.
    2. RAG over notes/publications for qualitative context relevant to the question.
    3. Hand both to the LLM with strict citation/grounding rules.
    """
    def __init__(self) -> None:
        self.store = DataStore.instance()
        self.conv = ConversionEngine()
        self.opp = OpportunityEngine()
        self.kol = KOLEngine()

    def _build_dossier(self) -> dict:
        overall = self.conv.overall()
        by_therapy = self.conv.breakdown("specialty_group").head(10).to_dict("records") if not self.conv.calls().empty else []
        by_territory = self.conv.breakdown("territory").head(10).to_dict("records") if not self.conv.calls().empty else []
        by_rep = self.conv.breakdown("rep_name").head(10).to_dict("records") if not self.conv.calls().empty else []
        by_brand = self.conv.breakdown("brand_name").head(10).to_dict("records") if not self.conv.calls().empty else []
        kol_dash = self.kol.dashboard()
        top_opp = self.opp.score_all().head(10)[["hcp_id", "hcp_name", "specialty_group", "territory",
                                                  "opportunity_score", "consent_status"]].to_dict("records")
        return {
            "overall_conversion": overall.__dict__,
            "by_therapy_area": by_therapy,
            "by_territory": by_territory,
            "by_rep": by_rep,
            "by_brand": by_brand,
            "kol_summary": kol_dash["summary"],
            "top_opportunities": top_opp,
            "tables_available": [
                "hcp_master", "field_interactions_source", "prescription_claims_source",
                "conversion_events_source", "publication_source", "event_source",
                "digital_engagement_source", "market_events_source", "kol_master",
                "kol_relationship_source", "rep_master", "rep_quota_source",
            ],
        }

    async def ask(self, question: str, session_id: Optional[str] = None, history: Optional[list] = None) -> dict:
        vs = VectorStore.instance()
        retrieved = await vs.search(question, k=6)
        dossier = self._build_dossier()
        system = build_system_prompt("analytics")
        ctx_str = trim_context(json.dumps({"dossier": dossier, "retrieved_records": retrieved}, default=str), 14000)
        msgs = []
        if history:
            for h in history[-6:]:
                msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        msgs.append({"role": "user", "content": f"""Question: {question}

Use ONLY the supplied dossier/retrieved records. Answer with:
1. **Direct Answer** (2-4 sentences)
2. **Supporting Data** (bullet points with concrete numbers)
3. **Cited Sources** (list source IDs you used)
4. **Caveats** (any limitations or data gaps)

DATA:
{ctx_str}
"""})
        resp = await llm_service.chat(messages=msgs, system=system, max_tokens=1100)
        out = {
            "question": question,
            "answer_markdown": resp.text,
            "provider": resp.provider,
            "model": resp.model,
            "latency_ms": resp.latency_ms,
            "fallback_used": resp.fallback_used,
            "retrieved_sources": retrieved,
            "session_id": session_id,
        }
        try:
            audit_id = await log_ai_output(
                "chat", out, question=question,
                provider=resp.provider, model=resp.model,
                latency_ms=resp.latency_ms, fallback_used=resp.fallback_used,
                citations=[s["source_id"] for s in retrieved],
            )
            out["audit_id"] = audit_id
        except Exception:
            out["audit_id"] = None
        return out

    async def build_stream_payload(self, question: str, history: Optional[list] = None) -> dict:
        """Returns the (system, messages, retrieved) tuple as dict for streaming endpoint."""
        vs = VectorStore.instance()
        retrieved = await vs.search(question, k=6)
        dossier = self._build_dossier()
        system = build_system_prompt("analytics")
        ctx_str = trim_context(json.dumps({"dossier": dossier, "retrieved_records": retrieved}, default=str), 14000)
        msgs = []
        if history:
            for h in history[-6:]:
                msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        msgs.append({"role": "user", "content": f"""Question: {question}

Use ONLY the supplied dossier/retrieved records. Answer with:
1. **Direct Answer** (2-4 sentences)
2. **Supporting Data** (bullet points with concrete numbers)
3. **Cited Sources** (list source IDs you used)
4. **Caveats** (any limitations or data gaps)

DATA:
{ctx_str}
"""})
        return {"system": system, "messages": msgs, "retrieved": retrieved}
