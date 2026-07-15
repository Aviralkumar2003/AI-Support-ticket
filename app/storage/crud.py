import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)


def _session_path(session_id: str) -> Path:
    return Path(settings.SESSION_DIR) / f"{session_id}.json"


def _read_session_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_session_file(path: Path, session: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)


async def load_session(session_id: str) -> Optional[dict]:
    """Load a session JSON file. Returns None if missing, empty, or corrupted."""
    path = _session_path(session_id)
    if not path.exists():
        log_with_context(
            logger,
            "WARNING",
            "SESSION-STORAGE: Session file not found (session.py load_session)",
            context={"session_id": session_id},
        )
        return None
    try:
        session = await asyncio.to_thread(_read_session_file, path)
        log_with_context(
            logger,
            "INFO",
            "SESSION-STORAGE: Session loaded (session.py load_session)",
            context={"session_id": session_id},
        )
        return session
    except Exception as e:
        log_with_context(
            logger,
            "WARNING",
            "SESSION-STORAGE: Failed to read session file (session.py load_session)",
            context={"session_id": session_id, "error": str(e)},
        )
        return None


async def save_session(session: dict) -> None:
    """Persist a session dict to its JSON file, always refreshing updated_at."""
    session_id = session.get("session_id")
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = _session_path(session_id)
    try:
        await asyncio.to_thread(_write_session_file, path, session)
        log_with_context(
            logger,
            "INFO",
            "SESSION-STORAGE: Session saved (session.py save_session)",
            context={"session_id": session_id},
        )
    except Exception as e:
        log_with_context(
            logger,
            "ERROR",
            "SESSION-STORAGE: Failed to write session file (session.py save_session)",
            context={"session_id": session_id, "error": str(e)},
        )
        raise
