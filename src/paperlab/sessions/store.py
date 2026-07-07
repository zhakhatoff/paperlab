"""JSONL persistence for ReviewReport sessions."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel

from paperlab.orchestrator import ReviewReport


def default_sessions_dir() -> Path:
    home = os.environ.get("PAPERLAB_HOME")
    if home:
        return Path(home) / "sessions"
    return Path.home() / ".paperlab" / "sessions"


def save_report(report: ReviewReport, base_dir: Path | None = None) -> Path:
    base_dir = base_dir or default_sessions_dir()
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{report.session_id}.jsonl"
    path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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
        except Exception:
            continue
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def load_report(session_id: str, base_dir: Path | None = None) -> ReviewReport:
    base_dir = base_dir or default_sessions_dir()
    path = base_dir / f"{session_id}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id} ({path})")
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    data = json.loads(first_line)
    return ReviewReport(**data)
