from fastapi import APIRouter

from app.workflow.orchestrator import get_session, process_ticket
from app.workflow.state import SessionResponse, TicketRequest, TicketResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}


@router.post("/api/v1/support/tickets/process", response_model=TicketResponse)
async def process_ticket_endpoint(request: TicketRequest) -> TicketResponse:
    return await process_ticket(request)


@router.get("/api/v1/support/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str) -> SessionResponse:
    return await get_session(session_id)
