"""Deterministic judge: evaluates session length and context management."""


def judge_session_discipline(session_prompts: list[dict]) -> dict:
    """Check whether a session stayed within reasonable bounds.

    Args:
        session_prompts: List of prompt dicts from a single session.
            Each dict should have at least a "display" key.

    Returns:
        Verdict dict with PASS/FAIL/WARN, confidence, and reason.
    """
    count = len(session_prompts)
    clears = sum(
        1
        for p in session_prompts
        if "/clear" in p.get("display", "") or "/compact" in p.get("display", "")
    )
    duplicates = _count_duplicate_commands(session_prompts)

    reasons = []

    if count > 100:
        reasons.append(f"Session has {count} prompts (limit: 100)")
    if duplicates > 10:
        reasons.append(f"{duplicates} duplicate/repeated commands")
    if count > 50 and clears == 0:
        reasons.append(f"{count} prompts without any /clear")

    if any("limit: 100" in r for r in reasons):
        return {
            "verdict": "FAIL",
            "confidence": 0.95,
            "reason": "; ".join(reasons),
        }

    if reasons:
        return {
            "verdict": "FAIL",
            "confidence": 0.80,
            "reason": "; ".join(reasons),
        }

    return {
        "verdict": "PASS",
        "confidence": 0.90,
        "reason": f"Session: {count} prompts, {clears} clears",
    }


def _count_duplicate_commands(prompts: list[dict]) -> int:
    """Count consecutive duplicate prompts (e.g., triple-fired /clear)."""
    dupes = 0
    prev = None
    for p in prompts:
        text = p.get("display", "").strip()
        if text and text == prev:
            dupes += 1
        prev = text
    return dupes
