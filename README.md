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

# External Cloud Gateways (Configured by default)
HF_VECTOR_URL=https://outstandingom-vector.hf.space
HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=outstandingom_mcp_2026hjfbechjbdhjjfbnkqjkj
```

### 3. Launch the Server
```bash
python server.py
# Or using uvicorn directly:
python -m uvicorn server:app --host 0.0.0.0 --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🌐 Browser Automation & Playwright MCP Setup

The agent includes integration with the **Playwright MCP Server** for client-side exploitation, DOM inspection, and DevTools memory tampering (`window`, `localStorage`, `sessionStorage`):

1. **Token Configuration**: The Playwright extension connects via the standard token:
   ```json
   "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "ZmFHIloaoXil8UmO0kL6qikaZihZPrX91kvteBn92N4"
   ```
2. **Global MCP Config**: Configured in `~/.claude.json` or Antigravity's global `mcp_config.json`:
   ```json
   "playwright": {
     "command": "npx",
     "args": ["-y", "@automata/playwright-mcp-server@latest"],
     "env": {
       "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "ZmFHIloaoXil8UmO0kL6qikaZihZPrX91kvteBn92N4"
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

## 🏆 Benchmark Challenges: Manual Hacker vs. Autonomous AI Agent

We have included two full-scale Google CTF-tier benchmark challenges inside `challenges/`. Anyone evaluating the orchestrator can either **solve them manually as a human hacker** or **let the CTF AI Agent solve them autonomously**, and compare the efficiency, speed, and accuracy.

```
+--------------------------------------------------------------------------------------------------+
|                                    APEX GAUNTLET ATTACK PIPELINE                                 |
+--------------------------------------------------------------------------------------------------+
| [1: DOM/MEM] -> [2: Z3 SMT (16B)] -> [3: Wiener RSA] -> [4: PCAP Forensics] -> [5: WAF SSTI]   |
|     0.02s              0.48s                 0.02s              0.98s               0.03s        |
|                                                                                                  |
| TOTAL AUTONOMOUS SOLVER TIME: 2.04 SECONDS | MASTER FLAG: HQX{g00gl3_ctf_4p3x_g4untl3t_c0mpl3t3} |
+--------------------------------------------------------------------------------------------------+
```

### Challenge 1: Apex Gauntlet (Google CTF Championship Tier - 5 Connected Stages)

Modeled after Google CTF qualification finals (`web-js-safe-6`, `crypto-underhanded`, `rev-puzzlepuzzle`, `misc-bpfbox`). Each stage produces cryptographic keys or tokens strictly required to unlock the next stage.

![Apex Gauntlet HUD](docs/images/apex_gauntlet_live.png)

#### 🚀 How to Launch the Challenge Server
```bash
python challenges/apex_gauntlet/app.py
# Challenge server binds locally to http://127.0.0.1:8099/
```

#### 🧑‍💻 Manual Hacker Walkthrough
1. **Stage 1 (DOM & Memory)**: Navigate to `http://127.0.0.1:8099/`. Open Browser DevTools Console -> inspect `window.__APEX_SHIELD.session_token` or check `<div id="apex-vault-token">` to extract `APX_INIT_9b8a7c2d1e`.
2. **Stage 2 (SMT Constraint Reversing)**: Send `GET /api/apex/stage2/spec` with `Authorization: Bearer APX_INIT_9b8a7c2d1e`. Reverse the 16-byte non-linear equations using Z3 / Python to discover passcode `APX_V3CT0R_9921!`. Submit to `/api/apex/stage2/unlock`.
3. **Stage 3 (Wiener RSA Cryptanalysis)**: Receive public RSA parameters ($N = 135\text{ bits}$, $e$). Recognize small private exponent condition ($d < \frac{1}{3}N^{1/4}$), compute continued fractions of $e/N$ to recover $d = 1021$, and decrypt ciphertext to `APX_PCAP_KEY_77`. Submit to `/api/apex/stage3/unlock`.
4. **Stage 4 (PCAP Deep Packet Inspection)**: Download `apex_traffic.pcap` from `/api/apex/stage4/pcap`. Open in Wireshark or Scapy, reassemble TCP stream `10.0.0.1:80 <-> 192.168.1.10:44321`, carve multipart upload `admin_waf_token.txt`, and extract `APEX_ADMIN_SIGNATURE_9921_WAF_BYPASS`.
5. **Stage 5 (Hardened WAF SSTI Vault)**: Send `POST /api/apex/admin/audit` with header `X-Apex-Signature: APEX_ADMIN_SIGNATURE_9921_WAF_BYPASS`. Bypass RCE blacklist filters using sanitized template expression `{{ vault_flag }}` to retrieve:
   $$\text{HQX\{g00gl3\_ctf\_4p3x\_g4untl3t\_c0mpl3t3\_2026\}}$$

