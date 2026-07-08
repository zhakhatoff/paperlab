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


def _sessions_html(limit: int = 25) -> str:
    """Render sessions as an HTML table, or an empty-state message."""
    rows = _list_recent_sessions(limit)
    if not rows:
        return '<p class="pl-empty-msg">No sessions yet. Completed reviews are saved automatically.</p>'
    headers = ["session_id", "created_at", "mode", "lang", "model", "title"]
    th = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cls = ' class="pl-mono"' if i == 0 else ""
            cells.append(f"<td{cls}>{cell}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        '<div class="pl-sessions-wrap"><table class="pl-sessions-table">'
        f"<thead><tr>{th}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Instrument+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ── Design tokens ─────────────────────────────────────────────────────── */
:root {
  --pl-paper:      #FBFAFD;
  --pl-surface:    #FFFFFF;
  --pl-surface-2:  #F4F2FA;
  --pl-border:     #E4E0F0;
  --pl-border-2:   #CFC9E4;
  --pl-ink:        #1A1523;
  --pl-muted:      #6E6787;
  --pl-hema:       #4A3AA3;
  --pl-hema-dark:  #3B2E85;
  --pl-hema-soft:  #EDEAFB;
  --pl-eosin:      #D2497A;
  --pl-eosin-soft: #FBEAF1;
  --pl-teal:       #0F766E;
  --pl-teal-soft:  #E4F3F1;
  --pl-amber:      #B45309;
  --pl-amber-soft: #FBEFE0;
  --pl-radius:     12px;
  --pl-radius-sm:  8px;
  --pl-shadow:     0 1px 2px rgba(26,21,35,0.05), 0 4px 16px rgba(74,58,163,0.06);
}

/* Force light theme — override Gradio's .dark class */
.dark, html.dark, body.dark {
  --pl-paper:      #FBFAFD !important;
  --pl-surface:    #FFFFFF !important;
  --pl-surface-2:  #F4F2FA !important;
  --pl-border:     #E4E0F0 !important;
  --pl-border-2:   #CFC9E4 !important;
  --pl-ink:        #1A1523 !important;
  --pl-muted:      #6E6787 !important;
}
.dark body, .dark .gradio-container {
  background: var(--pl-paper) !important;
  color: var(--pl-ink) !important;
}

/* ── Base ───────────────────────────────────────────────────────────────── */
body, .gradio-container {
  background: var(--pl-paper) !important;
  color: var(--pl-ink) !important;
  font-family: 'Instrument Sans', system-ui, -apple-system, sans-serif !important;
  font-size: 15px;
  line-height: 1.6;
}
.gradio-container {
  max-width: 1240px !important;
  margin: 0 auto !important;
  padding: 28px 24px !important;
}
@media (max-width: 640px) {
  .gradio-container { padding: 12px !important; }
}
/* Stack the two main columns on narrow viewports.
   NB: gradio auto-prefixes selectors with the container class, so selectors
   here must NOT mention .gradio-container themselves. */
@media (max-width: 768px) {
  .row { flex-direction: column !important; }
  .row > .column {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 0 !important;
  }
}
footer { display: none !important; }

/* ── Header ─────────────────────────────────────────────────────────────── */
.pl-header {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px 24px 28px;
  margin-bottom: 24px;
  background: var(--pl-surface);
  border: 1px solid var(--pl-border);
  border-radius: var(--pl-radius);
  box-shadow: var(--pl-shadow);
  position: relative;
  overflow: hidden;
}
.pl-header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #4A3AA3 0%, #7A5AC8 35%, #D2497A 100%);
}
.pl-header h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 700;
  font-size: 30px;
  margin: 0 0 3px 0;
  letter-spacing: -0.02em;
  color: var(--pl-ink);
}
.pl-header-sub {
  font-size: 14px;
  color: var(--pl-muted);
  margin: 0;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-badge {
  padding: 5px 14px;
  border-radius: 999px;
  background: var(--pl-hema-soft);
  color: var(--pl-hema);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  white-space: nowrap;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}

/* ── Panels / cards ─────────────────────────────────────────────────────── */
.block, .form, .gap {
  background: var(--pl-surface) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: var(--pl-radius) !important;
  box-shadow: var(--pl-shadow) !important;
  min-width: 0 !important;
  max-width: 100% !important;
}
/* Flat HTML blocks: eyebrows, hints, header wrapper — no card chrome */
.pl-flat, .pl-flat.block {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
/* Prevent horizontal overflow on narrow viewports */
.gradio-container { overflow-x: hidden; }
.row, .column { min-width: 0 !important; }

/* ── Eyebrow section titles ─────────────────────────────────────────────── */
.pl-eyebrow {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--pl-hema);
  margin: 0 0 10px 0;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-eyebrow-gap { margin-top: 18px; }

/* ── File upload zone ───────────────────────────────────────────────────── */
.pl-file input[type="file"],
.pl-file .wrap,
.pl-file .file-preview,
[data-testid="file"] {
  border: 1.5px dashed var(--pl-border-2) !important;
  background: var(--pl-surface-2) !important;
  border-radius: var(--pl-radius) !important;
  color: var(--pl-muted) !important;
  transition: border-color 160ms ease;
}
.pl-file:hover input[type="file"],
.pl-file:hover .wrap,
.pl-file:hover [data-testid="file"] {
  border-color: var(--pl-hema) !important;
}
/* Drop zone spans the full card width */
.pl-file,
.pl-file > div,
.pl-file .wrap,
.pl-file .file-preview,
.pl-file [data-testid="file"],
.pl-file [data-testid="file-upload"],
.pl-file .upload-container,
.pl-file button {
  width: 100% !important;
  max-width: 100% !important;
}

/* ── Field labels: flat, not pill chips ─────────────────────────────────── */
span[data-testid="block-info"],
.block-label,
.block-title,
label > span,
.container > label > span {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-bottom: 4px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--pl-ink) !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
}

/* ── Inputs / radio / dropdown ──────────────────────────────────────────── */
input, textarea, select,
.wrap input, .wrap select,
.svelte-1cl284s input {
  background: var(--pl-surface-2) !important;
  color: var(--pl-ink) !important;
  border-color: var(--pl-border) !important;
  border-radius: var(--pl-radius-sm) !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
}
input:focus, textarea:focus, select:focus {
  outline: 2px solid var(--pl-hema) !important;
  outline-offset: 2px !important;
  border-color: var(--pl-hema) !important;
}

/* ── Run button ─────────────────────────────────────────────────────────── */
.pl-run > button,
button.primary {
  background: var(--pl-hema) !important;
  color: #FFFFFF !important;
  border: none !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  border-radius: 10px !important;
  width: 100% !important;
  cursor: pointer !important;
  transition: background 180ms ease, transform 120ms ease !important;
}
.pl-run > button:hover { background: var(--pl-hema-dark) !important; }
.pl-run > button:active { transform: translateY(1px) !important; }
.pl-run > button:disabled {
  background: var(--pl-surface-2) !important;
  color: var(--pl-muted) !important;
  cursor: not-allowed !important;
}
.pl-run > button:focus-visible {
  outline: 2px solid var(--pl-hema) !important;
  outline-offset: 2px !important;
}
.pl-run-hint {
  font-size: 12px;
  color: var(--pl-muted);
  margin: 8px 0 0 0;
  text-align: center;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}

/* ── Refresh button (secondary) ─────────────────────────────────────────── */
.pl-refresh > button,
button.secondary {
  background: var(--pl-surface) !important;
  color: var(--pl-ink) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: var(--pl-radius-sm) !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: border-color 160ms ease, color 160ms ease !important;
}
.pl-refresh > button:hover {
  border-color: var(--pl-hema) !important;
  color: var(--pl-hema) !important;
}
.pl-refresh > button:focus-visible {
  outline: 2px solid var(--pl-hema) !important;
  outline-offset: 2px !important;
}

/* ── Agent cards ─────────────────────────────────────────────────────────── */
.pl-agents {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 4px 0 12px 0;
}
@media (max-width: 900px) {
  .pl-agents { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.pl-agent {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: var(--pl-surface);
  border: 1px solid var(--pl-border);
  border-radius: 10px;
  box-shadow: var(--pl-shadow);
}
/* Per-agent stain colours */
.pl-agent--summarizer     { --agent-color: #4A3AA3; --agent-glow: rgba(74,58,163,0.18);  border-left: 3px solid #4A3AA3; }
.pl-agent--methodologist  { --agent-color: #0E7490; --agent-glow: rgba(14,116,144,0.18); border-left: 3px solid #0E7490; }
.pl-agent--critic         { --agent-color: #D2497A; --agent-glow: rgba(210,73,122,0.18); border-left: 3px solid #D2497A; }
.pl-agent--contextualizer { --agent-color: #B45309; --agent-glow: rgba(180,83,9,0.18);  border-left: 3px solid #B45309; }

.pl-dot {
  flex-shrink: 0;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #C9C4DA;
  margin-top: 3px;
}
.pl-agent.running .pl-dot {
  background: var(--agent-color);
  box-shadow: 0 0 0 4px var(--agent-glow);
  animation: pl-pulse 1.3s ease-in-out infinite;
}
.pl-agent.done .pl-dot {
  background: #0F766E;
  box-shadow: 0 0 0 4px rgba(15,118,110,0.18);
}
.pl-agent.error .pl-dot {
  background: #D2497A;
  box-shadow: 0 0 0 4px rgba(210,73,122,0.18);
}
@keyframes pl-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.45; }
}
.pl-agent-info { display: flex; flex-direction: column; gap: 2px; }
.pl-agent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--pl-ink);
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-agent-role {
  font-size: 11px;
  color: var(--pl-muted);
  font-family: 'Instrument Sans', system-ui, sans-serif;
}

/* ── Status bar ─────────────────────────────────────────────────────────── */
.pl-status {
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--pl-surface-2);
  border: 1px solid var(--pl-border);
  font-size: 13px;
  color: var(--pl-muted);
  margin-bottom: 4px;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-status.ok {
  background: var(--pl-teal-soft);
  color: var(--pl-teal);
  border-color: rgba(15,118,110,0.3);
}
.pl-status.error {
  background: var(--pl-eosin-soft);
  color: var(--pl-eosin);
  border-color: rgba(210,73,122,0.3);
}
.pl-status code {
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  font-size: 12px;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.tabs > .tab-nav button,
[role="tab"] {
  color: var(--pl-muted) !important;
  border-bottom: 2px solid transparent !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  background: transparent !important;
  transition: color 160ms ease, border-color 160ms ease !important;
}
.tabs > .tab-nav button:hover,
[role="tab"]:hover {
  color: var(--pl-ink) !important;
}
.tabs > .tab-nav button.selected,
[role="tab"][aria-selected="true"] {
  color: var(--pl-hema) !important;
  border-bottom-color: var(--pl-hema) !important;
}
.tabs > .tab-nav button:focus-visible,
[role="tab"]:focus-visible {
  outline: 2px solid var(--pl-hema) !important;
  outline-offset: 2px !important;
}

/* ── Report markdown ─────────────────────────────────────────────────────── */
.prose, .markdown, .md {
  color: var(--pl-ink) !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  line-height: 1.6 !important;
  font-size: 15px !important;
}
.prose h1, .md h1, .markdown h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 600 !important;
  font-size: 24px !important;
  color: var(--pl-ink) !important;
  margin-top: 0 !important;
  letter-spacing: -0.01em;
}
.prose h2, .md h2, .markdown h2 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 600 !important;
  font-size: 20px !important;
  color: var(--pl-ink) !important;
  border-bottom: 1px solid var(--pl-border) !important;
  padding-bottom: 6px !important;
  margin-top: 28px !important;
}
.prose h3, .md h3, .markdown h3 {
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  color: var(--pl-hema) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  margin-top: 18px !important;
}
.prose li, .md li, .markdown li { line-height: 1.65 !important; }
.prose li::marker, .md li::marker, .markdown li::marker { color: var(--pl-hema) !important; }
.prose code, .md code, .markdown code,
.prose pre, .md pre, .markdown pre,
code, pre {
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  background: var(--pl-surface-2) !important;
  color: var(--pl-ink) !important;
  border-radius: 6px !important;
  font-size: 13px !important;
}
code { padding: 1px 5px !important; }
pre  { padding: 12px 16px !important; overflow-x: auto; }
.prose blockquote, .md blockquote, .markdown blockquote {
  border-left: 3px solid var(--pl-eosin) !important;
  background: var(--pl-eosin-soft) !important;
  color: #9C2F5A !important;
  border-radius: 6px !important;
  padding: 8px 12px !important;
  margin-left: 0 !important;
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.pl-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: var(--pl-muted);
  font-size: 14px;
  gap: 12px;
  font-family: 'Instrument Sans', system-ui, sans-serif;
  text-align: center;
}
.pl-empty svg { opacity: 0.45; }
.pl-empty-msg {
  color: var(--pl-muted);
  font-size: 13px;
  padding: 20px 0;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}

/* ── Sessions table ──────────────────────────────────────────────────────── */
.pl-sessions-wrap { overflow-x: auto; }
.pl-sessions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-sessions-table thead th {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--pl-muted);
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--pl-border);
}
.pl-sessions-table tbody td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--pl-border);
  color: var(--pl-ink);
  vertical-align: top;
}
.pl-sessions-table tbody tr:hover td { background: var(--pl-surface-2); }
.pl-mono {
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  font-size: 12px;
}

