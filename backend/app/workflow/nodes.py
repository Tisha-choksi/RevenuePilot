from app.workflow.state import WorkflowState

FOLLOW_UP_LIMIT = 3


def lead_qualification_node(state: WorkflowState) -> dict:
    score = (state.get("lead_profile") or {}).get("score", 0)
    qualified = score >= 50
    return {"qualification_status": "QUALIFIED" if qualified else "DISQUALIFIED"}


def route_after_qualification(state: WorkflowState) -> str:
    return "qualified" if state.get("qualification_status") == "QUALIFIED" else "disqualified"


def product_recommendation_node(state: WorkflowState) -> dict:
    return {"recommended_products": ["RevenuePilot Starter Plan"]}


def pricing_node(state: WorkflowState) -> dict:
    return {
        "active_quote": {"total_amount": 4999.00, "currency": "USD", "discount_pct": 0},
        "deal_stage": "PROPOSAL_SENT",
    }


def engagement_node(state: WorkflowState) -> dict:
    event = state.get("simulated_event") or "accept"
    history = list(state.get("conversation_history") or [])
    history.append({"role": "AGENT", "content": f"Presented quote, customer event: {event}"})
    return {"conversation_history": history}


def route_after_engagement(state: WorkflowState) -> str:
    event = state.get("simulated_event") or "accept"
    if event == "objection":
        return "objection"
    if event == "needs_approval":
        return "escalation"
    if event == "timeout":
        return "timeout"
    return "accepted"


def negotiation_node(state: WorkflowState) -> dict:
    objections = list(state.get("objections_raised") or [])
    objections.append("price")
    # Stub assumes the re-pitch succeeds; a real Negotiation Agent (Phase 3)
    # would derive the next simulated_event from the customer's actual reply.
    return {"objections_raised": objections, "simulated_event": "accept"}


def escalation_node(state: WorkflowState) -> dict:
    return {"escalation_flag": True, "terminal": True}


def follow_up_node(state: WorkflowState) -> dict:
    count = state.get("follow_up_count", 0) + 1
    if count >= FOLLOW_UP_LIMIT:
        return {"follow_up_count": count, "deal_stage": "LOST", "terminal": True}
    return {"follow_up_count": count, "simulated_event": "accept"}


def route_after_follow_up(state: WorkflowState) -> str:
    return "exhausted" if state.get("terminal") else "retry"


def crm_update_node(state: WorkflowState) -> dict:
    return {"deal_stage": "WON"}


def analytics_log_node(state: WorkflowState) -> dict:
    return {"terminal": True}
