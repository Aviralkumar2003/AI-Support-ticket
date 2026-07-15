import json

from app.core.logging import get_logger, log_with_context
from app.providers.llm import get_llm_client
from app.workflow.nodes.generate.prompt import GENERATE_SYSTEM_PROMPT
from app.workflow.state import WorkflowState

logger = get_logger(__name__)
llm = get_llm_client()


async def generate_response(state: WorkflowState) -> WorkflowState:
    session_id = state.get("session_id")
    ticket_id = state.get("ticket_id")
    retry_count = state.get("retry_count", 0)

    log_with_context(
        logger,
        "INFO",
        "TICKET-GENERATE: Response generation started (generate.py generate_response)",
        context={"session_id": session_id, "ticket_id": ticket_id, "retry_count": retry_count},
    )

    faq_text = json.dumps(state.get("selected_faqs", []))
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.get("messages", []))

    user_prompt_parts = [
        f"Category: {state.get('category')}",
        f"Category constraints: {state.get('handler_constraints', '')}",
        f"Relevant FAQ content:\n{faq_text}",
        f"Conversation history:\n{history_text}",
        f"Customer's latest message:\n{state.get('message')}",
    ]
    if retry_count > 0 and state.get("judge_feedback"):
        user_prompt_parts.append(
            f"Your previous response was not approved. Judge feedback to address:\n{state['judge_feedback']}"
        )
    user_prompt = "\n\n".join(user_prompt_parts)

    try:
        response = await llm(
            messages=[
                {"role": "system", "content": GENERATE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        state["response"] = parsed.get("response", "")
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-GENERATE: Response generation failed (generate.py generate_response)",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )
        state["response"] = (
            "We're sorry, we ran into an issue preparing a response. "
            "Your ticket has been forwarded to a human agent."
        )
        state["escalate"] = True
        state["escalation_reason"] = "generation_error"

    log_with_context(
        logger,
        "INFO",
        "TICKET-GENERATE: Response generation complete (generate.py generate_response)",
        context={"session_id": session_id, "ticket_id": ticket_id, "retry_count": retry_count},
    )
    return state
