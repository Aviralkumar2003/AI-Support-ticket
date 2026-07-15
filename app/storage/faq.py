import json
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)

_faqs: Optional[list[dict]] = None


def load_faqs() -> list[dict]:
    global _faqs
    if _faqs is not None:
        return _faqs
    try:
        with open(Path(settings.FAQ_FILE), "r", encoding="utf-8") as f:
            _faqs = json.load(f)
        log_with_context(
            logger,
            "INFO",
            "FAQ-LOAD: FAQ file loaded",
            context={"count": len(_faqs)},
        )
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "FAQ-LOAD: Failed to load FAQ file",
            context={"faq_file": settings.FAQ_FILE, "error": str(e)},
        )
        _faqs = []
    return _faqs
