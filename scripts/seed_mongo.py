"""
Optional: seed all source CSVs into MongoDB.
The runtime DataStore is in-memory (pandas) by default. This script materializes
the same data into Mongo for downstream pipelines (e.g., persistent audit logs,
collaborative annotations).
"""
import os
import sys
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data/raw/data"))
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "commercial_analytics")

TABLES = [
    "hcp_master", "account_master", "product_master", "rep_master", "rep_quota_source",
    "field_interactions_source", "prescription_claims_source", "publication_source",
    "event_source", "digital_engagement_source", "market_events_source",
    "conversion_events_source", "kol_master", "kol_relationship_source",
]


def main():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    for t in TABLES:
        fp = DATA_DIR / f"{t}.csv"
        if not fp.exists():
            print(f"[skip] {t}: missing {fp}")
            continue
        df = pd.read_csv(fp)
        # parse dates
        for c in df.columns:
            if "date" in c or "timestamp" in c or "month" in c:
                df[c] = pd.to_datetime(df[c], errors="coerce")
        records = df.to_dict(orient="records")
        db[t].drop()
        if records:
            db[t].insert_many(records)
        print(f"[ok] {t}: {len(records)} rows")
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
