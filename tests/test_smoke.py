"""Smoke tests — just verify the package imports and CLI runs."""

from typer.testing import CliRunner

from paperlab import __version__
from paperlab.cli.main import app

runner = CliRunner()


def test_version_string() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "paperlab" in result.stdout
