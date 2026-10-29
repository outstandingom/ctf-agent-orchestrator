# 🤖 CTF AI Orchestrator Agent

An autonomous cybersecurity co-pilot and CTF problem solver agent built for automated challenge analysis, multi-tier vector retrieval, local forensic sandboxing, and autonomous code execution & GitHub deployment.

---

## 🏗️ Architecture & Component Integration

```
                         ┌──────────────────────────────────────────┐
                         │         CTF AI Orchestrator Agent        │
                         │     (Groq Qwen 27B / Claude 3.5)         │
                         └──────────────────┬───────────────────────┘
                                            │
        ┌───────────────────────────────────┼────────────────────────────────────┐
        │                                   │                                    │
        ▼                                   ▼                                    ▼
┌──────────────┐                  ┌──────────────────┐                 ┌──────────────────┐
│ Vector RAG   │                  │ Forensic Engine  │                 │ Render GitHub    │
│ Gateway      │                  │ Sandbox          │                 │ MCP Gateway      │
│ (HF ZeroGPU) │                  │ (Steg / Hashes)  │                 │ (Render Server)  │
└──────────────┘                  └──────────────────┘                 └──────────────────┘
```

1. **Multi-Tier Knowledge Retrieval (`search_knowledge_base`)**:
   - **Tier 1 (Cloud ZeroGPU)**: Connects to high-memory Hugging Face Space (`https://outstandingom-vector.hf.space`) for TF-IDF / cosine semantic similarity search over past writeups.
   - **Tier 2 (Local RAG)**: Fast fallback to local FastAPI vector service (`http://localhost:8001`).
   - **Tier 3 (DNA Knowledge Graph)**: Queries self-evolving knowledge graph (`https://outstandingom-knowledge-graph-env.hf.space`).

2. **Forensic Sandbox Tools**:
   - **`run_forensics_inspection`**: Performs LSB chi-square uniformity tests, ZIP file signature carving, and SHA256/MD5 hashing.
   - **`search_flag_patterns`**: Extracts `flag{...}`, `CTF{...}`, base64 payloads, and invisible Unicode zero-width characters (`\u200b`, `\u200c`).

3. **Autonomous GitHub Commits (`read_github_file`, `commit_github_file`, `list_github_repos`)**:
   - Commits generated Python solvers, exploit scripts, and writeup documentation directly to your GitHub repositories via your Render MCP server.

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/outstandingom/ctf-agent-orchestrator.git
cd ctf-agent-orchestrator
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b

HF_VECTOR_URL=https://outstandingom-vector.hf.space
MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
MCP_API_KEY=your_mcp_api_key
```

### 3. Usage

Run interactive challenge solving:

```bash
python agent.py
```

Or invoke in code:

```python
from agent import CTFOrchestratorAgent

agent = CTFOrchestratorAgent()
result = agent.run("Server uses time(0) as random seed for XOR cipher. Write solver.")
print(result)
```

---

## 🔒 Security
- Secrets and tokens are kept strictly in `.env`.
- Destructive operations on GitHub are protected via 2-Step verification lock on the MCP server.
