"""Tests for the `paperlab web` CLI command."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

import paperlab.web
from paperlab.cli.main import app

runner = CliRunner()


def test_web_command_launches_gradio(monkeypatch):
    fake_app = MagicMock()
    monkeypatch.setattr(paperlab.web, "build_app", lambda: fake_app)

    result = runner.invoke(app, ["web", "--no-browser"])

    assert result.exit_code == 0, result.output
    fake_app.launch.assert_called_once()
    kwargs = fake_app.launch.call_args.kwargs
    assert kwargs["server_name"] == "127.0.0.1"
    assert kwargs["server_port"] == 7860
    assert kwargs["inbrowser"] is False
    assert kwargs["share"] is False


def test_web_command_respects_flags(monkeypatch):
    fake_app = MagicMock()
    monkeypatch.setattr(paperlab.web, "build_app", lambda: fake_app)

    result = runner.invoke(
        app,
        ["web", "--host", "0.0.0.0", "--port", "9000", "--share"],
    )

    assert result.exit_code == 0, result.output
    kwargs = fake_app.launch.call_args.kwargs
    assert kwargs["server_name"] == "0.0.0.0"
    assert kwargs["server_port"] == 9000
    assert kwargs["share"] is True
    assert kwargs["inbrowser"] is True
