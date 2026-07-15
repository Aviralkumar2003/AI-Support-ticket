from typing import Callable, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.core.logging import get_logger, log_with_context
from app.workflow.nodes.classify import classify_ticket
from app.workflow.nodes.escalate import escalate_to_human
from app.workflow.nodes.faq_select import select_faq
from app.workflow.nodes.generate import generate_response
from app.workflow.nodes.handlers import apply_handler
from app.workflow.nodes.judge import judge_response
from app.workflow.nodes.routing import route_by_category, route_judge_decision
from app.workflow.state import WorkflowState

logger = get_logger(__name__)


def _escalate_or(next_node: str) -> Callable[[WorkflowState], str]:
    """Conditional edge: divert to escalation if flagged, else continue."""
    return lambda state: "escalate_to_human" if state.escalate else next_node


def _build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("classify_ticket", classify_ticket)
    graph.add_node("apply_handler", apply_handler)
    graph.add_node("select_faq", select_faq)
    graph.add_node("generate_response", generate_response)
    graph.add_node("judge_response", judge_response)
    graph.add_node("escalate_to_human", escalate_to_human)

    graph.set_entry_point("classify_ticket")

    graph.add_conditional_edges(
        "classify_ticket",
        route_by_category,
        {
            "apply_handler": "apply_handler",
            "escalate_to_human": "escalate_to_human",
        },
    )

    graph.add_edge("apply_handler", "select_faq")

    graph.add_conditional_edges(
        "select_faq",
        _escalate_or("generate_response"),
        {
            "escalate_to_human": "escalate_to_human",
            "generate_response": "generate_response",
        },
    )

    graph.add_conditional_edges(
        "generate_response",
        _escalate_or("judge_response"),
        {
            "escalate_to_human": "escalate_to_human",
            "judge_response": "judge_response",
        },
    )

    graph.add_conditional_edges(
        "judge_response",
        route_judge_decision,
        {
            "END": END,
            "generate_response": "generate_response",
            "escalate_to_human": "escalate_to_human",
        },
    )

    graph.add_edge("escalate_to_human", END)

    return graph


_checkpointer = MemorySaver()
_compiled_graph = _build_graph().compile(checkpointer=_checkpointer)


async def run_workflow(state: Optional[WorkflowState], thread_id: str) -> WorkflowState:
    config = {"configurable": {"thread_id": thread_id}}
    log_with_context(
        logger,
        "INFO",
        "WORKFLOW: Workflow run started",
        context={"thread_id": thread_id, "resume": state is None},
    )
    result = await _compiled_graph.ainvoke(state, config=config)
    log_with_context(
        logger,
        "INFO",
        "WORKFLOW: Workflow run complete",
        context={"thread_id": thread_id, "status": result.get("status")},
    )
    return result
