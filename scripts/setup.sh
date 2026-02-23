#!/usr/bin/env bash
set -euo pipefail

echo "=== phoenix-claude-code setup ==="
echo ""

# 1. Check for required tools
echo "Checking dependencies..."

if ! command -v docker &> /dev/null; then
    echo "  ERROR: docker not found. Install Docker Desktop first."
    exit 1
fi
echo "  docker: $(docker --version | head -1)"

if ! command -v npm &> /dev/null; then
    echo "  WARN: npm not found. Install Node.js to use the Phoenix CLI."
else
    echo "  npm: $(npm --version)"
fi

if ! command -v python3 &> /dev/null; then
    echo "  ERROR: python3 not found."
    exit 1
fi
echo "  python3: $(python3 --version)"

# 2. Install Phoenix CLI
echo ""
echo "Installing Arize Phoenix CLI..."
npm install -g @arizeai/phoenix-cli 2>/dev/null || echo "  WARN: npm install failed. Install manually: npm install -g @arizeai/phoenix-cli"

# 3. Check for .env
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
fi

# 4. Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -e .
else
    pip install -e .
fi

# 5. Start services
echo ""
echo "Starting Phoenix + LiteLLM..."
docker compose up -d

echo ""
echo "Waiting for Phoenix to be healthy..."
for i in {1..30}; do
    if curl -sf http://localhost:6006/healthz > /dev/null 2>&1; then
        echo "  Phoenix is ready at http://localhost:6006"
        break
    fi
    sleep 2
done

# 6. Configure shell
echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. Add to your shell profile (~/.zshrc or ~/.bashrc):"
echo ""
echo '   export PHOENIX_HOST=http://localhost:6006'
echo '   export PHOENIX_PROJECT=claude-code'
echo ""
echo "2. Configure Claude Code to use the LiteLLM proxy:"
echo ""
echo '   In Claude Code settings, set:'
echo '   ANTHROPIC_BASE_URL=http://localhost:4000'
echo ""
echo "3. Run the analysis:"
echo ""
echo '   python analysis/history_analyzer.py    # Analyze your prompt history'
echo '   python analysis/trace_analyzer.py      # Analyze Phoenix traces'
echo '   python scripts/run_judges.py           # Run all judges'
echo '   python analysis/golden_dataset.py      # Generate annotation CSV'
echo ""
echo "4. Open Phoenix UI: http://localhost:6006"
echo ""
echo "=== Setup complete ==="
