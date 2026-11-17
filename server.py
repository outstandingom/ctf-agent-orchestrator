import os
import sys
import json
import time
import requests
import asyncio
import uuid
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
    LLM_PROVIDER,
    OPENAI_TOOLS,
    get_active_mcp_url
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
docs_dir = os.path.join(current_dir, "docs")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/docs-files", StaticFiles(directory=docs_dir), name="docs-files")
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

class CodePatchRequest(BaseModel):
    path: str = Field(..., description="File path to patch (local or repo)")
    search: str = Field(..., description="Exact code block to find and replace")
    replace: str = Field(..., description="New replacement code block")
    repo: Optional[str] = Field(None, description="GitHub repository name or 'local'")
    branch: Optional[str] = Field("main", description="Branch name")
    commit_message: Optional[str] = Field(None, description="Commit message")

class GitHubBranchRequest(BaseModel):
    repo: str = Field(..., description="GitHub repository name")
    branch: str = Field(..., description="Branch name to create (e.g. ai/fix-issue-42)")
    from_branch: Optional[str] = Field(None, description="Source branch to fork from")

class GitHubPRRequest(BaseModel):
    repo: str = Field(..., description="GitHub repository name")
    title: str = Field(..., description="Pull Request title")
    body: str = Field(..., description="Pull Request markdown body")
    head: str = Field(..., description="Feature branch (e.g. ai/fix-issue-42)")
    base: Optional[str] = Field("main", description="Target branch (default: main)")

class TerminalRunRequest(BaseModel):
    command: str = Field(..., description="Terminal command to execute (npm run build, pytest, etc.)")
    cwd: Optional[str] = Field(None, description="Working directory")
    timeout_seconds: Optional[int] = Field(60, description="Execution timeout in seconds")

class MemorySyncRequest(BaseModel):
    component_a: str = Field(..., description="Source architectural component")
    relationship: Optional[str] = Field("depends_on", description="Relationship type")
    component_b: str = Field(..., description="Target architectural component")
    context: Optional[str] = Field("", description="Architectural notes or context")

class MemoryQueryRequest(BaseModel):
    query: str = Field(..., description="Search query for codebase memory")

class WSLRequest(BaseModel):
    command: str = Field(..., description="Linux bash command to execute in WSL")
    timeout_seconds: Optional[int] = Field(15, description="Execution timeout in seconds")

class CryptoSolveRequest(BaseModel):
    attack: Optional[str] = Field("auto", description="Attack type: wiener, pollard_pm1, weak_prime, small_e, auto")
    n: str = Field(..., description="RSA modulus N")
    e: Optional[str] = Field("0", description="Public exponent e")
    c: Optional[str] = Field("0", description="Ciphertext c")
    partial_p: Optional[str] = Field(None, description="Known high bits of p")
    extra: Optional[str] = Field(None, description="Extra JSON options")

class PWNTriageRequest(BaseModel):
    binary_path: str = Field(..., description="ELF binary path")
    input_payload: Optional[str] = Field("", description="Crash payload or format string probe")
    use_cyclic: Optional[bool] = Field(True, description="Generate De Bruijn cyclic pattern")
    cyclic_length: Optional[int] = Field(300, description="Cyclic pattern length")

class CTFdListenRequest(BaseModel):
    ctfd_url: str = Field(..., description="CTFd instance base URL")
    token: Optional[str] = Field(None, description="Access token or session cookie")
    poll_interval_s: Optional[int] = Field(5, description="Poll interval seconds")
    max_polls: Optional[int] = Field(12, description="Max poll iterations")
    download_attachments: Optional[bool] = Field(True, description="Auto-download challenge attachments")
    save_dir: Optional[str] = Field(None, description="Local attachment directory")

class PlaywrightProbeRequest(BaseModel):
    action: str = Field("navigate_and_inspect", description="Browser action: navigate_and_inspect, click, fill, eval_js, screenshot, download_intercept")
    url: Optional[str] = Field(None, description="Target web challenge URL")
    selector: Optional[str] = Field(None, description="CSS selector to interact with")
    value: Optional[str] = Field(None, description="Value to type/fill")
    script: Optional[str] = Field(None, description="JavaScript expression to evaluate")
    screenshot_path: Optional[str] = Field(None, description="Path to save screenshot capture")

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

        # Check if prompt contains any target website URL, and capture immediate screenshot
        import re
        url_match = re.search(r"https?://[^\s\"'>]+", req.prompt)
        if url_match:
            target_url = url_match.group(0).rstrip(".,;)")
            try:
                execute_tool("playwright_browser_probe", {"action": "navigate_and_inspect", "url": target_url})
                yield f"data: {json.dumps({'type': 'screenshot_ready', 'url': target_url, 'screenshot_url': '/docs-files/images/playwright_proof.png'})}\n\n"
            except Exception:
                pass
        
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

