import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower().strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()

RAG_URL = os.getenv("RAG_URL", "http://localhost:8001").strip()
HF_VECTOR_URL = os.getenv("HF_VECTOR_URL", "https://outstandingom-vector.hf.space").strip()
HF_URL = os.getenv("HF_KNOWLEDGE_URL", "https://outstandingom-knowledge-graph-env.hf.space").strip()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://mcp-server-2sl7.onrender.com").strip()
MCP_API_KEY = os.getenv("MCP_API_KEY", "").strip()

# Universal Tool Definitions (OpenAI / Groq Format)
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the CTF Knowledge Base on Hugging Face Spaces (ZeroGPU) and Knowledge Graph for challenge writeups, cryptographic patterns (PRNG, XOR), and exploit templates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Challenge prompt or keywords (e.g. 'time based random seed', 'zero width steganography')"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional domain filter: Cryptography, Forensics, Web"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_forensics_inspection",
            "description": "Executes the Forensic Sandbox Engine on a file to inspect file integrity, detect steganography / hidden zip archives, and compute cryptographic hashes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Local path to the target file to inspect"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_flag_patterns",
            "description": "Scans raw text or a file for standard CTF flag formats (flag{...}, CTF{...}), base64 strings, and invisible unicode zero-width characters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Raw string content to scan"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional file path to read and scan"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_github_file",
            "description": "Reads a code file from your GitHub repositories via your Render MCP Gateway.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name (e.g. MCP-SERVER, forensic, ctf-vector-rag)"},
                    "path": {"type": "string", "description": "File path (e.g. README.md, solver.py)"},
                    "branch": {"type": "string", "description": "Branch name (optional, default: main)"}
                },
                "required": ["repo", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "commit_github_file",
            "description": "Commits a new file or updates an existing solver/writeup script to GitHub via Render MCP Gateway.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "Path to create/update"},
                    "content": {"type": "string", "description": "Complete text content of the file"},
                    "message": {"type": "string", "description": "Commit message"}
                },
                "required": ["repo", "path", "content", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_repos",
            "description": "Lists repositories accessible to your GitHub account via Render MCP Gateway.",
            "parameters": {
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "description": "Number of repos to return (default 10)"}
                }
            }
        }
    }
]

def execute_tool(tool_name: str, tool_input: dict) -> str:
    print(f"\n[AGENT TOOL CALL] Executing: {tool_name}({json.dumps(tool_input)})")

    if tool_name == "search_knowledge_base":
        query = tool_input.get("query", "")
        domain = tool_input.get("domain", "All")

        # 1. Primary: High-Memory Hugging Face ZeroGPU Vector Space
        try:
            call_res = requests.post(
                f"{HF_VECTOR_URL}/gradio_api/call/query",
                json={"data": [query, domain if domain else "All", 3]},
                timeout=12
            )
            if call_res.status_code == 200:
                event_id = call_res.json().get("event_id")
                if event_id:
                    res = requests.get(f"{HF_VECTOR_URL}/gradio_api/call/query/{event_id}", timeout=12)
                    for line in res.text.split("\n"):
                        if line.startswith("data:"):
                            parsed = json.loads(line[5:].strip())
                            print("[TOOL] Hugging Face Vector Space (ZeroGPU) returned matching writeups.")
                            return str(parsed[0])
        except Exception as e:
            print(f"[RAG fallback] HF Vector Space unavailable ({e}), trying local RAG...")

        # 2. Secondary: Local RAG (port 8001)
        try:
            res = requests.post(
                f"{RAG_URL}/query",
                json={"query": query, "domain": domain if domain != "All" else None, "k": 3},
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                print(f"[TOOL] Local RAG found {len(data.get('results', []))} results.")
                return json.dumps(data.get("results", []))
        except Exception as e:
            print(f"[RAG fallback] Local RAG offline ({e}), querying Hugging Face Knowledge Graph...")

        # 3. Tertiary: Hugging Face DNA Knowledge Graph
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

    elif tool_name == "run_forensics_inspection":
        file_path = tool_input.get("file_path", "")
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})
        try:
            import sys
            forensic_dir = r"c:\Users\SGI\Downloads\forensic"
            if forensic_dir not in sys.path:
                sys.path.insert(0, forensic_dir)
            from forensic_engine.engine import ForensicEngine
            engine = ForensicEngine()
            report = engine.process_file(file_path)
            print(f"[TOOL] ForensicEngine processed {os.path.basename(file_path)} successfully.")
            return json.dumps(report, indent=2)
        except Exception as err:
            return json.dumps({"error": f"ForensicEngine error: {err}"})

    elif tool_name == "search_flag_patterns":
        import re
        text = tool_input.get("text", "")
        file_path = tool_input.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text += "\n" + f.read()

        flags = re.findall(r"(?:flag|CTF|hackquest)\{[^}]+\}", text, re.IGNORECASE)
        b64_matches = re.findall(r"(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?", text)
        zero_width = [char for char in text if char in ['\u200b', '\u200c', '\u200d', '\ufeff']]

        result = {
            "flags_found": list(set(flags)),
            "b64_candidates": list(set(b64_matches))[:5],
            "zero_width_chars_count": len(zero_width)
        }
        print(f"[TOOL] Flag Pattern Search found {len(result['flags_found'])} flags and {len(zero_width)} zero-width chars.")
        return json.dumps(result, indent=2)

    elif tool_name in ["read_github_file", "commit_github_file", "list_github_repos"]:
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
            print(f"[TOOL] Render MCP Gateway responded successfully.")
            return resp.text
        except Exception as err:
            return json.dumps({"error": f"MCP Gateway call failed: {err}"})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})

