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
    Controlled path resolver for the Forensic Engine.
    Prioritizes the exact local installation at c:\Users\SGI\Downloads\forensic
    while safely supporting environment overrides and relative fallbacks.
    """
    candidates = [
        r"c:\Users\SGI\Downloads\forensic",
        os.getenv("FORENSIC_DIR", ""),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forensic"),
        os.path.join(os.getcwd(), "forensic")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return r"c:\Users\SGI\Downloads\forensic"

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
    }
]

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
            
            result = {
                "status": "success" if ret == 0 else "error",
                "returncode": ret,
                "elapsed_seconds": elapsed,
                "stdout": out[-2000:] if len(out) > 2000 else out,
                "stderr": err[-1000:] if len(err) > 1000 else err,
                "flags_captured": list(set(found_flags))
            }
            return json.dumps(result, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"Execution timed out after {timeout} seconds"}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Sandbox execution failed: {str(e)}"}, indent=2)
        finally:
            try:
                os.remove(tmp_name)
            except Exception:
                pass

    # 7. FORENSICS SANDBOX ENGINE (Controlled Path Safe)
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
            return resp.text
        except Exception as err:
            return json.dumps({"error": f"MCP Gateway call failed: {err}"})

    # 10. CTFD PLATFORM MANAGER (Autonomous Challenge Fetching & Flag Submission)
    elif tool_name == "ctfd_manage":
        action = tool_input.get("action", "list_challenges")
        ctfd_url = tool_input.get("ctfd_url", "").rstrip("/")
        token = tool_input.get("token", "").strip()
        challenge_id = tool_input.get("challenge_id")
        flag = tool_input.get("flag", "").strip()

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
                    data = r.json().get("data", [])
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
                return json.dumps({"status": "error", "code": r.status_code, "response": r.text})

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
            "3. Use your specialized tools (CyberChef decoder, Binary Strings & Decompiler inspector, Web probe, Forensic Engine, Netcat Socket probe, CTFd manager). "
            "4. Verify your exploits autonomously using execute_python_sandbox before returning your answer! You can use z3 (from z3 import *), pycryptodome, sympy, and randcrack directly! "
            "5. If you find a new attack relationship, register it with sync_dna_attack_tree. "
            "6. Remember all past clues, keys, and findings across conversational session turns. "
            "7. Output clean, runnable exploit code and the extracted flag (format: HQX{...}, flag{...}, or CTF{...})."
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

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output
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
