import os
import sys
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
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
    get_forensic_dir,
    clear_session_history,
    get_session_history,
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
    session_id: Optional[str] = Field(None, description="Session ID for continuous multi-turn memory")

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

class CTFdRequest(BaseModel):
    action: str = Field("list_challenges", description="list_challenges, get_challenge, submit_flag, get_scoreboard")
    ctfd_url: str = Field(..., description="Base URL of CTFd instance")
    token: Optional[str] = Field(None, description="API token or session cookie")
    challenge_id: Optional[int] = Field(None, description="Challenge ID")
    flag: Optional[str] = Field(None, description="Flag string to submit")

class SocketProbeRequest(BaseModel):
    host: str = Field(..., description="Target host or IP")
    port: int = Field(..., description="Target port")
    payload: Optional[str] = Field("", description="Payload (text or hex:...)")
    timeout_seconds: Optional[float] = Field(5.0, description="Socket timeout")

class SandboxRunRequest(BaseModel):
    code: str = Field(..., description="Python code to run in sandbox")
    timeout_seconds: Optional[int] = Field(10, description="Execution timeout in seconds")

class ParallelRunRequest(BaseModel):
    scripts: List[str] = Field(..., description="List of Python scripts to run concurrently")
    timeout_seconds: Optional[int] = Field(12, description="Per-script timeout in seconds")

class FuzzRequest(BaseModel):
    target_url: str = Field(..., description="Target URL")
    category: Optional[str] = Field("SQLi", description="Attack category: SQLi, SSTI, CommandInjection, PathTraversal, AuthBypass, IDOR")
    method: Optional[str] = Field("GET", description="HTTP method: GET or POST")
    param_name: Optional[str] = Field(None, description="Target parameter name")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional POST body / payload data")

class SymbolicRequest(BaseModel):
    constraints: str = Field(..., description="Z3 / Python equations or constraint code")
    target_var: Optional[str] = Field("flag", description="Target variable name to solve for")
    length: Optional[int] = Field(None, description="Length in bytes if solving for byte array")

class WSLRequest(BaseModel):
    command: str = Field(..., description="Linux bash command to execute in WSL")
    timeout_seconds: Optional[int] = Field(15, description="Execution timeout in seconds")

