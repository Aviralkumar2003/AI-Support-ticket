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


async def _apply_handler(state: WorkflowState, category: str, constraints: str) -> WorkflowState:
    state["handler_constraints"] = constraints
    log_with_context(
        logger,
        "INFO",
        f"TICKET-HANDLER: {category.capitalize()} handler applied (handlers.py {category}_handler)",
        context={"session_id": state.get("session_id"), "ticket_id": state.get("ticket_id"), "category": category},
    )
    return state


async def billing_handler(state: WorkflowState) -> WorkflowState:
    return await _apply_handler(state, "billing", BILLING_CONSTRAINTS)


async def technical_handler(state: WorkflowState) -> WorkflowState:
    return await _apply_handler(state, "technical", TECHNICAL_CONSTRAINTS)


async def account_handler(state: WorkflowState) -> WorkflowState:
    return await _apply_handler(state, "account", ACCOUNT_CONSTRAINTS)


async def subscription_handler(state: WorkflowState) -> WorkflowState:
    return await _apply_handler(state, "subscription", SUBSCRIPTION_CONSTRAINTS)


async def general_handler(state: WorkflowState) -> WorkflowState:
    return await _apply_handler(state, "general", GENERAL_CONSTRAINTS)
