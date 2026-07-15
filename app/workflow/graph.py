from langgraph.graph import END, StateGraph

from app.core.logging import get_logger, log_with_context
from app.workflow.nodes.classify import classify_ticket
from app.workflow.nodes.escalate import escalate_to_human
from app.workflow.nodes.faq_select import select_faq
from app.workflow.nodes.generate import generate_response
from app.workflow.nodes.handlers import (
    account_handler,
    billing_handler,
    general_handler,
    subscription_handler,
    technical_handler,
)
from app.workflow.nodes.judge import judge_response
from app.workflow.nodes.route import route_by_category, route_judge_decision
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


def _build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("classify_ticket", classify_ticket)
    graph.add_node("billing_handler", billing_handler)
    graph.add_node("technical_handler", technical_handler)
    graph.add_node("account_handler", account_handler)
    graph.add_node("subscription_handler", subscription_handler)
    graph.add_node("general_handler", general_handler)
    graph.add_node("select_faq", select_faq)
    graph.add_node("generate_response", generate_response)
    graph.add_node("judge_response", judge_response)
    graph.add_node("escalate_to_human", escalate_to_human)

    graph.set_entry_point("classify_ticket")

    graph.add_conditional_edges(
        "classify_ticket",
        route_by_category,
        {
            "billing_handler": "billing_handler",
            "technical_handler": "technical_handler",
            "account_handler": "account_handler",
            "subscription_handler": "subscription_handler",
            "general_handler": "general_handler",
            "escalate_to_human": "escalate_to_human",
        },
    )

    for handler_node in (
        "billing_handler",
        "technical_handler",
        "account_handler",
        "subscription_handler",
        "general_handler",
    ):
        graph.add_edge(handler_node, "select_faq")

    graph.add_conditional_edges(
        "select_faq",
        lambda state: "escalate_to_human" if state.get("escalate") else "generate_response",
        {
            "escalate_to_human": "escalate_to_human",
            "generate_response": "generate_response",
        },
    )

    graph.add_edge("generate_response", "judge_response")

    graph.add_conditional_edges(
        "judge_response",
        route_judge_decision,
        {
            "END": END,
            "generate_response": "generate_response",
            "escalate_to_human": "escalate_to_human",
        },
    )

    graph.add_edge("escalate_to_human", END)

    return graph.compile()


_compiled_graph = _build_graph()


async def run_workflow(state: WorkflowState) -> WorkflowState:
    """Run the full ticket resolution workflow to completion and return the final state."""
    log_with_context(
        logger,
        "INFO",
        "WORKFLOW: Workflow run started (graph.py run_workflow)",
        context={"session_id": state.get("session_id"), "ticket_id": state.get("ticket_id")},
    )
    result = await _compiled_graph.ainvoke(state)
    log_with_context(
        logger,
        "INFO",
        "WORKFLOW: Workflow run complete (graph.py run_workflow)",
        context={
            "session_id": state.get("session_id"),
            "ticket_id": state.get("ticket_id"),
            "status": result.get("status"),
        },
    )
    return result
