import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger, log_with_context
from app.storage.crud import load_session, save_session
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


_session_locks: dict[str, asyncio.Lock] = {}


def _lock_for(session_id: str) -> asyncio.Lock:
    lock = _session_locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[session_id] = lock
    return lock


def new_session(session_id: str, ticket_id: Optional[str], now: str) -> dict:
    return {
        "session_id": session_id,
        "ticket_id": ticket_id or "",
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
        "reasoning": [],
        "created_at": now,
        "updated_at": now,
    }


def apply_state_to_session(session: dict, state: WorkflowState) -> dict:
    if not session:
        session = {}

    session_id = state.session_id or session.get("session_id")
    if not session_id:
        return session

    now = datetime.now(timezone.utc).isoformat()
    session.setdefault("session_id", session_id)
    session.setdefault("ticket_id", state.ticket_id or session.get("ticket_id") or "")

    session["messages"] = state.messages or session.get("messages", [])
    session["classification"] = {
        "category": state.category,
        "urgency": state.urgency,
        "sentiment": state.sentiment,
        "summary": state.summary,
    }
    session["selected_faq_ids"] = state.selected_faq_ids or session.get("selected_faq_ids", [])
    session["judge_score"] = state.judge_score
    session["judge_decision"] = state.judge_decision
    session["judge_feedback"] = state.judge_feedback
    session["retry_count"] = state.retry_count
    session["status"] = state.status or session.get("status", "in_progress")
    session["human_review_required"] = state.human_review_required
    session["escalation_reason"] = state.escalation_reason
    session["reasoning"] = state.reasoning_log or session.get("reasoning", [])
    session["updated_at"] = now
    session.setdefault("created_at", now)
    return session


async def load_or_create_session(session_id: str, ticket_id: Optional[str]) -> dict:
    session = await load_session(session_id)
    if session is None:
        session = new_session(session_id, ticket_id, datetime.now(timezone.utc).isoformat())
    return session


async def get_persisted_session(session_id: str) -> Optional[dict]:
    return await load_session(session_id)


async def persist_workflow_state(state: WorkflowState) -> Optional[dict]:
    session_id = state.session_id if state else None
    if not session_id:
        return None

    async with _lock_for(session_id):
        existing_session = await load_session(session_id)
        session = apply_state_to_session(existing_session or new_session(session_id, state.ticket_id, datetime.now(timezone.utc).isoformat()), state)

        try:
            await save_session(session)
            log_with_context(
                logger,
                "INFO",
                "WORKFLOW-PERSIST: Session state persisted",
                context={"session_id": session_id, "status": session.get("status")},
            )
            return session
        except Exception as exc:
            log_with_context(
                logger,
                "ERROR",
                "WORKFLOW-PERSIST: Failed to persist workflow state",
                context={"session_id": session_id, "error": str(exc)},
            )
            raise
