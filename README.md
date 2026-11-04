# 🤖 CTF AI Orchestrator Command Center (v2.0)

An autonomous cybersecurity copilot, CTF solver engine, SWE developer agent, and real-time command center built for high-stakes cybersecurity competitions (**TCS HackQuest, PicoCTF, Google CTF**) and automated software engineering.

Combines ultra-fast LPU inference (Groq), automated SMT theorem proving (`z3-solver`), dynamic web fuzzing with differential testing, cryptographic attacks (Wiener, Pollard $p-1$, Fermat), PRNG state recovery (`randcrack`), network PCAP stream carving (`scapy`), WSL2 Linux binary analysis, CTFd competition monitoring, and Playwright browser DOM/memory manipulation.

📖 **For the detailed developer reference, see [docs/COMPLETE_USER_GUIDE.md](docs/COMPLETE_USER_GUIDE.md) and [docs/MASTER_SYSTEM_ARCHITECTURE.md](docs/MASTER_SYSTEM_ARCHITECTURE.md).**

---

## ⚡ 1-Click Automated Setup (Zero Configuration)

### 🪟 Windows (1-Click)
Simply double-click or run from PowerShell:
```cmd
start.bat
```
`start.bat` will automatically:
1. Verify Python 3.10+ installation.
2. Auto-initialize `.env` from `.env.example` if not already present.
3. Automatically clone the companion **Forensic Engine** (`outstandingom/forensic`) into `..\forensic` if missing.
4. Install all Python dependencies from `requirements.txt` (`z3-solver`, `sympy`, `scapy`, `pycryptodome`, etc.).
5. Launch the Command Center on port 8080 and automatically open your default browser to **[http://localhost:8080/](http://localhost:8080/)**.

### 🐧 Linux / macOS / WSL (1-Click)
```bash
chmod +x start.sh
./start.sh
```

---

## ⚙️ Manual Setup & Environment Configuration

If you prefer setting up manually or running in a container:

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/outstandingom/ctf-agent-orchestrator.git
cd ctf-agent-orchestrator

# Clone companion forensic engine into parent directory (optional but recommended)
git clone https://github.com/outstandingom/forensic.git ../forensic

# Install complete requirement suite
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)
Copy the example template:
```bash
cp .env.example .env
```
Edit `.env` with your preferred settings:
```env
# LLM Provider: "groq" (fastest, free tier available) or "anthropic"
LLM_PROVIDER=groq

# Groq Configuration (Get free key at https://console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b

# Anthropic Configuration (Optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Dashboard Port
DASHBOARD_PORT=8080

# External Cloud Gateways (URLs are defaults; credentials are local)
HF_VECTOR_URL=https://outstandingom-vector.hf.space
HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=your_mcp_gateway_key_here
```

### 3. Launch the Server
```bash
python server.py
# Or using uvicorn directly:
python -m uvicorn server:app --host 127.0.0.1 --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🌐 Browser Automation & Playwright MCP Setup

The agent includes integration with the **Playwright MCP Server** for client-side exploitation, DOM inspection, and DevTools memory tampering (`window`, `localStorage`, `sessionStorage`):

1. **Token Configuration**: Configure your own extension token locally using the MCP server's documented setup. Never commit the token to Git.
   ```json
   "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "YOUR_LOCAL_PLAYWRIGHT_MCP_TOKEN"
   ```
2. **Global MCP Config**: Configured in `~/.claude.json` or Antigravity's global `mcp_config.json`:
   ```json
   "playwright": {
     "command": "npx",
     "args": ["-y", "@automata/playwright-mcp-server@latest"],
     "env": {
       "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "YOUR_LOCAL_PLAYWRIGHT_MCP_TOKEN"
     }
   }
   ```
3. **Capabilities**:
   * `browser_navigate`: Open challenge URLs headlessly.
   * `browser_snapshot`: Read the full DOM tree and form element refs.
   * `browser_evaluate`: Read or tamper with client-side JavaScript memory (`window.__VAULT_SESSION`).
   * `browser_take_screenshot`: Capture visual confirmation of challenge state.

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
│ & DNA Graph      │               │ (Z3, SymPy, LLL) │                 │ (Safe Branch/PR) │
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
│ CTFd Autopilot       │         │ Advanced Crypto Suite│          │ Forensic Engine      │
│ Speed Listener       │         │ (Wiener/Pollard/RSA) │          │ (Scapy PCAP + Stego) │
└──────────────────────┘         └──────────────────────┘          └──────────────────────┘
```

---

## 🛠️ Specialized Tool Inventory

