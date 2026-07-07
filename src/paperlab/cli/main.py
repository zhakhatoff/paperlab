"""paperlab CLI entrypoint."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import typer
from rich.console import Console
from rich.table import Table

from paperlab import __version__
from paperlab.ingest import extract_text
from paperlab.providers.factory import make_provider

# ---------------------------------------------------------------------------
# Runtime shim — replace fields in tests to avoid real I/O.
# ---------------------------------------------------------------------------
_RUNTIME = SimpleNamespace(
    extract_text=extract_text,
    make_provider=make_provider,
)

# ---------------------------------------------------------------------------
# Typer apps
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="paperlab",
    help="Multi-agent LLM tool for critically reading biomedical research papers.",
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(
    name="config",
    help="Get or set configuration values.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

console = Console()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show paperlab version."""
    typer.echo(f"paperlab {__version__}")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
) -> None:
    """Create ~/.paperlab with config.toml and sessions/."""
    from paperlab.cli.config import PaperlabConfig, default_config_path, default_home, save_config

    home = default_home()
    sessions_dir = home / "sessions"
    config_path = default_config_path()

    if config_path.exists() and not force:
        typer.echo(f"Config already exists: {config_path}", err=True)
        typer.echo("Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    sessions_dir.mkdir(parents=True, exist_ok=True)
    save_config(PaperlabConfig(), config_path)

    typer.echo(f"home:     {home}")
    typer.echo(f"sessions: {sessions_dir}")
    typer.echo(f"config:   {config_path}")


@app.command()
def read(
    paper: Path = typer.Argument(..., help="Path to the PDF file"),
    mode: str | None = typer.Option(None, help="rigorous | learning"),
    lang: str | None = typer.Option(None, help="en | ru"),
    model: str | None = typer.Option(None, help="Override the configured model"),
    provider: str | None = typer.Option(None, help="Provider name"),
    format: str = typer.Option("markdown", help="markdown | json"),
    output: Path | None = typer.Option(None, help="Write report to file"),
) -> None:
    """Run the multi-agent review on a paper."""
    from paperlab.cli.config import load_config
    from paperlab.orchestrator import review
    from paperlab.sessions import save_report, to_json, to_markdown

    cfg = load_config()
    effective_mode = mode or cfg.mode
    effective_lang = lang or cfg.lang
    effective_model = model or cfg.model
    effective_provider = provider or cfg.provider

    provider_instance = _RUNTIME.make_provider(effective_provider)
    paper_obj = _RUNTIME.extract_text(paper)

    report = asyncio.run(
        review(paper_obj, provider_instance, effective_mode, effective_lang, effective_model)
    )
    save_report(report)

    content = to_json(report) if format == "json" else to_markdown(report)
    print(content)

    if output:
        output.write_text(content, encoding="utf-8")

    print(f"session: {report.session_id}")


@app.command(name="list")
def list_sessions_cmd() -> None:
    """List past review sessions."""
    from paperlab.sessions import list_sessions

    sessions = list_sessions()
    if not sessions:
        typer.echo("No sessions found.")
        raise typer.Exit(code=0)

    table = Table(show_header=True, header_style="bold")
    table.add_column("session_id")
    table.add_column("created_at")
    table.add_column("mode")
    table.add_column("lang")
    table.add_column("model")
    for s in sessions:
        table.add_row(s.session_id, s.created_at, s.mode, s.lang, s.model)
    console.print(table)


@app.command()
def show(
    session_id: str = typer.Argument(..., help="Session ID to display"),
    format: str = typer.Option("markdown", help="markdown | json"),
) -> None:
    """Show a past review session."""
    from paperlab.sessions import load_report, to_json, to_markdown

    report = load_report(session_id)
    print(to_json(report) if format == "json" else to_markdown(report))


@app.command()
def web() -> None:
    """Launch the local Gradio web dashboard."""
    try:
        from paperlab.web import launch
    except ImportError as exc:
        typer.echo(
            f"Could not import paperlab.web: {exc}\n"
            "Install the web extras: pip install paperlab[web]",
            err=True,
        )
        raise typer.Exit(code=1) from None
    launch()


# ---------------------------------------------------------------------------
# config sub-commands
# ---------------------------------------------------------------------------


@config_app.command(name="get")
def config_get(
    key: str = typer.Argument(..., help="Config key (e.g. provider, model, extra.foo)"),
) -> None:
    """Print the value of a config key."""
    from paperlab.cli.config import get_field, load_config

    cfg = load_config()
    try:
        value = get_field(cfg, key)
    except KeyError:
        typer.echo(f"Unknown key: {key}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(value)


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="New value"),
) -> None:
    """Set a config key to a new value."""
    from paperlab.cli.config import load_config, save_config, set_field

    cfg = load_config()
    try:
        cfg = set_field(cfg, key, value)
    except KeyError:
        typer.echo(f"Unknown key: {key}", err=True)
        raise typer.Exit(code=1) from None
    save_config(cfg)
    typer.echo(f"{key} = {value}")


if __name__ == "__main__":
    app()
