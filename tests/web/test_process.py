"""Tests for paperlab.web.app.process()."""

from __future__ import annotations

import json

import paperlab.web.app as web_app
from paperlab.ingest import IngestedPaper
from paperlab.providers.fake import FakeProvider

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _fake_extract(path, converter=None):
    return IngestedPaper(source_path="p.pdf", text="SAMPLE", backend="docling")


def _fake_make_provider(name):
    return FakeProvider()


# ---------------------------------------------------------------------------
# empty path validation
# ---------------------------------------------------------------------------


def test_process_empty_path_returns_error_json():
    md, js = web_app.process("", "rigorous", "en", "x", "fake")
    assert md == ""
    data = json.loads(js)
    assert "error" in data


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_process_returns_markdown_and_json(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(web_app._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(web_app._RUNTIME, "make_provider", _fake_make_provider)

    md, js = web_app.process("p.pdf", "rigorous", "en", "x", "fake")

    assert "# paperlab review" in md
    data = json.loads(js)
    assert "session_id" in data


# ---------------------------------------------------------------------------
# session saved to disk
# ---------------------------------------------------------------------------


def test_process_saves_session_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(web_app._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(web_app._RUNTIME, "make_provider", _fake_make_provider)

    _, js = web_app.process("p.pdf", "rigorous", "en", "x", "fake")
    session_id = json.loads(js)["session_id"]

    session_file = tmp_path / "sessions" / f"{session_id}.jsonl"
    assert session_file.exists(), f"session file not found: {session_file}"


# ---------------------------------------------------------------------------
# HTML escape in sessions table
# ---------------------------------------------------------------------------


def test_sessions_html_escapes_user_data(monkeypatch):
    from paperlab.sessions.store import SessionSummary

    xss = "<script>alert(1)</script>"

    def _fake_list_sessions():
        return [
            SessionSummary(
                session_id=xss,
                created_at="2026-07-11",
                mode="rigorous",
                lang="en",
                model=xss,
                title=xss,
            )
        ]

    import paperlab.sessions as sessions_pkg

    monkeypatch.setattr(sessions_pkg, "list_sessions", _fake_list_sessions)

    html = web_app._sessions_html()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
