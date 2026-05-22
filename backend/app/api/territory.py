from typing import Optional
from fastapi import APIRouter

from app.data.store import DataStore, serialize_df
from app.services.conversion_engine import ConversionEngine

router = APIRouter(prefix="/territory", tags=["territory"])


@router.get("/list")
def territories():
    store = DataStore.instance()
    df = store.df("hcp_master").groupby(["region", "territory"]).agg(
        hcps=("hcp_id", "count")
    ).reset_index()
    return df.to_dict("records")


@router.get("/heatmap")
def heatmap():
    eng = ConversionEngine()
    df = eng.breakdown("territory")
    if df.empty:
        return []
    return df.to_dict("records")


@router.get("/{territory}")
def territory_detail(territory: str):
    store = DataStore.instance()
    hcps = store.df("hcp_master")
    hcps = hcps[hcps["territory"] == territory]
    eng = ConversionEngine()
    calls = eng.calls()
    calls = calls[calls["hcp_id"].isin(hcps["hcp_id"])]
    total = len(calls)
    conv = int(calls["converted"].sum()) if total else 0
    rate = round(100.0 * conv / total, 2) if total else 0.0
    return {
        "territory": territory,
        "hcp_count": int(len(hcps)),
        "total_calls": total,
        "converted_calls": conv,
        "conversion_rate": rate,
        "hcps_sample": serialize_df(hcps, 20),
    }
