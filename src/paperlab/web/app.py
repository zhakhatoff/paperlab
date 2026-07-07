"""paperlab Gradio web dashboard."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from paperlab.ingest import extract_text
from paperlab.providers.factory import make_provider

# ---------------------------------------------------------------------------
# Runtime shim — replace fields in tests to avoid real I/O.
# ---------------------------------------------------------------------------
_RUNTIME = SimpleNamespace(
    extract_text=extract_text,
    make_provider=make_provider,
)


def process(
    paper_path: str,
    mode: str,
    lang: str,
    model: str,
    provider_name: str,
) -> tuple[str, str]:
    """Run review pipeline on a paper.

    Returns
    -------
    tuple[str, str]
        (markdown report, JSON report)
    """
    from paperlab.orchestrator import review
    from paperlab.sessions import save_report, to_json, to_markdown

    if not paper_path:
        return ("", json.dumps({"error": "no paper uploaded"}))

    paper = _RUNTIME.extract_text(paper_path)
    provider = _RUNTIME.make_provider(provider_name)
    report = asyncio.run(review(paper, provider, mode, lang, model))
    save_report(report)
    return (to_markdown(report), to_json(report))


def build_app():
    """Build and return the Gradio Blocks application (lazy gradio import)."""
    import gradio as gr  # lazy import — not required at module level

    import paperlab.providers as _providers

    with gr.Blocks() as app:
        gr.Markdown("# paperlab web dashboard")

        with gr.Row():
            paper = gr.File(label="Paper (PDF)")
            with gr.Column():
                mode = gr.Radio(
                    choices=["rigorous", "learning"],
                    value="rigorous",
                    label="Mode",
                )
                lang = gr.Radio(
                    choices=["en", "ru"],
                    value="en",
                    label="Language",
                )
                model = gr.Textbox(
                    value="qwen2.5:7b",
                    label="Model",
                )
                provider = gr.Dropdown(
                    choices=list(_providers.SUPPORTED_PROVIDERS),
                    value="ollama",
                    label="Provider",
                )
                run_btn = gr.Button("Run")

        md_output = gr.Markdown(label="Report")
        json_output = gr.Code(language="json", label="JSON")

        def _on_click(paper_file, mode_val, lang_val, model_val, provider_val):
            path = paper_file.name if paper_file is not None else ""
            return process(path, mode_val, lang_val, model_val, provider_val)

        run_btn.click(
            fn=_on_click,
            inputs=[paper, mode, lang, model, provider],
            outputs=[md_output, json_output],
        )

    return app


def launch(share: bool = False, inbrowser: bool = True) -> None:
    """Build and launch the Gradio app."""
    app = build_app()
    app.launch(share=share, inbrowser=inbrowser)
