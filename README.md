# 🤖 CTF AI Orchestrator Command Center (v2.0)

An autonomous cybersecurity copilot, CTF solver engine, and real-time command center built for high-stakes cybersecurity competitions (such as **TCS HackQuest, PicoCTF, and Google CTF**).

Combines ultra-fast LPU inference (Groq), automated SMT theorem proving (`z3-solver`), dynamic web fuzzing with differential testing, cryptographic analysis (`pycryptodome`, `sympy`), PRNG state recovery (`randcrack`), network PCAP stream carving (`scapy`), WSL2 Linux binary analysis, and CTFd competition management.

📖 **For the full in-depth user and developer manual, see [COMPLETE_USER_GUIDE.md](docs/COMPLETE_USER_GUIDE.md).**

---

## 🏗️ Architecture & Component Integration

```
                         ┌──────────────────────────────────────────┐
                         │         CTF AI Orchestrator Agent        │
                         │    (Groq Qwen 27B / Claude 3.5 Sonnet)   │
                         └──────────────────┬───────────────────────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        │   Ponytail Lean Domain Tool Selector  │
                        │   (-75.3% Schema Token Reduction)     │
                        └───────────────────┬───────────────────┘
                                            │
         ┌──────────────────────────────────┼────────────────────────────────────┐
         │                                  │                                    │
         ▼                                  ▼                                    ▼
┌──────────────────┐               ┌──────────────────┐                 ┌──────────────────┐
│ Hugging Face     │               │ Python 3.15      │                 │ Render GitHub    │
│ ZeroGPU RAG      │               │ Sandbox Engine   │                 │ MCP Gateway      │
│ & DNA Graph      │               │ (Z3, PyCrypto)   │                 │ (Remote Micro)   │
└──────────────────┘               └────────┬─────────┘                 └──────────────────┘
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          │                                 │                                 │
          ▼                                 ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐          ┌──────────────────────┐
│ Dynamic Web Fuzzer   │         │ Z3 SMT Symbolic      │          │ WSL2 Linux Subsystem │
│ (SQLi, SSTI, CmdInj) │         │ Crackme Solver       │          │ Bridge (checksec)    │
└──────────────────────┘         └──────────────────────┘          └──────────────────────┘
          │                                 │                                 │
          ▼                                 ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐          ┌──────────────────────┐
│ CTFd Autopilot       │         │ Interactive TCP      │          │ Forensics Engine     │
│ Manager (REST v1)    │         │ Netcat Socket Probe  │          │ (Scapy PCAP + Stego) │
└──────────────────────┘         └──────────────────────┘          └──────────────────────┘
```

---

## 🚀 Key Engines & Capabilities

1. **🚀 Dynamic Web Fuzzing Engine (`web_dynamic_fuzzer`)**:
   - Differential baseline testing for SQLi, SSTI, Command Injection, Path Traversal, Auth Bypass, and IDOR.
   - Detects timing delays ($\Delta t > 2.0\text{s}$), response length variances, and leaks.
   - Automatically queries ZeroGPU Vector RAG and syncs findings to the DNA Knowledge Graph.
2. **🧮 Z3 Symbolic SMT Solver (`symbolic_execution_solver`)**:
   - Solves crackme branch conditions, bitwise XOR equations, and modular arithmetic in `<0.6s`.
   - Automatically decodes BitVec byte constraints into printable ASCII flag strings.
3. **🐧 WSL2 Linux Subsystem Bridge (`wsl_linux_bridge`)**:
   - Directly executes `checksec`, `readelf`, strings, and Linux exploit scripts in native WSL2 Ubuntu.
4. **🔍 Forensic Network Dissector (`pcap_analyzer.py`)**:
   - Reassembles TCP streams, carves multipart file uploads, extracts HTTP Basic/Bearer auth tokens, and detects DNS query exfiltration using Scapy.
5. **⚡ Ponytail Token Optimization Engine**:
   - Dynamic domain tool selection slashes schema tokens from **2,687 down to 664 tokens (-75.3%)**.
   - Solves multi-turn challenges in **46 seconds** (65.2% faster) with zero Groq 429 rate limit delays.

