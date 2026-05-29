"""
Dynamic replanning service for the AI execution copilot.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.data.mongo import log_execution_plan_audit
from app.services.daily_plan_service import DailyPlanService


class DynamicReplanningService:
    def __init__(self) -> None:
        self.daily_plan = DailyPlanService()

    def refresh_plan(self, rep_id: str, plan_date: Optional[str] = None) -> dict:
        return self.daily_plan.generate_plan(rep_id, plan_date)

    async def update_status(
        self,
        rep_id: str,
        action_id: str,
        status: str,
        completion_timestamp: Optional[str] = None,
        actual_outcome: Optional[str] = None,
        reason: Optional[str] = None,
        trigger_event: Optional[str] = None,
    ) -> dict:
        plan = self.daily_plan.generate_plan(rep_id)
        action = next((a for a in plan.get("actions", []) if a["action_id"] == action_id), None)
        if not action:
            return {"updated": False, "reason": "action_not_found"}

        old_priority = action.get("priority")
        action["status"] = status
        action["actual_outcome"] = actual_outcome
        action["reason"] = reason
        action["completion_timestamp"] = completion_timestamp or datetime.utcnow().isoformat()

        await log_execution_plan_audit(
            rep_id=rep_id,
            action_id=action_id,
            old_priority=old_priority,
            new_priority=action.get("priority"),
            reason=reason or "status_update",
            trigger_event=trigger_event or status,
            model_version="v1",
        )
        return {"updated": True, "action": action}
