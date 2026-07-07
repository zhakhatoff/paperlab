# CLAUDE.md — paperlab quick map for contributors

Read this first. It's the shortest path to a mental model of the codebase.

## What paperlab is

CLI + web dashboard that runs 4 LLM agents over a biomedical paper PDF and produces a structured critique. Local by default (Ollama), any LiteLLM-compatible provider works.

## Project layout

```
src/paperlab/
  __init__.py             __version__ read via importlib.metadata (0.0.0+unknown fallback)
  cli/
    main.py               Typer app: version / init / read / list / show / config / web
    config.py             PaperlabConfig (pydantic) + TOML load/save + dotted get/set
  prompts/
    loader.py             load_prompt(agent, mode, lang) + render(template, **kwargs)
    summarizer.yaml       en/ru × rigorous/learning → {system, user_template}
    methodologist.yaml    same shape
    critic.yaml           same shape
    contextualizer.yaml   same shape
  providers/
    base.py               LLMProvider (abstract) + ProviderError
    litellm_provider.py   Real provider — lazy imports litellm.acompletion
    fake.py               FakeProvider — records calls, prefix-matched responses, JSON echo default
    factory.py            make_provider(name) + SUPPORTED_PROVIDERS tuple
  ingest/
    pdf.py                extract_text(path, converter=None) → IngestedPaper; docling lazy import
  agents/
    base.py               Agent + AgentReport + _parse_json (direct → regex {…} fallback)
    summarizer.py         NAME = "summarizer"
    methodologist.py      NAME = "methodologist"
    critic.py             NAME = "critic"
    contextualizer.py     NAME = "contextualizer"
    __init__.py           ALL_AGENTS = [Summarizer, Methodologist, Critic, Contextualizer]
  orchestrator/
    runner.py             review(paper, provider, mode, lang, model) → ReviewReport
                          asyncio.gather with return_exceptions=True (per-agent isolation)
  sessions/
    store.py              default_sessions_dir / save_report / list_sessions / load_report
                          (JSONL, one full report per line, filename = <session_id>.jsonl)
    export.py             to_markdown(report) / to_json(report)
  web/
    app.py                process(paper_path, mode, lang, model, provider) → (md, json)
                          build_app() + launch(); gradio lazy import

tests/                    Mirrors src layout; 120 tests, all pass, run via .venv/bin/pytest -q
docs/architecture.md      ASCII data-flow diagram + module table
docs/user-research.md     Interview script (no real participant data yet)
```

## Data flow

```
paperlab read paper.pdf --mode rigorous --lang en --provider ollama
        │
        ▼
  cli/main.py:read
        │
        ├─► ingest.extract_text(paper.pdf)  ── docling ──► IngestedPaper(text, ...)
        │
        ├─► providers.factory.make_provider("ollama") ──► LiteLLMProvider
        │
        ▼
  orchestrator.review(paper, provider, mode, lang, model)
        │
        │  asyncio.gather (return_exceptions=True)
        │
        ├── SummarizerAgent.run(text)     ─┐
        ├── MethodologistAgent.run(text)  ─┤
        ├── CriticAgent.run(text)         ─┼─► dict[name → AgentReport]
        └── ContextualizerAgent.run(text) ─┘
        │
        ▼
  ReviewReport(paper, mode, lang, model, session_id, created_at, agents)
        │
        ├─► sessions.save_report(...)  → ~/.paperlab/sessions/<id>.jsonl
        │
        └─► sessions.to_markdown(report) → stdout / --output file
            sessions.to_json(report)     → stdout / --output file
```

Every Agent.run does the same three things: `load_prompt(name, mode, lang)` → `provider.complete(system, user, model)` → `_parse_json(raw)`. The 4 concrete agents differ only by their YAML files.

## Key design decisions

