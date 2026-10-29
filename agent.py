import os
import json
import requests
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()
RAG_URL = os.getenv("RAG_URL", "http://localhost:8001").strip()
HF_URL = os.getenv("HF_KNOWLEDGE_URL", "https://outstandingom-knowledge-graph-env.hf.space").strip()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://mcp-server-2sl7.onrender.com").strip()
MCP_API_KEY = os.getenv("MCP_API_KEY", "").strip()

# Tool Definitions for Claude
TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Searches the CTF Knowledge Base and Hugging Face Knowledge Graph for challenge writeups, cryptographic patterns (PRNG, XOR), and exploit templates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or challenge description (e.g. 'time based random seed', 'zero width steganography', 'JWT bypass')"
                },
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter: Cryptography, Forensics, Web, Binary"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_github_file",
        "description": "Reads a code file from your GitHub repositories via your Render MCP Gateway.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name (e.g. MCP-SERVER, forensic)"},
                "path": {"type": "string", "description": "File path (e.g. README.md, solver.py)"},
                "branch": {"type": "string", "description": "Branch name (optional, default: main)"}
            },
            "required": ["repo", "path"]
        }
    },
    {
        "name": "commit_github_file",
        "description": "Commits a new file or updates an existing solver/writeup script to GitHub via Render MCP Gateway.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name"},
                "path": {"type": "string", "description": "Path to create/update"},
                "content": {"type": "string", "description": "Complete text content of the file"},
                "message": {"type": "string", "description": "Commit message"}
            },
            "required": ["repo", "path", "content", "message"]
        }
    },
    {
        "name": "list_github_repos",
        "description": "Lists repositories accessible to your GitHub account via Render MCP Gateway.",
        "input_schema": {
            "type": "object",
            "properties": {
                "per_page": {"type": "integer", "description": "Number of repos to return (default 10)"}
            }
        }
    }
]

# Tool Executors
def execute_tool(tool_name: str, tool_input: dict) -> str:
    print(f"\n[AGENT TOOL CALL] Executing: {tool_name}({json.dumps(tool_input)})")

    if tool_name == "search_knowledge_base":
        query = tool_input.get("query", "")
        domain = tool_input.get("domain")

        # Try local RAG first
        try:
            res = requests.post(
                f"{RAG_URL}/query",
                json={"query": query, "domain": domain, "top_k": 3},
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                return json.dumps(data.get("results", []))
        except Exception as e:
            print(f"[RAG fallback] Local RAG offline ({e}), querying Hugging Face Knowledge Graph...")

        # Fallback to Hugging Face Space
        try:
            hf_res = requests.post(
                f"{HF_URL}/search/essence",
                json={"text": query, "top_k": 3},
                timeout=10
            )
            if hf_res.status_code == 200:
                return hf_res.text
        except Exception as hf_err:
            return json.dumps({"error": f"Knowledge base unreachable: {hf_err}"})

    elif tool_name in ["read_github_file", "commit_github_file", "list_github_repos"]:
        # Map to Render MCP Server /api/test-tool endpoint
        tool_map = {
            "read_github_file": "read_file",
            "commit_github_file": "create_or_update_file",
            "list_github_repos": "list_repositories"
        }
        target_tool = tool_map[tool_name]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MCP_API_KEY}"
        }
        try:
            resp = requests.post(
                f"{MCP_SERVER_URL}/api/test-tool",
                headers=headers,
                json={"tool": target_tool, "params": tool_input},
                timeout=15
            )
            return resp.text
        except Exception as err:
            return json.dumps({"error": f"MCP Gateway call failed: {err}"})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})

class CTFOrchestratorAgent:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not configured in .env")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.system_prompt = (
            "You are an expert Autonomous Cybersecurity & CTF Copilot Agent. "
            "You help reverse-engineer challenges, extract flags, write Python solvers, and commit solutions to GitHub. "
            "When given a challenge: "
            "1. Query the knowledge base for known patterns and writeups. "
            "2. Formulate an actionable hypothesis. "
            "3. Generate complete, executable Python solution code. "
            "4. If requested, save/commit the solver directly to GitHub via your MCP tools."
        )

    def run(self, user_prompt: str, max_turns: int = 5) -> str:
        messages = [{"role": "user", "content": user_prompt}]
        print(f"\n[CTF AGENT STARTED] Model: {CLAUDE_MODEL}")
        print(f"Task: {user_prompt}\n" + "-"*50)

        for turn in range(max_turns):
            try:
                response = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=2048,
                    system=self.system_prompt,
                    tools=TOOLS,
                    messages=messages
                )
            except anthropic.BadRequestError as e:
                if "credit balance is too low" in str(e):
                    return (
                        f"[ANTHROPIC BILLING NOTICE] Your Anthropic API Key is valid, but your account credit balance is $0.\n"
                        f"Please add credits at https://console.anthropic.com/settings/plans to enable Claude execution."
                    )
                raise e

            # Check if model wants to call tools
            if response.stop_reason == "tool_use":
                # Find tool use blocks
                tool_results = []
                assistant_content = response.content

                # Append assistant message
                messages.append({"role": "assistant", "content": assistant_content})

                for block in assistant_content:
                    if block.type == "tool_use":
                        output = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output
                        })

                # Append tool response
                messages.append({"role": "user", "content": tool_results})
            else:
                # Agent completed answer
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                return final_text

        return "Agent reached maximum execution turns."

if __name__ == "__main__":
    agent = CTFOrchestratorAgent()
    prompt = "I have a cryptography challenge where a token is generated by random.seed(int(time.time())). Search our past writeups for how to break this, and give me a complete Python solver."
    result = agent.run(prompt)
    print("\n[AGENT FINAL OUTPUT]:\n")
    print(result)
