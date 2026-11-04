#!/usr/bin/env bash
# ========================================================================
# CTF AI Orchestrator — 1-Click Automated Launcher (Linux / macOS / WSL)
# ========================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🛡️  CTF AI Orchestrator — 1-Click Automated Setup & Launch Command Center"
echo "========================================================================"
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ [ERROR] python3 is not installed or not in PATH."
    echo "Please install Python 3.10+ (sudo apt install python3 python3-pip)"
    exit 1
fi

PY_VER=$(python3 --version)
echo "✅ [1/5] Python Environment: $PY_VER"

# 2. Auto-initialize .env if missing
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚙️  [2/5] Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "⚙️  [2/5] Initializing default .env file..."
        cat << 'EOF' > .env
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=qwen/qwen3.8-27b
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DASHBOARD_PORT=8080
HF_VECTOR_URL=https://outstandingom-vector.hf.space
HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=
SUPABASE_URL=https://vtlmgubzcktztkuymtir.supabase.co
SUPABASE_ANON_KEY=
EOF
    fi
else
    echo "✅ [2/5] Environment File: .env found"
fi

# 3. Auto-clone Companion Forensic Engine if missing
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
if [ ! -d "$PARENT_DIR/forensic" ] && [ ! -d "$SCRIPT_DIR/forensic" ]; then
    echo "📥 [3/5] Companion Forensic Engine not detected. Checking git..."
    if command -v git &> /dev/null; then
        echo "       Auto-cloning Forensic Engine into $PARENT_DIR/forensic ..."
        git clone --depth 1 https://github.com/outstandingom/forensic.git "$PARENT_DIR/forensic"
    else
        echo "⚠️     [WARNING] git not found. Place forensic repository at ../forensic manually."
    fi
else
    echo "✅ [3/5] Forensic Engine: Repository present"
fi

# 4. Verify & Install Python Dependencies
echo "📦 [4/5] Verifying dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt --quiet || python3 -m pip install -r requirements.txt

# 5. Launch Command Center
echo ""
echo "========================================================================"
echo "🚀 CTF AI Orchestrator Command Center Live on http://localhost:8080/"
echo "   API Docs: http://localhost:8080/docs"
echo "========================================================================"
echo ""

# Try opening browser if desktop environment is detected
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080/" &> /dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:8080/" &> /dev/null &
fi

python3 -m uvicorn server:app --host 127.0.0.1 --port 8080
