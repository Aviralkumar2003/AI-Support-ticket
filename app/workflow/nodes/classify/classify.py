import json

from app.core.logging import get_logger, log_with_context
from app.providers.llm import get_llm_client
from app.workflow.nodes.classify.prompt import CLASSIFY_SYSTEM_PROMPT
from app.workflow.state import WorkflowState

logger = get_logger(__name__)
llm = get_llm_client()

VALID_CATEGORIES = {"billing", "technical", "account", "subscription", "general", "security"}
VALID_URGENCIES = {"low", "medium", "high", "critical"}


async def classify_ticket(state: WorkflowState) -> WorkflowState:
    log_with_context(
        logger,
        "INFO",
        "TICKET-CLASSIFY: Classification started (classify.py classify_ticket)",
        context={"session_id": state.get("session_id"), "ticket_id": state.get("ticket_id")},
    )

    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("messages", [])
    )
    user_prompt = f"Conversation so far:\n{history_text}\n\nLatest message:\n{state['message']}"

    try:
        response = await llm(
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)

        category = parsed.get("category", "general")
        if category not in VALID_CATEGORIES:
            category = "general"
        urgency = parsed.get("urgency", "medium")
        if urgency not in VALID_URGENCIES:
            urgency = "medium"

        state["category"] = category
        state["urgency"] = urgency
        state["sentiment"] = parsed.get("sentiment", "neutral")
        state["summary"] = parsed.get("summary", "")

        log_with_context(
            logger,
            "INFO",
            "TICKET-CLASSIFY: Classification complete (classify.py classify_ticket)",
            context={
                "session_id": state.get("session_id"),
                "ticket_id": state.get("ticket_id"),
                "category": category,
                "urgency": urgency,
            },
        )
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-CLASSIFY: Classification failed (classify.py classify_ticket)",
            context={"session_id": state.get("session_id"), "ticket_id": state.get("ticket_id"), "error": str(e)},
        )
        state["category"] = "general"
        state["urgency"] = "medium"
        state["sentiment"] = "neutral"
        state["summary"] = ""

    return state