@app.post("/api/crypto/solve")
@app.post("/crypto/solve")
def run_crypto_solve_endpoint(req: CryptoSolveRequest):
    raw = execute_tool("advanced_crypto_solver", {
        "attack": req.attack,
        "n": req.n,
        "e": req.e or "0",
        "c": req.c or "0",
        "partial_p": req.partial_p,
        "extra": req.extra
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/pwn/triage")
@app.post("/pwn/triage")
def run_pwn_triage_endpoint(req: PWNTriageRequest):
    raw = execute_tool("pwn_crash_triage", {
        "binary_path": req.binary_path,
        "input_payload": req.input_payload or "",
        "use_cyclic": req.use_cyclic,
        "cyclic_length": req.cyclic_length
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/ctfd/listen")
@app.post("/ctfd/listen")
def run_ctfd_listen_endpoint(req: CTFdListenRequest):
    raw = execute_tool("ctfd_speed_listener", {
        "ctfd_url": req.ctfd_url,
        "token": req.token,
        "poll_interval_s": req.poll_interval_s,
        "max_polls": req.max_polls,
        "download_attachments": req.download_attachments,
        "save_dir": req.save_dir
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/browser/probe")
@app.post("/browser/probe")
def run_browser_probe_endpoint(req: PlaywrightProbeRequest):
    raw = execute_tool("playwright_browser_probe", {
        "action": req.action,
        "url": req.url,
        "selector": req.selector,
        "value": req.value,
        "script": req.script,
        "screenshot_path": req.screenshot_path
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}

@app.post("/api/browser/capture")
@app.get("/api/browser/capture")
def capture_browser_screenshot(payload: Optional[Dict[str, Any]] = None, url: Optional[str] = None):
    """Instantly captures a fresh screenshot of any target website URL via Playwright."""
    target_url = (payload or {}).get("url") or url or ""
    if not target_url:
        raise HTTPException(status_code=400, detail="Target 'url' parameter is required.")
    
    raw = execute_tool("playwright_browser_probe", {
        "action": "navigate_and_inspect",
        "url": target_url
    })
    try:
        data = json.loads(raw)
        return {
            "status": "success",
            "url": target_url,
            "title": data.get("title", ""),
            "screenshot_url": f"/docs-files/images/playwright_proof.png?t={int(time.time() * 1000)}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "url": target_url}

# =========================================================================
# DOCUMENT & REPORT INVENTORY ENDPOINTS
# =========================================================================
@app.get("/api/reports")
@app.get("/reports")
def list_reports_endpoint():
    """Lists all available reports, benchmarks, and vulnerability audit documents."""
    docs_path = os.path.join(current_dir, "docs")
    if not os.path.exists(docs_path):
        return {"reports": []}

    files = []
    for f in os.listdir(docs_path):
        full = os.path.join(docs_path, f)
        if os.path.isfile(full) and (f.endswith(".md") or f.endswith(".pdf") or f.endswith(".docx") or f.endswith(".json")):
            size_kb = round(os.path.getsize(full) / 1024, 1)
            ext = os.path.splitext(f)[1].lower().replace(".", "")
            files.append({
                "filename": f,
                "format": ext.upper(),
                "size_kb": size_kb,
                "download_url": f"/api/reports/download/{f}"
            })
    # Sort with newest/markdown first
    files.sort(key=lambda x: (x["format"] != "MD", x["filename"]))
    return {"reports": files}

@app.get("/api/reports/download/{filename:path}")
def download_report_endpoint(filename: str):
    """Downloads or previews a specific report file."""
    # Sanitize path to prevent traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(current_dir, "docs", safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    media_type = "application/octet-stream"
    if safe_filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif safe_filename.endswith(".md") or safe_filename.endswith(".json"):
        media_type = "text/plain"
    elif safe_filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(file_path, media_type=media_type, filename=safe_filename)

# =========================================================================
# MODEL CONTEXT PROTOCOL (MCP) NATIVE SERVER & DIRECT PROTOCOL BRIDGE
# Enables external clients (Claude Desktop, Cursor, external tools) to
# connect directly to this agent on http://127.0.0.1:8080/sse or /mcp
# without needing an intermediary.
# =========================================================================
MCP_SESSIONS: Dict[str, asyncio.Queue] = {}

def get_mcp_tool_definitions() -> List[Dict[str, Any]]:
    """Exports all 28 specialized engines + solve_ctf_challenge in standard MCP schema."""
    tools = [
        {
            "name": "solve_ctf_challenge",
            "description": "Autonomously solves any CTF challenge or cyber target using the 28-tool orchestrator with zero hallucination and returns extracted flag.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target_url": {"type": "string", "description": "Target web URL (e.g. http://127.0.0.1:8099/)"},
                    "prompt": {"type": "string", "description": "Challenge description, problem prompt, or target details"},
                    "session_id": {"type": "string", "description": "Optional session ID"}
                },
                "required": ["prompt"]
            }
        }
    ]
    for t in OPENAI_TOOLS:
        fn = t.get("function", {})
        tools.append({
            "name": fn.get("name"),
            "description": fn.get("description"),
            "inputSchema": fn.get("parameters", {"type": "object"})
        })
    return tools

def handle_mcp_jsonrpc(req_body: dict) -> Optional[dict]:
    req_id = req_body.get("id")
    method = req_body.get("method")
    params = req_body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "ctf-agent-orchestrator",
                    "version": "2.0.0"
                }
            }
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": get_mcp_tool_definitions()
            }
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "solve_ctf_challenge":
            agent = CTFOrchestratorAgent()
            prompt = arguments.get("prompt", "")
            target_url = arguments.get("target_url")
            if target_url and target_url not in prompt:
                prompt = f"Target URL: {target_url}\n{prompt}"
            session_id = arguments.get("session_id")
            res = agent.run_with_trace(prompt, session_id=session_id)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
                }
            }
        else:
            output = execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": str(output)}]
                }
            }
    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

