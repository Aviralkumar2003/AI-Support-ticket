import json

from app.core.logging import get_logger, log_with_context
from app.providers.llm import get_llm_client
from app.storage.faq import get_faqs_by_category
from app.workflow.nodes.faq_select.prompt import FAQ_SELECT_SYSTEM_PROMPT
from app.workflow.state import WorkflowState

logger = get_logger(__name__)
llm = get_llm_client()


async def select_faq(state: WorkflowState) -> WorkflowState:
    session_id = state.get("session_id")
    ticket_id = state.get("ticket_id")
    category = state.get("category", "general")

    log_with_context(
        logger,
        "INFO",
        "FAQ-SELECT: FAQ selection started (faq_select.py select_faq)",
        context={"session_id": session_id, "ticket_id": ticket_id, "category": category},
    )

    candidates = get_faqs_by_category(category)

    if not candidates:
        state["selected_faq_ids"] = []
        state["selected_faqs"] = []
        state["escalate"] = True
        state["escalation_reason"] = "no_faq_match"
        log_with_context(
            logger,
            "WARNING",
            "FAQ-SELECT: No FAQ candidates for category, escalating (faq_select.py select_faq)",
            context={"session_id": session_id, "ticket_id": ticket_id, "category": category},
        )
        return state

    candidate_text = json.dumps(
        [{"id": f["id"], "question": f["question"], "answer": f["answer"]} for f in candidates]
    )
    user_prompt = f"Candidate FAQ entries:\n{candidate_text}\n\nCustomer message:\n{state['message']}"

    selected_ids: list[str] = []
    try:
        response = await llm(
            messages=[
                {"role": "system", "content": FAQ_SELECT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        candidate_ids = {f["id"] for f in candidates}
        selected_ids = [fid for fid in parsed.get("selected_ids", []) if fid in candidate_ids]
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "FAQ-SELECT: LLM relevance selection failed (faq_select.py select_faq)",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )

    if not selected_ids:
        state["selected_faq_ids"] = []
        state["selected_faqs"] = []
        state["escalate"] = True
        state["escalation_reason"] = "no_faq_match"
        log_with_context(
            logger,
            "WARNING",
            "FAQ-SELECT: No relevant FAQ found, escalating (faq_select.py select_faq)",
            context={"session_id": session_id, "ticket_id": ticket_id},
        )
        return state

    state["selected_faq_ids"] = selected_ids
    state["selected_faqs"] = [f for f in candidates if f["id"] in selected_ids]
    state["escalate"] = False

    log_with_context(
        logger,
        "INFO",
        "FAQ-SELECT: FAQ selection complete (faq_select.py select_faq)",
        context={"session_id": session_id, "ticket_id": ticket_id, "selected_faq_ids": selected_ids},
    )
    return state
