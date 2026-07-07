"""Tests for the `paperlab web` CLI command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import paperlab.web
from paperlab.cli.main import app

runner = CliRunner()


def test_web_command_calls_launch(monkeypatch):
    mock_launch = MagicMock()
    monkeypatch.setattr(paperlab.web, "launch", mock_launch)

    result = runner.invoke(app, ["web"])

    assert result.exit_code == 0, result.output
    mock_launch.assert_called_once()