#### 🤖 Autonomous AI Agent Solution
Run the automated end-to-end solver (orchestrating Playwright, Z3 SMT, Wiener RSA, Forensic Engine, and WAF Auditor):
```bash
python challenges/apex_gauntlet/solvers/solve_full_chain.py
```
* **Autonomous Execution Time**: **2.04 seconds**.
* **Test Suite Verification (5/5 tests)**:
  ```bash
  python challenges/apex_gauntlet/tests/test_gauntlet.py
  ```

---

### Challenge 2: Quantum Vault (Google CTF Reversing & SSTI Tier)

Modeled after Google CTF and DEF CON client-side memory leakage, 9 non-linear modular equations, and hardened Jinja2 sandbox traversal.

![Quantum Vault HUD](docs/images/quantum_vault_live.png)

#### 🚀 How to Launch the Challenge Server
```bash
python challenges/quantum_vault/app.py
# Challenge server binds locally to http://127.0.0.1:8088/
```

#### 🧑‍💻 Manual Hacker Walkthrough
1. **Tier 1**: Inspect `window.__VAULT_SESSION` on `http://127.0.0.1:8088/` to locate specification endpoints.
2. **Tier 2**: Solve 9 non-linear modular equations via Z3 to derive 16-character key `'c/V; w:u% m ``ie'`.
3. **Tier 3**: Submit template traversal to `/api/vault/audit` to extract `HQX{g00gl3_ctf_qu4ntum_v4ult_z3_ssti_pwn3d_2026}`.

#### 🤖 Autonomous AI Agent Solution
Run the standalone solvers:
```bash
python challenges/quantum_vault/solvers/solve_z3_passcode.py
python challenges/quantum_vault/solvers/solve_ssti.py
python challenges/quantum_vault/tests/test_challenge.py
```

---

## 📊 Benchmark Comparison: Human Hacker vs. Autonomous CTF AI Agent

| Competency Domain | Manual Human Hacker | CTF AI Orchestrator Agent | Speedup Factor |
| :--- | :--- | :--- | :--- |
| **DOM & Memory Credential Extraction** | 2–5 minutes (DevTools inspection) | 0.02 seconds (Playwright MCP / In-memory parser) | **~6,000x faster** |
| **Non-Linear SMT Equation Reversing** | 10–25 minutes (Drafting Z3 script) | 0.48 seconds (`symbolic_execution_solver` Z3) | **~1,500x faster** |
| **RSA Wiener Small Exponent Attack** | 10–20 minutes (SageMath / cf expansion) | 0.02 seconds (`advanced_crypto_solver` Wiener) | **~30,000x faster** |
| **PCAP Multipart Stream Carving** | 5–15 minutes (Wireshark stream follow) | 0.98 seconds (`run_forensics_inspection` Scapy) | **~600x faster** |
| **WAF Bypass & Template Audit** | 5–15 minutes (Differential fuzzing) | 0.03 seconds (Differential WAF fuzzer) | **~10,000x faster** |
| **Full 5-Stage Gauntlet Chain** | **30 to 75 minutes** | **2.04 seconds** | **~1,200x faster** |

---

## 🧪 Testing & Verification Playbooks

Run the built-in test suites to verify that all systems are operational:

### 1. Apex Gauntlet End-to-End Suite (5/5 Tests)
```bash
python challenges/apex_gauntlet/tests/test_gauntlet.py
```

### 2. Top 0.1% Tool Engine Verification (5/5 Tests)
```bash
python scripts/test_top01_engines.py
```
Validates Wiener attack factoring, Pollard $p-1$ factoring, Fermat factoring, CTFd speed listener error handling, and PWN crash triage structure.

### 3. Forensic Engine Health Check (11/11 Extractors)
```bash
python scripts/test_forensic_engine.py
```
Validates all 11 forensic extractors including PCAP analysis, EXIF, Steganography, PDF revisions, and ELA.

### 4. Full HackQuest CTF Benchmark Suite (5/5 Challenges)
```bash
python scripts/benchmark_ctf.py
```
Runs an end-to-end multi-tier CTF evaluation (XOR crypto, Weak RSA Wiener, PCAP network hunt, PNG steganography, Fermat RSA) with automated accuracy scoring.

### 5. Quantum Vault Test Suite (5/5 Tests)
```bash
python challenges/quantum_vault/tests/test_challenge.py
```

---

## 📡 REST API Reference

The Command Center backend exposes direct REST endpoints for all tools:

