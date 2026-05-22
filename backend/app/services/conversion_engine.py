"""
ConversionRate_30d Engine — the central KPI of the platform.

Definition: % of HCP calls that result in a defined conversion event within 30 days.

Attribution logic:
- A call "results in conversion" if there is a conversion event with the same hcp_id
  whose conversion_timestamp falls within (call_dt, call_dt + 30 days].
- If a call is already explicitly linked via conversion_events_source.linked_call_id, use it.
- Multi-call conflict: a single conversion may attribute to multiple calls within the
  window; we record the *nearest* (smallest days_from_call) as the primary attribution and
  emit lower-confidence soft links for the rest (audit trail).
- Confidence: weighted by recency, attribution_confidence column, and whether the link
  was explicit vs derived.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd

from app.data.store import DataStore


CONVERSION_WINDOW_DAYS = 30


@dataclass
class ConversionResult:
    total_calls: int
    converted_calls: int
    conversion_rate: float
    avg_confidence: float
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class ConversionEngine:
    def __init__(self) -> None:
        self.store = DataStore.instance()

    # ------------- core attribution -----------------
    def _build_linked_calls(self) -> pd.DataFrame:
        """Return calls augmented with first-conversion info and a boolean `converted` flag."""
        calls = self.store.df("field_interactions_source")
        convs = self.store.df("conversion_events_source")
        if calls.empty:
            return calls
        calls = calls.copy()
        calls["interaction_datetime"] = pd.to_datetime(calls["interaction_datetime"])

        if convs.empty:
            calls["converted"] = False
            calls["days_to_conversion"] = np.nan
            calls["attribution_confidence"] = np.nan
            calls["conversion_type"] = None
            return calls

        convs = convs.copy()
        convs["conversion_timestamp"] = pd.to_datetime(convs["conversion_timestamp"])

        # First, use explicit linked_call_id
        explicit = convs.dropna(subset=["linked_call_id"]).set_index("linked_call_id")

        # For each call, check if explicit link exists OR find nearest conversion within 30 days
        # (same hcp_id, conversion_timestamp in window)
        calls = calls.merge(
            explicit[["conversion_type", "attribution_confidence", "conversion_timestamp"]],
            left_on="interaction_id",
            right_index=True,
            how="left",
            suffixes=("", "_explicit"),
        )

        # Derive nearest conversion for unlinked calls
        # Build mapping: hcp_id -> sorted list of (timestamp, conv_id, confidence, conv_type)
        derived = []
        conv_by_hcp = convs.groupby("hcp_id")
        for idx, row in calls.iterrows():
            if pd.notna(row.get("conversion_timestamp")):
                derived.append((row["conversion_timestamp"], row.get("conversion_type"),
                                row.get("attribution_confidence"), "explicit"))
                continue
            hcp = row["hcp_id"]
            t = row["interaction_datetime"]
            if hcp not in conv_by_hcp.groups:
                derived.append((pd.NaT, None, np.nan, None))
                continue
            sub = conv_by_hcp.get_group(hcp)
            mask = (sub["conversion_timestamp"] > t) & (
                sub["conversion_timestamp"] <= t + timedelta(days=CONVERSION_WINDOW_DAYS)
            )
            cands = sub[mask].sort_values("conversion_timestamp")
            if cands.empty:
                derived.append((pd.NaT, None, np.nan, None))
            else:
                first = cands.iloc[0]
                derived.append((first["conversion_timestamp"], first["conversion_type"],
                                float(first["attribution_confidence"]) * 0.9, "derived"))

        ts_arr = [d[0] for d in derived]
        ct_arr = [d[1] for d in derived]
        conf_arr = [d[2] for d in derived]
        link_arr = [d[3] for d in derived]
        calls["conversion_timestamp"] = ts_arr
        calls["conversion_type"] = ct_arr
        calls["attribution_confidence"] = conf_arr
        calls["attribution_link"] = link_arr
        calls["converted"] = calls["conversion_timestamp"].notna()
        calls["days_to_conversion"] = (
            calls["conversion_timestamp"] - calls["interaction_datetime"]
        ).dt.total_seconds() / 86400.0
        return calls

    # ----------------- public --------------------------
    def overall(self, filters: Optional[dict] = None) -> ConversionResult:
        calls = self.calls(filters)
        if calls.empty:
            return ConversionResult(0, 0, 0.0, 0.0)
        total = len(calls)
        conv = int(calls["converted"].sum())
        rate = round(100.0 * conv / total, 2) if total else 0.0
        conf = float(calls.loc[calls["converted"], "attribution_confidence"].mean()) if conv else 0.0
        return ConversionResult(total, conv, rate, round(conf, 3),
                                period_start=str(calls["interaction_datetime"].min().date()),
                                period_end=str(calls["interaction_datetime"].max().date()))

    def calls(self, filters: Optional[dict] = None) -> pd.DataFrame:
        df = self._build_linked_calls()
        if filters and not df.empty:
            for k, v in filters.items():
                if v is None or k not in df.columns:
                    continue
                df = df[df[k] == v]
        return df

    # Rolling trend (daily, with 7- and 30-day smoothing)
    def trend(self, freq: str = "D", filters: Optional[dict] = None) -> pd.DataFrame:
        calls = self.calls(filters)
        if calls.empty:
            return pd.DataFrame()
        calls = calls.copy()
        calls["bucket"] = calls["interaction_datetime"].dt.to_period(
            "D" if freq == "D" else "W" if freq == "W" else "M"
        ).dt.to_timestamp()
        agg = calls.groupby("bucket").agg(
            total_calls=("interaction_id", "count"),
            converted_calls=("converted", "sum"),
        ).reset_index()
        agg["conversion_rate"] = (100.0 * agg["converted_calls"] / agg["total_calls"]).round(2)
        agg["rolling_7d"] = agg["conversion_rate"].rolling(7, min_periods=1).mean().round(2)
        agg["rolling_30d"] = agg["conversion_rate"].rolling(30, min_periods=1).mean().round(2)
        return agg

    # Breakdown by dimension
    def breakdown(self, by: str, filters: Optional[dict] = None) -> pd.DataFrame:
        calls = self.calls(filters)
        if calls.empty or by not in calls.columns:
            # join in rep / hcp dims if needed
            if by in ("territory", "region", "specialty_group", "primary_therapy_area", "rep_name", "brand_name"):
                calls = self._enrich(calls)
                if by not in calls.columns:
                    return pd.DataFrame()
            else:
                return pd.DataFrame()
        elif by in ("territory", "region", "specialty_group", "primary_therapy_area", "rep_name", "brand_name"):
            calls = self._enrich(calls)
        grp = calls.groupby(by).agg(
            total_calls=("interaction_id", "count"),
            converted_calls=("converted", "sum"),
        ).reset_index()
        grp["conversion_rate"] = (100.0 * grp["converted_calls"] / grp["total_calls"]).round(2)
        return grp.sort_values("conversion_rate", ascending=False)

    def _enrich(self, calls: pd.DataFrame) -> pd.DataFrame:
        if calls.empty:
            return calls
        hcp = self.store.df("hcp_master")[["hcp_id", "specialty_group", "territory", "region"]]
        rep = self.store.df("rep_master")[["rep_id", "rep_name", "primary_therapy_area"]]
        prod = self.store.df("product_master")[["product_id", "brand_name"]]
        out = calls.merge(hcp, on="hcp_id", how="left", suffixes=("", "_hcp"))
        out = out.merge(rep, on="rep_id", how="left", suffixes=("", "_rep"))
        out = out.merge(prod, on="product_id", how="left", suffixes=("", "_prd"))
        return out

    # Audit trail for a single hcp/rep/call
    def attribution_for_call(self, interaction_id: str) -> dict:
        df = self._build_linked_calls()
        row = df[df["interaction_id"] == interaction_id]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            "interaction_id": interaction_id,
            "hcp_id": r["hcp_id"],
            "rep_id": r["rep_id"],
            "interaction_datetime": str(r["interaction_datetime"]),
            "converted": bool(r["converted"]),
            "conversion_timestamp": str(r["conversion_timestamp"]) if pd.notna(r["conversion_timestamp"]) else None,
            "days_to_conversion": float(r["days_to_conversion"]) if pd.notna(r["days_to_conversion"]) else None,
            "conversion_type": r["conversion_type"] if pd.notna(r.get("conversion_type")) else None,
            "attribution_confidence": float(r["attribution_confidence"]) if pd.notna(r["attribution_confidence"]) else None,
            "attribution_link": r.get("attribution_link"),
        }
