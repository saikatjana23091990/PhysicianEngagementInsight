from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import json

import pandas as pd

from app.services.conversion_engine import ConversionEngine
from app.data.store import DataStore
from app.utils.filters import filter_calls

router = APIRouter(prefix="/conversion", tags=["conversion"])


def _filtered_enriched(specialty: Optional[str], territory: Optional[str],
                       region: Optional[str], time_window_days: Optional[int]) -> pd.DataFrame:
    eng = ConversionEngine()
    enriched = eng._enrich(eng.calls())
    return filter_calls(enriched, specialty=specialty, territory=territory,
                        region=region, time_window_days=time_window_days)


@router.get("/overview")
def overview(specialty: Optional[str] = None, territory: Optional[str] = None,
             region: Optional[str] = None, time_window_days: Optional[int] = None,
             rep_id: Optional[str] = None, product_id: Optional[str] = None):
    df = _filtered_enriched(specialty, territory, region, time_window_days)
    if rep_id and "rep_id" in df.columns:
        df = df[df["rep_id"] == rep_id]
    if product_id and "product_id" in df.columns:
        df = df[df["product_id"] == product_id]
    total = len(df)
    conv = int(df["converted"].sum()) if total else 0
    rate = round(100.0 * conv / total, 2) if total else 0.0
    return {
        "total_calls": total,
        "converted_calls": conv,
        "conversion_rate": rate,
        "target": 12.0,
        "uplift_vs_target": round(rate - 12.0, 2),
    }


@router.get("/trend")
def trend(freq: str = "W", specialty: Optional[str] = None, territory: Optional[str] = None,
          region: Optional[str] = None, time_window_days: Optional[int] = None):
    df = _filtered_enriched(specialty, territory, region, time_window_days)
    if df.empty:
        return []
    df = df.copy()
    df["bucket"] = df["interaction_datetime"].dt.to_period(
        "D" if freq == "D" else "W" if freq == "W" else "M"
    ).dt.to_timestamp()
    agg = df.groupby("bucket").agg(
        total_calls=("interaction_id", "count"),
        converted_calls=("converted", "sum"),
    ).reset_index()
    agg["conversion_rate"] = (100.0 * agg["converted_calls"] / agg["total_calls"]).round(2)
    agg["rolling_7d"] = agg["conversion_rate"].rolling(7, min_periods=1).mean().round(2)
    agg["rolling_30d"] = agg["conversion_rate"].rolling(30, min_periods=1).mean().round(2)
    out = []
    for _, r in agg.iterrows():
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
def breakdown(dim: str, specialty: Optional[str] = None, territory: Optional[str] = None,
              region: Optional[str] = None, time_window_days: Optional[int] = None):
    df = _filtered_enriched(specialty, territory, region, time_window_days)
    if df.empty or dim not in df.columns:
        return []
    grp = df.groupby(dim).agg(
        total_calls=("interaction_id", "count"),
        converted_calls=("converted", "sum"),
    ).reset_index()
    grp["conversion_rate"] = (100.0 * grp["converted_calls"] / grp["total_calls"]).round(2)
    grp = grp.sort_values("conversion_rate", ascending=False)
    return json.loads(grp.to_json(orient="records"))


@router.get("/heatmap")
def heatmap(specialty: Optional[str] = None, territory: Optional[str] = None,
            region: Optional[str] = None, time_window_days: Optional[int] = None):
    """Rep vs Therapy heatmap."""
    df = _filtered_enriched(specialty, territory, region, time_window_days)
    if df.empty:
        return {"rows": [], "columns": [], "matrix": []}
    pivot = df.pivot_table(
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
def forecast(weeks_ahead: int = 8, specialty: Optional[str] = None, territory: Optional[str] = None,
             region: Optional[str] = None, time_window_days: Optional[int] = None):
    """Forecasts TWO series: total_calls/week and converted_calls/week.
    Returns each point's forecast values, CIs, derived rate, and the convergence
    week (where the gap between the two forecasted lines is smallest)."""
    from app.ml.forecast import forecast_holt_winters
    df_calls = _filtered_enriched(specialty, territory, region, time_window_days)
    if df_calls.empty:
        return {"history": [], "forecast": [], "convergence": None}

    df_calls = df_calls.copy()
    df_calls["bucket"] = df_calls["interaction_datetime"].dt.to_period("W").dt.to_timestamp()
    agg = df_calls.groupby("bucket").agg(
        total_calls=("interaction_id", "count"),
        converted_calls=("converted", "sum"),
    ).reset_index()
    if agg.empty:
        return {"history": [], "forecast": [], "convergence": None}
    agg["conversion_rate"] = (100.0 * agg["converted_calls"] / agg["total_calls"]).round(2)

    last = agg["bucket"].iloc[-1]
    total_series = pd.Series(agg["total_calls"].astype(float).values, index=agg["bucket"])
    conv_series = pd.Series(agg["converted_calls"].astype(float).values, index=agg["bucket"])
    fc_total = forecast_holt_winters(total_series, steps=weeks_ahead)
    fc_conv = forecast_holt_winters(conv_series, steps=weeks_ahead)

    history = [
        {
            "bucket": r["bucket"].isoformat(),
            "total_calls": int(r["total_calls"]),
            "converted_calls": int(r["converted_calls"]),
            "conversion_rate": float(r["conversion_rate"]),
        }
        for _, r in agg.iterrows()
    ]

    forecast_points = []
    convergence_week = None
    convergence_gap_min = None
    for i, ((_, tr), (_, cr)) in enumerate(zip(fc_total.iterrows(), fc_conv.iterrows()), start=1):
        bucket = (last + pd.Timedelta(weeks=i)).isoformat()
        total_f = max(0.0, float(tr["forecast"]))
        conv_f = max(0.0, min(float(cr["forecast"]), total_f))
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

    last_hist = history[-1]
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
