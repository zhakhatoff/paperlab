"""Tests for paperlab.sessions.store."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from paperlab.agents import AgentReport
from paperlab.ingest import IngestedPaper
from paperlab.orchestrator import ReviewReport
from paperlab.sessions import (
    default_sessions_dir,
    list_sessions,
    load_report,
    save_report,
)


def _make_report(
    session_id: str = "abc123",
    created_at: str | None = None,
    title: str | None = "Test Paper",
    with_error: bool = False,
) -> ReviewReport:
    if created_at is None:
        created_at = datetime.now(UTC).isoformat()
    paper = IngestedPaper(
        source_path="/tmp/test.pdf",
        title=title,
        text="Some text.",
        num_pages=1,
        backend="docling",
    )
    agents = {
        "summarizer": AgentReport(
            agent_name="summarizer",
            mode="fast",
            lang="en",
            model="fake",
            output={"summary": "short summary"},
            raw='{"summary": "short summary"}',
            error=None,
        ),
        "methodologist": AgentReport(
            agent_name="methodologist",
            mode="fast",
            lang="en",
            model="fake",
            output={"methods": ["method A"]},
            raw='{"methods": ["method A"]}',
            error=None,
        ),
        "critic": AgentReport(
            agent_name="critic",
            mode="fast",
            lang="en",
            model="fake",
            output={"weaknesses": ["weak point"]},
            raw='{"weaknesses": ["weak point"]}',
            error="parse failed" if with_error else None,
        ),
        "contextualizer": AgentReport(
            agent_name="contextualizer",
            mode="fast",
            lang="en",
            model="fake",
            output={"context": "broad context"},
            raw='{"context": "broad context"}',
            error=None,
        ),
    }
    return ReviewReport(
        paper=paper,
        mode="fast",
        lang="en",
        model="fake",
        session_id=session_id,
        created_at=created_at,
        agents=agents,
    )


# --- default_sessions_dir ---


def test_default_sessions_dir_with_env(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    result = default_sessions_dir()
    assert result == tmp_path / "sessions"


def test_default_sessions_dir_without_env(monkeypatch):
    monkeypatch.delenv("PAPERLAB_HOME", raising=False)
    result = default_sessions_dir()
    assert result.parts[-2:] == (".paperlab", "sessions")


# --- save / list / load round-trip ---


def test_save_list_load_round_trip(tmp_path):
    report = _make_report(session_id="roundtrip01")
    saved_path = save_report(report, base_dir=tmp_path)
    assert saved_path.name == "roundtrip01.jsonl"
    assert saved_path.exists()

    sessions = list_sessions(base_dir=tmp_path)
    assert len(sessions) == 1
    assert sessions[0].session_id == "roundtrip01"

    loaded = load_report("roundtrip01", base_dir=tmp_path)
    assert loaded.model_dump(mode="json") == report.model_dump(mode="json")


def test_list_sessions_empty_dir(tmp_path):
    result = list_sessions(base_dir=tmp_path)
    assert result == []


def test_list_sessions_missing_dir(tmp_path):
    missing = tmp_path / "nonexistent"
    result = list_sessions(base_dir=missing)
    assert result == []


def test_list_sessions_sorted_desc(tmp_path):
    early = "2024-01-01T00:00:00+00:00"
    late = "2025-06-01T00:00:00+00:00"
    r1 = _make_report(session_id="sess_early", created_at=early)
    r2 = _make_report(session_id="sess_late", created_at=late)
    save_report(r1, base_dir=tmp_path)
    save_report(r2, base_dir=tmp_path)

    sessions = list_sessions(base_dir=tmp_path)
    assert len(sessions) == 2
    assert sessions[0].session_id == "sess_late"
    assert sessions[1].session_id == "sess_early"


def test_load_missing_session_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_report("doesnotexist", base_dir=tmp_path)


def test_load_report_rejects_bad_session_id(tmp_path):
    with pytest.raises(ValueError):
        load_report("../../etc/passwd", base_dir=tmp_path)


def test_default_home_and_sessions_agree(monkeypatch, tmp_path):
    from paperlab.cli.config import default_home

    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    assert default_home() == tmp_path
    assert default_sessions_dir() == tmp_path / "sessions"


def test_save_report_file_mode_0600(tmp_path):
    import stat

    report = _make_report(session_id="modecheck")
    path = save_report(report, base_dir=tmp_path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_list_sessions_skips_bad_jsonl(tmp_path):
    report = _make_report(session_id="goodone")
    save_report(report, base_dir=tmp_path)
    (tmp_path / "bad.jsonl").write_text("not-json\n", encoding="utf-8")

    result = list_sessions(base_dir=tmp_path)
    ids = [s.session_id for s in result]
    assert ids == ["goodone"]


def test_session_summary_title(tmp_path):
    report = _make_report(session_id="titled", title="My Paper")
    save_report(report, base_dir=tmp_path)
    sessions = list_sessions(base_dir=tmp_path)
    assert sessions[0].title == "My Paper"
