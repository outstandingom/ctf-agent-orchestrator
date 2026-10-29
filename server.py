import os
import sys
import json
import time
import requests
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

# Ensure local modules are accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agent import (
    CTFOrchestratorAgent,
    execute_tool,
    HF_VECTOR_URL,
    HF_URL,
    MCP_SERVER_URL,
    MCP_API_KEY,
    RAG_URL,
    LLM_PROVIDER
)

app = FastAPI(
    title="CTF AI Orchestrator Command Center",
    description="Unified Cyber Dashboard & Real-Time Mission Control for CTF AI Agent, ZeroGPU Vector RAG, and GitHub MCP Gateway.",
    version="2.0.0",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception:
    pass

# Request Models
class SolveRequest(BaseModel):
    prompt: str = Field(..., description="CTF challenge description or problem prompt")
    provider: Optional[str] = Field("groq", description="LLM provider: groq or anthropic")
    model: Optional[str] = Field(None, description="Model override")

class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Keywords or problem text to search")
    domain: Optional[str] = Field("All", description="Category: All, Cryptography, Forensics, Web, Binary Exploitation")
    k: Optional[int] = Field(3, ge=1, le=10)

class ForensicsScanRequest(BaseModel):
    file_path: Optional[str] = Field(None, description="Local path to file to inspect")
    text: Optional[str] = Field("", description="Raw string / ciphertext to scan")

class GitHubCommitRequest(BaseModel):
    repo: str = Field(..., description="Repository name (e.g. forensic, ctf-agent-orchestrator)")
    path: str = Field(..., description="File path (e.g. solvers/exploit.py)")
    content: str = Field(..., description="File text content")
    message: str = Field(..., description="Commit message")

class GitHubReadRequest(BaseModel):
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path")
    branch: Optional[str] = Field("main", description="Branch name")

def render_dashboard_html() -> str:
    candidates = [
        os.path.join(current_dir, "static", "index.html"),
        os.path.join(os.getcwd(), "static", "index.html"),
        os.path.join("/var/task", "static", "index.html"),
        os.path.join(os.path.dirname(__file__), "static", "index.html")
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>CTF AI Orchestrator Command Center</h1><p>Dashboard is online and operational.</p>"

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
def get_dashboard():
    return HTMLResponse(content=render_dashboard_html())

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and request.method == "GET":
        return HTMLResponse(content=render_dashboard_html())
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/api/status")
@app.get("/status")
def get_system_status():
    status = {
        "timestamp": time.time(),
        "services": {}
    }

    # 1. Render MCP Server
    try:
        t0 = time.time()
        mcp_res = requests.get(f"{MCP_SERVER_URL}/health", timeout=4)
        mcp_latency = int((time.time() - t0) * 1000)
        status["services"]["mcp_server"] = {
            "name": "Render GitHub MCP Gateway",
            "url": MCP_SERVER_URL,
            "status": "online" if mcp_res.status_code == 200 else "degraded",
            "latency_ms": mcp_latency,
            "details": mcp_res.json() if mcp_res.status_code == 200 else {}
        }
    except Exception as e:
        status["services"]["mcp_server"] = {
            "name": "Render GitHub MCP Gateway",
            "url": MCP_SERVER_URL,
            "status": "offline",
            "error": str(e)
        }

    # 2. Hugging Face ZeroGPU Vector Space
    try:
        t0 = time.time()
        hf_res = requests.get(f"{HF_VECTOR_URL}/config", timeout=4)
        hf_latency = int((time.time() - t0) * 1000)
        status["services"]["hf_vector_space"] = {
            "name": "Hugging Face Vector RAG (ZeroGPU A10G)",
            "url": HF_VECTOR_URL,
            "status": "online" if hf_res.status_code == 200 else "degraded",
            "latency_ms": hf_latency
        }
    except Exception as e:
        status["services"]["hf_vector_space"] = {
            "name": "Hugging Face Vector RAG (ZeroGPU A10G)",
            "url": HF_VECTOR_URL,
            "status": "offline",
            "error": str(e)
        }

    # 3. Hugging Face DNA Knowledge Graph
    try:
        t0 = time.time()
        kg_res = requests.get(f"{HF_URL}/ping", timeout=4)
        kg_latency = int((time.time() - t0) * 1000)
        status["services"]["knowledge_graph"] = {
            "name": "DNA Knowledge Graph",
            "url": HF_URL,
            "status": "online" if kg_res.status_code == 200 else "degraded",
            "latency_ms": kg_latency
        }
    except Exception as e:
        status["services"]["knowledge_graph"] = {
            "name": "DNA Knowledge Graph",
            "url": HF_URL,
            "status": "offline",
            "error": str(e)
        }

    # 4. Forensic Sandbox Engine
    try:
        sys.path.insert(0, r"c:\Users\SGI\Downloads\forensic")
        from forensic_engine.engine import ForensicEngine
        status["services"]["forensic_engine"] = {
            "name": "Forensic Sandbox Engine",
            "status": "online",
            "extractors_count": 8
        }
    except Exception as e:
        status["services"]["forensic_engine"] = {
            "name": "Forensic Sandbox Engine",
            "status": "offline",
            "error": str(e)
        }

    return status

@app.post("/api/solve")
@app.post("/solve")
def solve_challenge(req: SolveRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Challenge prompt is required.")

    agent = CTFOrchestratorAgent()
    if req.provider:
        agent.provider = req.provider.lower()
        if req.provider.lower() == "groq" and req.model:
            agent.model = req.model

    t0 = time.time()
    result = agent.run_with_trace(req.prompt)
    elapsed = round(time.time() - t0, 2)
    result["elapsed_seconds"] = elapsed
    return result

@app.post("/api/rag/search")
@app.post("/rag/search")
def search_rag(req: RAGSearchRequest):
    output = execute_tool("search_knowledge_base", {
        "query": req.query,
        "domain": req.domain
    })
    return {"query": req.query, "results": output}

@app.post("/api/forensics/scan")
@app.post("/forensics/scan")
def scan_forensics(req: ForensicsScanRequest):
    res = {}
    if req.text:
        flag_data = execute_tool("search_flag_patterns", {"text": req.text})
        try:
            res["flag_analysis"] = json.loads(flag_data)
        except:
            res["flag_analysis"] = flag_data

    if req.file_path:
        file_data = execute_tool("run_forensics_inspection", {"file_path": req.file_path})
        try:
            res["file_forensics"] = json.loads(file_data)
        except:
            res["file_forensics"] = file_data

    return res

@app.get("/api/github/repos")
@app.get("/github/repos")
def list_repos():
    repos_raw = execute_tool("list_github_repos", {"per_page": 15})
    try:
        return json.loads(repos_raw)
    except:
        return {"data": repos_raw}

@app.post("/api/github/commit")
@app.post("/github/commit")
def commit_file(req: GitHubCommitRequest):
    res = execute_tool("commit_github_file", {
        "repo": req.repo,
        "path": req.path,
        "content": req.content,
        "message": req.message
    })
    try:
        return json.loads(res)
    except:
        return {"output": res}

@app.post("/api/github/read")
@app.post("/github/read")
def read_file(req: GitHubReadRequest):
    res = execute_tool("read_github_file", {
        "repo": req.repo,
        "path": req.path,
        "branch": req.branch
    })
    try:
        return json.loads(res)
    except:
        return {"output": res}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    print(f"\n=======================================================")
    print(f"🚀 CTF AI Orchestrator Command Center Live on http://localhost:{port}")
    print(f"=======================================================\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
