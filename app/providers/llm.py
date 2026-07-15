from typing import Any, Callable, Coroutine, Optional

from litellm import acompletion

from app.core.config import settings
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)

LlmClient = Callable[..., Coroutine[Any, Any, Any]]


def get_llm_client() -> LlmClient:
    """Return a single reusable async callable wrapping LiteLLM with env-configured model."""

    async def _call(messages: list[dict], response_format: Optional[dict] = None, **kwargs: Any) -> Any:
        log_with_context(
            logger,
            "INFO",
            "LLM-CALL: Requesting completion (llm.py get_llm_client)",
            context={"model": settings.LLM_MODEL, "provider": settings.LLM_PROVIDER},
        )
        try:
            response = await acompletion(
                model=settings.LLM_MODEL,
                messages=messages,
                api_key=settings.GROQ_API_KEY,
                response_format=response_format,
                **kwargs,
            )
            log_with_context(
                logger,
                "INFO",
                "LLM-CALL: Completion received (llm.py get_llm_client)",
                context={"model": settings.LLM_MODEL},
            )
            return response
        except Exception as e:
            log_with_context(
                logger,
                "ERROR",
                "LLM-CALL: Completion failed (llm.py get_llm_client)",
                context={"model": settings.LLM_MODEL, "error": str(e)},
            )
            raise

    return _call