class CTFOrchestratorAgent:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.system_prompt = (
            "You are an expert Autonomous Cybersecurity & CTF Copilot Agent. "
            "You help reverse-engineer challenges, extract flags, write Python solvers, and commit solutions to GitHub. "
            "When given a challenge: "
            "1. Query the knowledge base for known patterns and writeups. "
            "2. Formulate an actionable hypothesis. "
            "3. Generate complete, executable Python solution code. "
            "4. If requested, save/commit the solver directly to GitHub via your MCP tools."
        )

        if self.provider == "groq":
            from openai import OpenAI
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is missing in .env")
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY
            )
            self.model = GROQ_MODEL
        else:
            import anthropic
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is missing in .env")
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = CLAUDE_MODEL

    def run(self, user_prompt: str, max_turns: int = 10) -> str:
        trace_result = self.run_with_trace(user_prompt, max_turns)
        return trace_result.get("final_answer", "")

    def run_with_trace(self, user_prompt: str, max_turns: int = 10) -> dict:
        print(f"\n[CTF AGENT STARTED] Engine: {self.provider.upper()} | Model: {self.model}", flush=True)
        print(f"Task: {user_prompt}\n" + "-"*50, flush=True)

        trace = []
        if self.provider == "groq":
            final_ans = self._run_groq_trace(user_prompt, max_turns, trace)
        else:
            final_ans = self._run_anthropic_trace(user_prompt, max_turns, trace)

        return {
            "final_answer": final_ans,
            "trace": trace,
            "provider": self.provider,
            "model": self.model
        }

    def _run_groq_trace(self, user_prompt: str, max_turns: int, trace: list) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for turn in range(max_turns):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=OPENAI_TOOLS,
                tool_choice="auto"
            )

            msg = response.choices[0].message
            messages.append(msg)

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except:
                        fn_args = {}

                    tool_output = execute_tool(fn_name, fn_args)
                    trace.append({
                        "turn": turn + 1,
                        "type": "tool_call",
                        "tool": fn_name,
                        "args": fn_args,
                        "output": tool_output
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
                    })
            else:
                return msg.content or ""

        return "Agent reached maximum execution turns."

    def _run_anthropic_trace(self, user_prompt: str, max_turns: int, trace: list) -> str:
        import anthropic
        claude_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"]
            }
            for t in OPENAI_TOOLS
        ]

        messages = [{"role": "user", "content": user_prompt}]

        for turn in range(max_turns):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=self.system_prompt,
                    tools=claude_tools,
                    messages=messages
                )
            except anthropic.BadRequestError as e:
                if "credit balance is too low" in str(e):
                    return "[ANTHROPIC BILLING NOTICE] Balance $0. Switch LLM_PROVIDER=groq in .env to run on Groq."
                raise e

            if response.stop_reason == "tool_use":
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        output = execute_tool(block.name, block.input)
                        trace.append({
                            "turn": turn + 1,
                            "type": "tool_call",
                            "tool": block.name,
                            "args": block.input,
                            "output": output
                        })
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                final_text = "".join([b.text for b in response.content if b.type == "text"])
                return final_text

        return "Agent reached maximum execution turns."

if __name__ == "__main__":
    agent = CTFOrchestratorAgent()
    test_prompt = "I have a cryptography challenge where random.seed(int(time.time())) is used to generate the XOR key. Search our past writeups for how to break this and generate a complete Python solver script."
    result = agent.run(test_prompt)
    print("\n[AGENT FINAL OUTPUT]:\n")
    print(result)
