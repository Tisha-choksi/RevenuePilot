import uuid
from typing import Literal

from pydantic import BaseModel


class WorkflowAdvanceRequest(BaseModel):
    simulated_event: Literal["accept", "objection", "timeout", "needs_approval"] | None = None


class WorkflowStateOut(BaseModel):
    lead_id: uuid.UUID
    status: str
    state: dict
