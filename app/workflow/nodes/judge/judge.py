import json

from app.core.logging import get_logger, log_with_context
from app.workflow.nodes._common import append_reasoning, complete_structured
from app.workflow.nodes.judge.prompt import JUDGE_SYSTEM_PROMPT
from app.workflow.state import JudgeVerdict, WorkflowState

logger = get_logger(__name__)


async def judge_response(state: WorkflowState) -> dict:
    session_id = state.session_id
    ticket_id = state.ticket_id

    log_with_context(
        logger,
        "INFO",
        "TICKET-JUDGE: Judge evaluation started",
        context={"session_id": session_id, "ticket_id": ticket_id},
    )

    faq_text = json.dumps(state.selected_faqs)
    user_prompt = (
        f"Customer message:\n{state.message}\n\n"
        f"Relevant FAQ content:\n{faq_text}\n\n"
        f"Draft response:\n{state.response}"
    )

    try:
        verdict = await complete_structured(JUDGE_SYSTEM_PROMPT, user_prompt, JudgeVerdict)
        score = verdict.score
        decision = verdict.decision
        feedback = verdict.feedback
        reasoning = verdict.reasoning or feedback
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-JUDGE: Judge evaluation failed",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )
        score = 0.0
        decision = "revise"
        feedback = "Judge evaluation failed; defaulting to revise."
        reasoning = feedback

    updates = {
        "judge_score": score,
        "judge_decision": decision,
        "judge_feedback": feedback,
    }

    if decision == "revise":
        updates["retry_count"] = state.retry_count + 1
    else:
        updates["status"] = "resolved"
        updates["human_review_required"] = False

    updates["reasoning_log"] = append_reasoning(state, "judge", decision, reasoning)

    log_with_context(
        logger,
        "INFO",
        "TICKET-JUDGE: Judge evaluation complete",
        context={
            "session_id": session_id,
            "ticket_id": ticket_id,
            "score": score,
            "decision": decision,
            "retry_count": updates.get("retry_count", state.retry_count),
        },
    )
    return updates
