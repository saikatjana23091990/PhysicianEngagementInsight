"""
DataStore: In-memory + Mongo-backed raw layer with derived feature tables computed at runtime.

Layers:
- RAW: pandas DataFrames loaded from /app/data/raw/data/*.csv (source-only)
- PROCESSED: cleaned + ID-resolved
- FEATURE: rolling conversion, recency, opportunity features computed lazily

This in-memory store keeps things simple for the demo while preserving layer separation
declared by the design. Mongo can be plugged in later for persistence (see app.data.mongo_sync).
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data/raw/data"))

SOURCE_TABLES = [
    "hcp_master",
    "account_master",
    "product_master",
    "rep_master",
    "rep_quota_source",
    "field_interactions_source",
    "prescription_claims_source",
    "publication_source",
    "event_source",
    "digital_engagement_source",
    "market_events_source",
    "conversion_events_source",
    "kol_master",
    "kol_relationship_source",
]


class DataStore:
    _instance: Optional["DataStore"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.raw: Dict[str, pd.DataFrame] = {}
        self.loaded = False

    @classmethod
    def instance(cls) -> "DataStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = DataStore()
        return cls._instance

    # ----------------------- LOADING ------------------------------------
    def load_all(self) -> None:
        for t in SOURCE_TABLES:
            fp = DATA_DIR / f"{t}.csv"
            if not fp.exists():
                self.raw[t] = pd.DataFrame()
                continue
            df = pd.read_csv(fp)
            # Coerce datetime columns
            for col in df.columns:
                if "date" in col or "timestamp" in col or "month" in col:
                    try:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    except Exception:
                        pass
            self.raw[t] = df
        self._post_process()
        self.loaded = True

    def _post_process(self) -> None:
        # Identity resolution: ensure hcp_master has flags merged
        # Build convenient indexes
        if not self.raw.get("field_interactions_source", pd.DataFrame()).empty:
            self.raw["field_interactions_source"]["interaction_date"] = (
                self.raw["field_interactions_source"]["interaction_datetime"].dt.date
            )

    def counts(self) -> Dict[str, int]:
        return {t: len(df) for t, df in self.raw.items()}

    # ------------------- ACCESSORS --------------------------------------
    def df(self, name: str) -> pd.DataFrame:
        return self.raw.get(name, pd.DataFrame()).copy()

    # Quick lookups
    def hcp(self, hcp_id: str) -> Optional[dict]:
        df = self.raw["hcp_master"]
        row = df[df["hcp_id"] == hcp_id]
        return None if row.empty else _to_dict(row.iloc[0])

    def rep(self, rep_id: str) -> Optional[dict]:
        df = self.raw["rep_master"]
        row = df[df["rep_id"] == rep_id]
        return None if row.empty else _to_dict(row.iloc[0])

    def account(self, account_id: str) -> Optional[dict]:
        df = self.raw["account_master"]
        row = df[df["account_id"] == account_id]
        return None if row.empty else _to_dict(row.iloc[0])

    def product(self, product_id: str) -> Optional[dict]:
        df = self.raw["product_master"]
        row = df[df["product_id"] == product_id]
        return None if row.empty else _to_dict(row.iloc[0])


def _to_dict(row: pd.Series) -> dict:
    d = row.to_dict()
    out = {}
    for k, v in d.items():
        if pd.isna(v):
            out[k] = None
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (np.integer,)):
            out[k] = int(v)
        elif isinstance(v, (np.floating,)):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def serialize_df(df: pd.DataFrame, limit: Optional[int] = None) -> list:
    """Convert DataFrame to list of dicts safe for JSON."""
    if df is None or df.empty:
        return []
    if limit is not None:
        df = df.head(limit)
    out = []
    for _, row in df.iterrows():
        out.append(_to_dict(row))
    return out
