"""
Execution copilot service that builds AI coach narratives for daily plan execution.
"""
from __future__ import annotations

import json
from typing import Optional

from app.ai.guardrails import build_system_prompt, trim_context
from app.ai.llm import llm_service
from app.services.daily_plan_service import DailyPlanService


class ExecutionCopilotService:
    def __init__(self) -> None:
        self.daily_plan = DailyPlanService()

    async def generate_coach_updates(self, rep_id: str, plan_date: Optional[str] = None) -> dict:
        plan = self.daily_plan.generate_plan(rep_id, plan_date)
        if not plan:
            return {}

        prompt = self._build_prompt(plan)
        system = build_system_prompt("analytics")
        resp = await llm_service.chat(messages=[{"role": "user", "content": prompt}], system=system, max_tokens=950)
        parsed = self._parse_json(resp.text)
        if not parsed:
            return {
                "morning_brief": resp.text,
                "today_focus": [],
                "midday_review": "",
                "end_of_day_summary": "",
            }
        return parsed

    def _build_prompt(self, plan: dict) -> str:
        actions = [
            {
                "time": a["scheduled_time"],
                "title": a["title"],
                "priority": a["priority"],
                "hcp": a["hcp_name"],
                "conversion_probability": a["conversion_probability"],
            }
            for a in plan.get("actions", [])[:8]
        ]
        payload = {
            "rep_name": plan.get("rep_name"),
            "plan_date": plan.get("plan_date"),
            "summary": plan.get("summary"),
            "actions": actions,
        }
        return f"""Use the daily plan payload below to generate a smart AI execution copilot update.

Return valid JSON only with keys:
- morning_brief
- today_focus
- midday_review
- end_of_day_summary

Use the plan data to highlight what changed, what to do next, and risk signals.

PAYLOAD:
{json.dumps(payload, indent=2)}
"""

    def _parse_json(self, text: str) -> dict | None:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    "morning_brief": parsed.get("morning_brief", ""),
                    "today_focus": parsed.get("today_focus", []),
                    "midday_review": parsed.get("midday_review", ""),
                    "end_of_day_summary": parsed.get("end_of_day_summary", ""),
                }
        except Exception:
            return None
        return None
