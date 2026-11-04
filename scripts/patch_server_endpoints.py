import sys

SERVER_PATH = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\server.py"

with open(SERVER_PATH, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Models to add
models_anchor = """class WSLRequest(BaseModel):
    command: str = Field(..., description="Linux bash command to execute in WSL")
    timeout_seconds: Optional[int] = Field(15, description="Execution timeout in seconds")"""

new_models = """class WSLRequest(BaseModel):
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
    save_dir: Optional[str] = Field(None, description="Local attachment directory")"""

assert models_anchor in src, "models_anchor not found"
src = src.replace(models_anchor, new_models, 1)

# 2. Endpoints to add
endpoints_anchor = """@app.post("/api/wsl/exec")
@app.post("/wsl/exec")
def run_wsl_endpoint(req: WSLRequest):
    raw = execute_tool("wsl_linux_bridge", {
        "command": req.command,
        "timeout_seconds": req.timeout_seconds or 15
    })
    try:
        return json.loads(raw)
    except Exception:
        return {"response": raw}"""

new_endpoints = """@app.post("/api/wsl/exec")
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
        return {"response": raw}"""

assert endpoints_anchor in src, "endpoints_anchor not found"
src = src.replace(endpoints_anchor, new_endpoints, 1)

with open(SERVER_PATH, "w", encoding="utf-8") as f:
    f.write(src)

import ast
try:
    ast.parse(src)
    print("✅ server.py syntax valid with new endpoints added")
except Exception as e:
    print(f"❌ server.py syntax error: {e}")
