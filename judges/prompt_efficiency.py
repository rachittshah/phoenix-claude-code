"""LLM-as-judge: evaluates prompt quality and efficiency."""

import json

EVAL_TEMPLATE = """You are evaluating the quality of a prompt sent to an AI coding assistant (Claude Code).

<prompt>
{prompt}
</prompt>

Rate on these dimensions:

1. **Specificity** (1-5): Does it include file paths, expected behavior, constraints, or acceptance criteria?
   - 1: Completely vague ("fix it")
   - 3: Some context but missing key details
   - 5: Exact files, expected behavior, and success criteria specified

2. **Emotional regulation** (PASS/FAIL): Is the prompt professional and productive?
   - FAIL if it contains profanity, insults, or frustrated outbursts that waste tokens
   - PASS if focused on the technical problem

3. **Context provision** (1-5): Does it provide error logs, current state, or what was already tried?
   - 1: No context at all
   - 3: Some context but incomplete
   - 5: Full error output, current state, and prior attempts documented

Output ONLY valid JSON (no markdown):
{{"specificity": <int 1-5>, "emotional": "PASS" | "FAIL", "context": <int 1-5>, "overall": "PASS" | "FAIL"}}

The overall verdict is FAIL if specificity < 3 OR emotional = FAIL OR context < 2."""


def judge_prompt_efficiency(prompt: str, llm_call: callable = None) -> dict:
    """Evaluate prompt quality using an LLM judge.

    Args:
        prompt: The user's prompt text.
        llm_call: A callable that takes a string prompt and returns the LLM's
            response text. If None, uses a simple heuristic fallback.

    Returns:
        Verdict dict with PASS/FAIL, confidence, and reason.
    """
    if llm_call is None:
        return _heuristic_fallback(prompt)

    eval_prompt = EVAL_TEMPLATE.format(prompt=prompt[:2000])

    try:
        response = llm_call(eval_prompt)
        result = json.loads(response)

        verdict = result.get("overall", "FAIL")
        specificity = result.get("specificity", 1)
        emotional = result.get("emotional", "FAIL")
        context_score = result.get("context", 1)

        reasons = []
        if specificity < 3:
            reasons.append(f"Low specificity ({specificity}/5)")
        if emotional == "FAIL":
            reasons.append("Emotional escalation detected")
        if context_score < 2:
            reasons.append(f"Insufficient context ({context_score}/5)")

        return {
            "verdict": verdict,
            "confidence": 0.80,
            "reason": "; ".join(reasons) if reasons else "Prompt is well-structured",
            "scores": {
                "specificity": specificity,
                "emotional": emotional,
                "context": context_score,
            },
        }
    except (json.JSONDecodeError, KeyError):
        return _heuristic_fallback(prompt)


def _heuristic_fallback(prompt: str) -> dict:
    """Simple heuristic when no LLM is available."""
    issues = []

    if len(prompt) < 20:
        issues.append("Very short prompt")
    if not any(c in prompt for c in ["/", ".", "src", "def ", "function ", "class "]):
        issues.append("No file/code references")

    profanity_markers = ["fuck", "shit", "damn", "wtf", "stupid"]
    if any(word in prompt.lower() for word in profanity_markers):
        issues.append("Emotional language detected")

    if issues:
        return {
            "verdict": "FAIL",
            "confidence": 0.60,
            "reason": "; ".join(issues),
        }

    return {
        "verdict": "PASS",
        "confidence": 0.60,
        "reason": "Heuristic check passed (use LLM judge for higher accuracy)",
    }
