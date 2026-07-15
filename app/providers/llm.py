from typing import Any, Optional

from litellm import acompletion

from app.core.config import settings
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)


async def call_llm(messages: list[dict], response_format: Optional[dict] = None, **kwargs: Any) -> Any:
    """Async LiteLLM completion using the env-configured model."""
    log_with_context(
        logger,
        "INFO",
        "LLM-CALL: Requesting completion",
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
            "LLM-CALL: Completion received",
            context={"model": settings.LLM_MODEL},
        )
        return response
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "LLM-CALL: Completion failed",
            context={"model": settings.LLM_MODEL, "error": str(e)},
        )
        raise
