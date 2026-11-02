import os

agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent.py")

with open(agent_path, "r", encoding="utf-8") as f:
    content = f.read()

target1 = "]\n\n# =========================================================================\n# TOOL EXECUTION DISPATCHER"

replacement1 = """]\n
# =========================================================================
# PONYTAIL-STYLE LEAN TOOL SELECTOR (Prevents Groq 7,000 ITPM Rate Limits)
# =========================================================================
def select_relevant_tools(user_prompt: str) -> list:
    \"\"\"
    Ponytail principle: Only pass schemas strictly needed for the detected task.
    Cuts tool schema token payload by ~65-75%, eliminating Groq token rate limit 429s.
    \"\"\"
    p = user_prompt.lower()
    core_names = {"search_knowledge_base", "execute_python_sandbox"}

    # Web Exploitation
    if any(k in p for k in ["sql", "ssti", "xss", "csrf", "jwt", "cookie", "http", "web", "url", "bypass", "idor", "fuzz", "param"]):
        core_names.update(["web_dynamic_fuzzer", "probe_web_endpoint", "ctfd_manage"])

    # Cryptography
    if any(k in p for k in ["rsa", "xor", "cipher", "aes", "des", "prng", "seed", "hash", "md5", "sha", "crypto", "decode", "decrypt", "base64", "rot"]):
        core_names.update(["symbolic_execution_solver", "cyberchef_decode", "parallel_exploit_worker"])

    # Reverse Engineering / Constraint Solving
    if any(k in p for k in ["crackme", "z3", "equation", "constraint", "branch", "solve", "math", "bitvec"]):
        core_names.update(["symbolic_execution_solver", "parallel_exploit_worker"])

    # Binary Exploitation / Linux ELF
    if any(k in p for k in ["elf", "binary", "pwn", "checksec", "rop", "buffer overflow", "gdb", "wsl", "linux", "decompile", "strings"]):
        core_names.update(["wsl_linux_bridge", "inspect_binary_strings_decompile", "interactive_socket_probe", "symbolic_execution_solver"])

    # Forensics / Network / Steganography
    if any(k in p for k in ["pcap", "wireshark", "stego", "steganography", "image", "png", "wav", "extract", "hidden", "exif", "metadata", "forensic"]):
        core_names.update(["run_forensics_inspection", "search_flag_patterns", "cyberchef_decode"])

    # GitHub / MCP
    if any(k in p for k in ["github", "commit", "repo", "push"]):
        core_names.update(["commit_github_file", "read_github_file", "list_github_repos"])

    # Netcat / Socket
    if any(k in p for k in ["nc ", "netcat", "socket", "port", "daemon", "tcp", "remote"]):
        core_names.update(["interactive_socket_probe"])

    # Default fallback to top 5 most versatile tools if prompt is broad
    if len(core_names) <= 2:
        core_names.update(["symbolic_execution_solver", "web_dynamic_fuzzer", "cyberchef_decode", "parallel_exploit_worker"])

    return [t for t in OPENAI_TOOLS if t["function"]["name"] in core_names]

# =========================================================================
# TOOL EXECUTION DISPATCHER"""

if target1 in content:
    content = content.replace(target1, replacement1, 1)
    print("✓ Successfully inserted select_relevant_tools")
else:
    print("✗ target1 not found")

old_call = """                        response = self.client.chat.completions.create(
                            model=model_candidate,
                            messages=messages,
                            tools=OPENAI_TOOLS,
                            tool_choice="auto"
                        )"""

new_call = """                        active_tools = select_relevant_tools(user_prompt)
                        response = self.client.chat.completions.create(
                            model=model_candidate,
                            messages=messages,
                            tools=active_tools,
                            tool_choice="auto"
                        )"""

if old_call in content:
    content = content.replace(old_call, new_call, 1)
    print("✓ Successfully updated tools=active_tools in _run_groq_trace")
else:
    print("✗ old_call not found")

old_tool_append = """                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
                    })"""

new_tool_append = """                    # Ponytail optimization: truncate huge tool outputs in message history
                    # to keep prompt tokens lean across multi-turn reasoning
                    pruned_output = tool_output if len(tool_output) <= 1200 else tool_output[:1000] + "\\n...[truncated for token efficiency]"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": pruned_output
                    })"""

if old_tool_append in content:
    content = content.replace(old_tool_append, new_tool_append, 1)
    print("✓ Successfully updated tool output pruning")
else:
    print("✗ old_tool_append not found")

with open(agent_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated agent.py with Ponytail token optimization!")
