"""LLM-as-judge: evaluates whether a session stays focused on one domain."""

import json

EVAL_TEMPLATE = """You are evaluating whether a Claude Code session stayed focused on a single topic/domain or mixed unrelated concerns.

Below are the prompts from a single session (truncated to first 30):

<prompts>
{prompts}
</prompts>

Classify each prompt into a topic category (e.g., "frontend development", "debugging", "git operations", "personal/life", "business strategy", "configuration").

Then determine: does this session stay focused on one domain, or does it mix unrelated topics?

A session PASSES if all prompts relate to the same project/domain.
A session FAILS if it mixes unrelated domains (e.g., debugging code + personal financial planning + business strategy in one session).

Note: related sub-tasks within one project are fine (e.g., "implement feature" then "write tests" then "fix lint" is coherent).

Output ONLY valid JSON (no markdown):
{{"topics": ["topic1", "topic2"], "unique_domains": <int>, "coherent": true | false, "verdict": "PASS" | "FAIL", "reason": "<brief explanation>"}}"""


def judge_topic_coherence(
    session_prompts: list[dict], llm_call: callable = None
) -> dict:
    """Evaluate whether a session stays focused on one domain.

    Args:
        session_prompts: List of prompt dicts from a single session.
        llm_call: A callable that takes a string and returns LLM response text.
            If None, uses a heuristic fallback.

    Returns:
        Verdict dict with PASS/FAIL, confidence, and reason.
    """
    if llm_call is None:
        return _heuristic_fallback(session_prompts)

    prompt_texts = []
    for i, p in enumerate(session_prompts[:30]):
        text = p.get("display", "")[:200]
        prompt_texts.append(f"{i + 1}. {text}")

    eval_prompt = EVAL_TEMPLATE.format(prompts="\n".join(prompt_texts))

    try:
        response = llm_call(eval_prompt)
        result = json.loads(response)

        return {
            "verdict": result.get("verdict", "FAIL"),
            "confidence": 0.75,
            "reason": result.get("reason", ""),
            "topics": result.get("topics", []),
            "unique_domains": result.get("unique_domains", 0),
        }
    except (json.JSONDecodeError, KeyError):
        return _heuristic_fallback(session_prompts)


def _heuristic_fallback(session_prompts: list[dict]) -> dict:
    """Simple heuristic based on project field consistency."""
    projects = set()
    for p in session_prompts:
        proj = p.get("project", "")
        if proj:
            projects.add(proj)

    if len(projects) > 2:
        return {
            "verdict": "FAIL",
            "confidence": 0.60,
            "reason": f"Session spans {len(projects)} different projects",
        }

    return {
        "verdict": "PASS",
        "confidence": 0.60,
        "reason": f"Session uses {len(projects)} project(s) (heuristic)",
    }
