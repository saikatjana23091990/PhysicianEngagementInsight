from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import json

from app.data.store import DataStore, serialize_df
from app.services.conversion_engine import ConversionEngine
from app.services.opportunity_engine import OpportunityEngine

router = APIRouter(prefix="/hcp", tags=["hcp"])


@router.get("/list")
def hcp_list(
    q: Optional[str] = None,
    specialty: Optional[str] = None,
    territory: Optional[str] = None,
    region: Optional[str] = None,
    consent: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    store = DataStore.instance()
    df = store.df("hcp_master")
    if q:
        df = df[df["hcp_name"].str.contains(q, case=False, na=False) | df["hcp_id"].str.contains(q, case=False, na=False)]
    if specialty:
        df = df[df["specialty_group"] == specialty]
    if territory:
        df = df[df["territory"] == territory]
    if region:
        df = df[df["region"] == region]
    if consent:
        df = df[df["consent_status"] == consent]
    total = len(df)
    df = df.iloc[offset: offset + limit]
    return {"total": total, "items": serialize_df(df)}


@router.get("/specialties")
def specialties():
    store = DataStore.instance()
    df = store.df("hcp_master")
    return sorted(df["specialty_group"].dropna().unique().tolist())


@router.get("/{hcp_id}")
def hcp_detail(hcp_id: str):
    store = DataStore.instance()
    hcp = store.hcp(hcp_id)
    if not hcp:
        raise HTTPException(404, "HCP not found")
    account = store.account(hcp.get("affiliated_account_id")) or {}
    claims = store.df("prescription_claims_source")
    claims = claims[claims["hcp_id"] == hcp_id].sort_values("service_month", ascending=False)
    eng = ConversionEngine()
    calls = eng.calls()
    calls = calls[calls["hcp_id"] == hcp_id].sort_values("interaction_datetime", ascending=False)
    pubs = store.df("publication_source")
    pubs = pubs[pubs["hcp_id"] == hcp_id].sort_values("publication_date", ascending=False)
    events = store.df("event_source")
    events = events[events["hcp_id"] == hcp_id].sort_values("event_date", ascending=False)
    digital = store.df("digital_engagement_source")
    digital = digital[digital["hcp_id"] == hcp_id].sort_values("engagement_date", ascending=False)
    kols = store.df("kol_master")
    kol = kols[kols["hcp_id"] == hcp_id]
    return {
        "hcp": hcp,
        "account": account,
        "claims": serialize_df(claims, 60),
        "calls": serialize_df(calls[[
            "interaction_id", "interaction_datetime", "rep_id", "channel", "discussion_topic",
            "call_outcome", "objection_raised_flag", "follow_up_required_flag",
            "crm_note_raw", "next_step_raw", "converted", "conversion_type",
            "days_to_conversion", "attribution_confidence",
        ]], 50),
        "publications": serialize_df(pubs, 20),
        "events": serialize_df(events, 20),
        "digital_engagement": serialize_df(digital, 30),
        "kol_profile": serialize_df(kol)[0] if not kol.empty else None,
    }


@router.get("/{hcp_id}/opportunity")
def hcp_opportunity(hcp_id: str):
    opp = OpportunityEngine()
    nba = opp.nba_for(hcp_id)
    if not nba:
        raise HTTPException(404, "HCP not found")
    return nba