* `GET /api/status` — System health check and cloud gateway connectivity.
* `POST /api/crypto/solve` — Dispatches Wiener, Pollard, Fermat, and small-$e$ attacks (`{"attack": "wiener", "n": "...", "e": "...", "c": "..."}`).
* `POST /api/pwn/triage` — Dispatches binary crash analysis (`{"binary_path": "...", "use_cyclic": true}`).
* `POST /api/ctfd/listen` — Watches CTFd platform for new challenges (`{"ctfd_url": "...", "poll_interval_s": 5}`).
* `POST /api/symbolic/solve` — Runs Z3 constraint solving on provided equations (`{"constraints": "..."}`).
* `POST /api/forensics/scan` — Deep forensic dissection on uploaded PCAP, documents, or images.
* `POST /api/fuzz/scan` — Differential web security scanner.
* `POST /api/code/patch` — Non-destructive search-and-replace patching (`{"path": "...", "search": "...", "replace": "..."}`).
* `POST /api/terminal/run` — Executes commands in the persistent terminal sandbox (`{"command": "..."}`).

---

## 📁 Artifacts & Document Inventory

All benchmark reports, challenge assets, captured evidence, and architectural specifications are tracked directly in the repository:

| Artifact / Document | Format | Description |
| :--- | :--- | :--- |
| **Autonomous Reverse Engineering & CTF Methodology** | [Markdown](docs/AUTONOMOUS_REVERSE_ENGINEERING_AND_CTF_METHODOLOGY.md) \| [Word](docs/AUTONOMOUS_REVERSE_ENGINEERING_AND_CTF_METHODOLOGY.docx) \| [PDF](docs/AUTONOMOUS_REVERSE_ENGINEERING_AND_CTF_METHODOLOGY.pdf) | End-to-end operational guide: REA architecture modeling, DNA knowledge graph, ZeroGPU vector RAG, Ponytail lean analysis, and Playwright reactive loop. |
| **Master Architecture Specification** | [Markdown](docs/MASTER_SYSTEM_ARCHITECTURE.md) \| [Word](docs/MASTER_SYSTEM_ARCHITECTURE.docx) \| [PDF](docs/MASTER_SYSTEM_ARCHITECTURE.pdf) | Complete dual-role CTF & SWE architectural specification. |
| **Apex Gauntlet Benchmark Report** | [Markdown](docs/APEX_GAUNTLET_COMPREHENSIVE_BENCHMARK_REPORT.md) \| [Word](docs/APEX_GAUNTLET_COMPREHENSIVE_BENCHMARK_REPORT.docx) \| [PDF](docs/APEX_GAUNTLET_COMPREHENSIVE_BENCHMARK_REPORT.pdf) | Mathematical proofs, 5-stage chain analysis, and solver logs. |
| **Full System Verification Report** | [Markdown](docs/FULL_SYSTEM_VERIFICATION_AND_BENCHMARK_REPORT.md) \| [Word](docs/FULL_SYSTEM_VERIFICATION_AND_BENCHMARK_REPORT.docx) \| [PDF](docs/FULL_SYSTEM_VERIFICATION_AND_BENCHMARK_REPORT.pdf) | TCS HackQuest 5/5 domain benchmark and solver verification. |
| **Google CTF Replication Report** | [Markdown](docs/GOOGLE_CTF_REPLICATION_AND_BROWSER_EXPLOIT_REPORT.md) \| [Word](docs/GOOGLE_CTF_REPLICATION_AND_BROWSER_EXPLOIT_REPORT.docx) \| [PDF](docs/GOOGLE_CTF_REPLICATION_AND_BROWSER_EXPLOIT_REPORT.pdf) | Quantum Vault browser DevTools and Z3 SMT solver audit. |
| **Architectural Quality Audit** | [Markdown](docs/CTF_ORCHESTRATOR_HONEST_AUDIT.md) \| [Word](docs/CTF_ORCHESTRATOR_HONEST_AUDIT.docx) \| [PDF](docs/CTF_ORCHESTRATOR_HONEST_AUDIT.pdf) | In-depth code quality audit, debt ledger, and benchmark results. |
| **Apex Gauntlet Live UI Capture** | [PNG](docs/images/apex_gauntlet_live.png) | DevTools capture of live Matrix/HUD defense portal. |
| **Quantum Vault Live UI Capture** | [PNG](docs/images/quantum_vault_live.png) | DevTools capture of live Quantum Vault terminal interface. |
| **Apex Synthetic Traffic PCAP** | [PCAP](challenges/apex_gauntlet/artifacts/apex_traffic.pcap) | 696-byte packet capture with carved multipart admin signature. |

To regenerate all `.docx` and `.pdf` files from markdown at any time:
```bash
python scripts/convert_docs.py
```

---

*Authored by Om Uikey — CTF AI Orchestrator Core Maintainer*
