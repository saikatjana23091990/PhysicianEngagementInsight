"""Source Explorer API — raw layer access with pagination."""
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.data.store import DataStore, serialize_df, SOURCE_TABLES

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/tables")
def tables():
    store = DataStore.instance()
    return [{"name": t, "rows": len(store.df(t))} for t in SOURCE_TABLES]


@router.get("/table/{name}")
def table(name: str, limit: int = 100, offset: int = 0, q: Optional[str] = None):
    if name not in SOURCE_TABLES:
        raise HTTPException(404, "Unknown table")
    store = DataStore.instance()
    df = store.df(name)
    if q:
        text_cols = df.select_dtypes(include="object").columns
        if len(text_cols):
            mask = False
            for c in text_cols:
                mask = mask | df[c].astype(str).str.contains(q, case=False, na=False)
            df = df[mask]
    total = len(df)
    cols = list(df.columns)
    df = df.iloc[offset: offset + limit]
    return {"name": name, "total": total, "columns": cols, "items": serialize_df(df)}
