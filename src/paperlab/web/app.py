"""paperlab Gradio web dashboard."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from paperlab.ingest import extract_text
from paperlab.providers.factory import make_provider

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
    """Run review pipeline on a paper. Returns (markdown, json)."""
    from paperlab.orchestrator import review
    from paperlab.sessions import save_report, to_json, to_markdown

    if not paper_path:
        return ("", json.dumps({"error": "no paper uploaded"}))

    paper = _RUNTIME.extract_text(paper_path)
    provider = _RUNTIME.make_provider(provider_name)
    report = asyncio.run(review(paper, provider, mode, lang, model))
    save_report(report)
    return (to_markdown(report), to_json(report))


def _list_recent_sessions(limit: int = 25) -> list[list[str]]:
    """Return recent sessions as rows for gr.Dataframe."""
    from paperlab.sessions import list_sessions

    try:
        sessions = list_sessions()
    except Exception:
        return []
    rows = []
    for s in sessions[:limit]:
        rows.append([s.session_id, s.created_at, s.mode, s.lang, s.model, s.title or ""])
    return rows


_CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=EB+Garamond:wght@500;600;700&display=swap');

:root, .dark {
  --pl-bg:        #020617;
  --pl-surface:   #0F172A;
  --pl-surface-2: #1E293B;
  --pl-border:    #1F2A44;
  --pl-text:      #F8FAFC;
  --pl-muted:     #94A3B8;
  --pl-accent:    #22C55E;
  --pl-accent-2:  #16A34A;
  --pl-danger:    #EF4444;
  --pl-warn:      #F59E0B;
}

body, .gradio-container {
  background: var(--pl-bg) !important;
  color: var(--pl-text) !important;
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

.gradio-container { max-width: 1280px !important; margin: 0 auto !important; padding: 24px !important; }
footer { display: none !important; }

.pl-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; margin-bottom: 20px;
  background: linear-gradient(135deg, var(--pl-surface) 0%, var(--pl-surface-2) 100%);
  border: 1px solid var(--pl-border);
  border-radius: 14px;
}
.pl-header h1 {
  font-family: 'EB Garamond', 'Crimson Text', Georgia, serif !important;
  font-weight: 700; font-size: 28px; margin: 0 0 4px 0; letter-spacing: -0.01em;
}
.pl-header p { color: var(--pl-muted); margin: 0; font-size: 14px; }
.pl-badge {
  padding: 4px 10px; border-radius: 999px;
  background: rgba(34,197,94,0.12); color: var(--pl-accent);
  border: 1px solid rgba(34,197,94,0.35);
  font-size: 12px; font-weight: 600; letter-spacing: 0.02em;
}

.pl-panel, .block, .form {
  background: var(--pl-surface) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: 12px !important;
}
.pl-section-title { font-size: 12px; font-weight: 600; color: var(--pl-muted); text-transform: uppercase; letter-spacing: 0.08em; margin: 4px 0 10px 0; }

button.primary, .pl-run > button {
  background: var(--pl-accent) !important;
  color: #052e13 !important;
  border: none !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  cursor: pointer !important;
  transition: background 180ms ease, transform 120ms ease !important;
}
.pl-run > button:hover { background: var(--pl-accent-2) !important; }
.pl-run > button:active { transform: translateY(1px); }
.pl-run > button:disabled { background: var(--pl-surface-2) !important; color: var(--pl-muted) !important; cursor: not-allowed !important; }

input, textarea, .wrap.svelte-1cl284s input { background: var(--pl-surface-2) !important; color: var(--pl-text) !important; border-radius: 8px !important; }

.pl-agents { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 12px 0 4px 0; }
.pl-agent {
  padding: 10px 12px; border-radius: 10px;
  background: var(--pl-surface); border: 1px solid var(--pl-border);
  display: flex; align-items: center; gap: 10px;
}
.pl-dot { width: 8px; height: 8px; border-radius: 999px; background: var(--pl-muted); box-shadow: 0 0 0 3px rgba(148,163,184,0.15); }
.pl-agent.running .pl-dot { background: var(--pl-warn); box-shadow: 0 0 0 3px rgba(245,158,11,0.2); animation: pulse 1.4s ease-in-out infinite; }
.pl-agent.done    .pl-dot { background: var(--pl-accent); box-shadow: 0 0 0 3px rgba(34,197,94,0.2); }
.pl-agent.error   .pl-dot { background: var(--pl-danger); box-shadow: 0 0 0 3px rgba(239,68,68,0.2); }
.pl-agent-name { font-size: 13px; font-weight: 500; }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.55 } }

.pl-status { padding: 10px 12px; border-radius: 10px; background: var(--pl-surface-2); border: 1px solid var(--pl-border); font-size: 13px; color: var(--pl-muted); }
.pl-status.ok    { color: var(--pl-accent); border-color: rgba(34,197,94,0.35); background: rgba(34,197,94,0.06); }
.pl-status.error { color: var(--pl-danger); border-color: rgba(239,68,68,0.35); background: rgba(239,68,68,0.06); }

.prose, .markdown, .md { color: var(--pl-text) !important; font-family: 'Inter', system-ui, sans-serif !important; line-height: 1.65 !important; }
.prose h1, .md h1 { font-family: 'EB Garamond', Georgia, serif !important; font-size: 26px !important; margin-top: 0 !important; }
.prose h2, .md h2 { font-family: 'EB Garamond', Georgia, serif !important; font-size: 22px !important; color: var(--pl-text) !important; margin-top: 24px !important; border-bottom: 1px solid var(--pl-border); padding-bottom: 6px; }
.prose h3, .md h3 { font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 15px !important; color: var(--pl-muted) !important; margin-top: 18px !important; text-transform: uppercase; letter-spacing: 0.06em; }
.prose code, .md code, code, pre { font-family: 'JetBrains Mono', ui-monospace, monospace !important; background: var(--pl-surface-2) !important; border-radius: 6px; padding: 1px 6px; }
.prose blockquote, .md blockquote { border-left: 3px solid var(--pl-danger); color: var(--pl-danger); background: rgba(239,68,68,0.05); padding: 6px 12px; border-radius: 6px; }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
"""

