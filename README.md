# phoenix-claude-code

Monitor, evaluate, and improve your Claude Code usage with [Arize Phoenix](https://github.com/Arize-ai/phoenix).

```
TRACES --> MONITOR --> ANNOTATE --> JUDGE --> DATASET --> CI --> IMPROVE --> repeat
```

Most people use Claude Code without knowing what's actually happening: which models are called, how many tokens are spent, what errors occur, or whether their prompts are effective. This repo gives you full observability and an eval-driven improvement loop.

## What You Get

- **Full trace capture** — Every LLM call from Claude Code routed through a LiteLLM proxy into Phoenix
- **Usage analysis** — Parse `~/.claude/history.jsonl` for prompt patterns, project breakdown, monthly trends
- **4 automated judges** — Evaluate prompt quality, secret hygiene, session discipline, and topic coherence
- **Error analysis workflow** — Jupyter notebook for manual session review (the highest-ROI activity in AI evals)
- **Golden dataset builder** — Export sessions as annotatable CSV, build your eval dataset from real failures

## Quickstart

```bash
git clone https://github.com/rachittshah/phoenix-claude-code.git
cd phoenix-claude-code
cp .env.example .env
# Edit .env: add your ANTHROPIC_API_KEY

# Start Phoenix + LiteLLM proxy
docker compose up -d

# Install Python package
pip install -e .

# Install Phoenix CLI
npm install -g @arizeai/phoenix-cli
```

Configure Claude Code to route through the proxy:

```bash
# In your shell profile (~/.zshrc)
export ANTHROPIC_BASE_URL=http://localhost:4000
export PHOENIX_HOST=http://localhost:6006
export PHOENIX_PROJECT=claude-code
```

Restart Claude Code. All LLM calls now flow through LiteLLM → Phoenix.

Open Phoenix UI at **http://localhost:6006** to see traces.

## Usage

### Analyze Your Prompt History

```bash
python analysis/history_analyzer.py
```

Output: monthly breakdown, project usage, prompt length trends, command frequency.

### Analyze Phoenix Traces

```bash
python analysis/trace_analyzer.py
```

Output: model usage, error rates, latency stats, token consumption, tool spans.

### Run All Judges

```bash
python scripts/run_judges.py
```

Output: per-judge verdicts across your full history — secret leaks, session discipline violations, low-quality prompts, and incoherent sessions.

### Manual Error Analysis (Recommended First Step)

```bash
jupyter notebook notebooks/error_analysis.ipynb
```

Review sessions one by one. Write open-ended notes. Let patterns emerge. Build judges _after_ you understand your failure modes — not before.

### Build a Golden Dataset

```bash
python analysis/golden_dataset.py
```

Generates a CSV of your recent sessions with columns for manual PASS/FAIL annotation and critique notes. This becomes the foundation for calibrating LLM judges.

## Architecture

```
phoenix-claude-code/
├── docker-compose.yml          # Phoenix + LiteLLM proxy
├── litellm-config.yml          # Model routing + Phoenix callback
├── judges/
│   ├── secret_hygiene.py       # Regex: detect API keys in prompts
│   ├── session_discipline.py   # Session length + context management
│   ├── prompt_efficiency.py    # LLM-as-judge: prompt quality scoring
│   └── topic_coherence.py      # LLM-as-judge: session focus detection
├── analysis/
│   ├── history_analyzer.py     # Parse ~/.claude/history.jsonl
│   ├── trace_analyzer.py       # Analyze Phoenix traces via px CLI
│   └── golden_dataset.py       # Session extraction + annotation CSV
├── notebooks/
│   └── error_analysis.ipynb    # Manual review workflow
└── scripts/
    ├── setup.sh                # One-command setup
    └── run_judges.py           # Run all judges, print report
```

## The Eval Flywheel

This isn't just monitoring — it's a closed improvement loop:

1. **Traces** — Phoenix captures every LLM call. `history.jsonl` captures every user prompt.
2. **Monitor** — Track error rates, token efficiency, model usage over time.
3. **Annotate** — You manually review sessions. PASS/FAIL + open-ended critique.
4. **Judge** — Automated evaluators catch patterns you've identified. Code assertions first, LLM judges second.
5. **Dataset** — Failures auto-promote into your golden eval dataset.
6. **CI** — Gate your `CLAUDE.md` / rules / skills changes against the golden dataset.
7. **Improve** — Every config change has measured impact. No vibes-based optimization.

### Judge Types

| Judge              | Type                       | What It Catches                                      |
| ------------------ | -------------------------- | ---------------------------------------------------- |
| Secret Hygiene     | Deterministic (regex)      | API keys, tokens, credentials in prompts             |
| Session Discipline | Deterministic (thresholds) | Mega-sessions, missing /clear, duplicate commands    |
| Prompt Efficiency  | LLM-as-judge               | Vague prompts, emotional escalation, missing context |
| Topic Coherence    | LLM-as-judge               | Sessions mixing unrelated domains                    |

Each judge returns: `{"verdict": "PASS" | "FAIL", "confidence": float, "reason": str}`

### Using LLM Judges

The prompt efficiency and topic coherence judges support an optional `llm_call` parameter. Pass any function that takes a string prompt and returns a string response:

```python
from judges import judge_prompt_efficiency
import anthropic

client = anthropic.Anthropic()

def llm_call(prompt: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

verdict = judge_prompt_efficiency("fix the bug", llm_call=llm_call)
```

Without `llm_call`, judges use a heuristic fallback (lower confidence, still useful).

## Phoenix CLI Examples

```bash
# Recent traces
px traces --limit 20

# Error traces
px traces --limit 50 --format raw --no-progress | jq '.[] | select(.status == "ERROR")'

# Model usage
px traces --limit 100 --format raw --no-progress | \
  jq -r '.[].spans[] | select(.span_kind == "LLM") | .attributes["llm.model_name"]' | sort | uniq -c

# Slowest traces
px traces --limit 50 --format raw --no-progress | jq 'sort_by(-.duration) | .[0:5]'

# Project stats
px api graphql '{ projects { edges { node { name traceCount tokenCountTotal } } } }'
```

## Methodology

This repo is built on a proven eval methodology:

- **Binary verdicts only** — PASS/FAIL, not Likert scales. Forces clear thinking.
- **Error analysis first** — Review your data manually before building automated judges.
- **One judge per dimension** — No "God Evaluator" that tries to catch everything.
- **Domain expert as decision-maker** — You know your workflow better than any generic benchmark.
- **Calibrate before trusting** — Run judges against your manual annotations. If agreement < 60%, revise the judge.
- **60-80% of time on eval** — The bottleneck is understanding failures, not writing code.

## License

MIT
