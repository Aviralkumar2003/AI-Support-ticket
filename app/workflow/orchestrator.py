import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.logging import get_logger, log_with_context
from app.workflow.graph import run_workflow
from app.workflow.state import SessionResponse, TicketRequest, TicketResponse, WorkflowState
from app.workflow.state_persistence import (
    get_persisted_session,
    load_or_create_session,
    new_session,
    persist_workflow_state,
)

logger = get_logger(__name__)


async def _invoke_workflow(initial_state: WorkflowState, session_id: str) -> dict:
    try:
        return await run_workflow(initial_state, thread_id=session_id)
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "ORCHESTRATOR: Workflow failed, attempting resume from last checkpoint",
            context={"session_id": session_id, "error": str(e)},
        )

    try:
        return await run_workflow(None, thread_id=session_id)
    except Exception as resume_error:
        log_with_context(
            logger,
            "ERROR",
            "ORCHESTRATOR: Resume from checkpoint failed",
            context={"session_id": session_id, "error": str(resume_error)},
        )
        raise HTTPException(status_code=500, detail="Workflow execution failed") from resume_error


async def process_ticket(request: TicketRequest) -> TicketResponse:
    is_new_session = request.session_id is None
    session_id = request.session_id or f"SESSION-{uuid.uuid4().hex[:12]}"

    log_with_context(
        logger,
        "INFO",
        "TICKET-PROCESS: Ticket received",
        context={"session_id": session_id, "ticket_id": request.ticket_id, "new_session": is_new_session},
    )

    now = datetime.now(timezone.utc).isoformat()
    if is_new_session:
        session = new_session(session_id, request.ticket_id, now)
    else:
        session = await load_or_create_session(session_id, request.ticket_id)

    session["messages"].append({"role": "user", "content": request.message, "timestamp": now})

    initial_state = WorkflowState(
        session_id=session_id,
        ticket_id=request.ticket_id,
        message=request.message,
        messages=session["messages"],
        retry_count=0,
        escalate=False,
        reasoning_log=[],
    )

    final_state = await _invoke_workflow(initial_state, session_id)

    result_state = WorkflowState(**final_state)
    assistant_message = {
        "role": "assistant",
        "content": result_state.response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result_state = result_state.model_copy(
        update={"messages": [*result_state.messages, assistant_message]}
    )

    await persist_workflow_state(result_state)

    log_with_context(
        logger,
        "INFO",
        "TICKET-PROCESS: Ticket processing complete",
        context={
            "session_id": session_id,
            "ticket_id": request.ticket_id,
            "category": result_state.category,
            "status": result_state.status,
        },
    )

    return TicketResponse(
        session_id=session_id,
        ticket_id=request.ticket_id,
        category=result_state.category or "general",
        urgency=result_state.urgency or "medium",
        sentiment=result_state.sentiment or "neutral",
        selected_faq_ids=result_state.selected_faq_ids,
        judge_score=result_state.judge_score if result_state.judge_score is not None else 0.0,
        judge_decision=result_state.judge_decision or "revise",
        judge_feedback=result_state.judge_feedback or "",
        retry_count=result_state.retry_count,
        status=result_state.status or "resolved",
        human_review_required=result_state.human_review_required,
        escalation_reason=result_state.escalation_reason,
        reasoning=result_state.reasoning_log,
        response=result_state.response,
    )


async def get_session(session_id: str) -> SessionResponse:
    session = await get_persisted_session(session_id)
    if session is None:
        log_with_context(
            logger,
            "WARNING",
            "SESSION-FETCH: Session not found",
            context={"session_id": session_id},
        )
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)
