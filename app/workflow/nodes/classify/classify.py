from app.core.logging import get_logger, log_with_context
from app.workflow.nodes._common import append_reasoning, complete_structured
from app.workflow.nodes.classify.prompt import CLASSIFY_SYSTEM_PROMPT
from app.workflow.state import ClassificationResult, WorkflowState

logger = get_logger(__name__)


async def classify_ticket(state: WorkflowState) -> dict:
    log_with_context(
        logger,
        "INFO",
        "TICKET-CLASSIFY: Classification started",
        context={"session_id": state.session_id, "ticket_id": state.ticket_id},
    )

    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.messages)
    user_prompt = f"Conversation so far:\n{history_text}\n\nLatest message:\n{state.message}"

    try:
        result = await complete_structured(CLASSIFY_SYSTEM_PROMPT, user_prompt, ClassificationResult)
        category, urgency, sentiment, summary = result.category, result.urgency, result.sentiment, result.summary
        reasoning = result.reasoning
        log_with_context(
            logger,
            "INFO",
            "TICKET-CLASSIFY: Classification complete",
            context={
                "session_id": state.session_id,
                "ticket_id": state.ticket_id,
                "category": category,
                "urgency": urgency,
            },
        )
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-CLASSIFY: Classification failed",
            context={"session_id": state.session_id, "ticket_id": state.ticket_id, "error": str(e)},
        )
        category, urgency, sentiment, summary = "general", "medium", "neutral", ""
        reasoning = "Classification failed; defaulted to general/medium."

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "summary": summary,
        "reasoning_log": append_reasoning(state, "classify", category, reasoning),
    }