/* ── Reduced motion ──────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
"""

# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

_HEADER_HTML = """
<div class="pl-header">
  <div>
    <h1>paperlab</h1>
    <p class="pl-header-sub">Peer-review bench for biomedical papers</p>
  </div>
  <div class="pl-badge">H&amp;E &middot; four-agent review</div>
</div>
"""

_EMPTY_REPORT_HTML = """
<div class="pl-empty">
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="1.5"
       stroke-linecap="round" stroke-linejoin="round"
       xmlns="http://www.w3.org/2000/svg">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
  <span>No report yet. Upload a PDF and run the review.</span>
</div>
"""

_AGENT_ROLES: dict[str, str] = {
    "summarizer": "claims &amp; findings",
    "methodologist": "design &amp; checklists",
    "critic": "stats &amp; bias",
    "contextualizer": "field &amp; novelty",
}

_AGENT_LABELS: dict[str, str] = {
    "summarizer": "Summarizer",
    "methodologist": "Methodologist",
    "critic": "Critic",
    "contextualizer": "Contextualizer",
}

_AGENT_ORDER = ["summarizer", "methodologist", "critic", "contextualizer"]


def _agents_html(states: dict[str, str]) -> str:
    cards = []
    for key in _AGENT_ORDER:
        state = states.get(key, "idle")
        label = _AGENT_LABELS[key]
        role = _AGENT_ROLES[key]
        cards.append(
            f'<div class="pl-agent pl-agent--{key} {state}">'
            f'<span class="pl-dot"></span>'
            f'<div class="pl-agent-info">'
            f'<span class="pl-agent-name">{label}</span>'
            f'<span class="pl-agent-role">{role}</span>'
            f"</div></div>"
        )
    return f'<div class="pl-agents">{"".join(cards)}</div>'


def _status_html(text: str, kind: str = "info") -> str:
    css_class = f"pl-status {kind}".strip()
    return f'<div class="{css_class}">{text}</div>'


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


def build_app():
    """Build and return the Gradio Blocks application (lazy gradio import)."""
    import gradio as gr

    import paperlab.providers as _providers

    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.violet,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Instrument Sans"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace", "monospace"],
    )

    with gr.Blocks(
        theme=theme,
        css=_CUSTOM_CSS,
        title="paperlab — peer-review bench",
        analytics_enabled=False,
        js="() => { document.documentElement.classList.remove('dark'); document.body.classList.remove('dark'); }",
    ) as app:
        gr.HTML(_HEADER_HTML, elem_classes=["pl-flat"])

        with gr.Row(equal_height=False):
            # ── Left column: settings ────────────────────────────────────
            with gr.Column(scale=4, min_width=0):
                gr.HTML('<p class="pl-eyebrow">Specimen</p>', elem_classes=["pl-flat"])
                paper = gr.File(
                    label="",
                    file_types=[".pdf"],
                    file_count="single",
                    show_label=False,
                    elem_classes=["pl-file"],
                )
                gr.HTML(
                    '<p class="pl-eyebrow pl-eyebrow-gap">Protocol</p>',
                    elem_classes=["pl-flat"],
                )
                mode = gr.Radio(
                    choices=["rigorous", "learning"],
                    value="rigorous",
                    label="Mode",
                    info="rigorous — peer-review tone · learning — friendly",
                )
                lang = gr.Radio(
                    choices=["en", "ru"],
                    value="en",
                    label="Output language",
                )
                gr.HTML(
                    '<p class="pl-eyebrow pl-eyebrow-gap">Instrument</p>',
                    elem_classes=["pl-flat"],
                )
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
                run_btn = gr.Button(
                    "Run review",
                    elem_classes=["pl-run"],
                    variant="primary",
                )
                gr.HTML(
                    '<p class="pl-run-hint">Four agents read in parallel.'
                    " Nothing leaves your machine on ollama.</p>",
                    elem_classes=["pl-flat"],
                )

            # ── Right column: results ────────────────────────────────────
            with gr.Column(scale=7, min_width=0):
                agents_state = gr.HTML(_agents_html({}), elem_classes=["pl-flat"])
                status = gr.HTML(
                    _status_html("Idle. Upload a PDF and press Run review.", "info"),
                    elem_classes=["pl-flat"],
                )

                with gr.Tabs():
                    with gr.TabItem("Report"):
                        md_output = gr.Markdown(
                            value=_EMPTY_REPORT_HTML,
                            show_label=False,
                            elem_classes=["md"],
                        )
                    with gr.TabItem("JSON"):
                        json_output = gr.Code(language="json", label="", lines=24)
                    with gr.TabItem("Sessions"):
                        gr.HTML(
                            '<p class="pl-eyebrow" style="margin-bottom:12px;">Recent sessions</p>',
                            elem_classes=["pl-flat"],
                        )
                        sessions_display = gr.HTML(_sessions_html(), elem_classes=["pl-flat"])
                        refresh_btn = gr.Button(
                            "Refresh",
                            elem_classes=["pl-refresh"],
                            variant="secondary",
                        )

        # ── Event handlers ───────────────────────────────────────────────
        def _on_click(
            paper_file, mode_val, lang_val, model_val, provider_val, progress=gr.Progress()
        ):
            if paper_file is None:
                yield (
                    _EMPTY_REPORT_HTML,
                    json.dumps({"error": "no paper uploaded"}, indent=2),
                    _agents_html({}),
                    _status_html("No PDF uploaded. Choose a file above.", "error"),
                    _sessions_html(),
                    gr.update(),
                )
                return

            path = paper_file.name
            progress(0, desc="ingest")
            yield (
                _EMPTY_REPORT_HTML,
                "",
                _agents_html({k: "running" for k in _AGENT_ORDER}),
                _status_html(
                    "Extracting PDF text and dispatching four agents in parallel…", "info"
                ),
                gr.update(),
                gr.update(interactive=False),
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
                md or _EMPTY_REPORT_HTML,
                js,
                _agents_html(agent_states),
                _status_html(msg, kind),
                _sessions_html(),
                gr.update(interactive=True),
            )

        run_btn.click(
            fn=_on_click,
            inputs=[paper, mode, lang, model, provider],
            outputs=[md_output, json_output, agents_state, status, sessions_display, run_btn],
        )
        refresh_btn.click(fn=lambda: _sessions_html(), inputs=None, outputs=sessions_display)

    return app


def launch(share: bool = False, inbrowser: bool = True) -> None:
    """Build and launch the Gradio app."""
    app = build_app()
    app.launch(share=share, inbrowser=inbrowser)
