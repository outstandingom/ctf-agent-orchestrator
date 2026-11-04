"""
Apex Gauntlet - Playwright Browser Verification Test
===================================================
Automates real headless Chromium browser interaction against Apex Gauntlet:
- Navigates to http://127.0.0.1:8099/
- Intercepts live browser console logs
- Extracts window.__APEX_SHIELD memory object
- Inspects hidden DOM node attribute #apex-vault-token[data-token]
- Captures full-page viewport screenshot as evidence artifact
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Setup import path
TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright

TARGET_URL = os.environ.get("APEX_TARGET", "http://127.0.0.1:8099/")
ARTIFACTS_DIR = TEST_DIR.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PROOF_SCREENSHOT = ARTIFACTS_DIR / "apex_gauntlet_playwright_capture.png"

class TestApexPlaywrightBrowser(unittest.TestCase):

    def test_playwright_browser_interaction(self):
        """Launches headless Chromium, extracts in-memory credentials, and verifies screenshot."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg.text))

            response = page.goto(TARGET_URL, timeout=15000)
            self.assertIsNotNone(response)
            self.assertEqual(response.status, 200)

            # Wait for matrix HUD rendering
            page.wait_for_timeout(500)

            # 1. Verify Title & Header
            title = page.title()
            self.assertIn("Apex Gauntlet", title)

            # 2. Extract DOM Hidden Attribute
            hidden_token = page.get_attribute("#apex-vault-token", "data-token")
            self.assertEqual(hidden_token, "APX_INIT_9b8a7c2d1e")

            # 3. Extract in-memory window.__APEX_SHIELD
            shield_data = page.evaluate("() => window.__APEX_SHIELD")
            self.assertIsInstance(shield_data, dict)
            self.assertEqual(shield_data.get("stage"), 1)
            self.assertEqual(shield_data.get("session_token"), "APX_INIT_9b8a7c2d1e")
            self.assertEqual(shield_data.get("stage2_endpoint"), "/api/apex/stage2/spec")

            # 4. Verify Console Log Interception
            self.assertTrue(any("APX_INIT_9b8a7c2d1e" in msg for msg in console_messages))

            # 5. Capture Screenshot Proof
            page.screenshot(path=str(PROOF_SCREENSHOT))
            self.assertTrue(PROOF_SCREENSHOT.exists())
            self.assertGreater(PROOF_SCREENSHOT.stat().st_size, 1000)

            browser.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
