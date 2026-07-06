# paperlab architecture

High-level view of how the pieces fit together.

## Data flow

```
PDF file
  │
  ▼
[ingest]  docling → structured Document (+ optional GROBID for references)
  │
  ▼
[orchestrator]  LangGraph DAG
  │
  ├── Summarizer      ──┐
  ├── Methodologist   ──┤
  ├── Critic          ──┼──► Merge
  └── Contextualizer  ──┘        (paper-qa retrieval for citations)
  │
  ▼
Report (Markdown + JSON)  →  ~/.paperlab/sessions/<id>.jsonl
```

## Modules

| Module | Responsibility |
|---|---|
| `ingest/` | PDF → structured Document via docling; optional GROBID sidecar |
| `agents/` | Prompt loading, per-agent LLM calls, output schemas |
| `orchestrator/` | LangGraph state machine, token budgeting, streaming |
| `providers/` | LiteLLM wrapper: Ollama / OpenRouter / Together / Gemini / Anthropic / custom |
| `cli/` | Typer commands: init, config, read, list, show, web |
| `web/` | Gradio dashboard, reuses core modules |
| `prompts/` | YAML files: 4 agents × 2 modes × 2 languages |

## Key design decisions

- **Local by default.** Ollama is the default provider so anything works offline and free.
- **One LLM abstraction.** LiteLLM handles all providers — no bespoke wrappers.
- **Prompts as data.** YAML in `prompts/` so users and contributors can iterate without touching Python.
- **JSONL session log.** Same pattern as codbash — grep-friendly, easy to back up.
- **CLI and web share the core.** `paperlab read` and `paperlab web` both call the same orchestrator.

## Non-goals for 0.1.0

- Uploading data to a cloud service
- Training or fine-tuning models
- Non-biomedical domains (comes later via profile system)
- Non-PDF inputs (comes later)
