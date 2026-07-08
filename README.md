# paperlab

[English](#english) | [Русский](#русский)

---

## English

**paperlab** is an open-source multi-agent LLM tool for critically reading biomedical and pharmacology research papers. Local by default, provider-agnostic, built for students and researchers.

### What it does

You give paperlab a PDF of a research paper. Four AI agents read it in parallel:

- **Summarizer** — what the paper actually claims
- **Methodologist** — study design, CONSORT/PRISMA/STROBE compliance, reproducibility
- **Critic** — statistical weaknesses, p-hacking, cherry-picking, conflicts of interest
- **Contextualizer** — where this fits in the field, related work

You get a structured report in Markdown or JSON. Two modes:

- `rigorous` — strict peer-review style critique for postgrads and researchers
- `learning` — gentle explanation for undergraduates reading their first papers

Two output languages: English or Russian.

### Install

Requires Python 3.11 or 3.12. Python 3.14 is not yet supported (some transitive dependencies do not build on 3.14).

```bash
pipx install --python python3.12 paperlab
paperlab init
```

Alternative — install with pip inside a project venv:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install paperlab
paperlab init
```

Install from source:

```bash
git clone https://github.com/zhakhatoff/paperlab.git
cd paperlab
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
paperlab --help
```

`paperlab init` creates `~/.paperlab/` with a default `config.toml` and a `sessions/` subdirectory. Run with `--force` to overwrite an existing config.

**pipx broken on Python 3.14?** If `pipx install` fails with `ensurepip` errors, your pipx shared venv is running on Python 3.14. Pin it to 3.12:

```bash
rm -rf ~/.local/pipx/shared
PIPX_DEFAULT_PYTHON=$(brew --prefix python@3.12)/bin/python3.12 pipx ensurepath
```

### CLI

| Command | What it does |
|---|---|
| `paperlab version` | Print installed version |
| `paperlab init [--force]` | Create `~/.paperlab/{config.toml, sessions/}` |
| `paperlab read <paper.pdf>` | Run the 4-agent review (see flags below) |
| `paperlab list` | Table of past sessions |
| `paperlab show <session-id> [--format markdown\|json]` | Reprint a past session |
| `paperlab config get <key>` | Read `provider` / `model` / `mode` / `lang` / `extra.<k>` |
| `paperlab config set <key> <value>` | Update config.toml |
| `paperlab web` | Launch Gradio dashboard |

`paperlab read` flags:

| Flag | Values | Default |
|---|---|---|
| `--mode` | `rigorous`, `learning` | from config |
| `--lang` | `en`, `ru` | from config |
| `--provider` | see table below | from config |
| `--model` | any model string the provider accepts | from config |
| `--format` | `markdown`, `json` | `markdown` |
| `--output` | file path | stdout |

```bash
paperlab read paper.pdf --mode rigorous --lang en
paperlab read paper.pdf --mode learning --lang ru --provider ollama --model qwen2.5:7b
paperlab read paper.pdf --format json --output report.json
```

### Providers

paperlab uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood. Supported provider names:

| Name | Where it runs | Auth | Model string example |
|---|---|---|---|
| `ollama` | Local (default) | none | `qwen2.5:7b`, `llama3.2:3b` |
| `openrouter` | Cloud | `OPENROUTER_API_KEY` | `openrouter/anthropic/claude-3.5-sonnet` |
| `together` | Cloud | `TOGETHER_API_KEY` | `together_ai/meta-llama/Llama-3-70b-chat-hf` |
| `groq` | Cloud | `GROQ_API_KEY` | `groq/llama-3.1-70b-versatile` |
| `gemini` | Cloud | `GEMINI_API_KEY` | `gemini/gemini-1.5-pro` |
| `anthropic` | Cloud | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| `openai` | Cloud | `OPENAI_API_KEY` | `gpt-4o` |
| `custom` | Any OpenAI-compatible endpoint | as needed | LiteLLM convention |
| `fake` | In-process test double | none | any |

Switch globally with `paperlab config set provider <name>` or per invocation with `--provider`.

**API keys.** The web dashboard (`paperlab web`) lets you pick a provider, save its API key, and browse available models. Keys are stored locally in `~/.paperlab/keys.toml` (file mode 600, never leaves your machine); environment variables take precedence over the stored file. For Ollama the dashboard detects whether it is installed and running, lists installed models with sizes, and recommends models that fit your RAM.

### Config

```bash
paperlab config get provider          # print current value
paperlab config set provider openai   # update config.toml
paperlab config set model gpt-4o
paperlab config set extra.base_url http://localhost:11434
```

Config is stored in `~/.paperlab/config.toml` (or `$PAPERLAB_HOME/config.toml`).

### Privacy

Everything runs locally. PDFs never leave your machine unless you explicitly configure a cloud provider. History is stored in `~/.paperlab/sessions/` as JSONL — grep, back up, delete freely.

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

### License

MIT

---

## Русский

**paperlab** — open source инструмент для критического чтения биомедицинских и фармакологических научных статей с помощью команды ИИ-агентов. Локальный по умолчанию, поддерживает разных провайдеров, сделан для студентов и исследователей.

### Что делает

Вы даёте paperlab PDF научной статьи. Четыре агента читают её параллельно:

- **Summarizer** — что статья реально утверждает
- **Methodologist** — дизайн исследования, соответствие CONSORT/PRISMA/STROBE, воспроизводимость
- **Critic** — статистические слабости, p-hacking, cherry-picking, конфликты интересов
- **Contextualizer** — место в поле, связь с литературой

Получаете структурированный разбор в Markdown или JSON. Два режима:

- `rigorous` — жёсткая критика в стиле peer-review для аспирантов и исследователей
- `learning` — мягкий разбор для студентов, читающих первые статьи

Два языка вывода: английский или русский.

### Установка

Требуется Python 3.11 или 3.12. Python 3.14 пока не поддерживается (часть транзитивных зависимостей не собирается на 3.14).

```bash
pipx install --python python3.12 paperlab
paperlab init
```

Или через pip в проектном venv:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install paperlab
paperlab init
```

Из исходников:

```bash
git clone https://github.com/zhakhatoff/paperlab.git
cd paperlab
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
paperlab --help
```

**pipx падает на Python 3.14?** Если `pipx install` валится с ошибкой про `ensurepip`, у pipx общий venv на Python 3.14. Перегони его на 3.12:

```bash
rm -rf ~/.local/pipx/shared
PIPX_DEFAULT_PYTHON=$(brew --prefix python@3.12)/bin/python3.12 pipx ensurepath
```

Команда `paperlab init` создаёт `~/.paperlab/` с дефолтным `config.toml` и поддиректорией `sessions/`. Флаг `--force` перезаписывает существующий конфиг.

### Использование

```bash
paperlab read paper.pdf --mode rigorous --lang ru
paperlab read paper.pdf --mode learning --lang en --provider ollama --model qwen2.5:7b
paperlab list                    # история разборов
paperlab show <session-id>       # открыть прошлый разбор
paperlab web                     # веб-интерфейс в браузере (фаза 8)
```

Формат вывода:

```bash
paperlab read paper.pdf --format markdown          # по умолчанию
paperlab read paper.pdf --format json --output report.json
```

### Провайдеры

Работает с любым из этих без изменений в коде:

- `ollama` (локально, по умолчанию, бесплатно)
- `openrouter` (единый доступ к GPT, Claude, Gemini, Llama и т.д.)
- `together`, `groq`, `gemini`, `anthropic`, `openai`
- `custom` (любой OpenAI-совместимый endpoint)

Переключение: `paperlab config set provider ollama` или флаг `--provider` при запуске.

### Конфигурация

```bash
paperlab config get provider          # показать текущее значение
paperlab config set provider openai   # обновить config.toml
paperlab config set model gpt-4o
paperlab config set extra.base_url http://localhost:11434
```

Конфиг хранится в `~/.paperlab/config.toml` (или `$PAPERLAB_HOME/config.toml`).

### Приватность

Всё работает локально. PDF не покидает вашу машину, если вы явно не настроили облачного провайдера. История хранится в `~/.paperlab/sessions/` в формате JSONL — можно грепать, бэкапить, удалять.

### Участие в разработке

См. [CONTRIBUTING.md](CONTRIBUTING.md).

### Лицензия

MIT
