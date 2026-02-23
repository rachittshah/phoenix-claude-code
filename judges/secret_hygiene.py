"""Deterministic judge: detects API keys and secrets in prompts."""

import re

SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
    (r"sk-ant-[a-zA-Z0-9]{20,}", "Anthropic API key"),
    (r"sk-proj-[a-zA-Z0-9]{20,}", "OpenAI project key"),
    (r"AIza[a-zA-Z0-9_-]{35}", "Google API key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth token"),
    (r"xoxb-[a-zA-Z0-9-]+", "Slack bot token"),
    (r"xoxp-[a-zA-Z0-9-]+", "Slack user token"),
    (r"AKIA[A-Z0-9]{16}", "AWS access key"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key"),
    (r"eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}", "JWT token"),
]

_compiled = [(re.compile(pattern), label) for pattern, label in SECRET_PATTERNS]


def judge_secret_hygiene(prompt: str) -> dict:
    """Check a prompt for leaked secrets.

    Args:
        prompt: The user's prompt text.

    Returns:
        Verdict dict with PASS/FAIL, confidence, and reason.
    """
    found = []
    for pattern, label in _compiled:
        if pattern.search(prompt):
            found.append(label)

    if found:
        return {
            "verdict": "FAIL",
            "confidence": 0.99,
            "reason": f"Detected: {', '.join(found)}",
        }

    return {"verdict": "PASS", "confidence": 0.95, "reason": "No secrets detected"}
