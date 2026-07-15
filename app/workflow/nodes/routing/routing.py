from app.core.config import settings
from app.core.logging import get_logger, log_with_context
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


def route_by_category(state: WorkflowState) -> str:
    """Conditional edge: security escalates directly, all others go to the handler."""
    category = state.category or "general"
    next_node = "escalate_to_human" if category == "security" else "apply_handler"
    log_with_context(
        logger,
        "INFO",
        "TICKET-ROUTE: Routed by category",
        context={"session_id": state.session_id, "ticket_id": state.ticket_id, "category": category, "next_node": next_node},
    )
    return next_node


def route_judge_decision(state: WorkflowState) -> str:
    """Conditional edge: approve ends, revise retries or escalates based on retry_count."""
    decision = state.judge_decision or "approve"
    retry_count = state.retry_count

    if decision == "approve":
        next_node = "END"
    elif retry_count < settings.MAX_JUDGE_RETRIES:
        next_node = "generate_response"
    else:
        next_node = "escalate_to_human"

    log_with_context(
        logger,
        "INFO",
        "TICKET-ROUTE: Judge decision routed",
        context={
            "session_id": state.session_id,
            "ticket_id": state.ticket_id,
            "decision": decision,
            "retry_count": retry_count,
            "next_node": next_node,
        },
    )
    return next_node
