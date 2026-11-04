"""
CTF Performance & Memory Optimizer Patch
-----------------------------------------
Applies the 3 critical CTF-performance fixes:
1. SESSION_MEMORY LRU bounding (prevents memory leak in long competitions)
2. interactive_socket_probe multi-turn & buffer draining (handles real CTF menus & large outputs)
3. ctfd_speed_listener instant cache-diff (eliminates 60s dashboard freeze)
4. Localhost secure binding in server.py (127.0.0.1)
"""
import os, sys, re
from collections import OrderedDict

BASE_DIR = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator"
AGENT_PATH = os.path.join(BASE_DIR, "agent.py")
SERVER_PATH = os.path.join(BASE_DIR, "server.py")
START_BAT_PATH = os.path.join(BASE_DIR, "start.bat")
START_SH_PATH = os.path.join(BASE_DIR, "start.sh")

# =========================================================================
# 1. PATCH agent.py - SESSION_MEMORY
# =========================================================================
with open(AGENT_PATH, "r", encoding="utf-8") as f:
    src_agent = f.read()

old_session = """# =========================================================================
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
        del SESSION_MEMORY[session_id]"""

new_session = """# =========================================================================
# MULTI-TURN SESSION MEMORY (Capped LRU Cache — Prevents CTF Memory Leaks)
# =========================================================================
from collections import OrderedDict

MAX_ACTIVE_SESSIONS = 50
SESSION_MEMORY: OrderedDict[str, List[dict]] = OrderedDict()

def get_session_history(session_id: str) -> List[dict]:
    if not session_id or session_id not in SESSION_MEMORY:
        return []
    SESSION_MEMORY.move_to_end(session_id)
    return SESSION_MEMORY[session_id]

def save_session_history(session_id: str, history: List[dict]):
    if session_id:
        # Keep last 24 message turns to preserve context window
        SESSION_MEMORY[session_id] = history[-24:]
        SESSION_MEMORY.move_to_end(session_id)
        # Evict oldest sessions when exceeding cap
        while len(SESSION_MEMORY) > MAX_ACTIVE_SESSIONS:
            SESSION_MEMORY.popitem(last=False)

def clear_session_history(session_id: str):
    SESSION_MEMORY.pop(session_id, None)"""

assert old_session in src_agent, "old_session pattern not found"
src_agent = src_agent.replace(old_session, new_session, 1)
print("✅ [1/4] SESSION_MEMORY LRU bounding applied")

# =========================================================================
# 2. PATCH agent.py - interactive_socket_probe
# =========================================================================
old_socket = """    # 11. INTERACTIVE TCP / NETCAT SOCKET CLIENT
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
                    send_bytes = (payload + "\\n").encode("utf-8")
                s.sendall(send_bytes)
                time.sleep(0.3)
                try:
                    resp_raw = s.recv(4096)
                    response = resp_raw.decode("latin-1", errors="ignore")
                except Exception:
                    pass

            s.close()
            combined = banner + "\\n" + response
            flags = re.findall(r"(?:HQX|flag|CTF|hackquest)\\{[^}]+\\}", combined, re.IGNORECASE)

            return json.dumps({
                "status": "connected",
                "host": host,
                "port": port,
                "banner": banner[:1000],
                "response": response[:1000],
                "flags_found": list(set(flags))
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Socket connection to {host}:{port} failed: {str(e)}"})"""

new_socket = """    # 11. INTERACTIVE TCP / NETCAT SOCKET CLIENT (Multi-Turn Dialog & Stream Draining)
    elif tool_name == "interactive_socket_probe":
        host = tool_input.get("host", "").strip()
        port = int(tool_input.get("port", 0))
        payload = tool_input.get("payload", "")
        dialog = tool_input.get("dialog") or []
        timeout = float(tool_input.get("timeout_seconds", 6.0))

        if not host or not port:
            return json.dumps({"error": "host and port are required"})

        import socket
        import select

        def drain_socket(sock, max_bytes=65536, max_idle=0.4):
            buf = bytearray()
            while len(buf) < max_bytes:
                r, _, _ = select.select([sock], [], [], max_idle)
                if not r:
                    break
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf.extend(chunk)
                except Exception:
                    break
            return buf.decode("latin-1", errors="replace")

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))

            # Read initial banner
            banner = drain_socket(s, max_idle=0.3)
            dialog_transcript = []

            # Multi-turn interaction support: list of commands or multi-line payload
            commands = []
            if dialog and isinstance(dialog, list):
                commands = dialog
            elif payload:
                if payload.startswith("hex:"):
                    commands = [payload]
                else:
                    commands = [line for line in payload.splitlines() if line != ""]

            accumulated_response = []
            for cmd in commands:
                if str(cmd).startswith("hex:"):
                    s.sendall(bytes.fromhex(cmd[4:]))
                else:
                    s.sendall((str(cmd) + "\\n").encode("utf-8"))
                time.sleep(0.15)
                turn_resp = drain_socket(s, max_idle=0.4)
                dialog_transcript.append({"sent": str(cmd)[:200], "received": turn_resp[:1000]})
                accumulated_response.append(turn_resp)

            s.close()
            full_text = banner + "\\n" + "\\n".join(accumulated_response)
            flag_regex = re.compile(
                r"(?:HQX|flag|CTF|picoCTF|hackquest|HTB|SECCON|hitcon|google|rwctf)\\{[^}\\n\\r\\t ]+\\}",
                re.IGNORECASE
            )
            flags = flag_regex.findall(full_text)

            return json.dumps({
                "status": "connected",
                "host": host,
                "port": port,
                "banner": banner[:1000],
                "turns_completed": len(dialog_transcript),
                "dialog_transcript": dialog_transcript[:10],
                "response": full_text[-2000:] if len(full_text) > 2000 else full_text,
                "flags_found": list(set(flags))
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Socket connection to {host}:{port} failed: {str(e)}"})"""

