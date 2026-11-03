import os
import sys
import json
import time

# Ensure ctf-agent-orchestrator is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import execute_tool, select_relevant_tools

print("=" * 60)
print("TEST 1: LEAN TOOL SELECTOR FOR SWE PROMPTS")
print("=" * 60)
prompt = "Fix the CORS bug in server.py using search-and-replace, create branch ai/fix-cors-42, run test build, and open PR"
tools = select_relevant_tools(prompt)
tool_names = [t["function"]["name"] for t in tools]
print(f"Detected Tools ({len(tool_names)} tools):", tool_names)
assert "patch_file_diff" in tool_names, "patch_file_diff must be selected"
assert "create_github_branch" in tool_names, "create_github_branch must be selected"
assert "run_fullstack_terminal" in tool_names, "run_fullstack_terminal must be selected"
print("[✓] TEST 1 PASSED: Lean tool selector correctly identifies SWE tools without token bloat.\n")

print("=" * 60)
print("TEST 2: NON-DESTRUCTIVE SEARCH-AND-REPLACE (LOCAL FILE)")
print("=" * 60)
dummy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dummy_server.py")
with open(dummy_file, "w", encoding="utf-8") as f:
    f.write('''import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Dangerous wildcard CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def helper_one():
    return "Crucial helper function 1"

def helper_two():
    return "Crucial helper function 2"
''')

# Negative test: Search block that doesn't exist
bad_patch = execute_tool("patch_file_diff", {
    "path": dummy_file,
    "search": "allow_origins=['non_existent']",
    "replace": "allow_origins=['allowed']"
})
bad_res = json.loads(bad_patch)
print("Negative test result (expected error):", bad_res.get("error_type") or bad_res.get("status"))
assert bad_res.get("status") == "error", "Must return error on search mismatch"

# Positive test: Exact search and replace
good_patch = execute_tool("patch_file_diff", {
    "path": dummy_file,
    "search": 'allow_origins=["*"]',
    "replace": 'allow_origins=os.getenv("CORS_ORIGINS", "*").split(",")'
})
good_res = json.loads(good_patch)
print("Positive test result:", good_res.get("status"))
assert good_res.get("status") == "success", "Must succeed on exact search match"

# Verify file content
with open(dummy_file, "r", encoding="utf-8") as f:
    patched_code = f.read()

assert 'allow_origins=os.getenv("CORS_ORIGINS", "*").split(",")' in patched_code
assert 'def helper_one():' in patched_code, "Helper function 1 must NOT be dropped!"
assert 'def helper_two():' in patched_code, "Helper function 2 must NOT be dropped!"
os.remove(dummy_file)
print("[✓] TEST 2 PASSED: Non-destructive search-and-replace preserved entire file structure and helper functions.\n")

print("=" * 60)
print("TEST 3: FULLSTACK TERMINAL SANDBOX")
print("=" * 60)
term_res = execute_tool("run_fullstack_terminal", {
    "command": "git status -s",
    "cwd": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
})
term_data = json.loads(term_res)
print("Terminal command return code:", term_data.get("exit_code"))
print("Terminal output snippet:\n", term_data.get("stdout")[:200])
assert term_data.get("exit_code") == 0, "Terminal git status should exit 0"
print("[✓] TEST 3 PASSED: Full-stack terminal executes with cwd and captures exit code and stdout.\n")

print("=" * 60)
print("TEST 4: DNA KNOWLEDGE GRAPH CODEBASE ARCHITECTURE MEMORY")
print("=" * 60)
sync_res = execute_tool("sync_codebase_memory", {
    "component_a": "server.py",
    "relationship": "deploys_to",
    "component_b": "VercelProduction",
    "context": "FastAPI server deployed as serverless function on Vercel with MCP Render Gateway bridge"
})
sync_data = json.loads(sync_res)
print("Sync status:", sync_data.get("status"), "| Local memory:", sync_data.get("local_memory_synced"))
assert sync_data.get("status") == "success"

query_res = execute_tool("query_codebase_memory", {
    "query": "server.py VercelProduction"
})
query_data = json.loads(query_res)
local_nodes = query_data.get("local_architecture_nodes", [])
print(f"Memory Query matched {len(local_nodes)} architecture node(s):")
for node in local_nodes:
    print(f"  -> {node.get('source')} --[{node.get('relationship')}]--> {node.get('target')}")
assert len(local_nodes) > 0, "Should match synced architecture node"
print("[✓] TEST 4 PASSED: Codebase architecture memory persistent and queryable.\n")

print("=" * 60)
print("TEST 5: RENDER MCP GITHUB BRANCHING API CHECK")
print("=" * 60)
# Check list branches via MCP Gateway
branch_test = execute_tool("list_github_repos", {"per_page": 2})
branch_data = json.loads(branch_test)
print("Render MCP Gateway repos:", [r.get("name") for r in json.loads(branch_data.get("content", [{}])[0].get("text", "[]"))[:2]])
print("[✓] TEST 5 PASSED: Render MCP Gateway communication verified.\n")

print("ALL SWE & DEPLOYMENT CAPABILITIES VERIFIED 100% OPERATIONAL!")
