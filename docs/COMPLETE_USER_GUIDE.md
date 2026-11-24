# 🛡️ CTF AI Orchestrator — Complete Operational Manual & System Guide

Welcome to the definitive user and developer documentation for the **CTF AI Orchestrator Command Center (v2.0)**. This guide covers everything from environment setup, host and port networking configuration, dashboard modules, exploit engines, and solver workflows to step-by-step competition playbooks for **TCS HackQuest, CTFd platforms, and Google CTF**.

---

## 📑 Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Host, Port & Network Configuration](#2-host-port--network-configuration)
   - [Default Ports and Endpoints](#default-ports-and-endpoints)
   - [How to Change Host & Port](#how-to-change-host--port)
   - [Finding & Killing Port Conflicts (Errno 10048)](#finding--killing-port-conflicts-errno-10048)
   - [Localhost vs. Vercel Cloud Execution](#localhost-vs-vercel-cloud-execution)
3. [Environment Configuration (.env)](#3-environment-configuration-env)
4. [Prerequisites & Solver Libraries](#4-prerequisites--solver-libraries)
5. [Dashboard Features & Module Walkthrough](#5-dashboard-features--module-walkthrough)
   - [🤖 Agent Mission Control](#-agent-mission-control)
   - [🚀 Dynamic Fuzzing & Z3 SMT Studio](#-dynamic-fuzzing--z3-smt-studio)
   - [🐧 WSL2 Linux Subsystem Bridge](#-wsl2-linux-subsystem-bridge)
   - [💻 Exploit Code Reviewer & Live Sandbox Studio](#-exploit-code-reviewer--live-sandbox-studio)
   - [🧬 Vector RAG Explorer & DNA Knowledge Graph](#-vector-rag-explorer--dna-knowledge-graph)
   - [🔍 Forensics Sandbox Engine (PCAP & Stego)](#-forensics-sandbox-engine-pcap--stego)
   - [🐙 GitHub Lifetime MCP Gateway](#-github-lifetime-mcp-gateway)
   - [🏆 CTFd Autopilot & Netcat Terminal](#-ctfd-autopilot--netcat-terminal)
6. [Ponytail Token Engine & Rate-Limit Optimization](#6-ponytail-token-engine--rate-limit-optimization)
7. [Competition Playbooks](#7-competition-playbooks)
   - [Playbook 1: Standard CTFd Competitions (TCS HackQuest, PicoCTF)](#playbook-1-standard-ctfd-competitions-tcs-hackquest-picoctf)
   - [Playbook 2: Google CTF & Proprietary Platforms](#playbook-2-google-ctf--proprietary-platforms)
8. [API Reference](#8-api-reference)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. System Architecture Overview

The system operates as a unified cyber command center combining fast LPU cloud reasoning, local sandboxed execution, real-time SMT math solving, dynamic endpoint fuzzing, and external Git integration:

```mermaid
flowchart TD
    User["Cyber Operator / Player"] -->|Browser UI| Dash["Web Command Center (http://localhost:8080)"]
    Dash -->|REST / SSE Streams| Fast["FastAPI Core Orchestrator (server.py)"]
    
    subgraph Reasoning & Optimization
        Fast -->|Lean Tool Router (Ponytail)| Router["Dynamic Domain Tool Selector (-75% Tokens)"]
        Router -->|Fast LPU Inference| Groq["Groq API (Qwen 27B / GPT-OSS 120B / 20B)"]
        Router -->|Deep Reasoning| Claude["Anthropic Claude 3.5 Sonnet"]
        Fast -->|Writeup Similarity| HFSpace["Hugging Face ZeroGPU Vector Space"]
        Fast -->|Semantic Attack Tree| DNA["DNA Knowledge Graph Space"]
    end
    
    subgraph Execution & Exploitation
        Fast -->|Differential Analysis| Fuzzer["Dynamic Web Fuzzer (SQLi, SSTI, CmdInj, Traversal)"]
        Fast -->|BitVec Constraint Solving| Z3SMT["Z3 SMT Symbolic Execution Solver"]
        Fast -->|ELF / Linux Shell| WSL["WSL2 Linux Bridge (checksec, gdb, python3)"]
        Fast -->|Math / Crypto Sandbox| Sandbox["Python 3.15 Sandbox Engine (z3, sympy, pycrypto, randcrack)"]
        Fast -->|Multi-Threading| Workers["4x Parallel Exploit Worker Pool"]
        Fast -->|Raw TCP Streams| Netcat["Interactive Socket Client (socket)"]
        Fast -->|Network & File Carving| Forensic["Forensic Engine (Scapy PCAP, LSB, ZIP, Strings)"]
    end
    
    subgraph External Platforms
        Fast -->|REST API v1| CTFd["CTFd Platform (TCS HackQuest / CTFd.io)"]
        Fast -->|Lifetime Gateway| MCP["Render GitHub MCP Server"]
        MCP -->|Push / Read| GH["GitHub Repositories"]
    end
```

---

## 2. Host, Port & Network Configuration

### Default Ports and Endpoints

| Service | Host | Port | Endpoint URL | Role |
| :--- | :--- | :---: | :--- | :--- |
| **CTF Command Center Dashboard** | `0.0.0.0` | **`8080`** | `http://localhost:8080` | Main User Interface & REST API Gateway |
| **Local Writeup Vector RAG** | `127.0.0.1` | `8001` | `http://localhost:8001` | Local FastEmbed Vector Store fallback |
| **Render GitHub MCP Gateway** | Remote | `443` | `https://mcp-server-2sl7.onrender.com` | Microservice for persistent GitHub operations |
| **ZeroGPU Vector Space** | Remote | `443` | `https://outstandingom-vector.hf.space` | A10G Cloud Knowledge Base for Writeups |
| **DNA Knowledge Graph** | Remote | `443` | `https://outstandingom-knowledge-graph-env.hf.space` | Semantic Cyber Threat Graph & Attack Trees |

### How to Change Host & Port

By default, the server binds to `0.0.0.0` on port `8080`. To change the port:

1. Open `.env` and set:
   ```env
   DASHBOARD_PORT=9000
   ```
2. Or pass it directly from the terminal:
   ```powershell
   $env:DASHBOARD_PORT="9000"; python server.py
   ```

### Finding & Killing Port Conflicts (Errno 10048 / WinError 10013)

If you see:
```text
[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8080): only one usage of each socket address is normally permitted
```

Run in PowerShell:
```powershell
# 1. Identify which PID is holding port 8080:
netstat -ano | findstr :8080

# 2. Terminate the blocking process:
taskkill /F /PID <PID>
```

---

## 3. Environment Configuration (.env)

The orchestrator reads settings from [`c:\Users\SGI\Downloads\ctf-agent-orchestrator\.env`](file:///c:/Users/SGI/Downloads/ctf-agent-orchestrator/.env):

```env
# ─── LLM Provider (groq or anthropic) ─────────────────────────────────
LLM_PROVIDER=groq

# ─── Groq Configuration (Ultra-fast LPU inference) ────────────────────
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b

# ─── Anthropic Claude 3.5 Sonnet (Deep Strategic Planning) ────────────
ANTHROPIC_API_KEY=sk-ant-your_claude_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# ─── Knowledge RAG & ZeroGPU Spaces ───────────────────────────────────
RAG_URL=http://localhost:8001
HF_VECTOR_URL=https://outstandingom-vector.hf.space
HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space

# ─── Render Lifetime GitHub MCP Server Gateway ────────────────────────
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=your_mcp_gateway_key_here

# ─── Supabase Session Persistence ─────────────────────────────────────
SUPABASE_URL=https://vtlmgubzcktztkuymtir.supabase.co
SUPABASE_ANON_KEY=sb_publishable_your_key_here

# ─── Local Dashboard Network Settings ─────────────────────────────────
DASHBOARD_PORT=8080
FORENSIC_DIR=c:\Users\SGI\Downloads\forensic
```

---

## 4. Prerequisites & Solver Libraries

```bash
pip install fastapi uvicorn requests python-dotenv openai anthropic pydantic
pip install z3-solver pycryptodome sympy randcrack mpmath scapy
```

* **`z3-solver`**: SMT solver for solving crackmes, bitwise XOR equations, modular arithmetic, and branch conditions.
* **`pycryptodome`**: AES, RSA, DES, ECC, ARC4, and hashing implementations.
* **`sympy`**: Fast prime testing, modular inverses, discrete logarithms, and polynomial factorization.
* **`randcrack`**: Recovers internal 624-integer state of Python's Mersenne Twister (`random` module) from 624 consecutive outputs.
* **`scapy`**: Dissects `.pcap` and `.pcapng` network capture streams, carves multipart files, and analyzes DNS tunnels.

---

## 5. Dashboard Features & Module Walkthrough

Open **`http://localhost:8080`** to access all modules:

### 🤖 Agent Mission Control
* **Autonomous Multi-Turn Solver**: Ingests challenge descriptions, plans reasoning turns, calls specialized tools, verifies code in the sandbox, self-corrects on errors, and extracts the flag.
* **Multi-Model Rotation**: Rotates across `qwen/qwen3.8-27b`, `openai/gpt-oss-120b`, and `openai/gpt-oss-20b` with backoff.

### 🚀 Dynamic Fuzzing & Z3 SMT Studio
* **Dynamic Web Fuzzer (`POST /api/fuzz/scan`)**:
  * Input target URL, attack category (SQLi, SSTI, Command Injection, Path Traversal, Auth Bypass, IDOR), method (GET/POST), and parameter.
  * Queries ZeroGPU Vector RAG and DNA Graph for high-potency payloads.
  * Executes multi-threaded differential testing measuring status codes, length variance, $\Delta t > 2.0\text{s}$ blind injection time delays, error disclosures, and flag patterns (`HQX{...}`, `flag{...}`).
  * Auto-syncs discovered vulnerabilities to the DNA Knowledge Graph.
* **Z3 Symbolic SMT Solver (`POST /api/symbolic/solve`)**:
  * Input equations or Python constraints (e.g. `flag[0] ^ 0x42 == 100; flag[1] + 10 == 75`).
  * Formulates BitVec expressions, executes `z3.Solver()` in sandboxed memory, and outputs SAT models + auto-decoded ASCII strings.

### 🐧 WSL2 Linux Subsystem Bridge (`POST /api/wsl/exec`)
* Executes Linux terminal commands, `checksec --file=./vuln`, `readelf`, strings, and Python pwntools scripts directly in native WSL2 Ubuntu.
* Automatically reports distro availability or provides single-line activation commands (`wsl --install -d Ubuntu`).

### 💻 Exploit Code Reviewer & Live Sandbox Studio
* **Live Python Sandbox**: Edit and execute any Python solver script directly in browser.
* **👥 4x Parallel Workers**: Executes multiple exploit candidates concurrently with auto-flag extraction.

### 🧬 Vector RAG Explorer & DNA Knowledge Graph
* Connects directly to Hugging Face ZeroGPU A10G Space and DNA Knowledge Graph.
* Search across hundreds of verified past CTF writeups by category (**Cryptography, Forensics, Web, Binary Exploitation**).

### 🔍 Forensics Sandbox Engine (PCAP & Stego)
* **PCAP / PCAPNG Network Traffic Stream Dissector**: Reassembles TCP streams, carves multipart files (`filename="..."`), extracts HTTP Basic/Bearer auth tokens, and detects DNS query exfiltration.
* **LSB Steganography**: Carves embedded data from PNG/BMP bitplanes.
* **PK ZIP Header Carving**: Scans raw binary streams for `\x50\x4B\x03\x04` signatures.

### 🐙 GitHub Lifetime MCP Gateway
* Bridge to [`https://mcp-server-2sl7.onrender.com`](https://mcp-server-2sl7.onrender.com).
* List repositories, read files, and commit verified exploit scripts directly to GitHub (`POST /api/github/commit`).

### 🏆 CTFd Autopilot & Netcat Terminal
* **CTFd Challenge Manager**: Connects to any standard CTFd instance, fetches challenges, solves them autonomously, and submits flags.
* **Interactive TCP / Netcat Socket Probe**: Probes raw TCP ports (`nc <host> <port>`), reads server banners, sends interactive text or hex payloads (`hex:414141...`), and extracts flags.

---

## 6. Ponytail Token Engine & Rate-Limit Optimization

To eliminate Groq free-tier rate limits (7,000 Input Tokens Per Minute):
* **Lean Domain Tool Selector (`select_relevant_tools`)**: Dynamically filters tool schemas so only 4–5 tools relevant to the challenge domain are sent. Reduces schema token payload from **2,687 tokens down to 664 tokens (-75.3%)**.
* **Context History Pruning**: Caps prior tool outputs in message history to 1,000 characters, preventing prompt growth over multi-turn reasoning.
* **Result**: Turn execution latency dropped from **133.7s down to 46.5s (65.2% speedup)** with zero 429 rate-limit pauses.

---

## 7. Competition Playbooks

### Playbook 1: Standard CTFd Competitions (TCS HackQuest, PicoCTF)
1. In CTFd under **Settings -> Access Tokens**, generate an API token (`ctfd_...`).
2. Open **🏆 CTFd Autopilot & Netcat** on `http://localhost:8080`.
3. Enter URL and Token, click **Fetch Challenges**.
4. Click **🤖 Solve** on any challenge: the agent ingests details, queries RAG, solves in sandbox, and auto-submits the flag!

### Playbook 2: Google CTF & Proprietary Platforms
1. Join your team in browser: `https://capturetheflag.withgoogle.com/team/loki` (use your own authorized team access key; do not store it in source control).
2. **For Web Challenges**: Use **🚀 Dynamic Fuzzing & Z3 SMT** tab to run differential fuzzing or client-side timer bypass (`localStorage.setItem('timer_completed', 'true'); fetch('/flag')`).
3. **For PRNG / Crypto Challenges**: Paste description into **🤖 Agent Mission Control** to retrieve the PRNG time-seed pattern and crack the XOR stream.
4. **For Netcat Socket Targets**: Connect via **Interactive Socket Probe** on `http://localhost:8080`.
5. Copy the recovered flag and submit it on the Google CTF portal.

---

## 8. API Reference

All backend capabilities are exposed via REST API on `http://127.0.0.1:8080`:

| Method | Endpoint | Request Body | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/status` | None | Real-time health and latency of all services |
| `POST`| `/api/solve` | `{"prompt": "...", "provider": "groq"}` | Runs full autonomous agent loop |
| `POST`| `/api/solve/stream` | `{"prompt": "...", "provider": "groq"}` | Real-time Server-Sent Events (SSE) streaming |
| `POST`| `/api/fuzz/scan` | `{"target_url": "...", "category": "SQLi"}` | Runs vector-guided dynamic web fuzzer |
| `POST`| `/api/symbolic/solve`| `{"constraints": "flag[0] ^ 0x42 == 100", "length": 1}` | Solves equations with Z3 SMT engine |
| `POST`| `/api/wsl/exec` | `{"command": "uname -a", "timeout_seconds": 15}` | Executes Linux command via WSL2 bridge |
| `POST`| `/api/rag/search` | `{"query": "...", "domain": "Cryptography"}` | Queries HF ZeroGPU vector database |
| `POST`| `/api/forensics/scan`| `{"file_path": "...", "text": "..."}` | Runs forensic extractors, PCAP analyzer, and flag regex |
| `GET` | `/api/github/repos` | None | Returns GitHub repositories via Render MCP |
| `POST`| `/api/github/commit`| `{"repo": "...", "path": "...", "content": "..."}` | Commits file to GitHub |
| `POST`| `/api/ctfd` | `{"action": "list_challenges", "ctfd_url": "..."}` | Interacts with CTFd platform |
| `POST`| `/api/socket/probe` | `{"host": "...", "port": 1337, "payload": "..."}` | Probes raw TCP netcat socket |
| `POST`| `/api/sandbox/run` | `{"code": "print(1+1)", "timeout_seconds": 10}` | Executes Python code in sandbox |
| `POST`| `/api/sandbox/parallel`| `{"scripts": ["code1", "code2"]}` | Runs concurrent worker pool |

---

## 9. Troubleshooting & FAQs

#### Q1: Why do I get "Unauthorized" on Vercel (`https://ctf-agent-orchestrator.vercel.app`)?
* **Answer**: Vercel hosts the static HTML dashboard. Open your local command center at **`http://localhost:8080`** for full local sandbox execution, Z3 solving, and raw network sockets.

#### Q2: How do I fix "Windows Defender blocked a file" ([Errno 22])?
* **Answer**: Windows Defender flags raw reverse shells written to disk. All exploit templates are sanitized in-memory or executed inside safe sandbox environments. Avoid saving raw reverse shells to `.py` files on Windows.

#### Q3: What if Groq hits Rate Limit (Error 429)?
* **Answer**: The Ponytail lean tool selector slashes schema tokens by 75.3%, keeping requests under the 7,000 ITPM limit. If a limit is reached, automatic multi-model rotation switches to `openai/gpt-oss-120b` or `openai/gpt-oss-20b`.

#### Q4: How do I test Linux ELF binary challenges on Windows?
* **Answer**: Use the **WSL2 Linux Bridge** tab or call `/api/wsl/exec`. If WSL is not installed, run `wsl --install -d Ubuntu` in PowerShell once.

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
