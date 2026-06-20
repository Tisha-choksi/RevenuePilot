from typing import Literal, TypedDict

QualificationStatus = Literal["NEW", "QUALIFYING", "QUALIFIED", "DISQUALIFIED"]
DealStageLiteral = Literal["OPEN", "PROPOSAL_SENT", "NEGOTIATION", "WON", "LOST"]
SimulatedEvent = Literal["accept", "objection", "timeout", "needs_approval"]


class WorkflowState(TypedDict, total=False):
    lead_id: str
    lead_profile: dict
    conversation_history: list[dict]
    qualification_status: QualificationStatus
    recommended_products: list[str]
    active_quote: dict | None
    objections_raised: list[str]
    deal_stage: DealStageLiteral
    follow_up_count: int
    escalation_flag: bool
    terminal: bool
    # Stub-only control hook: lets callers force which branch the Engagement
    # node takes until the real Engagement Agent (Phase 3) reads actual
    # customer signals instead.
    simulated_event: SimulatedEvent | None
