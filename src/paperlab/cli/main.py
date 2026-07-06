"""paperlab CLI entrypoint."""

from __future__ import annotations

import typer
from rich.console import Console

from paperlab import __version__

app = typer.Typer(
    name="paperlab",
    help="Multi-agent LLM tool for critically reading biomedical research papers.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Show paperlab version."""
    console.print(f"paperlab {__version__}")


@app.command()
def init() -> None:
    """Interactive setup: pick a provider, download a model, save config."""
    console.print("[yellow]init: not implemented yet — coming in week 3[/yellow]")
    raise typer.Exit(code=1)


@app.command()
def read(
    paper: str = typer.Argument(..., help="Path to the PDF file"),
    mode: str = typer.Option("rigorous", help="rigorous | learning"),
    lang: str = typer.Option("en", help="en | ru"),
    model: str | None = typer.Option(None, help="Override the configured model"),
) -> None:
    """Run the multi-agent review on a paper."""
    console.print(
        f"[yellow]read: not implemented yet — coming in week 3.[/yellow]\n"
        f"paper={paper} mode={mode} lang={lang} model={model}"
    )
    raise typer.Exit(code=1)


@app.command()
def web() -> None:
    """Launch the local Gradio web dashboard."""
    console.print("[yellow]web: not implemented yet — coming in week 5[/yellow]")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
