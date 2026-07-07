"""Export ReviewReport to JSON or Markdown."""

from __future__ import annotations

import json

from paperlab.orchestrator import ReviewReport

_AGENT_ORDER = ["summarizer", "methodologist", "critic", "contextualizer"]


def to_json(report: ReviewReport) -> str:
    return json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)


def to_markdown(report: ReviewReport) -> str:
    lines: list[str] = []

    lines.append(f"# paperlab review {report.session_id}")
    lines.append("")

    lines.append(f"- created_at: {report.created_at}")
    lines.append(f"- mode: {report.mode}")
    lines.append(f"- lang: {report.lang}")
    lines.append(f"- model: {report.model}")
    lines.append(f"- source: {report.paper.source_path}")
    if report.paper.title:
        lines.append(f"- title: {report.paper.title}")
    lines.append("")

    agent_names = [n for n in _AGENT_ORDER if n in report.agents]
    remaining = [n for n in report.agents if n not in _AGENT_ORDER]
    for name in agent_names + remaining:
        agent_report = report.agents[name]
        lines.append(f"## {name}")
        lines.append("")
        if agent_report.error:
            lines.append(f"> error: {agent_report.error}")
            lines.append("")
        else:
            for key, value in agent_report.output.items():
                lines.append(f"### {key}")
                lines.append("")
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"- {item}")
                else:
                    lines.append("```")
                    lines.append(str(value))
                    lines.append("```")
                lines.append("")

    return "\n".join(lines)
