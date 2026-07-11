"""Smoke tests — verify the package imports, CLI runs, and pipeline works."""

from __future__ import annotations

import asyncio

from typer.testing import CliRunner

from paperlab import __version__
from paperlab.agents import ALL_AGENTS
from paperlab.cli.main import app
from paperlab.ingest import IngestedPaper
from paperlab.orchestrator import review
from paperlab.providers.fake import FakeProvider
from paperlab.sessions import save_report

runner = CliRunner()


def test_version_string() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "paperlab" in result.stdout


def test_pipeline_end_to_end(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    paper = IngestedPaper(source_path="x.pdf", text="SAMPLE PAPER TEXT", backend="docling")
    provider = FakeProvider(default='{"a":1}')

    report = asyncio.run(review(paper, provider, "rigorous", "en", "m"))
    assert len(report.agents) == len(ALL_AGENTS)

    saved = save_report(report)
    assert saved.exists()
