from app.core.logging import get_logger, log_with_context
from app.workflow.nodes.handlers.prompt import (
    ACCOUNT_CONSTRAINTS,
    BILLING_CONSTRAINTS,
    GENERAL_CONSTRAINTS,
    SUBSCRIPTION_CONSTRAINTS,
    TECHNICAL_CONSTRAINTS,
)
from app.workflow.state import WorkflowState

logger = get_logger(__name__)

CONSTRAINTS_BY_CATEGORY = {
    "billing": BILLING_CONSTRAINTS,
    "technical": TECHNICAL_CONSTRAINTS,
    "account": ACCOUNT_CONSTRAINTS,
    "subscription": SUBSCRIPTION_CONSTRAINTS,
    "general": GENERAL_CONSTRAINTS,
}


async def apply_handler(state: WorkflowState) -> dict:
    category = state.category or "general"
    constraints = CONSTRAINTS_BY_CATEGORY.get(category, GENERAL_CONSTRAINTS)
    log_with_context(
        logger,
        "INFO",
        f"TICKET-HANDLER: {category.capitalize()} handler applied",
        context={"session_id": state.session_id, "ticket_id": state.ticket_id, "category": category},
    )
    return {"handler_constraints": constraints}
