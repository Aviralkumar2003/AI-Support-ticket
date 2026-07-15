from typing import Optional

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Identifier of an existing conversation session. Omit to start a new session — the backend generates one.",
    )
    ticket_id: str = Field(..., description="Identifier of the support ticket")
    message: str = Field(..., description="The customer's support message")
