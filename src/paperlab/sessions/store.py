"""JSONL persistence for ReviewReport sessions."""

from __future__ import annotations

import contextlib
import json
import os
import re
from pathlib import Path

from pydantic import BaseModel

from paperlab.cli.config import default_home
from paperlab.orchestrator import ReviewReport

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not _SESSION_ID_RE.match(session_id):
        raise ValueError("invalid session_id")


def default_sessions_dir() -> Path:
    return default_home() / "sessions"


def save_report(report: ReviewReport, base_dir: Path | None = None) -> Path:
    _validate_session_id(report.session_id)
    base_dir = base_dir or default_sessions_dir()
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            base_dir.chmod(0o700)
    path = base_dir / f"{report.session_id}.jsonl"
    payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False) + "\n"
    flags = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(payload)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)
    return path


class SessionSummary(BaseModel):
    session_id: str
    created_at: str
    mode: str
    lang: str
    model: str
    title: str | None = None


def list_sessions(base_dir: Path | None = None) -> list[SessionSummary]:
    base_dir = base_dir or default_sessions_dir()
    if not base_dir.exists():
        return []
    summaries: list[SessionSummary] = []
    for jsonl_file in base_dir.glob("*.jsonl"):
        try:
            first_line = jsonl_file.read_text(encoding="utf-8").splitlines()[0]
            data = json.loads(first_line)
            paper = data.get("paper") or {}
            summaries.append(
                SessionSummary(
                    session_id=data["session_id"],
                    created_at=data["created_at"],
                    mode=data["mode"],
                    lang=data["lang"],
                    model=data["model"],
                    title=paper.get("title"),
                )
            )
        except (json.JSONDecodeError, KeyError, IndexError, OSError):
            continue
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def load_report(session_id: str, base_dir: Path | None = None) -> ReviewReport:
    _validate_session_id(session_id)
    base_dir = base_dir or default_sessions_dir()
    path = base_dir / f"{session_id}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id} ({path})")
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    data = json.loads(first_line)
    return ReviewReport(**data)
