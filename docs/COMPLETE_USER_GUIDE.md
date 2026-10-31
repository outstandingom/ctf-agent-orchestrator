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
   - [💻 Exploit Code Reviewer & Live Sandbox Studio](#-exploit-code-reviewer--live-sandbox-studio)
   - [🧬 Vector RAG Explorer](#-vector-rag-explorer)
   - [🔍 Forensics Sandbox Engine](#-forensics-sandbox-engine)
   - [🐙 GitHub Lifetime MCP Gateway](#-github-lifetime-mcp-gateway)
   - [🏆 CTFd Autopilot & Netcat Terminal](#-ctfd-autopilot--netcat-terminal)
6. [Competition Playbooks](#6-competition-playbooks)
   - [Playbook 1: Standard CTFd Competitions (TCS HackQuest, PicoCTF)](#playbook-1-standard-ctfd-competitions-tcs-hackquest-picoctf)
   - [Playbook 2: Google CTF & Proprietary Platforms](#playbook-2-google-ctf--proprietary-platforms)
7. [API Reference](#7-api-reference)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. System Architecture Overview

The system operates as a unified cyber command center combining fast LPU cloud reasoning, local sandboxed execution, real-time SMT math solving, and external Git integration:

```mermaid
flowchart TD
    User["Cyber Operator / Player"] -->|Browser UI| Dash["Web Command Center (http://localhost:8080)"]
    Dash -->|REST / SSE Streams| Fast["FastAPI Core Orchestrator (server.py)"]
    
    subgraph Reasoning & Retrieval
        Fast -->|Fast LPU Inference| Groq["Groq API (Qwen 27B / GPT-OSS 120B / 20B)"]
        Fast -->|Deep Reasoning| Claude["Anthropic Claude 3.5 Sonnet"]
        Fast -->|Writeup Similarity| HFSpace["Hugging Face ZeroGPU Vector Space"]
        Fast -->|Semantic Attack Tree| DNA["DNA Knowledge Graph Space"]
    end
    
    subgraph Execution & Exploitation
        Fast -->|Math / Crypto / SMT| Sandbox["Python 3.15 Sandbox Engine (z3, sympy, pycryptodome, randcrack)"]
        Fast -->|Multi-Threading| Workers["4x Parallel Exploit Worker Pool"]
        Fast -->|Raw TCP Streams| Netcat["Interactive Socket Client (socket)"]
        Fast -->|Carving & Stego| Forensic["Forensic Engine (LSB, PK-ZIP, Strings)"]
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

| Service | Host | Port | URL | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Command Center** | `0.0.0.0` | `8080` | `http://localhost:8080` | Main FastAPI app + UI dashboard |
| **Local Vector RAG** | `127.0.0.1` | `8001` | `http://localhost:8001` | Optional local vector retrieval engine |
| **Render MCP Gateway**| Remote | `443` | `https://mcp-server-2sl7.onrender.com` | Live GitHub MCP microservice |
| **Hugging Face Space**| Remote | `443` | `https://outstandingom-vector.hf.space` | ZeroGPU A10G semantic vector space |

---

### How to Change Host & Port

You can run the server on any custom port or interface using three different methods:

#### Method A: Environment Variable (Recommended)
Add or edit `DASHBOARD_PORT` in your `.env` file:
```env
DASHBOARD_PORT=9000
```
Then launch:
```bash
python server.py
```

#### Method B: Direct Uvicorn CLI
Run uvicorn directly from terminal, specifying `--host` and `--port`:
```powershell
# Run locally on port 5000:
python -m uvicorn server:app --host 127.0.0.1 --port 5000 --app-dir c:\Users\SGI\Downloads\ctf-agent-orchestrator

# Run accessible to all network devices (LAN):
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --app-dir c:\Users\SGI\Downloads\ctf-agent-orchestrator
```

#### Method C: Behind a Reverse Proxy (Nginx / Cloudflare Tunnel)
If binding behind Nginx or Cloudflare Tunnel:
```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

### Finding & Killing Port Conflicts (Errno 10048)

If you see:
```text
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8080): 
only one usage of each socket address is normally permitted
```
An existing Python process is already holding port 8080.

#### On Windows (PowerShell):
```powershell
# 1. Identify which process ID (PID) is listening on port 8080:
Get-NetTCPConnection -LocalPort 8080 | Select-Object OwningProcess, State

# 2. Check the process name:
Get-Process -Id <PID>

# 3. Kill the conflicting process immediately:
Stop-Process -Id <PID> -Force
```

#### On Linux / macOS:
```bash
# Find PID
lsof -i :8080
# Kill process
kill -9 <PID>
```

---

### Localhost vs. Vercel Cloud Execution

* **`http://localhost:8080` (Local Backend)**:
  Contains the **full autonomous engine**. It has direct access to your local Python environment, C++ binaries (`z3-solver`, `pycryptodome`), raw TCP network sockets, local files, and forensic engines.
* **`https://ctf-agent-orchestrator.vercel.app` (Vercel Cloud Frontend)**:
  Hosts the HTML/JS dashboard statically. Because Vercel serverless functions have strict 10s timeouts and cannot execute local C++ binaries or raw netcat sockets, all heavy computations must be executed on **`http://localhost:8080`**.

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
MCP_API_KEY=outstandingom_mcp_2026hjfbechjbdhjjfbnkqjkj

# ─── Supabase Session Persistence ─────────────────────────────────────
SUPABASE_URL=https://vtlmgubzcktztkuymtir.supabase.co
SUPABASE_ANON_KEY=sb_publishable_your_key_here

# ─── Local Dashboard Network Settings ─────────────────────────────────
DASHBOARD_PORT=8080
FORENSIC_DIR=c:\Users\SGI\Downloads\forensic
```

---

## 4. Prerequisites & Solver Libraries

The local Python environment is pre-equipped with gold-standard CTF tools:

```bash
pip install fastapi uvicorn requests python-dotenv openai anthropic pydantic
pip install z3-solver pycryptodome sympy randcrack mpmath
```

* **`z3-solver`**: SMT solver for cracking linear congruential equations, byte constraint systems, and reverse-engineering license keys.
* **`pycryptodome`**: AES, RSA, DES, ECC, ARC4, and hashing implementations.
* **`sympy`**: Fast prime testing, modular inverses, discrete logarithms, and polynomial factorization.
* **`randcrack`**: Recovers internal 624-integer state of Python's Mersenne Twister (`random` module) from 624 consecutive outputs to predict all future/past tokens.

---

## 5. Dashboard Features & Module Walkthrough

Open **`http://localhost:8080`** to access the 6 core tabs:

### 🤖 Agent Mission Control
* **Autonomous Multi-Turn Solver**: Enter any challenge prompt, code snippet, or math problem. The agent plans, calls external tools, writes exploit code, executes it in the sandbox, verifies the solution, and returns the flag.
* **Multi-Model Rotation**: If Groq's `qwen` model hits a rate-limit (429), it automatically falls back to `openai/gpt-oss-120b` or `openai/gpt-oss-20b` with automatic backoff.

### 💻 Exploit Code Reviewer & Live Sandbox Studio
* Located directly below Agent Mission Control.
* **Live Python Sandbox**: Edit any Python solver script directly in your browser and click **▶️ Run in Sandbox**.
* **👥 4x Parallel Workers**: Spawns 4 independent execution threads testing multiple candidate keys, offsets, or seeds concurrently.

### 🧬 Vector RAG Explorer
* Connects directly to Hugging Face ZeroGPU A10G Space.
* Search across hundreds of past real CTF writeups by category (**Cryptography, Forensics, Web, Binary Exploitation**).

### 🔍 Forensics Sandbox Engine
* Integrates directly with [`c:\Users\SGI\Downloads\forensic`](file:///c:/Users/SGI/Downloads/forensic).
* **LSB Byte Bitstream Reconstruction**: Extracts least significant bits from images and searches for `HQX{...}` or `CTF{...}`.
* **PK ZIP Header Carving**: Scans raw binary streams for `\x50\x4B\x03\x04` signatures and decompresses embedded archives.

### 🐙 GitHub Lifetime MCP Gateway
* Live bridge to [`https://mcp-server-2sl7.onrender.com`](https://mcp-server-2sl7.onrender.com).
* Click **Fetch Repositories** to inspect all 15 repositories.
* Click **Commit Solver to GitHub** to automatically push verified Python solvers directly to your `forensic` or `ctf-agent-orchestrator` repositories.

### 🏆 CTFd Autopilot & Netcat Terminal
* **CTFd Challenge Manager**: Connects to any standard CTFd instance. Loads all active challenges with point values, solves them autonomously, and submits the flag.
* **Interactive TCP / Netcat Socket Probe**: Probes raw TCP ports (`nc <host> <port>`), reads server banners, sends interactive text or hex payloads (`hex:414141...`), and flags captured tokens.

---

## 6. Competition Playbooks

### Playbook 1: Standard CTFd Competitions (TCS HackQuest, PicoCTF)

1. Obtain your CTFd platform URL (e.g., `https://hackquest.tcsapps.com` or `https://demo.ctfd.io`).
2. Generate an API Access Token inside CTFd under **Settings -> Access Tokens** (format: `ctfd_...`).
3. In your dashboard, open the **🏆 CTFd Autopilot & Netcat** tab.
4. Paste the URL and Token, then click **Fetch Challenges**.
5. All active challenges will load into your queue. Click **🤖 Solve** on any challenge: the agent will ingest the description, solve it, and submit the flag directly!

---

### Playbook 2: Google CTF & Proprietary Platforms

Google CTF (`capturetheflag.withgoogle.com`) uses Google OAuth and does not have a public CTFd REST API.

1. **Browser Login (One-Time)**:
   - Open your browser and navigate to: `https://capturetheflag.withgoogle.com/team/loki`
   - Sign in with your Google account and enter team access key: `-P5G9PyOgiLko9eg5WzD`.
2. **For Remote Netcat Challenges (`nc host port`)**:
   - Copy the challenge host and port.
   - Go to `http://localhost:8080` -> **🏆 CTFd Autopilot & Netcat** -> **Interactive Socket Probe**.
   - Connect, grab the banner, and inject payloads.
3. **For Math / Crypto / Reverse Engineering Challenges**:
   - Copy the challenge prompt or script from Google CTF.
   - Paste it into **🤖 Agent Mission Control** on `http://localhost:8080`.
   - The agent will formulate the SMT equation, solve it with Z3 in the sandbox, and display the flag: `CTF{...}`.
4. **Submit Flag**:
   - Copy the captured flag and paste it into the Google CTF web portal to claim your points.

---

## 7. API Reference

All backend capabilities are exposed via REST API on `http://127.0.0.1:8080`:

| Method | Endpoint | Request Body | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/status` | None | Returns real-time health and latency of all services |
| `POST`| `/api/solve` | `{"prompt": "...", "provider": "groq"}` | Runs full autonomous agent loop |
| `POST`| `/api/solve/stream` | `{"prompt": "...", "provider": "groq"}` | Real-time Server-Sent Events (SSE) streaming |
| `POST`| `/api/rag/search` | `{"query": "...", "domain": "Cryptography"}` | Queries HF ZeroGPU vector database |
| `POST`| `/api/forensics/scan`| `{"file_path": "...", "text": "..."}` | Runs forensic extractors and flag regex |
| `GET` | `/api/github/repos` | None | Returns GitHub repositories via Render MCP |
| `POST`| `/api/github/commit`| `{"repo": "...", "path": "...", "content": "..."}` | Commits file to GitHub |
| `POST`| `/api/ctfd` | `{"action": "list_challenges", "ctfd_url": "..."}` | Interacts with CTFd platform |
| `POST`| `/api/socket/probe` | `{"host": "...", "port": 1337, "payload": "..."}` | Probes raw TCP netcat socket |
| `POST`| `/api/sandbox/run` | `{"code": "print(1+1)", "timeout_seconds": 10}` | Executes Python code in sandbox |
| `POST`| `/api/sandbox/parallel`| `{"scripts": ["code1", "code2"]}` | Runs concurrent worker pool |

---

## 8. Troubleshooting & FAQs

#### Q1: Why do I get "Unauthorized" on Vercel (`https://ctf-agent-orchestrator.vercel.app`)?
* **Answer**: Vercel hosts the static HTML dashboard. It does not run your local Python interpreter, C++ libraries (`z3`), or raw network sockets. Open your local command center at **`http://localhost:8080`** for full execution.

#### Q2: How do I fix "Windows Defender blocked a file" ([Errno 22])?
* **Answer**: Windows Defender flags raw reverse shells or exploit payloads written to disk. All exploit templates are sanitized in-memory or executed inside safe sandbox environments. Avoid saving raw reverse-shell strings into `.py` files on Windows.

#### Q3: What if Groq hits Rate Limit (Error 429)?
* **Answer**: The system includes automatic multi-model rotation. If `qwen` hits a rate limit, the orchestrator automatically routes the query to `openai/gpt-oss-120b` or `openai/gpt-oss-20b` with exponential backoff.

#### Q4: How do I test Linux ELF binary challenges on Windows?
* **Answer**: Windows cannot run Linux ELF binaries natively. For ELF pwn challenges, route execution through a local WSL2 terminal or Docker container (`docker run -it kalilinux/kali-rolling`).

---

*Authored by Om Uikey — CTF AI Orchestrator Core Maintainer*
