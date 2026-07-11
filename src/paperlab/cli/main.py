"""paperlab CLI entrypoint."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

import typer
from rich.console import Console
from rich.table import Table

from paperlab import __version__
from paperlab.ingest import extract_text
from paperlab.providers.factory import SUPPORTED_PROVIDERS, make_provider

_CLOUD_PROVIDERS: frozenset[str] = frozenset(SUPPORTED_PROVIDERS) - {"ollama", "fake", "custom"}

log = logging.getLogger("paperlab")

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


@app.callback()
def _root(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable debug logging to stderr.",
    ),
) -> None:
    """paperlab root callback — configures logging."""
    level = logging.DEBUG if verbose else logging.WARNING
    root = logging.getLogger()
    # Reset handlers so repeated CLI invocations don't stack them (tests reuse the process).
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("paperlab").setLevel(level)


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
    skip_preflight: bool = typer.Option(
        False,
        "--skip-preflight",
        help="Skip provider readiness checks (Ollama running / API key present).",
    ),
) -> None:
    """Run the multi-agent review on a paper."""
    from paperlab.cli.config import load_config
    from paperlab.orchestrator import review
    from paperlab.providers import discovery, keys
    from paperlab.sessions import save_report, to_json, to_markdown

    if format not in {"markdown", "json"}:
        raise typer.BadParameter(
            f"--format must be 'markdown' or 'json', got {format!r}",
            param_hint="--format",
        )

    cfg = load_config()
    effective_mode = mode or cfg.mode
    effective_lang = lang or cfg.lang
    effective_model = model or cfg.model
    effective_provider = provider or cfg.provider

    if not skip_preflight:
        if effective_provider == "ollama":
            status = discovery.ollama_status()
            if not status.get("running"):
                typer.echo(
                    "Ollama is not running. Start it with: ollama serve",
                    err=True,
                )
                raise typer.Exit(code=1)
        elif effective_provider in _CLOUD_PROVIDERS:
            if keys.get_key(effective_provider) is None:
                typer.echo(
                    f"No API key saved for {effective_provider}. "
                    "Run: paperlab config set ...  or  paperlab web  to save it.",
                    err=True,
                )
                raise typer.Exit(code=1)

    log.info(
        "starting review, provider=%s model=%s mode=%s lang=%s",
        effective_provider,
        effective_model,
        effective_mode,
        effective_lang,
    )

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

    typer.echo(f"session: {report.session_id}", err=True)


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

    try:
        report = load_report(session_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Session not found: {session_id} ({exc})", err=True)
        raise typer.Exit(code=1) from None
    print(to_json(report) if format == "json" else to_markdown(report))


@app.command()
def web(
    port: int = typer.Option(7860, help="Port to bind"),
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't auto-open the browser"),
    share: bool = typer.Option(False, "--share", help="Create a public Gradio share link"),
) -> None:
    """Launch the local Gradio web dashboard."""
    try:
        from paperlab.web import build_app
    except ImportError as exc:
        typer.echo(
            f"Could not import paperlab.web: {exc}\n"
            "Install the web extras: pip install paperlab[web]",
            err=True,
        )
        raise typer.Exit(code=1) from None

    if host not in {"127.0.0.1", "localhost", "::1"} or share:
        console.print(
            "[bold red]WARNING[/]: exposing the dashboard beyond localhost has no auth; "
            "anyone reaching this URL can read saved keys and trigger reviews."
        )

    url = f"http://{host}:{port}"
    console.print(f"[green]paperlab web[/green] starting at [cyan]{url}[/cyan]")
    console.print(
        "[dim]First launch takes a few seconds while Gradio warms up. Ctrl+C to stop.[/dim]"
    )

    gradio_app = build_app()
    gradio_app.launch(
        server_name=host,
        server_port=port,
        inbrowser=not no_browser,
        share=share,
    )


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
