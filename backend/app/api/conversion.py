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
    """Holt-Winters forecast on weekly conversion rate with EWM fallback."""
    import pandas as pd
    from app.ml.forecast import forecast_holt_winters
    eng = ConversionEngine()
    df = eng.trend(freq="W")
    if df.empty:
        return []
    series = pd.Series(df["conversion_rate"].values, index=df["bucket"])
    fc = forecast_holt_winters(series, steps=weeks_ahead)
    last = df["bucket"].iloc[-1]
    out = []
    for i, (_, row) in enumerate(fc.iterrows(), start=1):
        out.append({
            "bucket": (last + pd.Timedelta(weeks=i)).isoformat(),
            "forecast_rate": float(row["forecast"]),
            "confidence_low": float(row["low"]),
            "confidence_high": float(row["high"]),
        })
    return out
