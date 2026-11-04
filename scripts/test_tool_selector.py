"""Regression tests for prompt-to-tool routing.

Run from the repository root with:
    python -m unittest scripts.test_tool_selector
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import select_relevant_tools


def selected(prompt):
    return {
        item["function"]["name"]
        for item in select_relevant_tools(prompt)
    }


class ToolSelectorTests(unittest.TestCase):
    def test_plain_rsa_prompt_includes_advanced_crypto_solver(self):
        tools = selected(
            "RSA challenge: given modulus n, public exponent e, and ciphertext c, recover the plaintext."
        )
        self.assertIn("advanced_crypto_solver", tools)

    def test_wiener_attack_includes_advanced_crypto_solver(self):
        self.assertIn("advanced_crypto_solver", selected("Try a Wiener attack on this RSA key."))

    def test_pcap_prompt_includes_forensics_tools(self):
        tools = selected("Analyze this PCAP file and find the hidden flag.")
        self.assertIn("run_forensics_inspection", tools)
        self.assertIn("search_flag_patterns", tools)

    def test_web_prompt_includes_web_fuzzer(self):
        self.assertIn("web_dynamic_fuzzer", selected("Investigate this authorized web challenge for SQL injection."))

    def test_unrelated_prompt_does_not_crash(self):
        self.assertTrue(selected("Help me understand this CTF challenge.") )


if __name__ == "__main__":
    unittest.main()
