import json
from typing import Type, TypeVar

from pydantic import BaseModel

from app.providers.llm import call_llm
from app.workflow.state import Reasoning, WorkflowState

T = TypeVar("T", bound=BaseModel)


async def complete_structured(system: str, user: str, model_cls: Type[T]) -> T:
    response = await call_llm(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response.choices[0].message.content)
    return model_cls.model_validate(parsed)


def append_reasoning(state: WorkflowState, node: str, response_type: str, reasoning: str) -> list[dict]:
    return [
        *state.reasoning_log,
        Reasoning(node=node, response_type=response_type, reasoning=reasoning).model_dump(),
    ]
