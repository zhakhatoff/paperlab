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

```bash
pipx install paperlab
paperlab init
```

`paperlab init` will:
1. Detect or install Ollama (default local backend)
2. Pull a default model (qwen2.5:7b, or llama3.2:3b for weaker machines)
3. Optionally start GROBID via Docker for better reference extraction
4. Save your config to `~/.paperlab/config.toml`

### Use

```bash
paperlab read paper.pdf --mode rigorous --lang en
paperlab read paper.pdf --mode learning --lang ru
paperlab list                    # your review history
paperlab show <session-id>       # revisit a past review
paperlab web                     # open the browser dashboard
```

### Providers

paperlab uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood, so any of these work out of the box:

- **Ollama** (local, default, free)
- **OpenRouter** (unified access to GPT, Claude, Gemini, Llama, etc.)
- **Together, Groq, Gemini, Anthropic, OpenAI**
- **Custom OpenAI-compatible endpoint** (your university's GPU cluster, etc.)

Switch with `paperlab config set provider ollama` or via the web UI.

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

```bash
pipx install paperlab
paperlab init
```

Команда `paperlab init` сделает:
1. Найдёт или установит Ollama (локальный бэкенд по умолчанию)
2. Скачает модель (qwen2.5:7b, или llama3.2:3b для слабых машин)
3. Опционально поднимет GROBID через Docker для лучшего извлечения ссылок
4. Сохранит конфиг в `~/.paperlab/config.toml`

### Использование

```bash
paperlab read paper.pdf --mode rigorous --lang ru
paperlab read paper.pdf --mode learning --lang en
paperlab list                    # история разборов
paperlab show <session-id>       # открыть прошлый разбор
paperlab web                     # веб-интерфейс в браузере
```

### Провайдеры

Работает с любым из этих без изменений в коде:

- **Ollama** (локально, по умолчанию, бесплатно)
- **OpenRouter** (единый доступ к GPT, Claude, Gemini, Llama и т.д.)
- **Together, Groq, Gemini, Anthropic, OpenAI**
- **Свой OpenAI-совместимый endpoint** (например, GPU-кластер университета)

Переключение: `paperlab config set provider ollama` или через веб-UI.

### Приватность

Всё работает локально. PDF не покидает вашу машину, если вы явно не настроили облачного провайдера. История хранится в `~/.paperlab/sessions/` в формате JSONL — можно грепать, бэкапить, удалять.

### Участие в разработке

См. [CONTRIBUTING.md](CONTRIBUTING.md).

### Лицензия

MIT
