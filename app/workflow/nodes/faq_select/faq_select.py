import json

from app.core.logging import get_logger, log_with_context
from app.storage.faq import load_faqs
from app.workflow.nodes._common import append_reasoning, complete_structured
from app.workflow.nodes.faq_select.prompt import FAQ_SELECT_SYSTEM_PROMPT
from app.workflow.state import FaqSelection, WorkflowState

logger = get_logger(__name__)


async def select_faq(state: WorkflowState) -> dict:
    session_id = state.session_id
    ticket_id = state.ticket_id

    log_with_context(
        logger,
        "INFO",
        "FAQ-SELECT: FAQ selection started",
        context={"session_id": session_id, "ticket_id": ticket_id},
    )
    
    candidates = load_faqs()

    if not candidates:
        log_with_context(
            logger,
            "WARNING",
            "FAQ-SELECT: FAQ knowledge base empty, escalating",
            context={"session_id": session_id, "ticket_id": ticket_id},
        )
        return {
            "selected_faq_ids": [],
            "selected_faqs": [],
            "escalate": True,
            "escalation_reason": "no_faq_match",
            "reasoning_log": append_reasoning(
                state, "faq_select", "escalate", "FAQ knowledge base is empty; cannot ground a response."
            ),
        }

    candidate_text = json.dumps(
        [{"id": f["id"], "question": f["question"], "answer": f["answer"]} for f in candidates]
    )
    user_prompt = f"Candidate FAQ entries:\n{candidate_text}\n\nCustomer message:\n{state.message}"

    selected_ids: list[str] = []
    reasoning = ""
    try:
        selection = await complete_structured(FAQ_SELECT_SYSTEM_PROMPT, user_prompt, FaqSelection)
        candidate_ids = {f["id"] for f in candidates}
        selected_ids = [fid for fid in selection.selected_ids if fid in candidate_ids]
        reasoning = selection.reasoning
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "FAQ-SELECT: FAQ selection failed",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )

    if not selected_ids:
        log_with_context(
            logger,
            "WARNING",
            "FAQ-SELECT: No relevant FAQ found, escalating",
            context={"session_id": session_id, "ticket_id": ticket_id},
        )
        return {
            "selected_faq_ids": [],
            "selected_faqs": [],
            "escalate": True,
            "escalation_reason": "no_faq_match",
            "reasoning_log": append_reasoning(
                state, "faq_select", "escalate", reasoning or "No FAQ entry was relevant enough to ground a response."
            ),
        }

    log_with_context(
        logger,
        "INFO",
        "FAQ-SELECT: FAQ selection complete",
        context={"session_id": session_id, "ticket_id": ticket_id, "selected_faq_ids": selected_ids},
    )
    return {
        "selected_faq_ids": selected_ids,
        "selected_faqs": [f for f in candidates if f["id"] in selected_ids],
        "escalate": False,
        "reasoning_log": append_reasoning(
            state, "faq_select", "faq_selected", reasoning or f"Selected {len(selected_ids)} relevant FAQ(s)."
        ),
    }
