# ☁️ Shifting CTF AI Orchestrator Entirely to the Cloud

This guide provides the complete blueprint for moving the **CTF AI Orchestrator Command Center** from your local machine to the cloud.

---

## 1. What Was Running Locally vs What Was Already Cloud

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CURRENT COMPONENT MAP                           │
├────────────────────────────────────────────────────────────────────────┤
│  ALREADY IN THE CLOUD:                                                 │
│  • Hugging Face ZeroGPU Vector Space (outstandingom-vector.hf.space)   │
│  • DNA Knowledge Graph (outstandingom-knowledge-graph-env.hf.space)    │
│  • Render MCP Server Gateway (mcp-server-2sl7.onrender.com)            │
│  • Supabase Solve Ledger (vtlmgubzcktztkuymtir.supabase.co)            │
│  • Groq LPU Inference Cloud (api.groq.com)                             │
├────────────────────────────────────────────────────────────────────────┤
│  RUNNING LOCALLY ON YOUR MACHINE (Now Cloud-Ready):                    │
│  • FastAPI Command Center (server.py on localhost:8080)                │
│  • Headless Playwright Chromium Browser Instance                       │
│  • Scapy Forensics & Z3 SMT Solver Subprocesses                        │
│  • Benchmark & Challenge Portals (Apex Gauntlet :8099)                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Option A: 1-Click Deployment to Render (Recommended)

Your repository now includes a production **`Dockerfile`** and a **`render.yaml`** blueprint.

### Steps to Deploy on Render:
1. Go to your **[Render Dashboard](https://dashboard.render.com/)**.
2. Click **New +** ➔ **Blueprint**.
3. Select your GitHub repository: **`outstandingom/ctf-agent-orchestrator`**.
4. Render will read `render.yaml` and configure:
   - Python 3.11 container with Chromium, Scapy, and Z3.
   - All cloud environment variables (`HF_VECTOR_URL`, `HF_KNOWLEDGE_URL`, `MCP_SERVER_URL`, `SUPABASE_URL`).
5. Add your `GROQ_API_KEY` in the environment settings.
6. Click **Apply**.
   - Your Command Center will be live on a public URL like:  
     `https://ctf-agent-orchestrator.onrender.com/`

---

## 3. Option B: Serverless Cloud on Modal.com

Your repository now includes **`modal_deploy.py`**, enabling serverless execution with auto-scaling to zero when idle.

### Steps to Deploy on Modal:
```bash
# 1. Install Modal CLI
pip install modal

# 2. Authenticate your Modal account
modal setup

# 3. Create secrets in your Modal dashboard or CLI:
modal secret create ctf-orchestrator-secrets GROQ_API_KEY="your-groq-key"

# 4. Deploy with one command!
modal deploy modal_deploy.py
```
Modal will build the Chromium-enabled Debian container and give you a live production URL:  
`https://outstandingom--ctf-agent-orchestrator-fastapi-app.modal.run`

---

## 4. Testing Your Cloud Deployment
Once deployed to Render or Modal:
1. Open the public URL in your browser.
2. The health pills will ping:
   - ✅ **HF Vector RAG**: Connected
   - ✅ **Render MCP**: Connected
   - ✅ **DNA Graph**: Connected
3. Enter any target URL in the **Live Link Investigator** and click **`⚡ Find Bugs`**—the entire 27-tool pipeline will execute completely in the cloud with **zero load on your local PC**!
