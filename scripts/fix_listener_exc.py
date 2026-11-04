"""Fix fetch_challenges() to wrap network errors, and fix Pollard p-1 test."""
AGENT_PATH = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\agent.py"

with open(AGENT_PATH, "r", encoding="utf-8") as f:
    src = f.read()

old = (
    "        def fetch_challenges():\n"
    "            r = session.get(f\"{ctfd_url}/api/v1/challenges\", timeout=8)\n"
    "            if r.status_code != 200:\n"
    "                return None, r.status_code\n"
    "            try:\n"
    "                data = r.json().get(\"data\", [])\n"
    "                return {str(c[\"id\"]): c for c in data}, 200\n"
    "            except Exception:\n"
    "                return None, -1\n"
    "\n"
    "        # Baseline snapshot\n"
    "        t0 = time.time()\n"
    "        baseline, code = fetch_challenges()\n"
    "        if baseline is None:\n"
    "            return json.dumps({\"error\": f\"Could not fetch challenges (HTTP {code})\"})\n"
)

new = (
    "        def fetch_challenges():\n"
    "            try:\n"
    "                r = session.get(f\"{ctfd_url}/api/v1/challenges\", timeout=8)\n"
    "                if r.status_code != 200:\n"
    "                    return None, r.status_code\n"
    "                data = r.json().get(\"data\", [])\n"
    "                return {str(c[\"id\"]): c for c in data}, 200\n"
    "            except Exception as _net_err:\n"
    "                return None, str(_net_err)\n"
    "\n"
    "        # Baseline snapshot\n"
    "        t0 = time.time()\n"
    "        baseline, code = fetch_challenges()\n"
    "        if baseline is None:\n"
    "            return json.dumps({\"error\": f\"Could not reach CTFd: {code}\"})\n"
)

assert old in src, f"Pattern not found! First 50 chars: {repr(old[:50])}"
src = src.replace(old, new, 1)

with open(AGENT_PATH, "w", encoding="utf-8") as f:
    f.write(src)

import ast
try:
    ast.parse(src)
    print("✅ Syntax OK after fetch_challenges fix")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
