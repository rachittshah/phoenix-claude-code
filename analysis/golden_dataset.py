"""Helper for building a golden dataset from manual annotation."""

import csv
from datetime import datetime

from analysis.history_analyzer import load_history


def extract_sessions(entries: list[dict], gap_minutes: int = 30) -> list[list[dict]]:
    """Group prompts into sessions based on time gaps.

    Args:
        entries: Sorted list of prompt entries.
        gap_minutes: Minutes of inactivity to split sessions.

    Returns:
        List of sessions, each a list of prompt dicts.
    """
    if not entries:
        return []

    sessions = []
    current_session = [entries[0]]
    gap_ms = gap_minutes * 60 * 1000

    for entry in entries[1:]:
        prev_ts = current_session[-1].get("timestamp", 0)
        curr_ts = entry.get("timestamp", 0)

        if curr_ts - prev_ts > gap_ms:
            sessions.append(current_session)
            current_session = [entry]
        else:
            current_session.append(entry)

    if current_session:
        sessions.append(current_session)

    return sessions


def session_summary(session: list[dict]) -> dict:
    """Create a summary of a session for annotation."""
    first = session[0]
    last = session[-1]

    start = datetime.fromtimestamp(first["timestamp"] / 1000)
    end = datetime.fromtimestamp(last["timestamp"] / 1000)
    project = first.get("project", "unknown").rstrip("/").split("/")[-1]

    prompts_preview = []
    for p in session[:5]:
        text = p.get("display", "")[:150]
        prompts_preview.append(text)

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_min": (last["timestamp"] - first["timestamp"]) / 60000,
        "prompt_count": len(session),
        "project": project,
        "first_prompts": prompts_preview,
    }


def export_for_annotation(
    sessions: list[list[dict]], output_path: str = "golden_dataset.csv"
) -> str:
    """Export sessions as a CSV ready for manual annotation.

    The CSV includes columns for you to fill in:
    - verdict: PASS or FAIL
    - critique: Open-ended notes about what went wrong

    Args:
        sessions: List of sessions from extract_sessions().
        output_path: Where to write the CSV.

    Returns:
        Path to the created CSV.
    """
    rows = []
    for i, session in enumerate(sessions):
        summary = session_summary(session)
        rows.append(
            {
                "session_id": i + 1,
                "start": summary["start"],
                "end": summary["end"],
                "duration_min": f"{summary['duration_min']:.1f}",
                "prompt_count": summary["prompt_count"],
                "project": summary["project"],
                "first_prompt": summary["first_prompts"][0]
                if summary["first_prompts"]
                else "",
                "verdict": "",  # Fill in: PASS or FAIL
                "critique": "",  # Fill in: What went wrong?
            }
        )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return output_path


if __name__ == "__main__":
    entries = load_history()
    sessions = extract_sessions(entries)
    print(f"Found {len(sessions)} sessions")

    path = export_for_annotation(sessions[:50])
    print(f"Annotation CSV written to: {path}")
    print("Open it, review each session, fill in verdict + critique columns.")
