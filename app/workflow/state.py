from typing import Optional

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {"billing", "technical", "account", "subscription", "general", "security"}
VALID_URGENCIES = {"low", "medium", "high", "critical"}
VALID_DECISIONS = {"approve", "revise"}


class TicketRequest(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Identifier of an existing conversation session. Omit to start a new session — the backend generates one.",
    )
    ticket_id: str = Field(..., description="Identifier of the support ticket")
    message: str = Field(..., description="The customer's support message")


class Message(BaseModel):
    role: str
    content: str
    timestamp: str


class Classification(BaseModel):
    category: Optional[str] = None
    urgency: Optional[str] = None
    sentiment: Optional[str] = None
    summary: Optional[str] = None


class Reasoning(BaseModel):
    node: str
    response_type: str
    reasoning: str


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
    reasoning: list[Reasoning] = Field(default_factory=list)
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
    reasoning: list[Reasoning] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ClassificationResult(BaseModel):
    category: str = "general"
    urgency: str = "medium"
    sentiment: str = "neutral"
    summary: str = ""
    reasoning: str = ""

    @field_validator("category")
    @classmethod
    def _coerce_category(cls, v: str) -> str:
        return v if v in VALID_CATEGORIES else "general"

    @field_validator("urgency")
    @classmethod
    def _coerce_urgency(cls, v: str) -> str:
        return v if v in VALID_URGENCIES else "medium"


class FaqSelection(BaseModel):
    selected_ids: list[str] = Field(default_factory=list)
    reasoning: str = ""


class JudgeVerdict(BaseModel):
    score: float = 0.0
    decision: str = "revise"
    feedback: str = ""
    reasoning: str = ""

    @field_validator("decision")
    @classmethod
    def _coerce_decision(cls, v: str) -> str:
        return v if v in VALID_DECISIONS else "revise"


class GenerationResult(BaseModel):
    response: str = ""
    reasoning: str = ""


class WorkflowState(BaseModel):
    session_id: str
    ticket_id: str
    message: str = ""
    messages: list[dict] = Field(default_factory=list)

    category: Optional[str] = None
    urgency: Optional[str] = None
    sentiment: Optional[str] = None
    summary: Optional[str] = None

    handler_constraints: str = ""

    selected_faq_ids: list[str] = Field(default_factory=list)
    selected_faqs: list[dict] = Field(default_factory=list)

    response: str = ""
    judge_score: Optional[float] = None
    judge_decision: Optional[str] = None
    judge_feedback: Optional[str] = None
    retry_count: int = 0

    escalate: bool = False
    escalation_reason: Optional[str] = None
    status: Optional[str] = None
    human_review_required: bool = False

    reasoning_log: list[dict] = Field(default_factory=list)
