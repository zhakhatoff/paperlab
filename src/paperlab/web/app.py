"""paperlab Gradio web dashboard."""

from __future__ import annotations

import asyncio
import json
from html import escape
from types import SimpleNamespace

from paperlab.ingest import extract_text
from paperlab.providers import discovery, keys
from paperlab.providers.factory import make_provider

_RUNTIME = SimpleNamespace(
    extract_text=extract_text,
    make_provider=make_provider,
)

CLOUD_PROVIDERS: tuple = (
    "openrouter",
    "together",
    "groq",
    "gemini",
    "anthropic",
    "openai",
    "custom",
)

_MODEL_DEFAULTS: dict[str, str] = {
    "ollama": "qwen2.5:7b",
    "anthropic": "claude-sonnet-4-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}

_KEY_SAVED_NOTE = "Key saved &mdash; stored in <code>~/.paperlab/keys.toml</code>"


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
            cells.append(f"<td{cls}>{escape(str(cell))}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        '<div class="pl-sessions-wrap"><table class="pl-sessions-table">'
        f"<thead><tr>{th}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )


# ---------------------------------------------------------------------------
# Provider setup panel — pure helpers (tested in tests/web/test_provider_panel.py)
# ---------------------------------------------------------------------------


def _model_default(provider: str, models: list) -> str:
    """Pick a sensible default model for a provider."""
    preset = _MODEL_DEFAULTS.get(provider)
    if preset:
        return preset
    fallback = discovery.STATIC_FALLBACK_MODELS.get(provider, [])
    if fallback:
        return fallback[0]
    if models:
        first = models[0]
        return first[1] if isinstance(first, tuple) else first
    return ""


def _key_mask(provider: str) -> str:
    return keys.list_keys().get(provider, "")


def _ollama_runtime_html(status: dict, ram_gb: float) -> str:
    """Render the Local runtime card for the given ollama status."""
    ram_line = f'<div class="pl-runtime-ram">Your machine: {ram_gb:g} GB RAM</div>'
    if not status.get("installed"):
        return (
            '<div class="pl-runtime warn">'
            '<div class="pl-runtime-title">Ollama is not installed.</div>'
            '<code class="pl-cmd">brew install ollama</code>'
            '<div class="pl-runtime-ram">or download from '
            '<a href="https://ollama.com/download" target="_blank" rel="noopener">'
            "ollama.com/download</a></div>"
            f"{ram_line}</div>"
        )
    if not status.get("running"):
        return (
            '<div class="pl-runtime warn">'
            '<div class="pl-runtime-title">Ollama is installed but not running.</div>'
            '<code class="pl-cmd">ollama serve</code>'
            f"{ram_line}</div>"
        )
    n = len(status.get("models", []))
    noun = "model" if n == 1 else "models"
    return (
        '<div class="pl-runtime ok">'
        f'<div class="pl-runtime-title">Ollama is running &middot; {n} {noun} installed</div>'
        f"{ram_line}</div>"
    )


def _ollama_model_choices(status: dict, ram_gb: float) -> list[tuple[str, str]]:
    """Installed models first (with size), then recommended-for-RAM pulls."""
    installed = {m["name"] for m in status.get("models", [])}
    choices: list[tuple[str, str]] = [
        (f"{m['name']} · {m['size_gb']} GB", m["name"]) for m in status.get("models", [])
    ]
    for rec in discovery.recommend_ollama_models(ram_gb):
        name = rec["name"]
        if name not in installed:
            choices.append((f"{name} — not installed · ollama pull {name}", name))
    return choices


def provider_panel_state(provider: str) -> dict:
    """Compute the full Instrument-panel state for a provider.

    Returns a dict with keys: is_cloud, key_saved, key_hint, models,
    model_default, ollama_html, error.
    """
    if provider == "ollama":
        status = discovery.ollama_status()
        ram_gb = discovery.system_ram_gb()
        choices = _ollama_model_choices(status, ram_gb)
        installed = [m["name"] for m in status.get("models", [])]
        prefers_qwen = "qwen2.5:7b" in installed or not installed
        default = "qwen2.5:7b" if prefers_qwen else installed[0]
        return {
            "is_cloud": False,
            "key_saved": False,
            "key_hint": "",
            "models": choices,
            "model_default": default,
            "ollama_html": _ollama_runtime_html(status, ram_gb),
            "error": None,
        }

    key = keys.get_key(provider)
    key_saved = bool(key)
    key_hint = ""
    if key_saved:
        mask = _key_mask(provider) or (key[:4] + "..." if key else "")
        key_hint = f"{escape(mask)} &middot; {_KEY_SAVED_NOTE}"

    if provider == "openrouter" or key_saved:
        models, error = discovery.list_models_safe(provider, api_key=key)
    else:
        models, error = list(discovery.STATIC_FALLBACK_MODELS.get(provider, [])), None

    return {
        "is_cloud": True,
        "key_saved": key_saved,
        "key_hint": key_hint,
        "models": models,
        "model_default": _model_default(provider, models),
        "ollama_html": None,
        "error": error,
    }


def save_key_action(provider: str, key: str) -> tuple[str, list, str]:
    """Save an API key, then load models. Returns (status_html, models, default)."""
    key = (key or "").strip()
    if not key:
        return (_status_html("Enter an API key before saving.", "error"), [], "")
    keys.save_key(provider, key)
    models, err = discovery.list_models_safe(provider, api_key=key)
    default = _model_default(provider, models)
    if err:
        msg = f"{_KEY_SAVED_NOTE}. Model discovery failed ({escape(str(err))}); showing fallback list."
        return (_status_html(msg, "error"), models, default)
    msg = f"{_KEY_SAVED_NOTE}. Loaded {len(models)} models."
    return (_status_html(msg, "ok"), models, default)


def load_models_action(provider: str) -> tuple[str, list, str]:
    """Refresh the model list for a provider. Returns (status_html, models, default)."""
    if provider == "ollama":
        state = provider_panel_state(provider)
        n = len(state["models"])
        return (
            _status_html(f"Found {n} local model option(s).", "ok"),
            state["models"],
            state["model_default"],
        )
    models, err = discovery.list_models_safe(provider, api_key=keys.get_key(provider))
    default = _model_default(provider, models)
    if err:
        return (
            _status_html(
                f"Could not load models ({escape(str(err))}); showing fallback list.",
                "error",
            ),
            models,
            default,
        )
    return (_status_html(f"Loaded {len(models)} models.", "ok"), models, default)


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

/* ── File upload zone ───────────────────────────────────────────────────────
   Gradio 6: the .pl-file block itself carries inline border-style
   (dashed when empty, solid when a file is selected). Set only
   border-width/-color so the inline dashed/solid switch keeps working. */
.pl-file, .pl-file.block {
  width: 100% !important;
  max-width: 100% !important;
  border-width: 1.5px !important;
  border-color: var(--pl-border-2) !important;
  background: var(--pl-surface-2) !important;
  border-radius: var(--pl-radius) !important;
  box-shadow: none !important;
  color: var(--pl-muted) !important;
  transition: border-color 160ms ease;
}
.pl-file:hover { border-color: var(--pl-hema) !important; }
/* .block's `border: solid !important` beats Gradio's inline dashed/solid
   switch, so re-derive the style from the presence of a file preview. */
.pl-file:not(:has(.file-preview-holder)) { border-style: dashed !important; }
.pl-file:has(.file-preview-holder) { border-style: solid !important; }
/* Empty state: drop-zone button fills the card */
.pl-file button[aria-label="Click to upload or drop files"] {
  width: 100% !important;
  background: transparent !important;
  color: var(--pl-muted) !important;
}
/* Filled state: compact file row card */
.pl-file .file-preview-holder {
  min-height: 56px !important;
  padding: 12px 14px !important;
  overflow: hidden;
  display: flex;
  align-items: center;
}
.pl-file table.file-preview {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  border: none !important;
  background: transparent !important;
}
.pl-file .file-preview td {
  padding: 2px 4px !important;
  border: none !important;
  font-size: 13px !important;
  font-family: 'Instrument Sans', system-ui, sans-serif !important;
  color: var(--pl-ink) !important;
  vertical-align: middle !important;
}
.pl-file .file-preview td.filename {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  font-weight: 500;
}
.pl-file .file-preview td.download {
  width: 90px !important;
  text-align: right !important;
  white-space: nowrap !important;
}
.pl-file .file-preview td.download a {
  color: var(--pl-muted) !important;
  font-size: 12px !important;
  text-decoration: none !important;
}
.pl-file .file-preview td.download a:hover { color: var(--pl-hema) !important; }
/* Clear (×) button in the top-right panel */
.pl-file .icon-button-wrapper {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.pl-file .icon-button-wrapper .icon-button {
  color: var(--pl-muted) !important;
  border-radius: 6px !important;
}
.pl-file .icon-button-wrapper .icon-button:hover { color: var(--pl-eosin) !important; }

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

/* ── Provider setup panel (API key / Local runtime) ─────────────────────── */
.pl-setup, .pl-setup.block {
  background: var(--pl-surface-2) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  padding: 12px 14px !important;
  margin-top: 8px !important;
}
.pl-setup .block, .pl-setup .form, .pl-setup .gap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.pl-setup input {
  background: var(--pl-surface) !important;
}
.pl-key-hint {
  font-size: 12px !important;
  color: var(--pl-muted) !important;
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-key-hint code {
  font-size: 11px !important;
}
.pl-runtime {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: var(--pl-ink);
  font-family: 'Instrument Sans', system-ui, sans-serif;
}
.pl-runtime-title { font-weight: 600; font-size: 13px; }
.pl-runtime.ok .pl-runtime-title { color: var(--pl-teal); }
.pl-runtime.warn .pl-runtime-title { color: var(--pl-amber); }
.pl-runtime-ram { font-size: 12px; color: var(--pl-muted); }
.pl-runtime a { color: var(--pl-hema); }
.pl-cmd {
  display: block;
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  font-size: 12px !important;
  background: var(--pl-surface) !important;
  border: 1px solid var(--pl-border) !important;
  border-radius: 6px !important;
  padding: 6px 10px !important;
  color: var(--pl-ink) !important;
  width: fit-content;
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
                try:
                    _init = provider_panel_state("ollama")
                except Exception:
                    _init = {
                        "is_cloud": False,
                        "key_saved": False,
                        "key_hint": "",
                        "models": [],
                        "model_default": "qwen2.5:7b",
                        "ollama_html": "",
                        "error": None,
                    }

                provider = gr.Dropdown(
                    choices=[p for p in _providers.SUPPORTED_PROVIDERS if p != "fake"],
                    value="ollama",
                    label="Provider",
                    info="ollama runs locally · cloud providers use LiteLLM",
                )
                with gr.Column(visible=False, elem_classes=["pl-setup"]) as key_group:
                    key_hint_html = gr.HTML("", elem_classes=["pl-flat", "pl-key-hint"])
                    api_key_box = gr.Textbox(
                        type="password",
                        label="API key",
                        placeholder="sk-...",
                    )
                    save_key_btn = gr.Button(
                        "Save key",
                        variant="secondary",
                        elem_classes=["pl-refresh"],
                    )
                with gr.Column(visible=True, elem_classes=["pl-setup"]) as ollama_group:
                    ollama_runtime_html = gr.HTML(
                        _init["ollama_html"] or "",
                        elem_classes=["pl-flat"],
                    )
                    ollama_refresh_btn = gr.Button(
                        "Refresh",
                        variant="secondary",
                        elem_classes=["pl-refresh"],
                    )
                model = gr.Dropdown(
                    choices=_init["models"] or [_init["model_default"]],
                    value=_init["model_default"],
                    allow_custom_value=True,
                    label="Model",
                )
                load_models_btn = gr.Button(
                    "Load models",
                    variant="secondary",
                    elem_classes=["pl-refresh"],
                )
                panel_status = gr.HTML("", elem_classes=["pl-flat"])
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

            # Preflight: cloud providers require a saved key or env var.
            if provider_val not in {"ollama", "fake"} and keys.get_key(provider_val) is None:
                yield (
                    _EMPTY_REPORT_HTML,
                    "",
                    _agents_html({}),
                    _status_html(
                        f"Save an API key for {escape(str(provider_val))} before running.",
                        "error",
                    ),
                    _sessions_html(),
                    gr.update(interactive=True),
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

            try:
                md, js = process(path, mode_val, lang_val, model_val, provider_val)
            except Exception as exc:
                yield (
                    _EMPTY_REPORT_HTML,
                    "",
                    _agents_html({k: "error" for k in _AGENT_ORDER}),
                    _status_html(f"Review failed: {escape(str(exc))}", "error"),
                    _sessions_html(),
                    gr.update(interactive=True),
                )
                return

            try:
                parsed = json.loads(js)
            except Exception:
                parsed = {}
            agent_states = {}
            for name, rep in (parsed.get("agents") or {}).items():
                agent_states[name] = "error" if rep.get("error") else "done"

            ok = agent_states and all(v == "done" for v in agent_states.values())
            session_id = escape(str(parsed.get("session_id", "?")))
            if ok:
                msg = f"Done. Session <code>{session_id}</code> saved to ~/.paperlab/sessions/."
                kind = "ok"
            elif agent_states:
                failed = [escape(k) for k, v in agent_states.items() if v == "error"]
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

        # ── Provider setup panel handlers (thin wrappers over pure funcs) ──
        def _on_provider_change(provider_val):
            try:
                state = provider_panel_state(provider_val)
            except Exception as exc:  # pragma: no cover — defensive
                state = {
                    "is_cloud": provider_val != "ollama",
                    "key_saved": False,
                    "key_hint": "",
                    "models": [],
                    "model_default": _MODEL_DEFAULTS.get(provider_val, ""),
                    "ollama_html": "",
                    "error": str(exc),
                }
            mask = _key_mask(provider_val) if state["key_saved"] else ""
            return (
                gr.update(visible=state["is_cloud"]),
                gr.update(visible=not state["is_cloud"]),
                gr.update(value="", placeholder=mask or "sk-..."),
                f'<div class="pl-key-hint">{state["key_hint"]}</div>' if state["key_hint"] else "",
                state["ollama_html"] or "",
                gr.update(
                    choices=state["models"] or [state["model_default"]],
                    value=state["model_default"],
                ),
                _status_html(escape(str(state["error"])), "error") if state["error"] else "",
            )

        _panel_outputs = [
            key_group,
            ollama_group,
            api_key_box,
            key_hint_html,
            ollama_runtime_html,
            model,
            panel_status,
        ]
        provider.change(fn=_on_provider_change, inputs=provider, outputs=_panel_outputs)
        ollama_refresh_btn.click(fn=_on_provider_change, inputs=provider, outputs=_panel_outputs)

        def _on_save_key(provider_val, key_val):
            status_msg, models, default = save_key_action(provider_val, key_val)
            if not models:
                return status_msg, gr.update(), gr.update(), gr.update()
            hint = (
                f'<div class="pl-key-hint">{escape(_key_mask(provider_val))} '
                f"&middot; {_KEY_SAVED_NOTE}</div>"
            )
            return (
                status_msg,
                gr.update(choices=models, value=default),
                gr.update(value="", placeholder=_key_mask(provider_val) or "sk-..."),
                hint,
            )

        save_key_btn.click(
            fn=_on_save_key,
            inputs=[provider, api_key_box],
            outputs=[panel_status, model, api_key_box, key_hint_html],
        )

        def _on_load_models(provider_val):
            status_msg, models, default = load_models_action(provider_val)
            return status_msg, gr.update(choices=models or [default], value=default)

        load_models_btn.click(
            fn=_on_load_models,
            inputs=provider,
            outputs=[panel_status, model],
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
