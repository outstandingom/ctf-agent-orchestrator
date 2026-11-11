import os
import sys
import json

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agent import execute_tool

REPO_NAME = "ctf-agent-orchestrator"

def push_file_via_mcp(rel_path, commit_message):
    full_path = os.path.join(current_dir, rel_path)
    if not os.path.exists(full_path):
        print(f"[-] File not found: {full_path}")
        return None

    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        file_content = f.read()

    print(f"\n[MCP PUSH] Uploading {rel_path} to {REPO_NAME} via Render MCP Gateway...")
    payload = {
        "repo": REPO_NAME,
        "path": rel_path.replace("\\", "/"),
        "content": file_content,
        "message": commit_message
    }
    res_str = execute_tool("commit_github_file", payload)
    print(f"[MCP PUSH RESULT]: {res_str}")
    return res_str

if __name__ == "__main__":
    files_to_push = [
        ("start.bat", "chore(launcher): 1-click launch with Playwright Chromium auto-install and REA engine cloning"),
        ("start.sh", "chore(launcher): linux/macOS 1-click launcher sync with REA and Playwright setup"),
        ("docs/AUTONOMOUS_REVERSE_ENGINEERING_AND_CTF_METHODOLOGY.md", "docs(methodology): add comprehensive autonomous reverse engineering and cognitive mapping framework"),
        ("scripts/test_complete_methodology.py", "test(methodology): add end-to-end black-box verification test suite"),
        ("challenges/apex_gauntlet/solvers/solve_playwright_interactive.py", "feat(solver): interactive Playwright browser UI solver with real file download"),
        ("challenges/apex_gauntlet/templates/index.html", "feat(ui): interactive Cyberpunk terminal HUD with live form inputs and flag display banner")
    ]

    for rel_path, msg in files_to_push:
        push_file_via_mcp(rel_path, msg)
