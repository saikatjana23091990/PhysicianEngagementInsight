from typing import Optional
from fastapi import APIRouter

from app.services.kol_engine import KOLEngine
from app.data.store import serialize_df, DataStore

router = APIRouter(prefix="/kol", tags=["kol"])


@router.get("/dashboard")
def dashboard():
    eng = KOLEngine()
    return eng.dashboard()


@router.get("/list")
def kol_list(tier: Optional[str] = None, region: Optional[str] = None, specialty: Optional[str] = None):
    store = DataStore.instance()
    df = store.df("kol_master")
    if tier:
        df = df[df["kol_tier"] == tier]
    if region:
        df = df[df["region"] == region]
    if specialty:
        df = df[df["specialty_group"] == specialty]
    return df.sort_values("influence_score", ascending=False).to_dict("records")


@router.get("/network")
def network(kol_id: Optional[str] = None):
    eng = KOLEngine()
    return eng.network(kol_id)


@router.get("/topics")
def topics():
    eng = KOLEngine()
    return eng.topic_trends()


@router.get("/{kol_id}")
def detail(kol_id: str):
    eng = KOLEngine()
    return eng.kol_detail(kol_id)
