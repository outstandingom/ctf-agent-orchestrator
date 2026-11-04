"""
Apex Gauntlet - End-to-End Test Suite
======================================
Tests all 5 defensive stages of the Apex Gauntlet challenge against the CTF Agent Orchestrator:
- Stage 1: DOM Session Extraction
- Stage 2: Z3 SMT Constraint Reversing
- Stage 3: Wiener RSA Factorization & Decryption
- Stage 4: PCAP Packet Dissection & Multipart Token Carving
- Stage 5: Hardened WAF Bypass & SSTI Master Flag Extraction
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Setup import path
CHALLENGE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = CHALLENGE_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from challenges.apex_gauntlet.app import (
    app,
    STAGE1_SESSION_TOKEN,
    STAGE2_CORRECT_KEY,
    STAGE3_CORRECT_KEY,
    STAGE4_ADMIN_SIGNATURE,
    MASTER_FLAG
)
from agent import execute_tool

client = TestClient(app)

class TestApexGauntlet(unittest.TestCase):

    def test_stage1_dom_nexus(self):
        """Stage 1: Verify index served and DOM contains security session tokens."""
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("APEX // GAUNTLET", html)
        self.assertIn("window.__APEX_SHIELD", html)
        self.assertIn(STAGE1_SESSION_TOKEN, html)
        self.assertIn('id="apex-vault-token"', html)

    def test_stage2_smt_reversing(self):
        """Stage 2: Fetch SMT constraints, solve with Z3 BitVec via execute_tool, and unlock."""
        # Unauthenticated request fails
        res_fail = client.get("/api/apex/stage2/spec")
        self.assertEqual(res_fail.status_code, 401)

        # Authenticated request succeeds
        headers = {"Authorization": f"Bearer {STAGE1_SESSION_TOKEN}"}
        res = client.get("/api/apex/stage2/spec", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["stage"], 2)
        constraints = data["constraints"]
        target_var = data["target_variable"]
        length = data["length"]

        # Solve constraints via Z3 SMT engine
        tool_out = execute_tool("symbolic_execution_solver", {
            "constraints": constraints,
            "target_var": target_var,
            "length": length
        })
        solver_res = json.loads(tool_out)
        self.assertEqual(solver_res["status"], "sat")
        solved_key = solver_res["solved_string"]
        self.assertEqual(solved_key, STAGE2_CORRECT_KEY)

        # Unlock Stage 2
        unlock_res = client.post(
            "/api/apex/stage2/unlock",
            headers=headers,
            json={"passcode": solved_key}
        )
        self.assertEqual(unlock_res.status_code, 200)
        stage3_data = unlock_res.json()
        self.assertEqual(stage3_data["stage"], 3)
        self.assertIn("crypto_spec", stage3_data)

    def test_stage3_wiener_cryptanalysis(self):
        """Stage 3: Execute Wiener continued fractions attack via advanced_crypto_solver."""
        headers = {"Authorization": f"Bearer {STAGE1_SESSION_TOKEN}"}
        stage2_unlock = client.post(
            "/api/apex/stage2/unlock",
            headers=headers,
            json={"passcode": STAGE2_CORRECT_KEY}
        ).json()

        crypto_spec = stage2_unlock["crypto_spec"]
        n = crypto_spec["N"]
        e = crypto_spec["e"]
        c = crypto_spec["c"]

        # Execute Wiener attack tool
        tool_out = execute_tool("advanced_crypto_solver", {
            "attack": "wiener",
            "n": n,
            "e": e,
            "c": c
        })
        crypto_res = json.loads(tool_out)
        self.assertIn("wiener", crypto_res)
        self.assertEqual(crypto_res["wiener"]["status"], "factored")
        decrypted_key = crypto_res["wiener"]["plaintext_bytes"]
        self.assertEqual(decrypted_key, STAGE3_CORRECT_KEY)

        # Submit key to unlock Stage 4
        unlock_res = client.post("/api/apex/stage3/unlock", json={"key": decrypted_key})
        self.assertEqual(unlock_res.status_code, 200)
        stage4_data = unlock_res.json()
        self.assertEqual(stage4_data["stage"], 4)
        self.assertIn("pcap_endpoint", stage4_data)

    def test_stage4_pcap_forensics(self):
        """Stage 4: Download PCAP and carve multipart admin token using run_forensics_inspection."""
        res = client.get("/api/apex/stage4/pcap")
        self.assertEqual(res.status_code, 200)
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
            tf.write(res.content)
            temp_pcap = tf.name

        try:
            self.assertGreater(os.path.getsize(temp_pcap), 0)

            # Execute forensic inspection
            tool_out = execute_tool("run_forensics_inspection", {"file_path": temp_pcap})
            forensic_data = json.loads(tool_out)

            # Inspect network forensics
            net_results = forensic_data["categories"]["network_forensics"]["results"][0]
            http_transfers = net_results["evidence"]["http_transfers"]
            self.assertGreater(len(http_transfers), 0)

            admin_transfer = None
            for transfer in http_transfers:
                if transfer["filename"] == "admin_waf_token.txt":
                    admin_transfer = transfer
                    break

            self.assertIsNotNone(admin_transfer)
            self.assertEqual(admin_transfer["content_preview"], STAGE4_ADMIN_SIGNATURE)
        finally:
            if os.path.exists(temp_pcap):
                try:
                    os.remove(temp_pcap)
                except Exception:
                    pass

    def test_stage5_waf_ssti_vault(self):
        """Stage 5: Test WAF defense, bypass with clean SSTI expression, and recover Master Flag."""
        audit_endpoint = "/api/apex/admin/audit"

        # Missing signature
        res_no_sig = client.post(audit_endpoint, json={"template": "test"})
        self.assertEqual(res_no_sig.status_code, 401)

        # Invalid signature
        res_bad_sig = client.post(
            audit_endpoint,
            headers={"X-Apex-Signature": "MALICIOUS_FORGED_SIGNATURE"},
            json={"template": "test"}
        )
        self.assertEqual(res_bad_sig.status_code, 403)

        # WAF blocked RCE attempt
        valid_headers = {"X-Apex-Signature": STAGE4_ADMIN_SIGNATURE}
        res_waf = client.post(
            audit_endpoint,
            headers=valid_headers,
            json={"template": "{{ ''.__class__.__mro__[1].__subclasses__() }}"}
        )
        self.assertEqual(res_waf.status_code, 400)
        self.assertEqual(res_waf.json()["status"], "waf_blocked")

        # Successful SSTI retrieval of Master Flag
        res_flag = client.post(
            audit_endpoint,
            headers=valid_headers,
            json={"template": "SECURE_AUDIT_LOG // FLAG: {{ vault_flag }}"}
        )
        self.assertEqual(res_flag.status_code, 200)
        flag_data = res_flag.json()
        self.assertTrue(flag_data["master_flag_captured"])
        self.assertIn(MASTER_FLAG, flag_data["audit_output"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
