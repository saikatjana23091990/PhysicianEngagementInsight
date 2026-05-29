"""
LLM enhancement for daily plan narratives.
Converts the generated action list into human-readable summaries and coach guidance.
"""
from __future__ import annotations

import json
from typing import Optional

from app.ai.guardrails import build_system_prompt, trim_context
from app.ai.llm import llm_service
from app.services.daily_plan_service import DailyPlanService


class DailyPlanLLMService:
    def __init__(self) -> None:
        self.plan_service = DailyPlanService()

    async def generate_plan_narrative(self, rep_id: str, plan_date: Optional[str] = None) -> dict:
        plan = self.plan_service.generate_plan(rep_id, plan_date)
        if not plan:
            return {}

        prompt = self._build_prompt(plan)
        system = build_system_prompt("analytics")
        resp = await llm_service.chat(messages=[{"role": "user", "content": prompt}], system=system, max_tokens=900)

        narrative = self._parse_json(resp.text)
        if not narrative:
            narrative = {
                "day_summary": resp.text,
                "top_priorities": [],
                "risk_alerts": [],
                "focus_areas": [],
            }
        return narrative

    def _build_prompt(self, plan: dict) -> str:
        plan_snapshot = {
            "rep_name": plan.get("rep_name"),
            "plan_date": plan.get("plan_date"),
            "total_actions": plan.get("summary", {}).get("total_planned_actions"),
            "high_priority": plan.get("summary", {}).get("high_priority_activities"),
            "expected_conversions": plan.get("summary", {}).get("expected_conversions"),
            "top_actions": [
                {
                    "time": a["scheduled_time"],
                    "title": a["title"],
                    "action_type": a["action_type"],
                    "priority": a["priority"],
                    "hcp_name": a["hcp_name"],
                    "account": a["account"],
                    "confidence": a["confidence_score"],
                    "conversion_probability": a["conversion_probability"],
                }
                for a in plan.get("actions", [])[:5]
            ],
        }
        return f"""Analyze the following daily plan for a sales rep and produce a grounded execution summary.

Respond with valid JSON only, containing these keys:
- day_summary: a concise human-readable summary of the plan.
- top_priorities: a list of the top 3 priorities and why they matter.
- risk_alerts: a list of 2 risks if the rep does not take the plan actions.
- focus_areas: a list of 3 recommended focus areas for the day.

PLAN:
{json.dumps(plan_snapshot, indent=2)}
"""

    def _parse_json(self, text: str) -> dict | None:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    "day_summary": parsed.get("day_summary", ""),
                    "top_priorities": parsed.get("top_priorities", []),
                    "risk_alerts": parsed.get("risk_alerts", []),
                    "focus_areas": parsed.get("focus_areas", []),
                }
        except Exception:
            return None
        return None
