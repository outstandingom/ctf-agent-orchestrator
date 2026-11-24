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
        ("agent.py", "feat(agent): full 27-tool suite with jailbreak_probe and Ponytail tool selector"),
        ("jailbreaks_loader.py", "feat(jailbreaks): dynamic loader for 53 red-team prompts across 19 vendors"),
        ("scripts/test_jailbreaks.py", "feat(scripts): automated AI red-teaming and prompt-injection bug finder"),
        ("start.bat", "chore(launcher): v2.6 1-click launcher with git submodule update and 7-stage bootstrap"),
        ("start.sh", "chore(launcher): linux/macOS v2.6 launcher with 7-stage submodule setup"),
        ("docs/CTF_AGENT_MASTER_ARCHITECTURE_AND_OPERATIONS_MANUAL.md", "docs(architecture): add master architecture with Section 7 jailbreak probe"),
        ("docs/CTF_TOOL_COMPARISON_AND_RATING.md", "docs(review): tool before vs after comparison and detailed 8.8/10 rating"),
        ("docs/CTF_TOOL_INTEGRATION_MAP.md", "docs(tools): complete specification map of all 27 integrated agent tools"),
        ("README.md", "docs: update README with v2.6 architecture and full toolset links")
    ]

    for rel_path, msg in files_to_push:
        push_file_via_mcp(rel_path, msg)
