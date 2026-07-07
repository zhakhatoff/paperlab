"""Tests for paperlab.sessions.export."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from paperlab.agents import AgentReport
from paperlab.ingest import IngestedPaper
from paperlab.orchestrator import ReviewReport
from paperlab.sessions import to_json, to_markdown


def _make_report(with_error: bool = False) -> ReviewReport:
    paper = IngestedPaper(
        source_path="/tmp/paper.pdf",
        title="Sample Paper",
        text="content",
        num_pages=2,
        backend="docling",
    )
    agents = {
        "summarizer": AgentReport(
            agent_name="summarizer",
            mode="fast",
            lang="en",
            model="fake",
            output={"summary": "A brief overview", "keywords": ["kw1", "kw2"]},
            raw='{"summary": "A brief overview", "keywords": ["kw1", "kw2"]}',
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
            output={},
            raw="",
            error="parse failed" if with_error else None,
        ),
        "contextualizer": AgentReport(
            agent_name="contextualizer",
            mode="fast",
            lang="en",
            model="fake",
            output={"context": "broad"},
            raw='{"context": "broad"}',
            error=None,
        ),
    }
    return ReviewReport(
        paper=paper,
        mode="fast",
        lang="en",
        model="fake",
        session_id="testxyz",
        created_at=datetime.now(timezone.utc).isoformat(),
        agents=agents,
    )


def test_to_json_contains_session_id():
    report = _make_report()
    result = to_json(report)
    assert "testxyz" in result


def test_to_json_round_trips():
    report = _make_report()
    result = to_json(report)
    parsed = json.loads(result)
    assert parsed == report.model_dump(mode="json")


def test_to_markdown_has_header():
    report = _make_report()
    md = to_markdown(report)
    assert "# paperlab review testxyz" in md


def test_to_markdown_has_all_agent_sections():
    report = _make_report()
    md = to_markdown(report)
    for name in ("summarizer", "methodologist", "critic", "contextualizer"):
        assert f"## {name}" in md.lower() or name in md.lower()


def test_to_markdown_has_output_key():
    report = _make_report()
    md = to_markdown(report)
    # summarizer has 'summary' key in output
    assert "summary" in md


def test_to_markdown_error_section():
    report = _make_report(with_error=True)
    md = to_markdown(report)
    assert "error" in md
    assert "parse failed" in md
