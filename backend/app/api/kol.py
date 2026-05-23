"""KOL analytics with optional specialty/region filters."""
from typing import Optional

import pandas as pd
from fastapi import APIRouter

from app.services.kol_engine import KOLEngine
from app.data.store import serialize_df, DataStore

router = APIRouter(prefix="/kol", tags=["kol"])


def _filtered_kols(specialty: Optional[str], region: Optional[str], tier: Optional[str] = None) -> pd.DataFrame:
    df = DataStore.instance().df("kol_master")
    if df.empty:
        return df
    if specialty:
        df = df[df["specialty_group"] == specialty]
    if region:
        df = df[df["region"] == region]
    if tier:
        df = df[df["kol_tier"] == tier]
    return df


@router.get("/dashboard")
def dashboard(specialty: Optional[str] = None, region: Optional[str] = None):
    kols = _filtered_kols(specialty, region)
    if kols.empty:
        return {"summary": {"total_kols": 0, "tier1": 0, "tier2": 0, "tier3": 0,
                            "rising_stars": 0, "avg_influence": 0.0},
                "by_tier": [], "top": []}
    summary = {
        "total_kols": int(len(kols)),
        "tier1": int((kols["kol_tier"] == "Tier 1").sum()),
        "tier2": int((kols["kol_tier"] == "Tier 2").sum()),
        "tier3": int((kols["kol_tier"] == "Tier 3").sum()),
        "rising_stars": int(kols["rising_star_flag"].sum()),
        "avg_influence": round(float(kols["influence_score"].mean()), 3),
    }
    by_tier = kols.groupby("kol_tier").agg(
        count=("kol_id", "count"),
        avg_influence=("influence_score", "mean"),
        avg_centrality=("network_centrality_score", "mean"),
        avg_citations=("citation_count_5y", "mean"),
    ).reset_index()
    by_tier["avg_influence"] = by_tier["avg_influence"].round(3)
    by_tier["avg_centrality"] = by_tier["avg_centrality"].round(3)
    by_tier["avg_citations"] = by_tier["avg_citations"].round(1)
    top = kols.sort_values("influence_score", ascending=False).head(15).to_dict(orient="records")
    return {"summary": summary, "by_tier": by_tier.to_dict(orient="records"), "top": top}


@router.get("/list")
def kol_list(tier: Optional[str] = None, region: Optional[str] = None, specialty: Optional[str] = None):
    df = _filtered_kols(specialty, region, tier=tier)
    return df.sort_values("influence_score", ascending=False).to_dict("records")


@router.get("/network")
def network(kol_id: Optional[str] = None, specialty: Optional[str] = None, region: Optional[str] = None):
    eng = KOLEngine()
    net = eng.network(kol_id)
    # Filter nodes/edges to filtered specialty/region if provided
    if specialty or region:
        nodes = net["nodes"]
        filtered_nodes = [
            n for n in nodes
            if (not specialty or n.get("specialty") == specialty)
            and (not region or n.get("region") == region)
        ]
        keep_ids = {n["id"] for n in filtered_nodes}
        edges = [e for e in net["edges"] if e["source"] in keep_ids and e["target"] in keep_ids]
        return {"nodes": filtered_nodes, "edges": edges}
    return net


@router.get("/topics")
def topics(specialty: Optional[str] = None, region: Optional[str] = None):
    df = _filtered_kols(specialty, region)
    if df.empty:
        return []
    topic = df.groupby("topic_focus_primary").agg(
        kols=("kol_id", "count"),
        avg_influence=("influence_score", "mean"),
        avg_citations=("citation_count_5y", "mean"),
        rising_stars=("rising_star_flag", "sum"),
    ).reset_index()
    topic["avg_influence"] = topic["avg_influence"].round(3)
    topic["avg_citations"] = topic["avg_citations"].round(1)
    topic["rising_stars"] = topic["rising_stars"].astype(int)
    topic = topic.sort_values("avg_influence", ascending=False)
    topic = topic.rename(columns={"topic_focus_primary": "topic"})
    return topic.to_dict(orient="records")


@router.get("/{kol_id}")
def detail(kol_id: str):
    eng = KOLEngine()
    return eng.kol_detail(kol_id)