def render_dashboard_html() -> str:
    candidates = [
        os.path.join(current_dir, "public", "index.html"),
        os.path.join(current_dir, "static", "index.html"),
        os.path.join(os.getcwd(), "public", "index.html"),
        os.path.join(os.getcwd(), "static", "index.html"),
        os.path.join("/var/task", "public", "index.html"),
        os.path.join("/var/task", "static", "index.html")
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

    def check_mcp():
        try:
            t0 = time.time()
            res = requests.get(f"{MCP_SERVER_URL}/health", timeout=3)
            return {
                "name": "Render GitHub MCP Gateway",
                "url": MCP_SERVER_URL,
                "status": "online" if res.status_code == 200 else "degraded",
                "latency_ms": int((time.time() - t0) * 1000),
                "details": res.json() if res.status_code == 200 else {}
            }
        except Exception as e:
            return {
                "name": "Render GitHub MCP Gateway",
                "url": MCP_SERVER_URL,
                "status": "offline",
                "error": str(e)
            }

    def check_hf():
        try:
            t0 = time.time()
            res = requests.get(f"{HF_VECTOR_URL}/config", timeout=3)
            return {
                "name": "Hugging Face Vector RAG (ZeroGPU A10G)",
                "url": HF_VECTOR_URL,
                "status": "online" if res.status_code == 200 else "degraded",
                "latency_ms": int((time.time() - t0) * 1000)
            }
        except Exception as e:
            return {
                "name": "Hugging Face Vector RAG (ZeroGPU A10G)",
                "url": HF_VECTOR_URL,
                "status": "offline",
                "error": str(e)
            }

    def check_kg():
        try:
            t0 = time.time()
            res = requests.get(f"{HF_URL}/ping", timeout=3)
            return {
                "name": "DNA Knowledge Graph",
                "url": HF_URL,
                "status": "online" if res.status_code == 200 else "degraded",
                "latency_ms": int((time.time() - t0) * 1000)
            }
        except Exception as e:
            return {
                "name": "DNA Knowledge Graph",
                "url": HF_URL,
                "status": "offline",
                "error": str(e)
            }

    # Execute health checks in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_mcp = executor.submit(check_mcp)
        f_hf = executor.submit(check_hf)
        f_kg = executor.submit(check_kg)

        status["services"]["mcp_server"] = f_mcp.result()
        status["services"]["hf_vector_space"] = f_hf.result()
        status["services"]["knowledge_graph"] = f_kg.result()

    # 4. Forensic Sandbox Engine (Controlled Path Safe)
    try:
        forensic_dir = get_forensic_dir()
        if os.path.exists(forensic_dir) and forensic_dir not in sys.path:
            sys.path.insert(0, forensic_dir)
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


@app.post("/api/upload")
@app.post("/upload")
async def upload_challenge_file(file: UploadFile = File(...)):
    import tempfile, shutil
    temp_dir = tempfile.mkdtemp(prefix="ctf_challenge_")
    safe_name = os.path.basename(file.filename)
    dest_path = os.path.join(temp_dir, safe_name)
    with open(dest_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)
    return {
        "status": "success",
        "filename": safe_name,
        "file_path": dest_path,
        "size_bytes": os.path.getsize(dest_path)
    }

@app.post("/api/solve/stream")
@app.post("/solve/stream")
def solve_challenge_stream(req: SolveRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Challenge prompt is required.")

    def event_stream():
        yield f"data: {json.dumps({'type': 'init', 'message': 'Agent dispatched'})}\n\n"
        
        agent = CTFOrchestratorAgent()
        if req.provider:
            agent.provider = req.provider.lower()
            if req.provider.lower() == "groq" and req.model:
                agent.model = req.model

        t0 = time.time()
        result = agent.run_with_trace(req.prompt, session_id=req.session_id)
        elapsed = round(time.time() - t0, 2)
        result["elapsed_seconds"] = elapsed

        for item in result.get("trace", []):
            yield f"data: {json.dumps({'type': 'tool_call', 'item': item})}\n\n"

        yield f"data: {json.dumps({'type': 'final_answer', 'final_answer': result.get('final_answer', ''), 'trace': result.get('trace', []), 'elapsed_seconds': elapsed})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/session/reset")
@app.post("/session/reset")
def reset_session_endpoint(payload: Optional[Dict[str, str]] = None):
    import uuid
    sess = (payload or {}).get("session_id")
    if sess:
        clear_session_history(sess)
    new_sess = str(uuid.uuid4())
    return {"status": "success", "session_id": new_sess, "message": "New conversation session initialized."}

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
    result = agent.run_with_trace(req.prompt, session_id=req.session_id)
    elapsed = round(time.time() - t0, 2)
    result["elapsed_seconds"] = elapsed
    result["solution"] = result.get("final_answer", "")
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

@app.post("/api/ctfd")
@app.post("/ctfd")
def manage_ctfd(req: CTFdRequest):
    payload = {
        "action": req.action,
        "ctfd_url": req.ctfd_url,
        "token": req.token,
        "challenge_id": req.challenge_id,
        "flag": req.flag
    }
    raw = execute_tool("ctfd_manage", payload)
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/socket/probe")
@app.post("/socket/probe")
def probe_socket(req: SocketProbeRequest):
    payload = {
        "host": req.host,
        "port": req.port,
        "payload": req.payload,
        "timeout_seconds": req.timeout_seconds
    }
    raw = execute_tool("interactive_socket_probe", payload)
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/sandbox/run")
@app.post("/sandbox/run")
def run_sandbox_endpoint(req: SandboxRunRequest):
    raw = execute_tool("execute_python_sandbox", {
        "code": req.code,
        "timeout_seconds": req.timeout_seconds
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/sandbox/parallel")
@app.post("/sandbox/parallel")
def run_parallel_endpoint(req: ParallelRunRequest):
    raw = execute_tool("parallel_exploit_worker", {
        "scripts": req.scripts,
        "timeout_seconds": req.timeout_seconds
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/fuzz/scan")
@app.post("/fuzz/scan")
def run_fuzzer_endpoint(req: FuzzRequest):
    raw = execute_tool("web_dynamic_fuzzer", {
        "target_url": req.target_url,
        "category": req.category or "SQLi",
        "method": req.method or "GET",
        "param_name": req.param_name,
        "data": req.data
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/symbolic/solve")
@app.post("/symbolic/solve")
def run_symbolic_endpoint(req: SymbolicRequest):
    raw = execute_tool("symbolic_execution_solver", {
        "constraints": req.constraints,
        "target_var": req.target_var or "flag",
        "length": req.length
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/wsl/exec")
@app.post("/wsl/exec")
def run_wsl_endpoint(req: WSLRequest):
    raw = execute_tool("wsl_linux_bridge", {
        "command": req.command,
        "timeout_seconds": req.timeout_seconds or 15
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    print(f"\n=======================================================")
    print(f"🚀 CTF AI Orchestrator Command Center Live on http://localhost:{port}")
    print(f"=======================================================\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
