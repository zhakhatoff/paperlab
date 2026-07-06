# Contributing to paperlab

Thanks for wanting to help. This project is built to serve students and researchers reading biomedical papers — practical contributions matter more than theoretical polish.

## How you can help

- **Report bugs** — open an issue with the PDF that broke it (if shareable), your OS, and the exact command.
- **Improve prompts** — the agents in `src/paperlab/prompts/` are YAML files. Better prompts = better reviews. PRs welcome.
- **Add a benchmark paper** — `tests/benchmark/` holds papers with expected critiques. More examples = more accurate agents.
- **Add a domain profile** — biomed is the default, but pharma subfields (oncology, immunology, PK/PD) can have their own critique rubrics.
- **Improve docs** — especially for non-programmers. Screenshots, videos, translations.

## Development setup

```bash
git clone https://github.com/zhakhatoff/paperlab
cd paperlab
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Code style

- `ruff format` and `ruff check` before commit
- Type hints on public APIs
- Tests for anything non-trivial

## Branches and PRs

- `main` is protected
- Branch names: `feat/`, `fix/`, `docs/`, `chore/`
- Keep PRs small and focused
- One approval to merge

## Questions

Open a GitHub Discussion or issue. Russian and English are both fine.
