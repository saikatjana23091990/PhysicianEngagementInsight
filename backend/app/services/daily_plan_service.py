"""
Daily plan generation service.
Uses existing opportunity, conversion, KOL, and market signals to generate a prioritized daily execution plan for reps.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, time, timedelta
from typing import Optional

import numpy as np

from app.data.mongo import log_daily_plan_history
from app.data.store import DataStore
from app.services.conversion_engine import ConversionEngine
from app.services.kol_engine import KOLEngine
from app.services.opportunity_engine import OpportunityEngine

PRIORITY_THRESHOLDS = [(85, "Critical"), (70, "High"), (50, "Medium"), (0, "Low")]
DEFAULT_DURATIONS = {
    "Pre-call Prep": 15,
    "Virtual Call": 30,
    "HCP Visit": 60,
    "MSL Discussion": 45,
    "KOL Meeting": 60,
    "Territory Review": 30,
    "Follow-up Task": 15,
    "Send Email": 15,
    "Clinical Discussion": 30,
    "Webinar Invite": 45,
    "Market Review": 30,
}
BUSINESS_START = time(8, 30)
BUSINESS_END = time(17, 30)


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value) if value is not None else default
    except Exception:
        return default


class DailyPlanService:
    def __init__(self) -> None:
        self.store = DataStore.instance()
        self.opp = OpportunityEngine()
        self.conv = ConversionEngine()
        self.kol = KOLEngine()

    def generate_plan(self, rep_id: str, plan_date: Optional[str] = None) -> dict:
        rep = self.store.rep(rep_id)
        if not rep:
            return {}

        if plan_date:
            plan_date_obj = datetime.fromisoformat(plan_date).date()
        else:
            plan_date_obj = datetime.utcnow().date()

        candidates = self._build_candidate_actions(rep)
        actions = self._score_and_schedule(candidates, plan_date_obj)
        summary = self._build_summary(actions)

        payload = {
            "rep_id": rep_id,
            "rep_name": rep.get("rep_name"),
            "plan_date": plan_date_obj.isoformat(),
            "generated_timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
            "actions": actions,
        }

        try:
            import asyncio

            if asyncio.get_event_loop().is_running():
                asyncio.create_task(
                    log_daily_plan_history(rep_id, payload["plan_date"], actions, payload["generated_timestamp"])
                )
        except Exception:
            pass

        return payload

    def _build_candidate_actions(self, rep: dict) -> list[dict]:
        actions = []
        opp_df = self.opp.score_all()
        if not opp_df.empty and rep.get("territory"):
            opp_df = opp_df[opp_df["territory"] == rep["territory"]]
        opp_df = opp_df.head(18)

        for _, row in opp_df.iterrows():
            action_type = (
                "HCP Visit"
                if row.get("channel_preference") == "In-Person"
                else "Virtual Call"
                if row.get("channel_preference") == "Virtual"
                else "HCP Visit"
            )
            actions.append(self._build_action_template(
                rep,
                row,
                action_type,
                DEFAULT_DURATIONS.get(action_type, 30),
                title=f"{action_type} with {row.get('hcp_name')}",
                expected_outcome=f"Advance {row.get('specialty_group')} opportunity with {row.get('hcp_name')}",
                conversion_probability=_safe_float(row.get("hcp_hist_conv_rate"), 0.0) * 100.0,
                extra={
                    "therapy_area": row.get("specialty_group"),
                    "product_focus": row.get("brand_name") or "Product Focus",
                    "conversion_opportunity": _safe_float(row.get("opportunity_score"), 0.0),
                    "nba_rationale": f"Opportunity score {row.get('opportunity_score')} with confidence {row.get('score_confidence')}",
                    "drivers": {
                        "growth": _safe_float(row.get("drv_growth")),
                        "engagement": _safe_float(row.get("drv_engagement")),
                        "publications": _safe_float(row.get("drv_publications")),
                        "kol": _safe_float(row.get("drv_kol")),
                        "history": _safe_float(row.get("drv_history")),
                        "urgency": _safe_float(row.get("drv_urgency")),
                    },
                },
            ))

        followups = self.store.df("field_interactions_source")
        if not followups.empty and "follow_up_required_flag" in followups.columns:
            followups = followups[
                (followups["rep_id"] == rep["rep_id"]) &
                (followups["follow_up_required_flag"] == True)
            ].sort_values("interaction_datetime", ascending=False).head(8)
            for _, row in followups.iterrows():
                hcp = self.store.hcp(row.get("hcp_id")) or {}
                actions.append(self._build_action_template(
                    rep,
                    row,
                    "Follow-up Task",
                    DEFAULT_DURATIONS["Follow-up Task"],
                    title=f"Follow-up with {hcp.get('hcp_name') or 'HCP'}",
                    expected_outcome="Close the follow-up loop and convert momentum",
                    conversion_probability=40.0,
                    extra={
                        "therapy_area": hcp.get("specialty_group"),
                        "product_focus": hcp.get("primary_therapy_area"),
                        "conversion_opportunity": 45.0,
                        "nba_rationale": "Follow-up required after recent interaction",
                        "drivers": {
                            "recent_interaction": 100.0,
                            "follow_up_flag": 100.0,
                        },
                    },
                ))

        kol_df = self.store.df("kol_master")
        if not kol_df.empty:
            kol_df = kol_df[kol_df["region"] == rep.get("region", "")]
            kol_df = kol_df.sort_values("influence_score", ascending=False).head(8)
            for _, row in kol_df.iterrows():
                actions.append(self._build_action_template(
                    rep,
                    row,
                    "KOL Meeting",
                    DEFAULT_DURATIONS["KOL Meeting"],
                    title=f"Meet KOL {row.get('hcp_name')}",
                    expected_outcome="Capture KOL influence and secure clinical advocacy",
                    conversion_probability=min(100.0, _safe_float(row.get("influence_score"), 0.0) * 20.0),
                    extra={
                        "therapy_area": row.get("specialty_group"),
                        "product_focus": row.get("topic_focus_primary") or "Clinical Discussion",
                        "conversion_opportunity": _safe_float(row.get("influence_score"), 0.0) * 20.0,
                        "nba_rationale": "High KOL influence score and relevant publication signals",
                        "drivers": {
                            "kol_influence": _safe_float(row.get("influence_score")),
                            "citation_count": _safe_float(row.get("citation_count_5y")),
                        },
                    },
                ))

        events = self.store.df("market_events_source")
        if not events.empty:
            events = events[events["region"] == rep.get("region", "")]
            if not events.empty:
                event = events.sort_values("event_date", ascending=False).iloc[0]
                actions.append(self._build_action_template(
                    rep,
                    event,
                    "Market Review",
                    DEFAULT_DURATIONS["Market Review"],
                    title="Review Market Event Impact",
                    expected_outcome="Understand the latest market changes driving territory urgency",
                    conversion_probability=25.0,
                    extra={
                        "therapy_area": event.get("therapy_area"),
                        "product_focus": (self.store.product(event.get("product_id")) or {}).get("brand_name", "Market Portfolio"),
                        "conversion_opportunity": _safe_float(event.get("engagement_score"), 0.0) * 10.0,
                        "nba_rationale": "Recent market event affecting rep region",
                        "drivers": {
                            "market_urgency": _safe_float(event.get("engagement_score")),
                        },
                    },
                ))

        actions.append(self._build_action_template(
            rep,
            {"hcp_name": rep.get("rep_name"), "territory": rep.get("territory")},
            "Territory Review",
            DEFAULT_DURATIONS["Territory Review"],
            title="Review Territory Opportunities",
            expected_outcome="Align daily focus with territory priorities and coverage gaps",
            conversion_probability=18.0,
            extra={
                "therapy_area": rep.get("primary_therapy_area"),
                "product_focus": "Territory portfolio",
                "conversion_opportunity": 32.0,
                "nba_rationale": "Daily territory coverage supports execution consistency",
                "drivers": {
                    "territory_priority": 80.0,
                },
            },
        ))

        return actions

    def _build_action_template(self, rep, row, action_type, duration, title=None, expected_outcome=None, conversion_probability=None, extra=None) -> dict:
        hcp_name = row.get("hcp_name") or row.get("rep_name") or "Unknown HCP"
        account = row.get("affiliated_account_id") or row.get("affiliated_hospital") or row.get("territory") or rep.get("territory")
        drivers = (extra or {}).get("drivers", {})
        return {
            "action_id": str(uuid.uuid4()),
            "action_type": action_type,
            "title": title or action_type,
            "hcp_name": hcp_name,
            "account": account,
            "priority": "Medium",
            "duration_minutes": duration,
            "scheduled_time": None,
            "expected_outcome": expected_outcome or "",
            "confidence_score": round(_safe_float(row.get("score_confidence"), 0.6) * 100.0, 1),
            "opportunity_score": _safe_float((extra or {}).get("conversion_opportunity") or row.get("opportunity_score"), 0.0),
            "conversion_probability": round(_safe_float(conversion_probability, 0.0), 1),
            "therapy_area": (extra or {}).get("therapy_area") or row.get("specialty_group") or rep.get("primary_therapy_area"),
            "product_focus": (extra or {}).get("product_focus") or row.get("brand_name") or "Product Focus",
            "conversion_opportunity": _safe_float((extra or {}).get("conversion_opportunity") or row.get("opportunity_score"), 0.0),
            "nba_rationale": (extra or {}).get("nba_rationale") or "",
            "details": {
                "drivers": drivers,
                "recent_claims_signals": [],
                "kol_influence": _safe_float(row.get("kol_influence"), 0.0),
                "market_event_impact": _safe_float(row.get("event_urgency"), 0.0),
            },
            "status": "planned",
            "actual_outcome": None,
            "reason": None,
        }

    def _score_and_schedule(self, actions: list[dict], plan_date: date) -> list[dict]:
        if not actions:
            return []

        opp = np.array([a["opportunity_score"] / 100.0 for a in actions], dtype=float)
        conv = np.array([a["conversion_probability"] / 100.0 for a in actions], dtype=float)
        kol = np.array([a["details"]["kol_influence"] / 100.0 for a in actions], dtype=float)
        gap = np.array([
            max(0.0, 1.0 - min(10.0, float(a["details"]["drivers"].get("recent_interaction", 0.0)) / 10.0))
            if a["details"]["drivers"] else 0.5
            for a in actions
        ], dtype=float)
        market = np.array([a["details"]["market_event_impact"] / 1.0 for a in actions], dtype=float)
        territory = np.array([min(1.0, float(a["details"]["drivers"].get("territory_priority", 0.0)) / 100.0) for a in actions], dtype=float)

        def normalize(values):
            if values.max() == values.min():
                return np.full_like(values, 0.5)
            return (values - values.min()) / (values.max() - values.min())

        opp_n = normalize(opp)
        conv_n = normalize(conv)
        kol_n = normalize(kol)
        gap_n = normalize(gap)
        market_n = normalize(market)
        territory_n = normalize(territory)

        raw_score = (
            0.30 * opp_n
            + 0.25 * conv_n
            + 0.15 * kol_n
            + 0.10 * gap_n
            + 0.10 * market_n
            + 0.10 * territory_n
        )
        scaled = 100.0 * raw_score
        if scaled.max() != scaled.min():
            scaled = 100.0 * (scaled - scaled.min()) / (scaled.max() - scaled.min())
        scaled = np.clip(scaled, 0.0, 100.0)

        for idx, action in enumerate(actions):
            score = float(scaled[idx])
            action["daily_plan_score"] = round(score, 1)
            action["priority"] = self._priority_label(score)
            action["confidence_score"] = round(float(action.get("confidence_score", 0.0)), 1)
            action["conversion_probability"] = round(float(action.get("conversion_probability", 0.0)), 1)

        actions = sorted(actions, key=lambda x: x["daily_plan_score"], reverse=True)

        current_dt = datetime.combine(plan_date, BUSINESS_START)
        end_dt = datetime.combine(plan_date, BUSINESS_END)
        for action in actions:
            if current_dt > end_dt:
                action["scheduled_time"] = end_dt.strftime("%I:%M %p")
            else:
                action["scheduled_time"] = current_dt.strftime("%I:%M %p")
                current_dt += timedelta(minutes=int(action["duration_minutes"]))
                if current_dt.time() > BUSINESS_END:
                    current_dt = end_dt
        return actions

    def _priority_label(self, score: float) -> str:
        for threshold, label in PRIORITY_THRESHOLDS:
            if score >= threshold:
                return label
        return "Low"

    def _build_summary(self, actions: list[dict]) -> dict:
        total = len(actions)
        expected_conversions = round(sum(a["conversion_probability"] for a in actions) / 100.0, 1)
        high_priority = sum(1 for a in actions if a["priority"] in ("Critical", "High"))
        kol_engagements = sum(1 for a in actions if "KOL" in a["action_type"] or "KOL" in (a.get("title") or ""))
        estimated_revenue = round(sum(a["opportunity_score"] * (a["conversion_probability"] / 100.0) * 0.08 for a in actions), 1)
        coverage = round(min(100.0, (len({a.get("account") for a in actions}) / max(1, total)) * 40.0 + 20.0), 1)
        return {
            "total_planned_actions": total,
            "expected_conversions": expected_conversions,
            "high_priority_activities": high_priority,
            "kol_engagements": kol_engagements,
            "estimated_revenue_impact": estimated_revenue,
            "estimated_coverage_improvement": f"{coverage}%",
        }
