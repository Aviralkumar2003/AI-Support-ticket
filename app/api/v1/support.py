import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger, log_with_context
from app.models.request import TicketRequest
from app.models.response import SessionResponse, TicketResponse
from app.storage.session import load_session, save_session
from app.workflow.graph import run_workflow
from app.workflow.state import WorkflowState

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}


@router.post("/api/v1/support/tickets/process", response_model=TicketResponse)
async def process_ticket(request: TicketRequest) -> TicketResponse:
    is_new_session = request.session_id is None
    session_id = request.session_id or f"SESSION-{uuid.uuid4().hex[:12]}"

    log_with_context(
        logger,
        "INFO",
        "TICKET-PROCESS: Ticket received (support.py process_ticket)",
        context={"session_id": session_id, "ticket_id": request.ticket_id, "new_session": is_new_session},
    )

    session = None if is_new_session else await load_session(session_id)
    now = datetime.now(timezone.utc).isoformat()

    if session is None:
        session = {
            "session_id": session_id,
            "ticket_id": request.ticket_id,
            "messages": [],
            "classification": None,
            "selected_faq_ids": [],
            "judge_score": None,
            "judge_decision": None,
            "judge_feedback": None,
            "retry_count": 0,
            "status": "in_progress",
            "human_review_required": False,
            "escalation_reason": None,
            "created_at": now,
            "updated_at": now,
        }

    session["messages"].append({"role": "user", "content": request.message, "timestamp": now})

    initial_state: WorkflowState = {
        "session_id": session_id,
        "ticket_id": request.ticket_id,
        "message": request.message,
        "messages": session["messages"],
        "retry_count": 0,
        "escalate": False,
    }

    final_state = await run_workflow(initial_state)

    session["messages"].append(
        {"role": "assistant", "content": final_state.get("response", ""), "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    session["classification"] = {
        "category": final_state.get("category"),
        "urgency": final_state.get("urgency"),
        "sentiment": final_state.get("sentiment"),
        "summary": final_state.get("summary"),
    }
    session["selected_faq_ids"] = final_state.get("selected_faq_ids", [])
    session["judge_score"] = final_state.get("judge_score")
    session["judge_decision"] = final_state.get("judge_decision")
    session["judge_feedback"] = final_state.get("judge_feedback")
    session["retry_count"] = final_state.get("retry_count", 0)
    session["status"] = final_state.get("status", "resolved")
    session["human_review_required"] = final_state.get("human_review_required", False)
    session["escalation_reason"] = final_state.get("escalation_reason")

    await save_session(session)

    log_with_context(
        logger,
        "INFO",
        "TICKET-PROCESS: Ticket processing complete (support.py process_ticket)",
        context={
            "session_id": session_id,
            "ticket_id": request.ticket_id,
            "category": final_state.get("category"),
            "status": final_state.get("status"),
        },
    )

    return TicketResponse(
        session_id=session_id,
        ticket_id=request.ticket_id,
        category=final_state.get("category", "general"),
        urgency=final_state.get("urgency", "medium"),
        sentiment=final_state.get("sentiment", "neutral"),
        selected_faq_ids=final_state.get("selected_faq_ids", []),
        judge_score=final_state.get("judge_score", 0.0),
        judge_decision=final_state.get("judge_decision", "revise"),
        judge_feedback=final_state.get("judge_feedback", ""),
        retry_count=final_state.get("retry_count", 0),
        status=final_state.get("status", "resolved"),
        human_review_required=final_state.get("human_review_required", False),
        escalation_reason=final_state.get("escalation_reason"),
        response=final_state.get("response", ""),
    )


@router.get("/api/v1/support/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    session = await load_session(session_id)
    if session is None:
        log_with_context(
            logger,
            "WARNING",
            "SESSION-FETCH: Session not found (support.py get_session)",
            context={"session_id": session_id},
        )
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(**session)
