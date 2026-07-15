import json

from app.core.logging import get_logger, log_with_context
from app.providers.llm import get_llm_client
from app.workflow.nodes.judge.prompt import JUDGE_SYSTEM_PROMPT
from app.workflow.state import WorkflowState

logger = get_logger(__name__)
llm = get_llm_client()


async def judge_response(state: WorkflowState) -> WorkflowState:
    session_id = state.get("session_id")
    ticket_id = state.get("ticket_id")

    log_with_context(
        logger,
        "INFO",
        "TICKET-JUDGE: Judge evaluation started (judge.py judge_response)",
        context={"session_id": session_id, "ticket_id": ticket_id},
    )

    faq_text = json.dumps(state.get("selected_faqs", []))
    user_prompt = (
        f"Customer message:\n{state.get('message')}\n\n"
        f"Relevant FAQ content:\n{faq_text}\n\n"
        f"Draft response:\n{state.get('response')}"
    )

    try:
        response = await llm(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        score = float(parsed.get("score", 0.0))
        decision = parsed.get("decision", "revise")
        if decision not in {"approve", "revise"}:
            decision = "revise"
        feedback = parsed.get("feedback", "")
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "TICKET-JUDGE: Judge evaluation failed (judge.py judge_response)",
            context={"session_id": session_id, "ticket_id": ticket_id, "error": str(e)},
        )
        score = 0.0
        decision = "revise"
        feedback = "Judge evaluation failed; defaulting to revise."

    state["judge_score"] = score
    state["judge_decision"] = decision
    state["judge_feedback"] = feedback

    if decision == "revise":
        state["retry_count"] = state.get("retry_count", 0) + 1
    else:
        state["status"] = "resolved"
        state["human_review_required"] = False

    log_with_context(
        logger,
        "INFO",
        "TICKET-JUDGE: Judge evaluation complete (judge.py judge_response)",
        context={
            "session_id": session_id,
            "ticket_id": ticket_id,
            "score": score,
            "decision": decision,
            "retry_count": state.get("retry_count", 0),
        },
    )
    return state