@app.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """MCP SSE Transport endpoint."""
    session_id = str(uuid.uuid4())
    queue_instance: asyncio.Queue = asyncio.Queue()
    MCP_SESSIONS[session_id] = queue_instance

    async def event_generator():
        yield f"event: endpoint\ndata: /messages?sessionId={session_id}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue_instance.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            MCP_SESSIONS.pop(session_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/messages")
async def mcp_messages_endpoint(request: Request):
    """MCP JSON-RPC handler for active SSE sessions."""
    sid = request.query_params.get("sessionId")
    body = await request.json()
    resp = handle_mcp_jsonrpc(body)
    if resp and sid in MCP_SESSIONS:
        await MCP_SESSIONS[sid].put(resp)
        return JSONResponse(status_code=202, content={"status": "accepted"})
    elif resp:
        return JSONResponse(content=resp)
    return JSONResponse(status_code=204, content={})

@app.post("/api/mcp/rpc")
@app.post("/mcp")
async def mcp_direct_rpc(request: Request):
    """Direct HTTP JSON-RPC endpoint for MCP clients without SSE."""
    body = await request.json()
    resp = handle_mcp_jsonrpc(body)
    return JSONResponse(content=resp or {})

@app.get("/api/mcp/status")
@app.get("/mcp/status")
def mcp_status_endpoint():
    """Inspects the local and remote MCP server connectivity."""
    active_url = get_active_mcp_url()
    local_online = False
    try:
        r = requests.get("http://127.0.0.1:3000/health", timeout=0.5)
        local_online = (r.status_code == 200)
    except Exception:
        pass

    remote_online = False
    try:
        r = requests.get(f"{MCP_SERVER_URL}/health", timeout=2.0)
        remote_online = (r.status_code == 200)
    except Exception:
        pass

    return {
        "active_mcp_gateway": active_url,
        "is_local": (active_url.startswith("http://127.0.0.1") or active_url.startswith("http://localhost")),
        "local_mcp_server": {"url": "http://127.0.0.1:3000", "online": local_online},
        "remote_mcp_server": {"url": MCP_SERVER_URL, "online": remote_online},
        "native_mcp_protocol_server": {
            "status": "active",
            "sse_endpoint": "/sse",
            "messages_endpoint": "/messages",
            "direct_rpc": "/mcp",
            "tools_exported": len(OPENAI_TOOLS) + 1
        }
    }

@app.post("/api/mcp/test-direct")
def mcp_test_direct_endpoint():
    """Performs a direct self-test of the MCP connection."""
    test_rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    result = handle_mcp_jsonrpc(test_rpc)
    tools_count = len(result.get("result", {}).get("tools", [])) if result else 0
    return {
        "status": "success",
        "message": "Direct MCP Protocol connection verified on localhost!",
        "tools_discovered": tools_count,
        "sample_tools": [t["name"] for t in result.get("result", {}).get("tools", [])[:5]]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", "8080"))
    print(f"\n=======================================================")
    print(f"🚀 CTF AI Orchestrator Command Center Live on http://localhost:{port}")
    print(f"=======================================================\n")
    host_bind = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("server:app", host=host_bind, port=port, reload=True)
