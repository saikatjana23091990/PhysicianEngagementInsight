"""KOL analytics: influence dashboard, network graph, trends, opportunity overlay."""
from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx

from app.data.store import DataStore


class KOLEngine:
    def __init__(self) -> None:
        self.store = DataStore.instance()

    def dashboard(self) -> dict:
        kols = self.store.df("kol_master")
        if kols.empty:
            return {"summary": {}, "by_tier": [], "top": []}

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

    def network(self, kol_id: str | None = None) -> dict:
        kols = self.store.df("kol_master")
        rels = self.store.df("kol_relationship_source")
        if kols.empty:
            return {"nodes": [], "edges": []}
        if kol_id:
            # 1-hop neighborhood
            mask = (rels["kol_id_1"] == kol_id) | (rels["kol_id_2"] == kol_id)
            sub = rels[mask]
            ids = set([kol_id]) | set(sub["kol_id_1"]) | set(sub["kol_id_2"])
            nodes = kols[kols["kol_id"].isin(ids)]
        else:
            nodes = kols
            sub = rels

        node_list = []
        for _, n in nodes.iterrows():
            node_list.append({
                "id": n["kol_id"],
                "label": n["hcp_name"],
                "specialty": n["specialty_group"],
                "tier": n["kol_tier"],
                "influence": float(n["influence_score"]),
                "centrality": float(n["network_centrality_score"]),
                "region": n["region"],
            })
        edges = []
        for _, e in sub.iterrows():
            edges.append({
                "source": e["kol_id_1"],
                "target": e["kol_id_2"],
                "weight": float(e["edge_weight"]),
                "type": e["relationship_type"],
                "topic": e["shared_topic"],
            })
        return {"nodes": node_list, "edges": edges}

    def topic_trends(self) -> list:
        kols = self.store.df("kol_master")
        if kols.empty:
            return []
        topic = kols.groupby("topic_focus_primary").agg(
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

    def kol_detail(self, kol_id: str) -> dict:
        kols = self.store.df("kol_master")
        rels = self.store.df("kol_relationship_source")
        pubs = self.store.df("publication_source")
        events = self.store.df("event_source")
        row = kols[kols["kol_id"] == kol_id]
        if row.empty:
            return {}
        profile = row.iloc[0].to_dict()
        hcp_id = profile["hcp_id"]
        related = rels[(rels["kol_id_1"] == kol_id) | (rels["kol_id_2"] == kol_id)]
        pub_list = pubs[pubs["hcp_id"] == hcp_id].sort_values("publication_date", ascending=False).head(10).to_dict("records")
        evt_list = events[events["hcp_id"] == hcp_id].sort_values("event_date", ascending=False).head(10).to_dict("records")
        return {
            "profile": profile,
            "publications": pub_list,
            "events": evt_list,
            "relationships": related.to_dict("records"),
        }