- **Prompts are data, not code.** YAML files in `src/paperlab/prompts/` are the source of truth for agent behavior. Editing a prompt does not require touching Python.
- **Providers via LiteLLM.** One abstraction covers Ollama, OpenRouter, Together, Groq, Gemini, Anthropic, OpenAI, and any OpenAI-compatible endpoint. `LiteLLMProvider` imports `litellm` lazily so unit tests don't need it.
- **`FakeProvider` is the testing seam.** Every agent, orchestrator, CLI, and web test wires a `FakeProvider` through dependency injection. Tests never hit the network.
- **`asyncio.gather` instead of LangGraph.** The four agents are independent; a DAG buys nothing. If a future feature needs cross-agent dependencies, revisit this.
- **Per-agent isolation.** `orchestrator.review` uses `return_exceptions=True` — one failing agent doesn't sink the report; its `AgentReport.error` is filled and `output` is `{}`.
- **`_RUNTIME` injection points.** `cli/main.py` and `web/app.py` expose `_RUNTIME` with `extract_text` and `make_provider` attributes so tests can swap them without monkeypatching module imports.
- **`PAPERLAB_HOME` env override.** All disk paths (config, sessions) route through `default_home()` / `default_sessions_dir()`, which honor this env var. Every persistence test uses `monkeypatch.setenv("PAPERLAB_HOME", tmp_path)` — do not add ad-hoc paths that skip it.
- **JSONL sessions.** One line = one full report (`ReviewReport.model_dump(mode='json')`). Filename is `<session_id>.jsonl`. Grep-friendly, back-up-friendly.
- **Version via `importlib.metadata`.** `paperlab.__version__` is read from installed package metadata; no duplication with `pyproject.toml`.
- **Lazy heavy imports.** `docling`, `litellm`, `gradio` are imported inside functions, not at module top. Keeps unit tests fast and lets the CLI start without pulling everything.

## Session file format

`~/.paperlab/sessions/<session_id>.jsonl` — a single line containing the full `ReviewReport` serialized via `pydantic.model_dump(mode="json")`. Fields:

```json
{
  "paper": {"source_path": "...", "title": null, "text": "...", "num_pages": 12, "backend": "docling"},
  "mode": "rigorous",
  "lang": "en",
  "model": "qwen2.5:7b",
  "session_id": "a1b2c3d4e5f6",
  "created_at": "2026-07-07T09:20:11+00:00",
  "agents": {
    "summarizer":     {"agent_name": "...", "output": {...}, "raw": "...", "error": null},
    "methodologist":  {...},
    "critic":         {...},
    "contextualizer": {...}
  }
}
```

## CLI surface

```
paperlab version
paperlab init [--force]                       Create ~/.paperlab/{config.toml, sessions/}
paperlab read <paper.pdf>                     Run the 4-agent review
    [--mode rigorous|learning]
    [--lang en|ru]
    [--model <name>]
    [--provider <name>]
    [--format markdown|json]
    [--output <path>]
paperlab list                                 Rich table of past sessions
paperlab show <session-id>                    Reprint a past session
    [--format markdown|json]
paperlab config get <key>                     provider | model | mode | lang | extra.<k>
paperlab config set <key> <value>
paperlab web                                  Launch Gradio dashboard
```

## Supported providers

`SUPPORTED_PROVIDERS = ("ollama", "openrouter", "together", "groq", "gemini", "anthropic", "openai", "custom", "fake")`.

`"fake"` returns `FakeProvider` and exists for CI and manual smoke tests. `"custom"` maps to `LiteLLMProvider` and expects the model string to encode the endpoint (LiteLLM convention).

## Testing

```
.venv/bin/pytest -q            120 tests, ~0.3s
.venv/bin/ruff check .         must be clean
.venv/bin/ruff format --check . must be clean
```

Every new feature was added test-first (Red → Green → Refactor). New contributions should follow the same pattern.

## Release

Tag `v<version>` on `main`. `.github/workflows/publish.yml` builds sdist + wheel, runs `twine check`, and publishes to PyPI via Trusted Publishing (OIDC, no tokens). Bump `pyproject.toml` version before tagging.

## Non-goals for 0.1.x

- Uploading data to a cloud service
- Training or fine-tuning models
- Non-biomedical domains (planned via profile system later)
- Non-PDF inputs (planned later)
- LangGraph — not needed until agents gain dependencies
