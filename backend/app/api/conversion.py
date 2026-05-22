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
    """Forecasts TWO series: total_calls/week and converted_calls/week.
    Returns each point's forecast values, CIs, derived rate, and the convergence
    week (where forecasted converted_calls would approach total_calls — i.e. 100%
    conversion would be implausible; we annotate the implied convergence-of-trends
    week as where rate >= 50%, plus distance-closing week)."""
    import pandas as pd
    from app.ml.forecast import forecast_holt_winters
    eng = ConversionEngine()
    df = eng.trend(freq="W")
    if df.empty:
        return {"history": [], "forecast": [], "convergence": None}

    last = df["bucket"].iloc[-1]
    total_series = pd.Series(df["total_calls"].astype(float).values, index=df["bucket"])
    conv_series = pd.Series(df["converted_calls"].astype(float).values, index=df["bucket"])
    fc_total = forecast_holt_winters(total_series, steps=weeks_ahead)
    fc_conv = forecast_holt_winters(conv_series, steps=weeks_ahead)

    history = [
        {
            "bucket": r["bucket"].isoformat(),
            "total_calls": int(r["total_calls"]),
            "converted_calls": int(r["converted_calls"]),
            "conversion_rate": float(r["conversion_rate"]),
        }
        for _, r in df.iterrows()
    ]

    forecast_points = []
    convergence_week = None
    convergence_gap_min = None
    for i, ((_, tr), (_, cr)) in enumerate(zip(fc_total.iterrows(), fc_conv.iterrows()), start=1):
        bucket = (last + pd.Timedelta(weeks=i)).isoformat()
        total_f = max(0.0, float(tr["forecast"]))
        conv_f = max(0.0, min(float(cr["forecast"]), total_f))  # cannot exceed total
        rate = round(100.0 * conv_f / total_f, 2) if total_f > 0 else 0.0
        gap = total_f - conv_f
        forecast_points.append({
            "bucket": bucket,
            "total_forecast": round(total_f, 2),
            "total_low": round(max(0.0, float(tr["low"])), 2),
            "total_high": round(float(tr["high"]), 2),
            "converted_forecast": round(conv_f, 2),
            "converted_low": round(max(0.0, float(cr["low"])), 2),
            "converted_high": round(float(cr["high"]), 2),
            "implied_rate": rate,
            "gap": round(gap, 2),
        })
        if convergence_gap_min is None or gap < convergence_gap_min:
            convergence_gap_min = gap
            convergence_week = bucket

    # convergence interpretation
    last_hist = history[-1] if history else {"total_calls": 0, "converted_calls": 0}
    last_gap = (last_hist["total_calls"] or 0) - (last_hist["converted_calls"] or 0)
    final_forecast = forecast_points[-1] if forecast_points else None
    direction = (
        "narrowing" if final_forecast and final_forecast["gap"] < last_gap
        else ("widening" if final_forecast and final_forecast["gap"] > last_gap else "stable")
    )

    return {
        "history": history,
        "forecast": forecast_points,
        "convergence": {
            "bucket": convergence_week,
            "min_gap": convergence_gap_min,
            "current_gap": last_gap,
            "direction": direction,
        },
    }
