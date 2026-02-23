#!/usr/bin/env python3
"""Run all judges against Claude Code history and output a verdict report."""

import sys
from collections import Counter
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.history_analyzer import load_history
from analysis.golden_dataset import extract_sessions
from judges.secret_hygiene import judge_secret_hygiene
from judges.session_discipline import judge_session_discipline
from judges.prompt_efficiency import judge_prompt_efficiency
from judges.topic_coherence import judge_topic_coherence


def run_all(history_path: str = None, limit: int = None):
    """Run all judges and print results.

    Args:
        history_path: Path to history.jsonl. Defaults to ~/.claude/history.jsonl.
        limit: Max number of sessions to evaluate.
    """
    print("Loading history...")
    entries = load_history(history_path)
    print(f"  {len(entries)} prompts loaded")

    sessions = extract_sessions(entries)
    if limit:
        sessions = sessions[:limit]
    print(f"  {len(sessions)} sessions detected\n")

    # --- Judge 1: Secret Hygiene (per-prompt) ---
    print("=" * 60)
    print("JUDGE: Secret Hygiene")
    print("=" * 60)
    secret_verdicts = Counter()
    secret_failures = []
    for entry in entries:
        v = judge_secret_hygiene(entry.get("display", ""))
        secret_verdicts[v["verdict"]] += 1
        if v["verdict"] == "FAIL":
            secret_failures.append(v["reason"])

    print(f"  PASS: {secret_verdicts['PASS']}")
    print(f"  FAIL: {secret_verdicts['FAIL']}")
    if secret_failures:
        print("  Failure types:")
        for reason in set(secret_failures):
            count = secret_failures.count(reason)
            print(f"    {count}x {reason}")

    # --- Judge 2: Session Discipline (per-session) ---
    print(f"\n{'=' * 60}")
    print("JUDGE: Session Discipline")
    print("=" * 60)
    discipline_verdicts = Counter()
    for session in sessions:
        v = judge_session_discipline(session)
        discipline_verdicts[v["verdict"]] += 1

    print(f"  PASS: {discipline_verdicts.get('PASS', 0)}")
    print(f"  FAIL: {discipline_verdicts.get('FAIL', 0)}")

    # --- Judge 3: Prompt Efficiency (per-prompt, heuristic) ---
    print(f"\n{'=' * 60}")
    print("JUDGE: Prompt Efficiency (heuristic mode)")
    print("=" * 60)
    efficiency_verdicts = Counter()
    for entry in entries:
        v = judge_prompt_efficiency(entry.get("display", ""))
        efficiency_verdicts[v["verdict"]] += 1

    print(f"  PASS: {efficiency_verdicts['PASS']}")
    print(f"  FAIL: {efficiency_verdicts['FAIL']}")

    # --- Judge 4: Topic Coherence (per-session, heuristic) ---
    print(f"\n{'=' * 60}")
    print("JUDGE: Topic Coherence (heuristic mode)")
    print("=" * 60)
    coherence_verdicts = Counter()
    for session in sessions:
        v = judge_topic_coherence(session)
        coherence_verdicts[v["verdict"]] += 1

    print(f"  PASS: {coherence_verdicts.get('PASS', 0)}")
    print(f"  FAIL: {coherence_verdicts.get('FAIL', 0)}")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Prompts analyzed: {len(entries)}")
    print(f"  Sessions analyzed: {len(sessions)}")
    print(f"  Secret leaks found: {secret_verdicts['FAIL']}")
    print(f"  Undisciplined sessions: {discipline_verdicts.get('FAIL', 0)}")
    print(f"  Low-quality prompts: {efficiency_verdicts['FAIL']}")
    print(f"  Incoherent sessions: {coherence_verdicts.get('FAIL', 0)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run judges on Claude Code history")
    parser.add_argument("--history", help="Path to history.jsonl")
    parser.add_argument("--limit", type=int, help="Max sessions to evaluate")
    args = parser.parse_args()

    run_all(history_path=args.history, limit=args.limit)
