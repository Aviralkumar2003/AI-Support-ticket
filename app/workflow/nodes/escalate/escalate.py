from app.core.logging import get_logger, log_with_context
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


async def escalate_to_human(state: WorkflowState) -> WorkflowState:
    session_id = state.get("session_id")
    ticket_id = state.get("ticket_id")

    reason = state.get("escalation_reason")
    if not reason:
        if state.get("category") == "security":
            reason = "security_category"
        elif state.get("judge_decision") == "revise":
            reason = "max_retries_exceeded"
        else:
            reason = "unspecified"

    state["escalation_reason"] = reason
    state["status"] = "escalated"
    state["human_review_required"] = True
    state.setdefault("response", "Your ticket has been forwarded to a human support agent for review.")
    state.setdefault("selected_faq_ids", [])
    state.setdefault("judge_score", 0.0)
    state.setdefault("retry_count", state.get("retry_count", 0))

    log_with_context(
        logger,
        "WARNING",
        "TICKET-ESCALATE: Ticket escalated to human review (escalate.py escalate_to_human)",
        context={"session_id": session_id, "ticket_id": ticket_id, "reason": reason},
    )
    return state
