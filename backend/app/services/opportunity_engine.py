"""
Opportunity scoring + Next-Best-Action engine.

Score drivers (explainable):
- prescribing_trajectory (claims growth)
- recent_engagement (calls / digital in last 90 days)
- specialty_fit (relevance to brand therapy area)
- publication_influence (KOL + pubs)
- event_urgency (market events affecting product/region)
- conversion_propensity (historical conversion rate of similar HCPs)
- consent / access (suppressor)
- engagement_saturation (suppressor when over-touched)

NBA rule layer turns the scores + signals into specific recommendations with rationale.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.data.store import DataStore
from app.services.conversion_engine import ConversionEngine


class OpportunityEngine:
    def __init__(self) -> None:
        self.store = DataStore.instance()
        self.conv = ConversionEngine()
        self._features_cache: Optional[pd.DataFrame] = None
        self._model: Optional[LogisticRegression] = None
        self._scaler: Optional[StandardScaler] = None

    # ----------------- feature engineering ------------------------
    def build_features(self) -> pd.DataFrame:
        if self._features_cache is not None:
            return self._features_cache

        hcps = self.store.df("hcp_master").copy()
        if hcps.empty:
            self._features_cache = hcps
            return hcps

        calls = self.conv.calls()
        claims = self.store.df("prescription_claims_source").copy()
        pubs = self.store.df("publication_source").copy()
        digital = self.store.df("digital_engagement_source").copy()
        events = self.store.df("event_source").copy()
        kols = self.store.df("kol_master").copy()
        mkt = self.store.df("market_events_source").copy()

        # Define analytical "now" as latest call datetime across data (so demo is stable)
        if not calls.empty:
            now = calls["interaction_datetime"].max()
        else:
            now = pd.Timestamp.utcnow()

        # claims growth: (recent 90d nrx) / (prior 90d nrx)
        if not claims.empty:
            claims["service_month"] = pd.to_datetime(claims["service_month"])
            recent_mask = claims["service_month"] >= (now - pd.Timedelta(days=90))
            prior_mask = (claims["service_month"] < (now - pd.Timedelta(days=90))) & (
                claims["service_month"] >= (now - pd.Timedelta(days=180))
            )
            r = claims[recent_mask].groupby("hcp_id")["n_rx"].sum().rename("rx_recent")
            p = claims[prior_mask].groupby("hcp_id")["n_rx"].sum().rename("rx_prior")
            total_rx = claims.groupby("hcp_id")["n_rx"].sum().rename("rx_total")
            new_rx = claims.groupby("hcp_id")["new_rx"].sum().rename("new_rx_total")
        else:
            r = p = total_rx = new_rx = pd.Series(dtype=float)

        # recent engagement: calls + digital touchpoints in last 90 days
        if not calls.empty:
            mask = calls["interaction_datetime"] >= (now - pd.Timedelta(days=90))
            recent_calls = calls[mask].groupby("hcp_id")["interaction_id"].count().rename("calls_90d")
        else:
            recent_calls = pd.Series(dtype=float)

        if not digital.empty:
            digital["engagement_date"] = pd.to_datetime(digital["engagement_date"])
            mask = digital["engagement_date"] >= (now - pd.Timedelta(days=90))
            recent_digital = digital[mask].groupby("hcp_id")["engagement_value"].sum().rename("digital_90d")
        else:
            recent_digital = pd.Series(dtype=float)

        # publication signal
        if not pubs.empty:
            pubs["publication_date"] = pd.to_datetime(pubs["publication_date"])
            mask = pubs["publication_date"] >= (now - pd.Timedelta(days=365))
            pub_count = pubs[mask].groupby("hcp_id")["publication_id"].count().rename("pub_count_12m")
            pub_relev = pubs[mask].groupby("hcp_id")["relevance_score"].mean().rename("pub_relevance_avg")
        else:
            pub_count = pub_relev = pd.Series(dtype=float)

        # event signal
        if not events.empty:
            events["event_date"] = pd.to_datetime(events["event_date"])
            mask = events["event_date"] >= (now - pd.Timedelta(days=365))
            evt_score = events[mask].groupby("hcp_id")["engagement_score"].mean().rename("event_score_avg")
        else:
            evt_score = pd.Series(dtype=float)

        # KOL features
        kol_features = pd.DataFrame()
        if not kols.empty:
            kol_features = kols.set_index("hcp_id")[["influence_score", "network_centrality_score",
                                                      "citation_count_5y", "kol_tier"]]
            kol_features.columns = ["kol_influence", "kol_centrality", "kol_citations", "kol_tier"]

        # historical conversion at hcp level
        if not calls.empty:
            hcp_conv = calls.groupby("hcp_id")["converted"].mean().rename("hcp_hist_conv_rate")
        else:
            hcp_conv = pd.Series(dtype=float)

        # event_urgency: any high severity market event in last 60 days for product in HCP's region
        urgency = pd.Series(0.0, index=hcps["hcp_id"])
        if not mkt.empty:
            mkt = mkt.copy()
            mkt["event_date"] = pd.to_datetime(mkt["event_date"])
            recent_mkt = mkt[mkt["event_date"] >= (now - pd.Timedelta(days=60))]
            sev_map = {"Low": 0.3, "Medium": 0.6, "High": 1.0}
            for _, row in recent_mkt.iterrows():
                sev = sev_map.get(row["event_severity"], 0.5)
                region = row["region"]
                hids = hcps.loc[hcps["region"] == region, "hcp_id"]
                urgency.loc[hids] = np.maximum(urgency.loc[hids].values, sev)

        # Assemble
        f = hcps.set_index("hcp_id")[[
            "hcp_name", "specialty_group", "sub_specialty", "territory", "region",
            "channel_preference", "consent_status", "digital_engagement_tier",
            "speaker_potential_flag", "publication_activity_level",
            "affiliated_account_id", "affiliated_hospital",
        ]].copy()
        f = f.join([r, p, total_rx, new_rx, recent_calls, recent_digital, pub_count,
                    pub_relev, evt_score, hcp_conv, kol_features], how="left")
        f["event_urgency"] = urgency
        f = f.fillna({
            "rx_recent": 0, "rx_prior": 0, "rx_total": 0, "new_rx_total": 0,
            "calls_90d": 0, "digital_90d": 0, "pub_count_12m": 0, "pub_relevance_avg": 0,
            "event_score_avg": 0, "hcp_hist_conv_rate": 0, "kol_influence": 0,
            "kol_centrality": 0, "kol_citations": 0, "event_urgency": 0,
        })

        # growth ratio (cap at 5x)
        f["rx_growth"] = np.where(f["rx_prior"] > 0, f["rx_recent"] / f["rx_prior"], 1.0)
        f["rx_growth"] = f["rx_growth"].clip(0, 5)

        # consent suppressor
        f["consent_ok"] = (f["consent_status"] != "Opted-out").astype(int)

        # engagement saturation: penalty if calls_90d > 6 and digital_90d > 200
        f["saturation"] = ((f["calls_90d"] > 6) & (f["digital_90d"] > 200)).astype(int)

        self._features_cache = f.reset_index()
        return self._features_cache

    # ---------------- scoring -------------------------
    def score_all(self) -> pd.DataFrame:
        f = self.build_features().copy()
        if f.empty:
            return f

        # Normalize key drivers to [0,1]
        def norm(s: pd.Series) -> pd.Series:
            if s.max() == s.min():
                return pd.Series(0.5, index=s.index)
            return (s - s.min()) / (s.max() - s.min())

        n_growth = norm(f["rx_growth"])
        n_eng = norm(f["calls_90d"] + 0.05 * f["digital_90d"])
        n_pub = norm(f["pub_count_12m"] * (0.5 + f["pub_relevance_avg"]))
        n_kol = norm(f["kol_influence"] + 0.5 * f["kol_centrality"])
        n_hist = norm(f["hcp_hist_conv_rate"])
        n_urg = f["event_urgency"]  # already 0-1

        # Weighted composite (rule-based)
        rule_score = (
            0.20 * n_growth
            + 0.15 * n_eng
            + 0.10 * n_pub
            + 0.15 * n_kol
            + 0.20 * n_hist
            + 0.10 * n_urg
            + 0.10 * (1.0 - 0.5 * f["saturation"])
        )

        # ML propensity score (XGBoost)
        from app.ml.propensity import get_propensity_model
        ml = get_propensity_model(f)
        ml_score = ml.predict_proba(f)

        # Blend rule (60%) + ML (40%), apply consent multiplier
        blended = (0.6 * rule_score + 0.4 * ml_score) * (0.4 + 0.6 * f["consent_ok"])
        f["opportunity_score"] = (blended * 100).round(2)
        f["ml_propensity"] = (ml_score * 100).round(1)
        f["rule_score"] = (rule_score * 100).round(1)
        f["model_status"] = ml.status

        # Drivers (for explainability)
        f["drv_growth"] = (n_growth * 100).round(1)
        f["drv_engagement"] = (n_eng * 100).round(1)
        f["drv_publications"] = (n_pub * 100).round(1)
        f["drv_kol"] = (n_kol * 100).round(1)
        f["drv_history"] = (n_hist * 100).round(1)
        f["drv_urgency"] = (n_urg * 100).round(1)

        # Confidence proxy from data completeness + ML confidence
        signals = (f[["rx_total", "calls_90d", "pub_count_12m", "kol_influence"]] > 0).sum(axis=1)
        base_conf = signals / 4.0 * 0.6 + 0.3
        # ML adds confidence when predictions are decisive (far from 0.5)
        ml_conf_boost = 0.1 * (1.0 - 4.0 * np.abs(ml_score - 0.5).clip(0, 0.5))
        f["score_confidence"] = (base_conf + ml_conf_boost).clip(0, 1).round(2)
        return f.sort_values("opportunity_score", ascending=False)

    # ---------------- NBA -----------------------------
    def nba_for(self, hcp_id: str) -> dict:
        df = self.score_all()
        row = df[df["hcp_id"] == hcp_id]
        if row.empty:
            return {}
        r = row.iloc[0].to_dict()
        return {
            "hcp_id": hcp_id,
            "opportunity_score": r["opportunity_score"],
            "confidence": r["score_confidence"],
            "recommendation": self._rule_engine(r),
            "drivers": self._top_drivers(r),
            "suppressors": self._suppressors(r),
        }

    def _rule_engine(self, r: dict) -> dict:
        if r["consent_status"] == "Opted-out":
            return {
                "action": "Hold — Consent",
                "rationale": "HCP is opted-out of commercial contact. Route any clinical needs to MSL.",
                "priority": "Suppressed",
                "channel": "MSL",
            }
        if r.get("drv_urgency", 0) > 60 and r["opportunity_score"] > 50:
            return {
                "action": "Visit now",
                "rationale": "Market event urgency is high in HCP region. Prioritize same-week visit.",
                "priority": "High",
                "channel": r.get("channel_preference", "In-person"),
            }
        if r.get("drv_publications", 0) > 70 and r.get("kol_influence", 0) > 0.6:
            return {
                "action": "Send clinical update + schedule meeting",
                "rationale": "Strong KOL influence and recent publication activity. Lead with evidence.",
                "priority": "High",
                "channel": "Hybrid",
            }
        if r.get("drv_growth", 0) > 65:
            return {
                "action": "Increase cadence",
                "rationale": "Prescribing trajectory is strongly accelerating. Reinforce engagement to capture growth.",
                "priority": "Medium",
                "channel": r.get("channel_preference", "In-person"),
            }
        if r.get("saturation", 0):
            return {
                "action": "Pause / digital-only",
                "rationale": "Engagement saturation detected. Pause field calls; shift to targeted digital.",
                "priority": "Low",
                "channel": "Digital",
            }
        if r["opportunity_score"] > 60:
            return {
                "action": "Maintain cadence",
                "rationale": "Stable high-opportunity HCP. Continue current engagement plan.",
                "priority": "Medium",
                "channel": r.get("channel_preference", "In-person"),
            }
        return {
            "action": "Monitor",
            "rationale": "Low opportunity signal. Monitor for triggering events before activation.",
            "priority": "Low",
            "channel": "Digital",
        }

    def _top_drivers(self, r: dict) -> list:
        keys = [
            ("Prescribing trajectory", r.get("drv_growth")),
            ("Recent engagement", r.get("drv_engagement")),
            ("Publication signal", r.get("drv_publications")),
            ("KOL influence", r.get("drv_kol")),
            ("Historical conversion", r.get("drv_history")),
            ("Market urgency", r.get("drv_urgency")),
        ]
        keys = [(k, v) for k, v in keys if v is not None]
        return sorted(keys, key=lambda x: -float(x[1]))[:5]

    def _suppressors(self, r: dict) -> list:
        sup = []
        if r["consent_status"] == "Opted-out":
            sup.append({"factor": "Consent", "impact": "Hard block"})
        if r.get("saturation"):
            sup.append({"factor": "Engagement saturation", "impact": "Medium"})
        return sup