| Tool Name | Subsystem | Functionality |
| :--- | :--- | :--- |
| **`advanced_crypto_solver`** | Cryptography | Automated Wiener attack ($d < N^{0.25}$), Pollard $p-1$ factoring (Montgomery Stage 1), Fermat factoring for close primes, small-$e$ attacks. |
| **`symbolic_execution_solver`** | Reversing | Z3 SMT solver with 8-bit `BitVec` modeling for non-linear constraint equations, passcodes, and crackmes. |
| **`pwn_crash_triage`** | Binary Exploitation | Dynamic GDB crash runner: parses SIGSEGV/SIGILL, catches 16-byte `movaps` RSP stack misalignment, calculates De Bruijn cyclic offsets, logs patterns to DNA graph. |
| **`ctfd_speed_listener`** | Competition Speed | Background polling watcher for CTFd platforms. Detects newly dropped challenges, downloads attachments, and classifies file types/packers (UPX, PyInstaller, ELF, PCAP). |
| **`run_forensics_inspection`** | Forensics | Invokes the Forensic Engine (11 extractors): PCAP TCP stream reassembly, multipart file carving, DNS exfil detection, and image LSB steganography. |
| **`patch_file_diff`** | SWE / Bug Fixing | Non-destructive search-and-replace patching engine. Replaces exact code blocks without truncating or corrupting files. |
| **`create_github_branch` / `pr`** | Safe Engineering | Creates isolated git branches and opens Pull Requests via Render MCP Gateway to avoid direct-to-main hazards. |
| **`run_fullstack_terminal`** | Terminal Sandbox | Persistent terminal runner with timeout, custom `cwd`, and exit code validation (`npm run build`, `pytest`, `docker`). |

---

## 🧪 Testing & Verification Playbooks

Run the built-in test suites to verify that all systems are operational:

### 1. Top 0.1% Tool Engine Verification (5/5 Tests)
```bash
python scripts/test_top01_engines.py
```
Validates Wiener attack factoring, Pollard $p-1$ factoring, Fermat factoring, CTFd speed listener error handling, and PWN crash triage structure.

### 2. Forensic Engine Health Check (11/11 Extractors)
```bash
python scripts/test_forensic_engine.py
```
Validates all 11 forensic extractors including PCAP analysis, EXIF, Steganography, PDF revisions, and ELA.

### 3. Full HackQuest CTF Benchmark Suite
```bash
python scripts/benchmark_ctf.py
```
Runs an end-to-end multi-tier CTF evaluation (XOR crypto, Weak RSA Wiener, PCAP network hunt, PNG steganography, Fermat RSA) with automated accuracy scoring.

### 4. Interactive Google CTF Quantum Vault Challenge
Launch the local multi-tier benchmark challenge:
```bash
python challenges/quantum_vault/app.py
```
Challenge will be live on **http://127.0.0.1:8088/**.

---

## 📡 REST API Reference

The Command Center backend exposes direct REST endpoints for all tools:

* `GET /api/status` — System health check and cloud gateway connectivity.
* `POST /api/crypto/solve` — Dispatches Wiener, Pollard, Fermat, and small-$e$ attacks (`{"attack": "wiener", "n": "...", "e": "...", "c": "..."}`).
* `POST /api/pwn/triage` — Dispatches binary crash analysis (`{"binary_path": "...", "use_cyclic": true}`).
* `POST /api/ctfd/listen` — Watches CTFd platform for new challenges (`{"ctfd_url": "...", "poll_interval_s": 5}`).
* `POST /api/symbolic/solve` — Runs Z3 constraint solving on provided equations (`{"constraints": "..."}`).
* `POST /api/code/patch` — Non-destructive search-and-replace patching (`{"path": "...", "search": "...", "replace": "..."}`).
* `POST /api/terminal/run` — Executes commands in the persistent terminal sandbox (`{"command": "..."}`).

---

## 📄 Documentation Exports

Full architecture reports are available in multiple formats:
* Markdown Source: [`docs/MASTER_SYSTEM_ARCHITECTURE.md`](docs/MASTER_SYSTEM_ARCHITECTURE.md)
* Word Document: [`docs/SYSTEM_VERIFICATION_REPORT.docx`](docs/SYSTEM_VERIFICATION_REPORT.docx)
* Printable PDF: [`docs/SYSTEM_VERIFICATION_REPORT.pdf`](docs/SYSTEM_VERIFICATION_REPORT.pdf)

To regenerate `.docx` and `.pdf` files from markdown:
```bash
python scripts/convert_docs.py
```

---

*Authored by Om Uikey — CTF AI Orchestrator Core Maintainer*
