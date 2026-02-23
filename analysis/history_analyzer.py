"""Analyze Claude Code history.jsonl for usage patterns."""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime


def load_history(path: str = None) -> list[dict]:
    """Load and parse history.jsonl.

    Args:
        path: Path to history.jsonl. Defaults to ~/.claude/history.jsonl.

    Returns:
        List of prompt entries sorted by timestamp.
    """
    if path is None:
        path = os.path.expanduser("~/.claude/history.jsonl")

    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    entries.sort(key=lambda x: x.get("timestamp", 0))
    return entries


def filter_by_date(
    entries: list[dict], start: str = None, end: str = None
) -> list[dict]:
    """Filter entries by date range (ISO format: YYYY-MM-DD)."""
    filtered = entries
    if start:
        start_ts = int(datetime.fromisoformat(start).timestamp() * 1000)
        filtered = [e for e in filtered if e.get("timestamp", 0) >= start_ts]
    if end:
        end_ts = int(datetime.fromisoformat(end + "T23:59:59").timestamp() * 1000)
        filtered = [e for e in filtered if e.get("timestamp", 0) <= end_ts]
    return filtered


def monthly_breakdown(entries: list[dict]) -> dict[str, int]:
    """Count prompts per month."""
    months = Counter()
    for e in entries:
        ts = e.get("timestamp", 0)
        if ts:
            dt = datetime.fromtimestamp(ts / 1000)
            months[dt.strftime("%Y-%m")] += 1
    return dict(sorted(months.items()))


def project_breakdown(entries: list[dict]) -> dict[str, int]:
    """Count prompts per project."""
    projects = Counter()
    for e in entries:
        proj = e.get("project", "unknown")
        # Use just the last directory component for readability
        projects[proj.rstrip("/").split("/")[-1]] += 1
    return dict(projects.most_common(20))


def prompt_length_stats(entries: list[dict]) -> dict:
    """Compute prompt length statistics."""
    lengths = [len(e.get("display", "")) for e in entries]
    if not lengths:
        return {}
    return {
        "count": len(lengths),
        "avg": sum(lengths) / len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "median": sorted(lengths)[len(lengths) // 2],
    }


def monthly_prompt_length(entries: list[dict]) -> dict[str, float]:
    """Average prompt length per month (tracks sophistication growth)."""
    monthly = defaultdict(list)
    for e in entries:
        ts = e.get("timestamp", 0)
        if ts:
            month = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m")
            monthly[month].append(len(e.get("display", "")))

    return {m: sum(lengths) / len(lengths) for m, lengths in sorted(monthly.items())}


def command_frequency(entries: list[dict]) -> dict[str, int]:
    """Count slash command usage."""
    commands = Counter()
    for e in entries:
        text = e.get("display", "").strip()
        if text.startswith("/"):
            cmd = text.split()[0]
            commands[cmd] += 1
    return dict(commands.most_common(20))


def generate_report(entries: list[dict]) -> str:
    """Generate a text report from history entries."""
    lines = []
    lines.append("# Claude Code Usage Report")
    lines.append(f"**Prompts analyzed:** {len(entries)}")

    if entries:
        first = datetime.fromtimestamp(entries[0]["timestamp"] / 1000)
        last = datetime.fromtimestamp(entries[-1]["timestamp"] / 1000)
        lines.append(
            f"**Date range:** {first.strftime('%Y-%m-%d')} to {last.strftime('%Y-%m-%d')}"
        )

    lines.append("")
    lines.append("## Monthly Breakdown")
    for month, count in monthly_breakdown(entries).items():
        lines.append(f"  {month}: {count} prompts")

    lines.append("")
    lines.append("## Top Projects")
    for proj, count in project_breakdown(entries).items():
        lines.append(f"  {count:4d} | {proj}")

    lines.append("")
    lines.append("## Prompt Length (Monthly Average)")
    for month, avg in monthly_prompt_length(entries).items():
        lines.append(f"  {month}: {avg:.0f} chars avg")

    lines.append("")
    lines.append("## Slash Commands")
    for cmd, count in command_frequency(entries).items():
        lines.append(f"  {count:4d} | {cmd}")

    stats = prompt_length_stats(entries)
    if stats:
        lines.append("")
        lines.append("## Overall Stats")
        lines.append(f"  Average prompt length: {stats['avg']:.0f} chars")
        lines.append(f"  Median: {stats['median']} chars")
        lines.append(f"  Longest: {stats['max']} chars")

    return "\n".join(lines)


if __name__ == "__main__":
    entries = load_history()
    print(generate_report(entries))
