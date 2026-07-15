from app.core.logging import get_logger, log_with_context
from app.workflow.nodes._common import append_reasoning
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


async def escalate_to_human(state: WorkflowState) -> dict:
    session_id = state.session_id
    ticket_id = state.ticket_id

    reason = state.escalation_reason
    if not reason:
        if state.category == "security":
            reason = "security_category"
        elif state.judge_decision == "revise":
            reason = "max_retries_exceeded"
        else:
            reason = "unspecified"

    updates = {
        "escalation_reason": reason,
        "status": "escalated",
        "human_review_required": True,
        "reasoning_log": append_reasoning(state, "escalate", "escalate", reason),
    }
    if not state.response:
        updates["response"] = "Your ticket has been forwarded to a human support agent for review."
    if state.judge_score is None:
        updates["judge_score"] = 0.0

    log_with_context(
        logger,
        "WARNING",
        "TICKET-ESCALATE: Ticket escalated to human review",
        context={"session_id": session_id, "ticket_id": ticket_id, "reason": reason},
    )
    return updates
