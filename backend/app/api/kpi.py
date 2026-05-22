from typing import Optional
from fastapi import APIRouter, Query

from app.services.conversion_engine import ConversionEngine
from app.data.store import DataStore

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/overview")
def overview():
    eng = ConversionEngine()
    overall = eng.overall()
    store = DataStore.instance()
    hcp_n = len(store.df("hcp_master"))
    rep_n = len(store.df("rep_master"))
    accounts = len(store.df("account_master"))
    products = len(store.df("product_master"))
    return {
        "conversion": overall.__dict__,
        "totals": {
            "hcps": hcp_n,
            "reps": rep_n,
            "accounts": accounts,
            "products": products,
            "interactions": len(store.df("field_interactions_source")),
            "conversions": len(store.df("conversion_events_source")),
            "publications": len(store.df("publication_source")),
            "events": len(store.df("event_source")),
            "kols": len(store.df("kol_master")),
        },
    }
