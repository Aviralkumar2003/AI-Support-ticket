import json

from app.core.logging import get_logger, log_with_context
from app.workflow.nodes._common import append_reasoning, complete_structured
from app.workflow.nodes.generate.prompt import GENERATE_SYSTEM_PROMPT
from app.workflow.state import GenerationResult, WorkflowState

logger = get_logger(__name__)


async def generate_response(state: WorkflowState) -> dict:
    session_id = state.session_id
    ticket_id = state.ticket_id
    retry_count = state.retry_count

    log_with_context(
        logger,
        "INFO",
        "TICKET-GENERATE: Response generation started",
        context={"session_id": session_id, "ticket_id": ticket_id, "retry_count": retry_count},
    )

    faq_text = json.dumps(state.selected_faqs)
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.messages)

    user_prompt_parts = [
        f"Category: {state.category}",
        f"Category constraints: {state.handler_constraints}",
        f"Relevant FAQ content:\n{faq_text}",
        f"Conversation history:\n{history_text}",
        f"Customer's latest message:\n{state.message}",
    ]
    if retry_count > 0 and state.judge_feedback:
        user_prompt_parts.append(
            f"Your previous response was not approved. Judge feedback to address:\n{state.judge_feedback}"
        )
    user_prompt = "\n\n".join(user_prompt_parts)

    updates: dict = {}
    try:
        result = await complete_structured(GENERATE_SYSTEM_PROMPT, user_prompt, GenerationResult)
        updates["response"] = result.response
        reasoning = result.reasoning
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-GENERATE: Response generation failed",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )
        updates["response"] = (
            "We're sorry, we ran into an issue preparing a response. "
            "Your ticket has been forwarded to a human agent."
        )
        updates["escalate"] = True
        updates["escalation_reason"] = "generation_error"
        reasoning = "Generation failed; escalating."

    updates["reasoning_log"] = append_reasoning(state, "generate", "answer", reasoning)

    log_with_context(
        logger,
        "INFO",
        "TICKET-GENERATE: Response generation complete",
        context={"session_id": session_id, "ticket_id": ticket_id, "retry_count": retry_count},
    )
    return updates
