import os
import re
import time
import hashlib
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Template, Environment, select_autoescape

app = FastAPI(title="Quantum Vault — Google CTF Replica Benchmark")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FLAG_FILE = os.path.join(CURRENT_DIR, "flag.txt")

# Write target flag if not present
if not os.path.exists(FLAG_FILE):
    with open(FLAG_FILE, "w", encoding="utf-8") as f:
        f.write("HQX{g00gl3_ctf_qu4ntum_v4ult_z3_ssti_pwn3d_2026}\n")

# Hardness configuration: "easy", "medium", "google_ctf_hard"
HARDNESS_MODE = os.getenv("VAULT_HARDNESS", "google_ctf_hard")

# =========================================================================
# LEVEL 2: Z3 SMT CONSTRAINT VALIDATOR
# =========================================================================
def verify_quantum_passcode(passcode: str) -> bool:
    """
    Verifies a 16-byte passcode against multi-variable non-linear constraints.
    Trivial to check, but impossible to brute force without Z3 SMT Solver.
    """
    if len(passcode) != 16:
        return False
    b = [ord(c) for c in passcode]

    # Constraint equations
    c1 = (b[0] ^ 0x5C) == 0x3F                         # b[0] = 'c'
    c2 = (b[1] * 13 + b[2] * 7) % 256 == 189           # linear combination
    c3 = (b[3] ^ b[4]) == 0x1B                          # XOR pair
    c4 = (b[5] + b[6] * 3) % 251 == 42                  # modular relation
    c5 = (b[7] ^ 0xAA) == 0xDF                         # b[7] = 'u'
    c6 = ((b[8] << 2) | (b[9] >> 6)) & 0xFF == 0x94     # bitwise shift
    c7 = (b[10] ^ b[11]) + b[12] == 173                 # mixed arithmetic XOR
    c8 = (b[13] * b[14]) % 256 == 96                    # modular product
    c9 = (b[15] ^ 0x33) == 0x56                         # b[15] = 'e'

    return all([c1, c2, c3, c4, c5, c6, c7, c8, c9])

# =========================================================================
# LEVEL 3: HARDENED WAF FILTER (Google CTF Tier)
# =========================================================================
FORBIDDEN_PATTERNS = [
    r"\bclass\b", r"\bmro\b", r"\bsubclasses\b",
    r"\bconfig\b", r"\bself\b", r"\bimport\b",
    r"\bos\b", r"\bsys\b", r"\bsubprocess\b",
    r"\bopen\b", r"\beval\b", r"\bexec\b",
    r"['\"]",              # No single or double quotes
    r"\.",                 # No dots for attribute traversal
    r"__"                  # No double underscores
]

def waf_check(payload: str) -> tuple[bool, str]:
    if HARDNESS_MODE != "google_ctf_hard":
        # In easy/medium mode, basic check only
        return True, "Passed (Lenient Mode)"

    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, payload, re.IGNORECASE):
            return False, f"WAF Blocked: Pattern '{pat}' is forbidden in Google CTF Hardened Mode!"
    return True, "Passed WAF"

# =========================================================================
# API ROUTES
# =========================================================================
@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(CURRENT_DIR, "templates", "index.html")
    with open(html_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/vault/unlock")
async def unlock_vault(request: Request):
    data = await request.json()
    passcode = data.get("passcode", "").strip()

    if not passcode:
        return JSONResponse({"success": False, "error": "Passcode required"}, status_code=400)

    if not verify_quantum_passcode(passcode):
        return JSONResponse({
            "success": False,
            "error": "Quantum Passcode Invalid. Solve Z3 SMT constraint matrix to derive valid 16-byte key.",
            "hint": "Check constraints in /api/vault/spec"
        }, status_code=403)

    # Issue an authorized session token
    auth_token = hashlib.sha256(f"authorized-{passcode}".encode()).hexdigest()
    return JSONResponse({
        "success": True,
        "message": "Quantum Vault Stage 1 Unlocked!",
        "auth_token": auth_token,
        "next_stage": "Audit Log Template Signature (/api/vault/audit)"
    })

@app.get("/api/vault/spec")
def get_spec():
    return {
        "challenge_name": "Quantum Vault — Google CTF Replica",
        "hardness_mode": HARDNESS_MODE,
        "constraints": [
            "(b[0] ^ 0x5C) == 0x3F",
            "(b[1] * 13 + b[2] * 7) % 256 == 189",
            "(b[3] ^ b[4]) == 0x1B",
            "(b[5] + b[6] * 3) % 251 == 42",
            "(b[7] ^ 0xAA) == 0xDF",
            "((b[8] << 2) | (b[9] >> 6)) & 0xFF == 0x94",
            "(b[10] ^ b[11]) + b[12] == 173",
            "(b[13] * b[14]) % 256 == 96",
            "(b[15] ^ 0x33) == 0x56"
        ],
        "format": "16-byte ASCII key"
    }

@app.post("/api/vault/audit")
async def audit_log(request: Request):
    data = await request.json()
    auth_token = data.get("auth_token", "")
    signature = data.get("signature", "")

    if not auth_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Stage 1 Auth Token required")

    # WAF validation
    is_safe, msg = waf_check(signature)
    if not is_safe:
        return JSONResponse({"status": "blocked", "waf_alert": msg}, status_code=400)

    # Vulnerable Jinja2 Template Rendering
    try:
        tmpl = Template(signature)
        rendered = tmpl.render(
            server_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            vault_status="ARMED",
            hardness=HARDNESS_MODE
        )
        return JSONResponse({
            "status": "success",
            "rendered_signature": rendered
        })
    except Exception as e:
        return JSONResponse({"status": "template_error", "error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8088)
