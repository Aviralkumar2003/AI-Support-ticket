from app.core.config import settings
from app.core.logging import get_logger, log_with_context
from app.workflow.state import WorkflowState

logger = get_logger(__name__)

CATEGORY_TO_HANDLER = {
    "billing": "billing_handler",
    "technical": "technical_handler",
    "account": "account_handler",
    "subscription": "subscription_handler",
    "general": "general_handler",
}


def route_by_category(state: WorkflowState) -> str:
    """Conditional edge: security escalates directly, all others go to their handler."""
    category = state.get("category", "general")
    next_node = "escalate_to_human" if category == "security" else CATEGORY_TO_HANDLER.get(category, "general_handler")
    log_with_context(
        logger,
        "INFO",
        "TICKET-ROUTE: Routed by category (route.py route_by_category)",
        context={"session_id": state.get("session_id"), "ticket_id": state.get("ticket_id"), "category": category, "next_node": next_node},
    )
    return next_node


def route_judge_decision(state: WorkflowState) -> str:
    """Conditional edge: approve ends, revise retries or escalates based on retry_count."""
    decision = state.get("judge_decision", "approve")
    retry_count = state.get("retry_count", 0)

    if decision == "approve":
        next_node = "END"
    elif retry_count < settings.MAX_JUDGE_RETRIES:
        next_node = "generate_response"
    else:
        next_node = "escalate_to_human"

    log_with_context(
        logger,
        "INFO",
        "TICKET-ROUTE: Judge decision routed (route.py route_judge_decision)",
        context={
            "session_id": state.get("session_id"),
            "ticket_id": state.get("ticket_id"),
            "decision": decision,
            "retry_count": retry_count,
            "next_node": next_node,
        },
    )
    return next_node
