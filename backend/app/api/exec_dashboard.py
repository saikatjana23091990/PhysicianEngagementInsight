"""Executive dashboard summary endpoint."""
import json
from fastapi import APIRouter

from app.services.conversion_engine import ConversionEngine
from app.services.kol_engine import KOLEngine
from app.services.opportunity_engine import OpportunityEngine
from app.data.store import DataStore
from app.ai.guardrails import build_system_prompt
from app.ai.llm import llm_service

router = APIRouter(prefix="/exec", tags=["exec"])


@router.get("/dashboard")
def dashboard():
    eng = ConversionEngine()
    kol = KOLEngine()
    opp = OpportunityEngine()
    store = DataStore.instance()
    overall = eng.overall()
    trend = eng.trend(freq="W")
    by_specialty = eng.breakdown("specialty_group").head(8).to_dict("records")
    by_territory = eng.breakdown("territory").head(8).to_dict("records")
    top_reps = eng.breakdown("rep_name").head(8).to_dict("records")
    top_opps = opp.score_all().head(8)[[
        "hcp_id", "hcp_name", "specialty_group", "territory", "opportunity_score"
    ]].to_dict("records")
    kol_summary = kol.dashboard()["summary"]
    market_recent = store.df("market_events_source").sort_values("event_date", ascending=False).head(6)
    return {
        "conversion": overall.__dict__,
        "trend": [
            {
                "bucket": r["bucket"].isoformat(),
                "conversion_rate": float(r["conversion_rate"]),
                "rolling_7d": float(r["rolling_7d"]),
                "rolling_30d": float(r["rolling_30d"]),
                "total_calls": int(r["total_calls"]),
                "converted_calls": int(r["converted_calls"]),
            }
            for _, r in trend.iterrows()
        ],
        "by_specialty": by_specialty,
        "by_territory": by_territory,
        "top_reps": top_reps,
        "top_opportunities": top_opps,
        "kol_summary": kol_summary,
        "recent_market_events": json.loads(market_recent.to_json(orient="records", date_format="iso")),
    }


@router.post("/narrative")
async def narrative():
    """LLM-generated executive narrative explaining current commercial state."""
    eng = ConversionEngine()
    overall = eng.overall()
    by_specialty = eng.breakdown("specialty_group").head(5).to_dict("records")
    by_territory = eng.breakdown("territory").head(5).to_dict("records")
    trend = eng.trend(freq="W").tail(12).to_dict("records")
    payload = {
        "conversion_overall": overall.__dict__,
        "trend_last_12w": [{"bucket": str(t["bucket"]), "rate": t["conversion_rate"]} for t in trend],
        "by_specialty_top5": by_specialty,
        "by_territory_top5": by_territory,
    }
    system = build_system_prompt("exec")
    prompt = f"""Write a 4-paragraph executive narrative explaining the current state of HCP engagement → conversion across the commercial organization.

Structure:
1) Headline KPI status (1 paragraph)
2) Where we are winning (1 paragraph, specific therapies/territories)
3) Where we need attention (1 paragraph, specific gaps)
4) Recommended next 30 days actions (3 bullet points)

DATA:
{json.dumps(payload, default=str)}"""
    resp = await llm_service.chat(messages=[{"role": "user", "content": prompt}], system=system, max_tokens=900)
    return {
        "narrative_markdown": resp.text,
        "provider": resp.provider,
        "model": resp.model,
        "latency_ms": resp.latency_ms,
        "fallback_used": resp.fallback_used,
    }
