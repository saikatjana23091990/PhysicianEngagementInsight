from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.daily_plan_service import DailyPlanService
from app.services.daily_plan_llm_service import DailyPlanLLMService
from app.services.dynamic_replanning_service import DynamicReplanningService
from app.services.execution_copilot_service import ExecutionCopilotService

router = APIRouter(prefix="/daily-plan", tags=["daily_plan"])


class GenerateRequest(BaseModel):
    rep_id: str
    plan_date: Optional[str] = None
    include_narrative: Optional[bool] = False


class UpdateStatusRequest(BaseModel):
    rep_id: str
    action_id: str
    status: str
    completion_timestamp: Optional[str] = None
    actual_outcome: Optional[str] = None
    reason: Optional[str] = None
    trigger_event: Optional[str] = None


@router.get("/{rep_id}")
async def get_daily_plan(rep_id: str, include_narrative: bool = False):
    svc = DailyPlanService()
    plan = svc.generate_plan(rep_id)
    if not plan:
        raise HTTPException(404, "Rep not found or plan generation failed")
    if include_narrative:
        try:
            narrative = await DailyPlanLLMService().generate_plan_narrative(rep_id, plan.get("plan_date"))
        except Exception as exc:
            narrative = {
                "day_summary": "AI narrative unavailable.",
                "top_priorities": [],
                "risk_alerts": [],
                "focus_areas": [],
                "error": str(exc),
            }
        plan["ai_narrative"] = narrative
    return plan


@router.post("/generate")
async def generate_daily_plan(req: GenerateRequest):
    svc = DailyPlanService()
    plan = svc.generate_plan(req.rep_id, req.plan_date)
    if not plan:
        raise HTTPException(404, "Rep not found or plan generation failed")
    if req.include_narrative:
        try:
            narrative = await DailyPlanLLMService().generate_plan_narrative(req.rep_id, plan.get("plan_date"))
        except Exception as exc:
            narrative = {
                "day_summary": "AI narrative unavailable.",
                "top_priorities": [],
                "risk_alerts": [],
                "focus_areas": [],
                "error": str(exc),
            }
        plan["ai_narrative"] = narrative
    return plan


@router.post("/update-status")
async def update_plan_status(req: UpdateStatusRequest):
    svc = DynamicReplanningService()
    result = await svc.update_status(
        rep_id=req.rep_id,
        action_id=req.action_id,
        status=req.status,
        completion_timestamp=req.completion_timestamp,
        actual_outcome=req.actual_outcome,
        reason=req.reason,
        trigger_event=req.trigger_event,
    )
    if not result.get("updated"):
        raise HTTPException(404, result.get("reason", "Action not found"))
    return result


@router.get("/summary")
def daily_plan_summary(rep_id: str):
    svc = DailyPlanService()
    plan = svc.generate_plan(rep_id)
    if not plan:
        raise HTTPException(404, "Rep not found or plan generation failed")
    return plan.get("summary", {})


@router.get("/manager-view")
def manager_daily_plan_view(
    territory: Optional[str] = None,
    rep_id: Optional[str] = None,
    therapy_area: Optional[str] = None,
):
    svc = DailyPlanService()
    store = svc.store
    reps = store.df("rep_master")
    if territory:
        reps = reps[reps["territory"] == territory]
    if therapy_area:
        reps = reps[reps["primary_therapy_area"] == therapy_area]
    if rep_id:
        reps = reps[reps["rep_id"] == rep_id]
    reps = reps.head(30)
    out = []
    for _, rep in reps.iterrows():
        plan = svc.generate_plan(rep["rep_id"])
        out.append({
            "rep_id": rep["rep_id"],
            "rep_name": rep["rep_name"],
            "territory": rep["territory"],
            "primary_therapy_area": rep["primary_therapy_area"],
            "summary": plan.get("summary", {}),
            "top_actions": plan.get("actions", [])[:5],
        })
    return out


@router.get("/execution-coach/{rep_id}")
async def execution_coach(rep_id: str):
    svc = ExecutionCopilotService()
    return await svc.generate_coach_updates(rep_id)
