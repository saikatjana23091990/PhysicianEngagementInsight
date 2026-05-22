from typing import Optional
from fastapi import APIRouter, HTTPException

from app.data.store import DataStore, serialize_df
from app.services.conversion_engine import ConversionEngine

router = APIRouter(prefix="/rep", tags=["rep"])


@router.get("/list")
def rep_list(territory: Optional[str] = None, region: Optional[str] = None):
    store = DataStore.instance()
    df = store.df("rep_master")
    if territory:
        df = df[df["territory"] == territory]
    if region:
        df = df[df["region"] == region]
    return serialize_df(df)


@router.get("/leaderboard")
def leaderboard():
    eng = ConversionEngine()
    df = eng.breakdown("rep_name")
    return df.head(50).to_dict("records")


@router.get("/{rep_id}")
def rep_detail(rep_id: str):
    store = DataStore.instance()
    rep = store.rep(rep_id)
    if not rep:
        raise HTTPException(404, "Rep not found")
    eng = ConversionEngine()
    calls = eng.calls()
    rep_calls = calls[calls["rep_id"] == rep_id]
    total = len(rep_calls)
    conv = int(rep_calls["converted"].sum()) if total else 0
    rate = round(100.0 * conv / total, 2) if total else 0.0
    # quota
    quota = store.df("rep_quota_source")
    quota = quota[quota["rep_id"] == rep_id].sort_values("report_month", ascending=False).head(12)
    # top hcps
    top_hcps = rep_calls.groupby("hcp_id").agg(
        calls=("interaction_id", "count"),
        converted=("converted", "sum"),
    ).reset_index().sort_values("calls", ascending=False).head(10)
    hcp_master = store.df("hcp_master")[["hcp_id", "hcp_name", "specialty_group", "territory"]]
    top_hcps = top_hcps.merge(hcp_master, on="hcp_id", how="left")
    return {
        "rep": rep,
        "performance": {
            "total_calls": total,
            "converted_calls": conv,
            "conversion_rate": rate,
        },
        "quota": serialize_df(quota),
        "top_hcps": top_hcps.to_dict("records"),
    }
