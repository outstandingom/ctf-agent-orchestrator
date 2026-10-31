#!/usr/bin/env bash
# CTF AI Orchestrator — Automated Launcher & Setup Manager (Linux / macOS)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🛡️  CTF AI Orchestrator — Unified Autonomous Command Center (v2.0)"
echo "========================================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ [ERROR] python3 is not installed or not in PATH."
    exit 1
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "⚠️  [WARNING] git is not installed. Repository cloning will be disabled."
fi

# Launch Setup & Launcher Wizard
if [ -f "scripts/setup_wizard.py" ]; then
    python3 scripts/setup_wizard.py "$@"
else
    echo "🚀 Starting server on http://0.0.0.0:8080..."
    python3 -m uvicorn server:app --host 0.0.0.0 --port 8080
fi
