import json
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)

_faqs: Optional[list[dict]] = None


def load_faqs() -> list[dict]:
    """Load data/faqs.json once and cache it in memory."""
    global _faqs
    if _faqs is not None:
        return _faqs
    try:
        with open(Path(settings.FAQ_FILE), "r", encoding="utf-8") as f:
            _faqs = json.load(f)
        log_with_context(
            logger,
            "INFO",
            "FAQ-LOAD: FAQ file loaded (faq.py load_faqs)",
            context={"count": len(_faqs)},
        )
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "FAQ-LOAD: Failed to load FAQ file (faq.py load_faqs)",
            context={"faq_file": settings.FAQ_FILE, "error": str(e)},
        )
        _faqs = []
    return _faqs


def get_faqs_by_category(category: str) -> list[dict]:
    """Return the subset of FAQ entries matching the given category."""
    faqs = load_faqs()
    matches = [faq for faq in faqs if faq.get("category") == category]
    log_with_context(
        logger,
        "INFO",
        "FAQ-FILTER: Filtered FAQs by category (faq.py get_faqs_by_category)",
        context={"category": category, "match_count": len(matches)},
    )
    return matches
