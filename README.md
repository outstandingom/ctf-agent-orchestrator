# 🤖 CTF AI Orchestrator Command Center (v2.0)

An autonomous cybersecurity copilot, CTF solver engine, and real-time command center built for high-stakes cybersecurity competitions (such as **TCS HackQuest, PicoCTF, and Google CTF**).

Combines ultra-fast LPU inference (Groq), automated SMT theorem proving (`z3-solver`), cryptographic analysis (`pycryptodome`, `sympy`), PRNG state recovery (`randcrack`), interactive Netcat TCP probing, and CTFd competition management.

📖 **For the full in-depth user and developer manual, see [COMPLETE_USER_GUIDE.md](docs/COMPLETE_USER_GUIDE.md).**

---

## 🏗️ Architecture & Component Integration

```
                         ┌──────────────────────────────────────────┐
                         │         CTF AI Orchestrator Agent        │
                         │    (Groq Qwen 27B / Claude 3.5 Sonnet)   │
                         └──────────────────┬───────────────────────┘
                                            │
         ┌──────────────────────────────────┼────────────────────────────────────┐
         │                                  │                                    │
         ▼                                  ▼                                    ▼
┌──────────────────┐               ┌──────────────────┐                 ┌──────────────────┐
│ Hugging Face     │               │ Python 3.15      │                 │ Render GitHub    │
│ ZeroGPU RAG      │               │ Sandbox Engine   │                 │ MCP Gateway      │
│ (A10G Space)     │               │ (Z3, PyCrypto)   │                 │ (Remote Micro)   │
└──────────────────┘               └────────┬─────────┘                 └──────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       │                                         │
                       ▼                                         ▼
            ┌──────────────────────┐                  ┌──────────────────────┐
            │ CTFd Autopilot       │                  │ Interactive TCP      │
            │ Manager (REST v1)    │                  │ Netcat Socket Probe  │
            └──────────────────────┘                  └──────────────────────┘
```

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/outstandingom/ctf-agent-orchestrator.git
cd ctf-agent-orchestrator
pip install -r requirements.txt
pip install z3-solver pycryptodome sympy randcrack mpmath
```

### 2. Configuration (.env)

Configure your `.env` file:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b

# Dashboard Port (Default: 8080)
DASHBOARD_PORT=8080

# External Gateways
HF_VECTOR_URL=https://outstandingom-vector.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=outstandingom_mcp_2026hjfbechjbdhjjfbnkqjkj
```

### 3. Launching the Command Center

```bash
# Starts local FastAPI backend + Web Command Center
python server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🌐 Host, Port & Network Configuration

### Changing Port & Host Interface
* **Via Environment Variable**: Set `DASHBOARD_PORT=9000` in `.env` and run `python server.py`.
* **Via Uvicorn CLI**:
  ```powershell
  python -m uvicorn server:app --host 0.0.0.0 --port 8080 --app-dir .
  ```
  * `host 127.0.0.1`: Binds locally (accessible only from your machine).
  * `host 0.0.0.0`: Binds to all network interfaces (accessible to your local network / LAN).

### Resolving Port Conflicts (Errno 10048)
If port 8080 is already in use:
```powershell
# PowerShell: Find and kill the conflicting process
$p = (Get-NetTCPConnection -LocalPort 8080).OwningProcess
Stop-Process -Id $p -Force
```

---

## 🎯 Competition Playbooks

### Standard CTFd Competitions (TCS HackQuest, PicoCTF)
1. Open the **🏆 CTFd Autopilot & Netcat** tab.
2. Enter the CTFd URL and your user API token (`ctfd_...`).
3. Click **Fetch Challenges** to populate your competition queue.
4. Click **🤖 Solve** to ingest challenge details, solve via SMT/crypto sandbox, and submit flags automatically.

### Google CTF & Proprietary Platforms
1. Join your team in your browser: `https://capturetheflag.withgoogle.com/team/loki` (Access Key: `-P5G9PyOgiLko9eg5WzD`).
2. For remote socket challenges (`nc host port`), probe them directly in the **Interactive Socket Probe** terminal.
3. For math, crypto, or reverse engineering, paste prompts into **🤖 Agent Mission Control** to solve with `z3-solver` and extract `CTF{...}` flags.

---

## 🔒 Security & Safe Execution
* All exploit verification runs inside local memory sandboxes.
* Remote GitHub operations are protected via 2-Step Verification Lock on the Render MCP Gateway.
* Automatic Groq model rotation prevents 429 rate limit errors during multi-turn agent loops.

---

*Authored by Om Uikey — CTF AI Orchestrator Core Maintainer*
