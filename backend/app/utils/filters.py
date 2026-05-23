"""Shared filter helpers for API endpoints."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from app.data.store import DataStore


def filter_calls(calls: pd.DataFrame,
                 specialty: Optional[str] = None,
                 territory: Optional[str] = None,
                 region: Optional[str] = None,
                 time_window_days: Optional[int] = None) -> pd.DataFrame:
    """Apply standard filters to an enriched calls DataFrame. Caller is responsible
    for enriching `calls` (joining hcp/rep/product) before calling this."""
    if calls is None or calls.empty:
        return calls
    df = calls
    if specialty and "specialty_group" in df.columns:
        df = df[df["specialty_group"] == specialty]
    if territory and "territory" in df.columns:
        df = df[df["territory"] == territory]
    if region and "region" in df.columns:
        df = df[df["region"] == region]
    if time_window_days:
        try:
            tw = int(time_window_days)
            if tw > 0 and not df.empty:
                cutoff = df["interaction_datetime"].max() - pd.Timedelta(days=tw)
                df = df[df["interaction_datetime"] >= cutoff]
        except (ValueError, TypeError):
            pass
    return df


def filter_hcp_ids(specialty: Optional[str] = None,
                   territory: Optional[str] = None,
                   region: Optional[str] = None) -> set[str]:
    """Return the set of hcp_ids matching the (HCP-level) filter combo. Useful when
    you have a non-call DataFrame and need to restrict by HCP attributes."""
    hcp = DataStore.instance().df("hcp_master")
    if hcp.empty:
        return set()
    df = hcp
    if specialty:
        df = df[df["specialty_group"] == specialty]
    if territory:
        df = df[df["territory"] == territory]
    if region:
        df = df[df["region"] == region]
    return set(df["hcp_id"].tolist())
