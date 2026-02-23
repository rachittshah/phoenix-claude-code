"""Analyze Phoenix traces pulled via the px CLI."""

import json
import subprocess
import os
from collections import Counter


def fetch_traces(limit: int = 100, project: str = None) -> list[dict]:
    """Fetch traces from Phoenix via the px CLI.

    Args:
        limit: Number of traces to fetch.
        project: Phoenix project name. Defaults to PHOENIX_PROJECT env var.

    Returns:
        List of trace dicts.
    """
    env = os.environ.copy()
    if project:
        env["PHOENIX_PROJECT"] = project

    result = subprocess.run(
        ["px", "traces", "--limit", str(limit), "--format", "raw", "--no-progress"],
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"px traces failed: {result.stderr}")

    return json.loads(result.stdout)


def analyze_traces(traces: list[dict]) -> dict:
    """Compute summary statistics from traces.

    Returns:
        Dict with status breakdown, model usage, duration stats,
        error count, and tool usage.
    """
    statuses = Counter()
    models = Counter()
    durations = []
    error_count = 0
    tool_names = Counter()
    token_totals = {"prompt": 0, "completion": 0}

    for t in traces:
        statuses[t.get("status", "unknown")] += 1
        dur = t.get("duration", 0)
        if dur:
            durations.append(dur)

        for s in t.get("spans", []):
            # Model usage
            attrs = s.get("attributes", {})
            model = (
                attrs.get("llm.model_name") or attrs.get("gen_ai.response.model") or ""
            )
            if model:
                models[model] += 1

            # Errors
            if s.get("status_code") == "ERROR":
                error_count += 1

            # Tool usage
            if s.get("span_kind") == "TOOL":
                tool_names[s.get("name", "unknown")] += 1

            # Tokens
            pt = attrs.get("llm.token_count.prompt", 0) or 0
            ct = attrs.get("llm.token_count.completion", 0) or 0
            token_totals["prompt"] += pt
            token_totals["completion"] += ct

    return {
        "trace_count": len(traces),
        "statuses": dict(statuses),
        "models": dict(models.most_common(10)),
        "duration_ms": {
            "avg": sum(durations) / len(durations) if durations else 0,
            "max": max(durations) if durations else 0,
            "min": min(durations) if durations else 0,
        },
        "error_spans": error_count,
        "error_rate": (statuses.get("ERROR", 0) / len(traces) * 100 if traces else 0),
        "tools": dict(tool_names.most_common(15)),
        "tokens": token_totals,
    }


def generate_report(traces: list[dict]) -> str:
    """Generate a text report from traces."""
    stats = analyze_traces(traces)

    lines = []
    lines.append("# Phoenix Trace Report")
    lines.append(f"**Traces analyzed:** {stats['trace_count']}")
    lines.append(f"**Error rate:** {stats['error_rate']:.1f}%")

    lines.append("")
    lines.append("## Status Breakdown")
    for status, count in stats["statuses"].items():
        lines.append(f"  {status}: {count}")

    lines.append("")
    lines.append("## Models Used")
    for model, count in stats["models"].items():
        lines.append(f"  {count:4d} | {model}")

    lines.append("")
    lines.append("## Duration (ms)")
    d = stats["duration_ms"]
    lines.append(f"  avg: {d['avg']:.0f}, max: {d['max']}, min: {d['min']}")

    lines.append("")
    lines.append("## Token Usage")
    lines.append(f"  Prompt tokens: {stats['tokens']['prompt']:,}")
    lines.append(f"  Completion tokens: {stats['tokens']['completion']:,}")

    if stats["tools"]:
        lines.append("")
        lines.append("## Tool Spans")
        for name, count in stats["tools"].items():
            lines.append(f"  {count:4d} | {name}")

    return "\n".join(lines)


if __name__ == "__main__":
    traces = fetch_traces()
    print(generate_report(traces))
