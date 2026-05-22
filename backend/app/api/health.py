from fastapi import APIRouter
from app.data.store import DataStore

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    ds = DataStore.instance()
    return {
        "status": "ok",
        "data_loaded": ds.loaded,
        "row_counts": ds.counts() if ds.loaded else {},
    }