assert old_socket in src_agent, "old_socket pattern not found"
src_agent = src_agent.replace(old_socket, new_socket, 1)
print("✅ [2/4] interactive_socket_probe multi-turn & buffer draining applied")

# =========================================================================
# 3. PATCH agent.py - ctfd_speed_listener instant cache diff
# =========================================================================
old_ctfd = """        # Baseline snapshot
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
            polls_done += 1"""

new_ctfd = """        # Instant baseline diff using cached state to prevent 60s server freeze
        t0 = time.time()
        cache_file = os.path.join(save_dir, ".ctfd_challenges_cache.json")
        cached_baseline = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as cf:
                    cached_baseline = json.load(cf)
            except Exception:
                cached_baseline = {}

        current_snapshot, code = fetch_challenges()
        if current_snapshot is None:
            return json.dumps({"error": f"Could not reach CTFd: {code}"})

        # Save latest snapshot to cache
        try:
            with open(cache_file, "w", encoding="utf-8") as cf:
                json.dump(current_snapshot, cf)
        except Exception:
            pass

        # If max_polls is 1 or baseline exists, perform INSTANT zero-wait diff
        baseline = cached_baseline if cached_baseline else current_snapshot
        new_challenges = []
        polls_done = 1

        # Check instant diff
        for cid, chal in current_snapshot.items():
            if cid not in baseline:
                new_chal = dict(chal)
                new_chal["detected_instantly"] = True
                new_chal["elapsed_seconds"] = round(time.time() - t0, 3)
                new_challenges.append(new_chal)

        # If user explicitly asked for a polling watch and no new challenge found yet:
        if not new_challenges and max_polls > 1:
            for poll in range(1, max_polls):
                time.sleep(poll_interval)
                current_snapshot, code = fetch_challenges()
                if current_snapshot is None:
                    continue
                polls_done += 1
                for cid, chal in current_snapshot.items():
                    if cid not in baseline:
                        new_chal = dict(chal)
                        new_chal["detected_at_poll"] = poll + 1
                        new_chal["elapsed_seconds"] = round(time.time() - t0, 2)
                        new_challenges.append(new_chal)
                if new_challenges:
                    break"""

assert old_ctfd in src_agent, "old_ctfd pattern not found"
src_agent = src_agent.replace(old_ctfd, new_ctfd, 1)

with open(AGENT_PATH, "w", encoding="utf-8") as f:
    f.write(src_agent)
print("✅ [3/4] ctfd_speed_listener instant cache diff applied")

# =========================================================================
# 4. PATCH server.py & start scripts - 127.0.0.1 localhost binding
# =========================================================================
with open(SERVER_PATH, "r", encoding="utf-8") as f:
    src_server = f.read()

src_server = src_server.replace(
    'uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)',
    'host_bind = os.getenv("HOST", "127.0.0.1")\\n    uvicorn.run("server:app", host=host_bind, port=port, reload=True)'
)
with open(SERVER_PATH, "w", encoding="utf-8") as f:
    f.write(src_server)

# start.bat
with open(START_BAT_PATH, "r", encoding="utf-8") as f:
    src_bat = f.read()
src_bat = src_bat.replace("--host 0.0.0.0", "--host 127.0.0.1")
with open(START_BAT_PATH, "w", encoding="utf-8") as f:
    f.write(src_bat)

# start.sh
with open(START_SH_PATH, "r", encoding="utf-8") as f:
    src_sh = f.read()
src_sh = src_sh.replace("--host 0.0.0.0", "--host 127.0.0.1")
with open(START_SH_PATH, "w", encoding="utf-8") as f:
    f.write(src_sh)

print("✅ [4/4] Secure 127.0.0.1 local binding applied across server.py, start.bat, and start.sh")

# Verify syntax
import ast
ast.parse(src_agent)
ast.parse(src_server)
print("\n🎉 ALL SYNTAX VERIFIED CLEAN! Patches applied successfully.")