_HEADER_HTML = """
<div class="pl-header">
  <div>
    <h1>paperlab</h1>
    <p>Multi-agent LLM review of biomedical research papers · rigorous · learning · en/ru</p>
  </div>
  <div class="pl-badge">v0.1</div>
</div>
"""


def _agents_html(states: dict[str, str]) -> str:
    order = [
        ("summarizer", "Summarizer"),
        ("methodologist", "Methodologist"),
        ("critic", "Critic"),
        ("contextualizer", "Contextualizer"),
    ]
    cards = []
    for key, label in order:
        state = states.get(key, "idle")
        cards.append(
            f'<div class="pl-agent {state}"><span class="pl-dot"></span>'
            f'<span class="pl-agent-name">{label}</span></div>'
        )
    return f'<div class="pl-agents">{"".join(cards)}</div>'


def _status_html(text: str, kind: str = "info") -> str:
    return f'<div class="pl-status {kind}">{text}</div>'


def build_app():
    """Build and return the Gradio Blocks application (lazy gradio import)."""
    import gradio as gr

    import paperlab.providers as _providers

    theme = gr.themes.Base(
        primary_hue="green",
        secondary_hue="slate",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
    )

    with gr.Blocks(
        theme=theme,
        css=_CUSTOM_CSS,
        title="paperlab",
        analytics_enabled=False,
    ) as app:
        gr.HTML(_HEADER_HTML)

        with gr.Row(equal_height=False):
            with gr.Column(scale=4, min_width=340):
                gr.HTML('<div class="pl-section-title">Paper</div>')
                paper = gr.File(
                    label="",
                    file_types=[".pdf"],
                    file_count="single",
                    show_label=False,
                )
                gr.HTML(
                    '<div class="pl-section-title" style="margin-top:14px;">Review settings</div>'
                )
                with gr.Row():
                    mode = gr.Radio(
                        choices=["rigorous", "learning"],
                        value="rigorous",
                        label="Mode",
                        info="rigorous — peer-review tone · learning — friendly",
                    )
                with gr.Row():
                    lang = gr.Radio(
                        choices=["en", "ru"],
                        value="en",
                        label="Output language",
                    )
                gr.HTML('<div class="pl-section-title" style="margin-top:14px;">Backend</div>')
                provider = gr.Dropdown(
                    choices=list(_providers.SUPPORTED_PROVIDERS),
                    value="ollama",
                    label="Provider",
                    info="ollama runs locally · cloud providers use LiteLLM",
                )
                model = gr.Textbox(
                    value="qwen2.5:7b",
                    label="Model",
                    placeholder="qwen2.5:7b, openrouter/…, gpt-4o, …",
                )
                run_btn = gr.Button("Run review", elem_classes=["pl-run"], variant="primary")

            with gr.Column(scale=7):
                agents_state = gr.HTML(_agents_html({}))
                status = gr.HTML(_status_html("Idle. Upload a PDF and press Run review.", "info"))

                with gr.Tabs():
                    with gr.TabItem("Report"):
                        md_output = gr.Markdown(
                            value="",
                            show_label=False,
                            elem_classes=["md"],
                        )
                    with gr.TabItem("JSON"):
                        json_output = gr.Code(language="json", label="", lines=24)
                    with gr.TabItem("Sessions"):
                        gr.HTML('<div class="pl-section-title">Recent sessions</div>')
                        sessions_df = gr.Dataframe(
                            headers=["session_id", "created_at", "mode", "lang", "model", "title"],
                            value=_list_recent_sessions(),
                            interactive=False,
                            wrap=True,
                            row_count=(0, "dynamic"),
                        )
                        refresh_btn = gr.Button("Refresh", variant="secondary")

        def _on_click(
            paper_file, mode_val, lang_val, model_val, provider_val, progress=gr.Progress()
        ):
            if paper_file is None:
                yield (
                    "",
                    json.dumps({"error": "no paper uploaded"}, indent=2),
                    _agents_html({}),
                    _status_html("No PDF uploaded. Choose a file above.", "error"),
                    _list_recent_sessions(),
                )
                return

            path = paper_file.name
            progress(0, desc="ingest")
            yield (
                "",
                "",
                _agents_html(
                    {
                        k: "running"
                        for k in ["summarizer", "methodologist", "critic", "contextualizer"]
                    }
                ),
                _status_html(
                    "Extracting PDF text and dispatching four agents in parallel…", "info"
                ),
                gr.update(),
            )

            md, js = process(path, mode_val, lang_val, model_val, provider_val)

            try:
                parsed = json.loads(js)
            except Exception:
                parsed = {}
            agent_states = {}
            for name, rep in (parsed.get("agents") or {}).items():
                agent_states[name] = "error" if rep.get("error") else "done"

            ok = agent_states and all(v == "done" for v in agent_states.values())
            session_id = parsed.get("session_id", "?")
            if ok:
                msg = f"Done. Session <code>{session_id}</code> saved to ~/.paperlab/sessions/."
                kind = "ok"
            elif agent_states:
                failed = [k for k, v in agent_states.items() if v == "error"]
                msg = f"Finished with issues in: {', '.join(failed)}. Session <code>{session_id}</code>."
                kind = "error"
            else:
                msg = "Finished, but response could not be parsed."
                kind = "error"

            yield (
                md,
                js,
                _agents_html(agent_states),
                _status_html(msg, kind),
                _list_recent_sessions(),
            )

        run_btn.click(
            fn=_on_click,
            inputs=[paper, mode, lang, model, provider],
            outputs=[md_output, json_output, agents_state, status, sessions_df],
        )
        refresh_btn.click(fn=lambda: _list_recent_sessions(), inputs=None, outputs=sessions_df)

    return app


def launch(share: bool = False, inbrowser: bool = True) -> None:
    """Build and launch the Gradio app."""
    app = build_app()
    app.launch(share=share, inbrowser=inbrowser)
