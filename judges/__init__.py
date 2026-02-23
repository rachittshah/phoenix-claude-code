"""Judges for evaluating Claude Code usage quality.

Each judge returns a verdict dict:
    {"verdict": "PASS" | "FAIL", "confidence": float, "reason": str}
"""

from judges.secret_hygiene import judge_secret_hygiene
from judges.session_discipline import judge_session_discipline
from judges.prompt_efficiency import judge_prompt_efficiency
from judges.topic_coherence import judge_topic_coherence

__all__ = [
    "judge_secret_hygiene",
    "judge_session_discipline",
    "judge_prompt_efficiency",
    "judge_topic_coherence",
]
