from typing import Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    timestamp: str


class Classification(BaseModel):
    category: str
    urgency: str
    sentiment: str
    summary: str


class TicketResponse(BaseModel):
    session_id: str
    ticket_id: str
    category: str
    urgency: str
    sentiment: str
    selected_faq_ids: list[str]
    judge_score: float
    judge_decision: str
    judge_feedback: str
    retry_count: int
    status: str
    human_review_required: bool
    escalation_reason: Optional[str] = None
    response: str


class SessionResponse(BaseModel):
    session_id: str
    ticket_id: str
    messages: list[Message]
    classification: Optional[Classification] = None
    selected_faq_ids: list[str]
    judge_score: Optional[float] = None
    judge_decision: Optional[str] = None
    judge_feedback: Optional[str] = None
    retry_count: int
    status: str
    human_review_required: bool
    escalation_reason: Optional[str] = None
    created_at: str
    updated_at: str
