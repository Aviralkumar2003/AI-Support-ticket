import logging
import sys
from typing import Optional

from app.core.config import settings

_CONFIGURED = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger sharing the project's root configuration."""
    _configure_root_logger()
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: Optional[dict] = None,
) -> None:
    """Log a message with structured context appended, per project logging convention."""
    context = context or {}
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(f"{message} | context={context}")
