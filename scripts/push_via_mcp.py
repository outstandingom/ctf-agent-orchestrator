import os
import sys
import json

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agent import execute_tool

def push_file_via_mcp(repo_name, rel_path, commit_message):
    full_path = os.path.join(current_dir, rel_path)
    with open(full_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    print(f"\n[MCP PUSH] Uploading {rel_path} to {repo_name} via Render MCP Gateway...")
    payload = {
        "repo": repo_name,
        "path": rel_path.replace("\\", "/"),
        "content": file_content,
        "message": commit_message
    }
    res_str = execute_tool("commit_github_file", payload)
    print(f"[MCP PUSH RESULT]: {res_str}")
    return res_str

if __name__ == "__main__":
    # 1. Push COMPLETE_USER_GUIDE.md via MCP Gateway
    push_file_via_mcp(
        "ctf-agent-orchestrator",
        "docs/COMPLETE_USER_GUIDE.md",
        "docs: update operational manual with Dynamic Fuzzer, Z3 SMT, WSL2 bridge, and Ponytail token engine"
    )

    # 2. Push README.md via MCP Gateway
    push_file_via_mcp(
        "ctf-agent-orchestrator",
        "README.md",
        "docs: update README with complete system architecture and Google CTF test playbooks"
    )
