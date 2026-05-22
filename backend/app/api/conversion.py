from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import json

from app.services.conversion_engine import ConversionEngine
from app.data.store import DataStore

router = APIRouter(prefix="/conversion", tags=["conversion"])


@router.get("/overview")
def overview(territory: Optional[str] = None, rep_id: Optional[str] = None, product_id: Optional[str] = None):
    eng = ConversionEngine()
    filters = {k: v for k, v in {"territory": territory, "rep_id": rep_id, "product_id": product_id}.items() if v}
    # Note: territory filter requires joining with hcp; do it via enrichment then re-filter
    calls = eng._build_linked_calls() if filters else eng.calls()
    if filters:
        enriched = eng._enrich(calls)
        for k, v in filters.items():
            if k in enriched.columns:
                enriched = enriched[enriched[k] == v]
        calls = enriched
    total = len(calls)
    conv = int(calls["converted"].sum()) if total else 0
    rate = round(100.0 * conv / total, 2) if total else 0.0
    return {
        "total_calls": total,
        "converted_calls": conv,
        "conversion_rate": rate,
        "target": 12.0,
        "uplift_vs_target": round(rate - 12.0, 2),
    }


@router.get("/trend")
def trend(freq: str = "W"):
    eng = ConversionEngine()
    df = eng.trend(freq=freq)
    if df.empty:
        return []
    out = []
    for _, r in df.iterrows():
        out.append({
            "bucket": r["bucket"].isoformat(),
            "total_calls": int(r["total_calls"]),
            "converted_calls": int(r["converted_calls"]),
            "conversion_rate": float(r["conversion_rate"]),
            "rolling_7d": float(r["rolling_7d"]),
            "rolling_30d": float(r["rolling_30d"]),
        })
    return out


@router.get("/breakdown/{dim}")
def breakdown(dim: str):
    eng = ConversionEngine()
    df = eng.breakdown(dim)
    if df.empty:
        return []
    df = df.copy()
    # convert nan
    return json.loads(df.to_json(orient="records"))


@router.get("/heatmap")
def heatmap():
    """Rep vs Therapy heatmap."""
    eng = ConversionEngine()
    calls = eng._enrich(eng.calls())
    if calls.empty:
        return {"rows": [], "columns": [], "matrix": []}
    pivot = calls.pivot_table(
        index="rep_name", columns="specialty_group",
        values="converted", aggfunc=lambda s: round(100.0 * s.mean(), 1) if len(s) else 0.0,
        fill_value=0.0,
    )
    return {
        "rows": list(pivot.index),
        "columns": list(pivot.columns),
        "matrix": pivot.values.tolist(),
    }


@router.get("/audit/{interaction_id}")
def audit(interaction_id: str):
    eng = ConversionEngine()
    res = eng.attribution_for_call(interaction_id)
    if not res:
        raise HTTPException(404, f"Unknown interaction_id {interaction_id}")
    return res


@router.get("/forecast")
def forecast(weeks_ahead: int = 8):
    """Lightweight EWM forecast on weekly conversion rate (Prophet not added to keep deps lean)."""
    import numpy as np
    eng = ConversionEngine()
    df = eng.trend(freq="W")
    if df.empty:
        return []
    series = df["conversion_rate"].values
    last = df["bucket"].iloc[-1]
    # exponential smoothing forecast
    alpha = 0.4
    level = series[0]
    for v in series[1:]:
        level = alpha * v + (1 - alpha) * level
    # add trend approx using last 4 weeks
    if len(series) >= 4:
        trend_val = float(np.mean(np.diff(series[-4:])))
    else:
        trend_val = 0.0
    out = []
    for i in range(1, weeks_ahead + 1):
        forecast_val = round(max(0.0, level + trend_val * i), 2)
        out.append({
            "bucket": (last + __import__("pandas").Timedelta(weeks=i)).isoformat(),
            "forecast_rate": forecast_val,
            "confidence_low": round(max(0.0, forecast_val - 2.5), 2),
            "confidence_high": round(forecast_val + 2.5, 2),
        })
    return out
