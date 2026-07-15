from typing import Optional, TypedDict


class WorkflowState(TypedDict, total=False):
    session_id: str
    ticket_id: str
    message: str
    messages: list[dict]

    category: str
    urgency: str
    sentiment: str
    summary: str

    handler_constraints: str

    selected_faq_ids: list[str]
    selected_faqs: list[dict]

    response: str
    judge_score: float
    judge_decision: str
    judge_feedback: Optional[str]
    retry_count: int

    escalate: bool
    escalation_reason: Optional[str]
    status: str
    human_review_required: bool