---

## ⚡ Quickstart

### 1. Installation

```bash
git clone https://github.com/outstandingom/ctf-agent-orchestrator.git
cd ctf-agent-orchestrator
pip install -r requirements.txt
pip install z3-solver pycryptodome sympy randcrack mpmath scapy
```

### 2. Configuration (.env)

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b
DASHBOARD_PORT=8080

# External Gateways
HF_VECTOR_URL=https://outstandingom-vector.hf.space
HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=outstandingom_mcp_2026hjfbechjbdhjjfbnkqjkj
```

### 3. Launching the Command Center

```bash
# Windows 1-Click Launcher
start.bat

# Or manual startup
python server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🎯 Verified Test Playbooks

* **Google CTF Web Preset (Client-Side Timer Bypass)**:
  ```bash
  python scripts/test_google_ctf_preset.py
  ```
* **Google CTF Cryptography Preset (PRNG Time-Seed Cracker)**:
  ```bash
  python scripts/test_google_ctf_crypto.py
  ```

---

*Authored by Om Uikey — CTF AI Orchestrator Core Maintainer*

---

## 🛠️ Autonomous SWE & Full-Stack Deployment Studio

In addition to cybersecurity CTF operations, the platform now functions as an **Autonomous Software Engineering (SWE) and Deployment Agent** capable of analyzing codebases, applying non-destructive surgical patches, executing full-stack build/test verification, and orchestrating safe Git pull-request workflows from a single prompt:

### 1. The "Full-File Overwrite" Flaw Eliminated (`patch_file_diff`)
* **The Problem**: Conventional AI agents overwrite whole 600+ line files when fixing a minor bug (e.g. CORS configuration), routinely dropping helper functions or truncating middle code blocks (`# ... rest of code remains the same`).
* **The Solution**: The engine emits targeted **Search-and-Replace Blocks**:
  ```json
  {
    "path": "server.py",
    "search": "allow_origins=['*']",
    "replace": "allow_origins=os.getenv('CORS_ORIGINS', '*').split(',')",
    "branch": "ai/fix-cors-wildcard",
    "commit_message": "fix(cors): restrict wildcard origins to environment configuration"
  }
  ```
  The patch engine validates exact matching of whitespace, indentation, and characters before applying changes, guaranteeing complete preservation of surrounding code.

### 2. Direct-to-Main Git Hazard Eliminated (`create_github_branch` & `create_github_pr`)
* **The Problem**: Autonomous agents committing directly to `main` break live production environments and trigger broken CI/CD pipelines.
* **The Solution**: Safe GitHub engineering workflows via the Render MCP Gateway:
  1. Auto-create isolated feature branch: `create_github_branch(branch="ai/fix-cors-42")`
  2. Apply non-destructive patch to the branch: `patch_file_diff(...)`
  3. Run local build and regression tests in the sandbox.
  4. Open a Pull Request with summary and test verification logs: `create_github_pr(...)`

### 3. Persistent Full-Stack Terminal & Build Sandbox (`run_fullstack_terminal`)
* Generalizes beyond simple single-script Python runs to persistent terminal execution across modern technology stacks:
  * **Frontend & Asset Builds**: `npm install`, `npm run build`, `vite build`
  * **Database Migrations**: `alembic upgrade head`, `npx prisma db push`
  * **Test Suites & Quality Checks**: `pytest tests/ -v`, `npm test`
  * **Container Management**: `docker-compose up -d`, `docker ps`
  * Captures exit codes, stdout, stderr, execution duration, and supports custom working directory (`cwd`).

### 4. Codebase Architecture Memory (DNA Knowledge Graph)
* Tracks architectural relationships, API routes, database schemas, and cloud deployment mappings using the Hugging Face DNA Knowledge Graph (`https://outstandingom-knowledge-graph-env.hf.space`):
  * `Component -> Imports -> Module`
  * `Endpoint -> HandledBy -> Controller`
  * `Service -> DeployedOn -> Vercel/Render`
* Exposes `sync_codebase_memory` and `query_codebase_memory` with instant local persistent fallback so project context is remembered across multi-turn sessions.
