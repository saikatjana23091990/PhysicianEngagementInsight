from typing import Optional
from fastapi import APIRouter, HTTPException

from app.services.opportunity_engine import OpportunityEngine
from app.data.store import DataStore

router = APIRouter(prefix="/nba", tags=["nba"])


@router.get("/ranked")
def ranked(territory: Optional[str] = None, specialty: Optional[str] = None,
           rep_id: Optional[str] = None, limit: int = 50):
    opp = OpportunityEngine()
    df = opp.score_all()
    if df.empty:
        return []
    if territory:
        df = df[df["territory"] == territory]
    if specialty:
        df = df[df["specialty_group"] == specialty]
    if rep_id:
        store = DataStore.instance()
        rep = store.rep(rep_id)
        if rep:
            df = df[df["territory"] == rep["territory"]]
    cols = [
        "hcp_id", "hcp_name", "specialty_group", "sub_specialty", "territory", "region",
        "opportunity_score", "score_confidence", "consent_status",
        "drv_growth", "drv_engagement", "drv_publications", "drv_kol", "drv_history", "drv_urgency",
        "channel_preference", "affiliated_hospital",
    ]
    return df.head(limit)[cols].to_dict("records")


@router.get("/explain/{hcp_id}")
def explain(hcp_id: str):
    opp = OpportunityEngine()
    nba = opp.nba_for(hcp_id)
    if not nba:
        raise HTTPException(404, "HCP not found")
    return nba


@router.get("/simulate")
def simulate(hcp_id: str, scenario: str = "competitor_event"):
    """Tiny scenario simulator — bumps drivers and recomputes rule output."""
    opp = OpportunityEngine()
    df = opp.score_all()
    base = df[df["hcp_id"] == hcp_id]
    if base.empty:
        raise HTTPException(404, "HCP not found")
    row = base.iloc[0].to_dict()
    before = opp.nba_for(hcp_id)
    # adjust based on scenario
    adj = dict(row)
    delta = {}
    if scenario == "competitor_event":
        adj["drv_urgency"] = min(100, row["drv_urgency"] + 35)
        delta["drv_urgency"] = "+35"
    elif scenario == "new_publication":
        adj["drv_publications"] = min(100, row["drv_publications"] + 25)
        adj["drv_kol"] = min(100, row["drv_kol"] + 10)
        delta = {"drv_publications": "+25", "drv_kol": "+10"}
    elif scenario == "digital_boost":
        adj["drv_engagement"] = min(100, row["drv_engagement"] + 20)
        delta = {"drv_engagement": "+20"}
    elif scenario == "rep_reassign":
        # reduce engagement and history
        adj["drv_engagement"] = max(0, row["drv_engagement"] - 15)
        delta = {"drv_engagement": "-15"}
    after_rule = opp._rule_engine(adj)
    new_score = round(
        0.20 * adj["drv_growth"]
        + 0.15 * adj["drv_engagement"]
        + 0.10 * adj["drv_publications"]
        + 0.15 * adj["drv_kol"]
        + 0.20 * adj["drv_history"]
        + 0.10 * adj["drv_urgency"]
        + 0.10 * (100 - 50 * row["saturation"]), 1
    ) / 100 * 100
    return {
        "hcp_id": hcp_id,
        "scenario": scenario,
        "before": before,
        "after": {
            "opportunity_score": round(new_score, 2),
            "recommendation": after_rule,
            "delta": delta,
        },
    }
