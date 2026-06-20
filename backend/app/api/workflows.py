import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.lead import Lead
from app.models.workflow_run import WorkflowRun
from app.schemas.workflow import WorkflowAdvanceRequest, WorkflowStateOut
from app.workflow.graph import workflow_graph

router = APIRouter(prefix="/workflows", tags=["workflows"])


async def _latest_run(db: AsyncSession, lead_id: uuid.UUID) -> WorkflowRun | None:
    return await db.scalar(
        select(WorkflowRun).where(WorkflowRun.lead_id == lead_id).order_by(WorkflowRun.created_at.desc())
    )


@router.post("/{lead_id}/advance", response_model=WorkflowStateOut)
async def advance_workflow(
    lead_id: uuid.UUID, payload: WorkflowAdvanceRequest, db: AsyncSession = Depends(get_db)
) -> WorkflowStateOut:
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    run = await _latest_run(db, lead_id)
    if run is None or run.status != "RUNNING":
        run = WorkflowRun(
            lead_id=lead_id,
            status="RUNNING",
            state={"lead_id": str(lead_id), "lead_profile": {"score": lead.score or 0}},
        )
        db.add(run)
        await db.flush()

    state = dict(run.state)
    if payload.simulated_event is not None:
        state["simulated_event"] = payload.simulated_event

    result = await workflow_graph.ainvoke(state)

    run.state = result
    if result.get("escalation_flag"):
        run.status = "PAUSED_ESCALATION"
    elif result.get("terminal"):
        run.status = "COMPLETED"
    else:
        run.status = "RUNNING"

    await db.commit()
    return WorkflowStateOut(lead_id=lead_id, status=run.status, state=run.state)


@router.get("/{lead_id}/state", response_model=WorkflowStateOut)
async def get_workflow_state(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> WorkflowStateOut:
    run = await _latest_run(db, lead_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No workflow run found for lead")
    return WorkflowStateOut(lead_id=lead_id, status=run.status, state=run.state)
