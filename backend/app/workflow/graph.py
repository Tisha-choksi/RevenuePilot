from langgraph.graph import END, START, StateGraph

from app.workflow import nodes
from app.workflow.state import WorkflowState


def build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("lead_qualification", nodes.lead_qualification_node)
    graph.add_node("analytics_log", nodes.analytics_log_node)
    graph.add_node("product_recommendation", nodes.product_recommendation_node)
    graph.add_node("pricing", nodes.pricing_node)
    graph.add_node("engagement", nodes.engagement_node)
    graph.add_node("negotiation", nodes.negotiation_node)
    graph.add_node("escalation", nodes.escalation_node)
    graph.add_node("follow_up", nodes.follow_up_node)
    graph.add_node("crm_update", nodes.crm_update_node)

    graph.add_edge(START, "lead_qualification")
    graph.add_conditional_edges(
        "lead_qualification",
        nodes.route_after_qualification,
        {"qualified": "product_recommendation", "disqualified": "analytics_log"},
    )
    graph.add_edge("analytics_log", END)

    graph.add_edge("product_recommendation", "pricing")
    graph.add_edge("pricing", "engagement")

    graph.add_conditional_edges(
        "engagement",
        nodes.route_after_engagement,
        {
            "objection": "negotiation",
            "escalation": "escalation",
            "timeout": "follow_up",
            "accepted": "crm_update",
        },
    )

    graph.add_edge("negotiation", "engagement")
    graph.add_edge("escalation", END)

    graph.add_conditional_edges(
        "follow_up",
        nodes.route_after_follow_up,
        {"retry": "engagement", "exhausted": END},
    )

    graph.add_edge("crm_update", "analytics_log")

    return graph.compile()


workflow_graph = build_graph()
