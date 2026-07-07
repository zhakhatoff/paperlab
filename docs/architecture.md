# paperlab architecture

How the pieces fit together. If you're new to the codebase, start with `CLAUDE.md` at the repo root — it's a shorter map.

## System diagram

```
CLI                                     Web
paperlab read paper.pdf                 paperlab web  →  Gradio Blocks
        │                                       │
        └───────────────┬───────────────────────┘
                        │
                        ▼
              +----------------------+
              |  cli/main.py         |   uses _RUNTIME.{extract_text, make_provider}
              |  web/app.py:process  |   uses _RUNTIME.{extract_text, make_provider}
              +----------+-----------+
                         │
   ┌─────────────────────┼──────────────────────┐
   ▼                     ▼                      ▼
 ingest              providers                orchestrator
 extract_text()      make_provider(name)      review(paper, provider, ...)
   │                    │                        │
   ▼                    ▼                        │
 docling            LiteLLMProvider              │  asyncio.gather (return_exceptions=True)
 (lazy import)      (lazy imports litellm)       │
                    FakeProvider (tests)         │
                                                 ├── SummarizerAgent      ─┐
                                                 ├── MethodologistAgent   ─┤
                                                 ├── CriticAgent          ─┼─► dict[name → AgentReport]
                                                 └── ContextualizerAgent  ─┘
                                                                            │
                                                                            ▼
                                                                    ReviewReport
                                                                            │
                                                        ┌───────────────────┴───────────────────┐
                                                        ▼                                       ▼
                                                 sessions.save_report               sessions.to_markdown / to_json
                                                        │                                       │
                                                        ▼                                       ▼
                                            ~/.paperlab/sessions/<id>.jsonl         stdout / --output file
```

Every agent runs the same three steps: load its prompt from YAML, call the provider, parse the JSON reply. The four agents differ only by their `NAME` and their YAML file.

## Modules

| Module | File | Responsibility |
|---|---|---|
| Prompts | `prompts/loader.py` | `load_prompt(agent, mode, lang)` + `render(template, **kwargs)` |
| Prompts | `prompts/*.yaml` | `en / ru → rigorous / learning → {system, user_template}` |
| Providers | `providers/base.py` | `LLMProvider` abstract, `ProviderError` |
| Providers | `providers/litellm_provider.py` | Real backend; lazy `import litellm` |
| Providers | `providers/fake.py` | Test double, records calls, prefix-matched responses |
| Providers | `providers/factory.py` | `make_provider(name)` + `SUPPORTED_PROVIDERS` |
| Ingest | `ingest/pdf.py` | `extract_text(path, converter=None)` → `IngestedPaper`; docling lazy |
| Agents | `agents/base.py` | `Agent` (prompt → provider → JSON parse) + `AgentReport` |
| Agents | `agents/{summarizer,methodologist,critic,contextualizer}.py` | `NAME` only |
| Orchestrator | `orchestrator/runner.py` | `review(...)` → `ReviewReport`; `asyncio.gather` |
| Sessions | `sessions/store.py` | JSONL persistence, `PAPERLAB_HOME` env |
| Sessions | `sessions/export.py` | `to_markdown`, `to_json` |
| CLI | `cli/config.py` | `PaperlabConfig` (pydantic), TOML load/save, dotted get/set |
| CLI | `cli/main.py` | Typer app: `init / read / list / show / config / web` |
| Web | `web/app.py` | `process(...)`, `build_app()`, `launch()`; gradio lazy |

## Session file format

`~/.paperlab/sessions/<session_id>.jsonl` — one line, one full `ReviewReport`:

```json
{
  "paper": {"source_path": "...", "title": null, "text": "...", "num_pages": 12, "backend": "docling"},
  "mode": "rigorous",
  "lang": "en",
  "model": "qwen2.5:7b",
  "session_id": "a1b2c3d4e5f6",
  "created_at": "2026-07-07T09:20:11+00:00",
  "agents": {
    "summarizer":     {"agent_name": "summarizer", "output": {"claims": [...], "findings": [...], "limitations_stated": [...]}, "raw": "...", "error": null},
    "methodologist":  {"agent_name": "methodologist", "output": {...}, "raw": "...", "error": null},
    "critic":         {"agent_name": "critic",        "output": {...}, "raw": "...", "error": null},
    "contextualizer": {"agent_name": "contextualizer","output": {...}, "raw": "...", "error": null}
  }
}
```

`save_report` writes exactly this shape. `list_sessions` reads only the top-level metadata (session_id, created_at, mode, lang, model, paper.title). `load_report` deserializes back to a `ReviewReport` via pydantic.

## Config file format

`~/.paperlab/config.toml`:

```toml
provider = "ollama"
model    = "qwen2.5:7b"
mode     = "rigorous"
lang     = "en"

[extra]
# free-form key/value overrides consumers may add
```

`PAPERLAB_HOME` env variable relocates everything (config + sessions), used in every persistence test.

## Key design decisions

- **Prompts are data.** YAML in `prompts/` is the source of truth for agent behavior.
- **One LLM abstraction.** LiteLLM covers Ollama, OpenRouter, Together, Groq, Gemini, Anthropic, OpenAI, custom endpoints — no bespoke wrappers.
- **`FakeProvider` is the test seam.** Every non-network test uses it, wired through `_RUNTIME` or direct constructor injection.
- **`asyncio.gather` instead of LangGraph.** Four agents are independent; a DAG buys nothing. Revisit only if agents gain cross-dependencies.
- **Per-agent isolation.** `return_exceptions=True` — one failing agent doesn't sink the report.
- **`_RUNTIME` injection.** `cli/main.py` and `web/app.py` expose a `SimpleNamespace(extract_text, make_provider)` that tests swap without patching module imports.
- **Lazy heavy imports.** `docling`, `litellm`, `gradio` are imported inside functions. Unit tests stay fast; the CLI starts without pulling everything.
- **`importlib.metadata` for version.** No duplication between `pyproject.toml` and Python code.
- **JSONL sessions.** Grep-friendly, back-up-friendly, one line per session.

## Non-goals for 0.1.x

- Uploading data to a cloud service
- Training or fine-tuning models
- Non-biomedical domains (planned via profile system later)
- Non-PDF inputs (planned later)
- LangGraph — not needed until agents gain dependencies
- GROBID sidecar — planned but not shipped in 0.1.x
- `paper-qa` retrieval for the Contextualizer — planned
