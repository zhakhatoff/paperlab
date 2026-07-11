"""Integration tests for the paperlab CLI."""

from __future__ import annotations

import re

from typer.testing import CliRunner

import paperlab.cli.main as cli_main
from paperlab.cli.main import app
from paperlab.ingest import IngestedPaper
from paperlab.providers.fake import FakeProvider

runner = CliRunner()


def _fake_extract(path, converter=None):
    return IngestedPaper(source_path=str(path), text="SAMPLE PAPER TEXT", backend="docling")


def _fake_make_provider(name):
    return FakeProvider()


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0, result.output
    assert "paperlab" in result.output


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_init_creates_home_sessions_and_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "sessions").is_dir()
    assert (tmp_path / "config.toml").is_file()


def test_init_without_force_fails_if_config_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "--force" in result.output


def test_init_with_force_overwrites(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# config get / set
# ---------------------------------------------------------------------------


def test_config_set_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    runner.invoke(app, ["init"])
    set_result = runner.invoke(app, ["config", "set", "model", "llama3:8b"])
    assert set_result.exit_code == 0, set_result.output
    assert "model" in set_result.output
    assert "llama3:8b" in set_result.output

    get_result = runner.invoke(app, ["config", "get", "model"])
    assert get_result.exit_code == 0, get_result.output
    assert "llama3:8b" in get_result.output


def test_config_get_invalid_key_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["config", "get", "totally_unknown_key"])
    assert result.exit_code != 0


def test_config_set_extra_key(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["config", "set", "extra.base_url", "http://localhost:9999"])
    assert result.exit_code == 0, result.output
    get_result = runner.invoke(app, ["config", "get", "extra.base_url"])
    assert "http://localhost:9999" in get_result.output


# ---------------------------------------------------------------------------
# list (empty)
# ---------------------------------------------------------------------------


def test_list_empty_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert "No sessions found" in result.output


# ---------------------------------------------------------------------------
# read + show
# ---------------------------------------------------------------------------


def test_read_with_fake_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app,
        ["read", str(paper), "--provider", "fake", "--model", "any", "--format", "markdown"],
    )

    assert result.exit_code == 0, result.output
    assert "# paperlab review" in result.output
    # session_id line goes to stderr — stdout stays clean for piping
    assert "session:" not in result.stdout

    stderr_lines = [ln for ln in result.stderr.strip().split("\n") if ln.strip()]
    session_line = next(ln for ln in stderr_lines if ln.startswith("session: "))
    session_id = session_line[len("session: ") :].strip()
    assert re.fullmatch(r"[0-9a-f]{12}", session_id), f"unexpected session_id: {session_id!r}"

    session_file = tmp_path / "sessions" / f"{session_id}.jsonl"
    assert session_file.exists(), f"session file not found: {session_file}"


def test_read_json_format(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app,
        ["read", str(paper), "--provider", "fake", "--model", "any", "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"session_id"' in result.output


def test_show_session(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    read_result = runner.invoke(
        app,
        ["read", str(paper), "--provider", "fake", "--model", "any", "--format", "markdown"],
    )
    assert read_result.exit_code == 0, read_result.output

    stderr_lines = [ln for ln in read_result.stderr.strip().split("\n") if ln.strip()]
    session_line = next(ln for ln in stderr_lines if ln.startswith("session: "))
    session_id = session_line[len("session: ") :].strip()

    show_result = runner.invoke(app, ["show", session_id])
    assert show_result.exit_code == 0, show_result.output
    assert "# paperlab review" in show_result.output
    assert session_id in show_result.output


def test_read_invalid_format_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app,
        ["read", str(paper), "--provider", "fake", "--model", "any", "--format", "yaml"],
    )
    assert result.exit_code != 0


def test_read_preflight_ollama_not_running(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    from paperlab.providers import discovery

    monkeypatch.setattr(
        discovery,
        "ollama_status",
        lambda *a, **kw: {"running": False, "installed": True, "models": []},
    )

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app, ["read", str(paper), "--provider", "ollama", "--model", "qwen2.5:7b"]
    )
    assert result.exit_code == 1
    assert "ollama serve" in (result.stderr or result.output).lower() or "Ollama" in (
        result.stderr or result.output
    )


def test_read_preflight_skipped_with_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    from paperlab.providers import discovery

    monkeypatch.setattr(
        discovery,
        "ollama_status",
        lambda *a, **kw: {"running": False, "installed": True, "models": []},
    )

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app,
        [
            "read",
            str(paper),
            "--provider",
            "ollama",
            "--model",
            "qwen2.5:7b",
            "--skip-preflight",
        ],
    )
    assert result.exit_code == 0, result.output


def test_read_preflight_cloud_missing_key(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")

    result = runner.invoke(
        app,
        ["read", str(paper), "--provider", "anthropic", "--model", "claude-sonnet-4-5"],
    )
    assert result.exit_code == 1
    combined = (result.stderr or "") + result.output
    assert "anthropic" in combined
    assert "paperlab" in combined


def test_verbose_flag_works_on_version():
    result = runner.invoke(app, ["--verbose", "version"])
    assert result.exit_code == 0, result.output
    assert "paperlab" in result.output


def test_read_writes_output_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    monkeypatch.setattr(cli_main._RUNTIME, "extract_text", _fake_extract)
    monkeypatch.setattr(cli_main._RUNTIME, "make_provider", _fake_make_provider)

    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4 fake")
    out_file = tmp_path / "report.md"

    result = runner.invoke(
        app,
        [
            "read",
            str(paper),
            "--provider",
            "fake",
            "--model",
            "any",
            "--format",
            "markdown",
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_file.exists()
    assert "# paperlab review" in out_file.read_text()
