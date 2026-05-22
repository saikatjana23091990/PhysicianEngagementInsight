"""Executive dashboard summary endpoint."""
import json
from typing import Optional
from fastapi import APIRouter, Query

from app.services.conversion_engine import ConversionEngine
from app.services.kol_engine import KOLEngine
from app.services.opportunity_engine import OpportunityEngine
from app.data.store import DataStore
from app.ai.guardrails import build_system_prompt
from app.ai.llm import llm_service

router = APIRouter(prefix="/exec", tags=["exec"])


def _apply_filters(eng: ConversionEngine, specialty: Optional[str], territory: Optional[str],
                   region: Optional[str], time_window_days: Optional[int]):
    """Return enriched + filtered calls DataFrame."""
    import pandas as pd
    calls = eng._enrich(eng.calls())
    if calls.empty:
        return calls
    if specialty:
        calls = calls[calls["specialty_group"] == specialty]
    if territory:
        calls = calls[calls["territory"] == territory]
    if region:
        calls = calls[calls["region"] == region]
    if time_window_days:
        cutoff = calls["interaction_datetime"].max() - pd.Timedelta(days=int(time_window_days))
        calls = calls[calls["interaction_datetime"] >= cutoff]
    return calls


@router.get("/filters")
def filters():
    """Return distinct filter options for the dashboard."""
    store = DataStore.instance()
    hcp = store.df("hcp_master")
    return {
        "specialties": sorted(hcp["specialty_group"].dropna().unique().tolist()),
        "territories": sorted(hcp["territory"].dropna().unique().tolist()),
        "regions": sorted(hcp["region"].dropna().unique().tolist()),
        "time_windows": [
            {"label": "Last 30 days", "value": 30},
            {"label": "Last 90 days", "value": 90},
            {"label": "Last 6 months", "value": 180},
            {"label": "Last 12 months", "value": 365},
            {"label": "All time", "value": 0},
        ],
    }


@router.get("/dashboard")
def dashboard(
    specialty: Optional[str] = None,
    territory: Optional[str] = None,
    region: Optional[str] = None,
    time_window_days: Optional[int] = None,
):
    eng = ConversionEngine()
    kol = KOLEngine()
    opp = OpportunityEngine()
    store = DataStore.instance()

    filtered = _apply_filters(eng, specialty, territory, region, time_window_days)
    total = len(filtered)
    conv_n = int(filtered["converted"].sum()) if total else 0
    conv_rate = round(100.0 * conv_n / total, 2) if total else 0.0
    conv_conf = float(filtered.loc[filtered["converted"], "attribution_confidence"].mean()) if conv_n else 0.0
    overall = {
        "total_calls": total,
        "converted_calls": conv_n,
        "conversion_rate": conv_rate,
        "avg_confidence": round(conv_conf, 3),
        "period_start": str(filtered["interaction_datetime"].min().date()) if total else None,
        "period_end": str(filtered["interaction_datetime"].max().date()) if total else None,
    }

    # Trend on filtered set
    import pandas as pd
    if total:
        ft = filtered.copy()
        ft["bucket"] = ft["interaction_datetime"].dt.to_period("W").dt.to_timestamp()
        agg = ft.groupby("bucket").agg(
            total_calls=("interaction_id", "count"),
            converted_calls=("converted", "sum"),
        ).reset_index()
        agg["conversion_rate"] = (100.0 * agg["converted_calls"] / agg["total_calls"]).round(2)
        agg["rolling_7d"] = agg["conversion_rate"].rolling(7, min_periods=1).mean().round(2)
        agg["rolling_30d"] = agg["conversion_rate"].rolling(30, min_periods=1).mean().round(2)
    else:
        agg = pd.DataFrame()

    def grp(by: str, top: int = 8):
        if filtered.empty or by not in filtered.columns:
            return []
        g = filtered.groupby(by).agg(
            total_calls=("interaction_id", "count"),
            converted_calls=("converted", "sum"),
        ).reset_index()
        g["conversion_rate"] = (100.0 * g["converted_calls"] / g["total_calls"]).round(2)
        return g.sort_values("conversion_rate", ascending=False).head(top).to_dict("records")

    # Opportunities filtered to specialty/territory if provided
    opps = opp.score_all()
    if specialty:
        opps = opps[opps["specialty_group"] == specialty]
    if territory:
        opps = opps[opps["territory"] == territory]
    if region:
        opps = opps[opps["region"] == region]
    top_opps = opps.head(8)[[
        "hcp_id", "hcp_name", "specialty_group", "territory", "opportunity_score"
    ]].to_dict("records")

    kol_summary = kol.dashboard()["summary"]
    mkt = store.df("market_events_source")
    if region:
        mkt = mkt[mkt["region"] == region]
    market_recent = mkt.sort_values("event_date", ascending=False).head(6)

    return {
        "filters_applied": {
            "specialty": specialty, "territory": territory,
            "region": region, "time_window_days": time_window_days,
        },
        "conversion": overall,
        "trend": [
            {
                "bucket": r["bucket"].isoformat(),
                "conversion_rate": float(r["conversion_rate"]),
                "rolling_7d": float(r["rolling_7d"]),
                "rolling_30d": float(r["rolling_30d"]),
                "total_calls": int(r["total_calls"]),
                "converted_calls": int(r["converted_calls"]),
            }
            for _, r in agg.iterrows()
        ] if not agg.empty else [],
        "by_specialty": grp("specialty_group"),
        "by_territory": grp("territory"),
        "top_reps": grp("rep_name"),
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
    out = {
        "narrative_markdown": resp.text,
        "provider": resp.provider,
        "model": resp.model,
        "latency_ms": resp.latency_ms,
        "fallback_used": resp.fallback_used,
    }
    try:
        from app.data.mongo import log_ai_output
        audit_id = await log_ai_output(
            "narrative", out, provider=resp.provider, model=resp.model,
            latency_ms=resp.latency_ms, fallback_used=resp.fallback_used,
        )
        out["audit_id"] = audit_id
    except Exception:
        out["audit_id"] = None
    return out
