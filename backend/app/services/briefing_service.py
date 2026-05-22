"""Pre-Call Briefing Service — orchestrates retrieval + LLM."""
from __future__ import annotations

import json
from typing import Optional

import pandas as pd

from app.data.store import DataStore
from app.data.mongo import log_ai_output
from app.services.conversion_engine import ConversionEngine
from app.services.opportunity_engine import OpportunityEngine
from app.ai.guardrails import build_system_prompt, trim_context
from app.ai.llm import llm_service
from app.ai.vector_store import VectorStore


class BriefingService:
    def __init__(self) -> None:
        self.store = DataStore.instance()
        self.conv = ConversionEngine()
        self.opp = OpportunityEngine()

    def assemble_context(self, hcp_id: str) -> dict:
        hcp = self.store.hcp(hcp_id)
        if not hcp:
            return {}
        account = self.store.account(hcp.get("affiliated_account_id")) or {}
        # Recent claims
        claims = self.store.df("prescription_claims_source")
        claims = claims[claims["hcp_id"] == hcp_id].sort_values("service_month", ascending=False).head(8)
        # Recent calls
        calls_full = self.conv.calls()
        calls_full = calls_full[calls_full["hcp_id"] == hcp_id].sort_values("interaction_datetime", ascending=False).head(8)
        # publications
        pubs = self.store.df("publication_source")
        pubs = pubs[pubs["hcp_id"] == hcp_id].sort_values("publication_date", ascending=False).head(5)
        events = self.store.df("event_source")
        events = events[events["hcp_id"] == hcp_id].sort_values("event_date", ascending=False).head(5)
        digital = self.store.df("digital_engagement_source")
        digital = digital[digital["hcp_id"] == hcp_id].sort_values("engagement_date", ascending=False).head(8)
        # market events for HCP region & relevant product list
        mkt = self.store.df("market_events_source")
        mkt = mkt[mkt["region"] == hcp.get("region")].sort_values("event_date", ascending=False).head(5)
        # KOL
        kols = self.store.df("kol_master")
        kol = kols[kols["hcp_id"] == hcp_id]
        kol_profile = kol.iloc[0].to_dict() if not kol.empty else None

        nba = self.opp.nba_for(hcp_id)

        # serialize
        def s(df):
            if df is None or df.empty:
                return []
            return json.loads(df.to_json(orient="records", date_format="iso"))

        return {
            "hcp": hcp,
            "account": account,
            "claims": s(claims),
            "calls": s(calls_full[[
                "interaction_id", "interaction_datetime", "channel", "discussion_topic",
                "call_outcome", "objection_raised_flag", "follow_up_required_flag",
                "crm_note_raw", "next_step_raw", "converted", "conversion_type",
            ]]),
            "publications": s(pubs),
            "events": s(events),
            "digital_engagement": s(digital),
            "market_events": s(mkt),
            "kol_profile": kol_profile,
            "nba": nba,
        }

    async def generate_brief(self, hcp_id: str) -> dict:
        ctx = self.assemble_context(hcp_id)
        if not ctx:
            return {"error": f"Unknown hcp_id {hcp_id}"}

        # Augment with RAG over notes specifically for this HCP (Mongo-backed vector store)
        vs = VectorStore.instance()
        retrieval_query = f"HCP {ctx['hcp']['hcp_name']} {ctx['hcp']['specialty_group']} engagement objections opportunities"
        retrieved = await vs.search(retrieval_query, k=8, filters={"hcp_id": hcp_id})

        system = build_system_prompt("rep_briefing")
        ctx_str = trim_context(json.dumps({"hcp_context": ctx, "retrieved_records": retrieved}, default=str), 12000)
        user_prompt = f"""Generate a pre-call briefing for the sales representative meeting this HCP.

OUTPUT FORMAT (STRICT MARKDOWN):
## 60-Second Summary
A 3-4 sentence executive summary of the HCP, their recent activity, and their current opportunity state. Cite source IDs.

## Recommended Discussion Angles (3)
1. Angle title — Rationale (cite source IDs)
2. ...
3. ...

## Likely Objections (2)
- **Objection 1** → Suggested response (compliance-safe, cite evidence)
- **Objection 2** → Suggested response

## Compliance-Safe Talking Point
A single talking point that is safe to use, grounded in approved evidence.

## Recent Evidence (cite)
- [SOURCE_ID] — short description

## Follow-up Tasks
- Concrete next step #1
- Concrete next step #2

CONTEXT (JSON):
{ctx_str}
"""
        resp = await llm_service.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system,
            max_tokens=1200,
        )

        return {
            "hcp_id": hcp_id,
            "hcp_name": ctx["hcp"]["hcp_name"],
            "specialty": ctx["hcp"]["specialty_group"],
            "territory": ctx["hcp"]["territory"],
            "region": ctx["hcp"]["region"],
            "consent": ctx["hcp"]["consent_status"],
            "brief_markdown": resp.text,
            "provider": resp.provider,
            "model": resp.model,
            "latency_ms": resp.latency_ms,
            "fallback_used": resp.fallback_used,
            "retrieved_sources": retrieved,
            "nba": ctx["nba"],
            "compliance_audit": {
                "context_record_count": sum(
                    len(ctx.get(k, [])) for k in ("claims", "calls", "publications", "events", "digital_engagement", "market_events")
                ),
                "retrieved_count": len(retrieved),
                "system_prompt_version": "v1.0-guardrailed",
            },
        }

    async def generate_brief_with_audit(self, hcp_id: str) -> dict:
        out = await self.generate_brief(hcp_id)
        if "error" in out:
            return out
        try:
            audit_id = await log_ai_output(
                "briefing", out,
                hcp_id=hcp_id, provider=out.get("provider"), model=out.get("model"),
                latency_ms=out.get("latency_ms"), fallback_used=out.get("fallback_used"),
                citations=[s["source_id"] for s in out.get("retrieved_sources", [])],
            )
            out["audit_id"] = audit_id
        except Exception as e:
            out["audit_id"] = None
            out["audit_error"] = str(e)
        return out
